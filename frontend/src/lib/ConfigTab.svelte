<script>
  import { onMount } from 'svelte';
  import { Plus, Search, Edit, Trash2, FolderOpen, Save, X } from 'lucide-svelte';
  import { GetApps, SaveApp, DeleteApp, SelectExeFromLocalPrograms, SelectFolderFromRoaming, SelectFolderFromLocalPrograms, GetPlatformInfo } from '../../wailsjs/go/main/App.js';
  import { confirm } from './ConfirmModal.svelte';
  import { toast } from './Toast.svelte';
  import { settings } from './stores/settings.js';

  export let logs = [];
  export let showAddDialog = false;

  let apps = [];
  let loading = false;
  let platformInfo = {};
  
  // Context menu state
  let contextMenu = { show: false, x: 0, y: 0, app: null };
  
  // Dialog mode: 'add' or 'edit'
  let dialogMode = 'add';
  let editingAppKey = null;
  
  // New app form
  let newApp = {
    app_name: '',
    display_name: '',
    exe_path: '',
    data_path: '',
    app_type: 'vscode', // 'vscode' or 'custom'
    backup_items: [],
    addon_paths: []
  };

  // VSCode preset backup items
  const vscodePresetItems = [
    { type: 'file', path: 'Preferences', description: 'Preferences', optional: false, enabled: true },
    { type: 'file', path: 'Local State', description: 'Local state', optional: false, enabled: true },
    { type: 'file', path: 'machineid', description: 'Machine ID', optional: false, enabled: true },
    { type: 'file', path: 'DIPS', description: 'DIPS', optional: false, enabled: true },
    { type: 'file', path: 'languagepacks.json', description: 'Language packs', optional: false, enabled: true },
    { type: 'folder', path: 'Network', description: 'Login/cookies', optional: false, enabled: true },
    { type: 'file', path: 'User/settings.json', description: 'User settings', optional: false, enabled: true },
    { type: 'file', path: 'User/globalStorage/state.vscdb', description: 'Global storage DB', optional: false, enabled: true },
    { type: 'file', path: 'User/globalStorage/storage.json', description: 'Global storage', optional: false, enabled: true },
    { type: 'file', path: 'User/globalStorage/state.vscdb.backup', description: 'Global storage DB backup', optional: false, enabled: true },
  ];

  // Custom backup item input
  let customItemPath = '';
  let customItemDesc = '';

  onMount(loadApps);

  onMount(async () => {
    try {
      platformInfo = await GetPlatformInfo();
    } catch (e) {
      platformInfo = {};
    }
  });

  onMount(() => {
    // Close context menu on click outside
    const handleClick = () => contextMenu.show = false;
    window.addEventListener('click', handleClick);
    return () => window.removeEventListener('click', handleClick);
  });

  async function loadApps() {
    loading = true;
    try {
      const allApps = (await GetApps()) || [];
      apps = await Promise.all(allApps.map(async (app) => {
        const installed = await CheckAppInstalled(app.app_name);
        return { ...app, installed };
      }));
    } catch (e) {
      log(`Error: ${e}`);
    }
    loading = false;
  }

  function log(msg) {
    const time = new Date().toLocaleTimeString();
    logs = [...logs.slice(-99), `[${time}] ${msg}`];
  }

  async function handleToggle(app) {
    try {
      await ToggleApp(app.app_name);
      log(`Toggled ${app.display_name}: ${app.active ? 'Inactive' : 'Active'}`);
      await loadApps();
    } catch (e) {
      log(`Error: ${e}`);
    }
  }

  async function handleDelete(app) {
    if ($settings.confirmBeforeDelete) {
      const confirmed = await confirm.delete(app.display_name);
      if (!confirmed) return;
    }
    
    try {
      await DeleteApp(app.app_name);
      log(`Deleted: ${app.display_name}`);
      await loadApps();
    } catch (e) {
      log(`Error: ${e}`);
    }
  }

  async function handleOpenFolder() {
    try {
      await OpenConfigFolder();
    } catch (e) {
      log(`Error: ${e}`);
    }
  }

  // Context menu handlers
  function handleContextMenu(event, app) {
    event.preventDefault();
    contextMenu = {
      show: true,
      x: event.clientX,
      y: event.clientY,
      app
    };
  }

  function closeContextMenu() {
    contextMenu.show = false;
  }

  async function handleOpenAppConfig(app) {
    try {
      // Open the config folder and let user find the JSON
      await OpenConfigFolder();
      log(`Opened config folder for ${app.display_name}`);
    } catch (e) {
      log(`Error: ${e}`);
    }
  }

  async function handleSetActive(app) {
    if (!app.active) {
      await handleToggle(app);
    }
  }

  async function handleSetInactive(app) {
    if (app.active) {
      await handleToggle(app);
    }
  }

  async function selectExe() {
    try {
      const path = await SelectExeFromLocalPrograms('Select Executable');
      if (path) {
        newApp.exe_path = path;
        // Only auto-fill app_name and display_name in add mode
        if (dialogMode === 'add') {
          const fileName = path.split(/[/\\]/).pop();
          const appName = fileName.replace('.exe', '');
          newApp.app_name = appName.toLowerCase();
          newApp.display_name = appName.charAt(0).toUpperCase() + appName.slice(1);
        }
      }
    } catch (e) {
      log(`Error: ${e}`);
    }
  }

  async function selectDataFolder() {
    try {
      const path = await SelectFolderFromRoaming('Select Data Folder');
      if (path) {
        newApp.data_path = path;
      }
    } catch (e) {
      log(`Error: ${e}`);
    }
  }

  async function addAddonFolder() {
    try {
      const path = await SelectFolderFromHome('Select Additional Folder');
      if (path && !newApp.addon_paths.includes(path)) {
        newApp.addon_paths = [...newApp.addon_paths, path];
      }
    } catch (e) {
      log(`Error: ${e}`);
    }
  }

  function removeAddonFolder(path) {
    newApp.addon_paths = newApp.addon_paths.filter(p => p !== path);
  }

  function setAppType(type) {
    newApp.app_type = type;
    if (type === 'vscode') {
      // Reset to preset items
      newApp.backup_items = vscodePresetItems.map(item => ({ ...item }));
    } else {
      // Custom: show all preset items as unchecked options
      newApp.backup_items = vscodePresetItems.map(item => ({ ...item, enabled: false }));
    }
  }

  // Open dialog for editing an existing app
  async function openEditDialog(app) {
    dialogMode = 'edit';
    editingAppKey = app.app_name;
    
    // Load full app config
    const fullConfig = await GetApp(app.app_name);
    if (!fullConfig) {
      log(`Error: Could not load config for ${app.display_name}`);
      return;
    }
    
    // Populate form with existing data
    newApp.app_name = fullConfig.app_name;
    newApp.display_name = fullConfig.display_name;
    newApp.exe_path = fullConfig.paths?.exe_paths?.[0] || '';
    newApp.data_path = fullConfig.paths?.data_paths?.[0] || '';
    newApp.addon_paths = fullConfig.addon_backup_paths || [];
    
    // Determine app type and populate backup items
    const existingItems = fullConfig.backup_items || [];
    const isVscodePreset = existingItems.some(item => 
      vscodePresetItems.some(preset => preset.path === item.path)
    );
    
    if (isVscodePreset && existingItems.length > 0) {
      newApp.app_type = 'vscode';
      // Map preset items with enabled state based on existing config
      newApp.backup_items = vscodePresetItems.map(preset => {
        const existing = existingItems.find(e => e.path === preset.path);
        return {
          ...preset,
          enabled: !!existing
        };
      });
      // Add any custom items that aren't in preset
      existingItems.forEach(item => {
        if (!vscodePresetItems.find(p => p.path === item.path)) {
          newApp.backup_items.push({
            type: item.type || (item.path.endsWith('/') ? 'folder' : (item.path.includes('.') ? 'file' : 'folder')),
            path: item.path,
            description: item.description || 'Custom item',
            optional: item.optional ?? true,
            enabled: true
          });
        }
      });
    } else {
      newApp.app_type = 'custom';
      // Start with all preset items disabled
      const allItems = vscodePresetItems.map(preset => ({
        ...preset,
        enabled: false
      }));
      
      // Enable items that exist in the saved config
      existingItems.forEach(item => {
        const presetIndex = allItems.findIndex(p => p.path === item.path);
        if (presetIndex >= 0) {
          allItems[presetIndex].enabled = true;
        } else {
          // Custom item not in preset, add it
          allItems.push({
            type: item.type || (item.path.endsWith('/') ? 'folder' : (item.path.includes('.') ? 'file' : 'folder')),
            path: item.path,
            description: item.description || 'Custom item',
            optional: item.optional ?? true,
            enabled: true
          });
        }
      });
      
      newApp.backup_items = allItems;
    }
    
    showAddDialog = true;
  }

  function openAddDialog() {
    dialogMode = 'add';
    editingAppKey = null;
    resetNewApp();
    showAddDialog = true;
  }

  function toggleBackupItem(index) {
    newApp.backup_items[index].enabled = !newApp.backup_items[index].enabled;
    newApp.backup_items = newApp.backup_items;
  }

  function addCustomBackupItem() {
    if (!customItemPath.trim()) return;
    
    newApp.backup_items = [...newApp.backup_items, {
      path: customItemPath.trim(),
      description: customItemDesc.trim() || 'Custom item',
      optional: true,
      enabled: true
    }];
    
    customItemPath = '';
    customItemDesc = '';
  }

  function removeBackupItem(index) {
    newApp.backup_items = newApp.backup_items.filter((_, i) => i !== index);
  }

  async function saveNewApp() {
    if (!newApp.app_name || !newApp.exe_path || !newApp.data_path) {
      alert('Please fill in all required fields');
      return;
    }

    // Prevent duplicate app IDs when adding
    if (dialogMode === 'add' && apps.some((a) => a.app_name.toLowerCase() === newApp.app_name.toLowerCase())) {
      alert('This app is already added. Please edit the existing entry.');
      return;
    }

    // Filter enabled backup items
    const enabledItems = newApp.backup_items
      .filter(item => item.enabled)
      .map(item => ({
        type: item.type || (item.path.endsWith('/') ? 'folder' : (item.path.includes('.') ? 'file' : 'folder')),
        path: item.path,
        description: item.description,
        optional: item.optional
      }));

    // For custom type, allow saving with no backup items (user might add later)
    // For vscode type, require at least one item
    if (newApp.app_type === 'vscode' && enabledItems.length === 0) {
      alert('Please select at least one backup item');
      return;
    }

    const config = {
      app_name: newApp.app_name,
      display_name: newApp.display_name || newApp.app_name,
      version: '1.0',
      active: true,
      description: `${newApp.display_name} - Managed by SurfManager`,
      paths: {
        data_paths: [newApp.data_path],
        exe_paths: [newApp.exe_path],
        reset_folder: newApp.data_path
      },
      backup_items: enabledItems,
      addon_backup_paths: newApp.addon_paths
    };

    try {
      await SaveApp(config);
      log(`${dialogMode === 'edit' ? 'Updated' : 'Added'}: ${config.display_name}`);
      showAddDialog = false;
      resetNewApp();
      await loadApps();
    } catch (e) {
      log(`Error: ${e}`);
    }
  }

  function resetNewApp() {
    newApp = {
      app_name: '',
      display_name: '',
      exe_path: '',
      data_path: '',
      app_type: 'vscode',
      backup_items: vscodePresetItems.map(item => ({ ...item })),
      addon_paths: []
    };
    customItemPath = '';
    customItemDesc = '';
    dialogMode = 'add';
    editingAppKey = null;
  }

  function getDataPathHint() {
    const platform = platformInfo?.platform;
    const user = platformInfo?.user || 'user';
    if (platform === 'windows') {
      return `C:\\Users\\${user}\\AppData\\Roaming\\<app>`;
    }
    if (platform === 'darwin') {
      return `~/Library/Application Support/<app>`;
    }
    if (platform === 'linux') {
      return `~/.config/<app>`;
    }
    return '';
  }

  function getAdditionalFolderExample() {
    const key = (newApp.app_name || newApp.display_name || '').toLowerCase();
    if (key.includes('codeium')) return '~/.codeium';
    if (key.includes('antigravity')) return '~/.antigravity';
    if (newApp.app_type === 'vscode' || key.includes('vscode') || key === 'code' || key.includes('visual studio code')) return '~/.vscode';
    if (key) return `~/.${key.replace(/\s+/g, '')}`;
    return '~/.vscode';
  }

  function handleWindowKeydown(e) {
    if (e.key === 'Escape' && showAddDialog) {
      showAddDialog = false;
      resetNewApp();
    }
  }

  // Initialize backup items when dialog opens for ADD mode only
  $: if (showAddDialog && dialogMode === 'add' && newApp.backup_items.length === 0) {
    newApp.backup_items = vscodePresetItems.map(item => ({ ...item }));
  }
</script>

<svelte:window on:keydown={handleWindowKeydown} />

<div class="h-full flex flex-col gap-4 animate-fadeIn">
  <div class="flex items-center justify-between">
    <h2 class="text-xl font-semibold text-[var(--text-primary)]">App Configuration</h2>
    <div class="flex items-center gap-3">
      <button 
        class="px-4 py-2 rounded-lg font-medium bg-[var(--primary)] hover:bg-[var(--primary-light)] hover:text-black text-white transition-all flex items-center gap-2"
        on:click={openAddDialog}
      >
        <Plus size={16} />
        Add App
      </button>
      <button 
        class="px-4 py-2 rounded-lg font-medium bg-[var(--bg-hover)] hover:bg-[var(--border)] border border-[var(--border)] text-[var(--text-secondary)] transition-all flex items-center gap-2"
        on:click={handleOpenFolder}
      >
        <FolderOpen size={16} />
        Open Folder
      </button>
      <button 
        class="p-2 rounded-lg text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)] transition-colors"
        on:click={loadApps} 
        title="Refresh"
      >
        <RefreshCw size={18} class={loading ? 'animate-spin' : ''} />
      </button>
    </div>
  </div>

  <div class="flex-1 bg-[var(--bg-elevated)] rounded-xl border border-[var(--border)] overflow-hidden">
    <div class="overflow-auto h-full">
      <table class="w-full">
        <thead class="bg-[var(--bg-card)] sticky top-0">
          <tr class="text-left text-sm text-[var(--text-secondary)]">
            <th class="p-3 w-10">#</th>
            <th class="p-3">App Name</th>
            <th class="p-3">Status</th>
            <th class="p-3 w-48">Actions</th>
          </tr>
        </thead>
        <tbody>
          {#if apps.length === 0}
            <tr>
              <td colspan="4" class="p-8 text-center text-[var(--text-muted)]">
                No apps configured. Click "Add App" to get started.
              </td>
            </tr>
          {/if}
          {#each apps as app, i}
            <tr 
              class="border-b border-[var(--border)] hover:bg-[var(--bg-card)] transition-colors cursor-pointer"
              on:contextmenu={(e) => handleContextMenu(e, app)}
            >
              <td class="p-3 text-[var(--text-muted)]">{i + 1}</td>
              <td class="p-3">
                <span class="font-medium text-[var(--text-primary)]">{app.display_name}</span>
                <span class="text-xs text-[var(--text-muted)] ml-2">({app.app_name})</span>
              </td>
              <td class="p-3">
                <div class="flex gap-1">
                  <span class="px-2 py-0.5 rounded-full text-xs font-medium
                              {app.installed ? 'bg-[var(--success)]/20 text-[var(--success)]' : 'bg-[var(--danger)]/20 text-[var(--danger)]'}">
                    {app.installed ? 'Installed' : 'Not Found'}
                  </span>
                  {#if !app.active}
                    <span class="px-2 py-0.5 rounded-full text-xs font-medium bg-[var(--warning)]/20 text-[var(--warning)]">
                      Inactive
                    </span>
                  {/if}
                </div>
              </td>
              <td class="p-3">
                <div class="flex items-center gap-2">
                  <button
                    class="px-3 py-1 rounded text-xs font-medium transition-all
                           {app.active 
                             ? 'bg-[var(--success)]/20 text-[var(--success)] hover:bg-[var(--success)]/30' 
                             : 'bg-[var(--bg-hover)] text-[var(--text-muted)] hover:bg-[var(--border)]'}"
                    on:click={() => handleToggle(app)}
                  >
                    {app.active ? 'Active' : 'Inactive'}
                  </button>
                  <button
                    class="p-1.5 rounded text-[var(--text-secondary)] hover:text-[var(--primary)] hover:bg-[var(--bg-hover)] transition-colors"
                    on:click={() => openEditDialog(app)}
                    title="Edit"
                  >
                    <Edit size={14} />
                  </button>
                  <button
                    class="p-1.5 rounded text-[var(--text-secondary)] hover:text-[var(--danger)] hover:bg-[var(--bg-hover)] transition-colors"
                    on:click={() => handleDelete(app)}
                    title="Delete"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  </div>

  <div class="text-sm text-[var(--text-muted)]">
    <p>Configs stored in: <code class="text-[var(--text-secondary)] bg-[var(--bg-hover)] px-2 py-0.5 rounded">~/.surfmanager/AppConfigs/</code></p>
  </div>
</div>

<!-- Context Menu -->
{#if contextMenu.show}
  <div 
    class="fixed bg-[var(--bg-card)] border border-[var(--border)] rounded-lg shadow-xl py-1 z-50 min-w-[180px]"
    style="left: {contextMenu.x}px; top: {contextMenu.y}px"
    on:click|stopPropagation={closeContextMenu}
  >
    <div class="px-3 py-2 border-b border-[var(--border)]">
      <span class="text-sm font-medium text-[var(--text-primary)]">{contextMenu.app?.display_name}</span>
    </div>
    
    <button
      class="w-full px-3 py-2 text-left text-sm text-[var(--text-secondary)] hover:bg-[var(--bg-hover)] hover:text-[var(--success)] transition-colors flex items-center gap-2"
      on:click={() => { handleSetActive(contextMenu.app); closeContextMenu(); }}
    >
      <Check size={14} />
      Set Active
    </button>
    <button
      class="w-full px-3 py-2 text-left text-sm text-[var(--text-secondary)] hover:bg-[var(--bg-hover)] hover:text-[var(--warning)] transition-colors flex items-center gap-2"
      on:click={() => { handleSetInactive(contextMenu.app); closeContextMenu(); }}
    >
      <ToggleLeft size={14} />
      Set Inactive
    </button>
    
    <div class="border-t border-[var(--border)] my-1"></div>
    
    <button
      class="w-full px-3 py-2 text-left text-sm text-[var(--text-secondary)] hover:bg-[var(--bg-hover)] hover:text-[var(--text-primary)] transition-colors flex items-center gap-2"
      on:click={() => { openEditDialog(contextMenu.app); closeContextMenu(); }}
    >
      <Edit size={14} />
      Edit App
    </button>
    <button
      class="w-full px-3 py-2 text-left text-sm text-[var(--text-secondary)] hover:bg-[var(--bg-hover)] hover:text-[var(--text-primary)] transition-colors flex items-center gap-2"
      on:click={() => { handleOpenAppConfig(contextMenu.app); closeContextMenu(); }}
    >
      <FileJson size={14} />
      Edit JSON Config
    </button>
    <button
      class="w-full px-3 py-2 text-left text-sm text-[var(--text-secondary)] hover:bg-[var(--bg-hover)] hover:text-[var(--text-primary)] transition-colors flex items-center gap-2"
      on:click={() => { handleOpenFolder(); closeContextMenu(); }}
    >
      <FolderOpen size={14} />
      Open Config Folder
    </button>
    
    <div class="border-t border-[var(--border)] my-1"></div>
    
    <button
      class="w-full px-3 py-2 text-left text-sm text-[var(--danger)] hover:bg-[var(--danger)]/10 transition-colors flex items-center gap-2"
      on:click={() => { handleDelete(contextMenu.app); closeContextMenu(); }}
    >
      <Trash2 size={14} />
      Delete App
    </button>
  </div>
{/if}

<!-- Add/Edit App Dialog -->
{#if showAddDialog}
  <div class="fixed inset-0 bg-black/60 flex items-center justify-center z-50" role="dialog" aria-modal="true" on:keydown={(e) => { if (e.key === 'Escape') { showAddDialog = false; resetNewApp(); } }} on:click|self={() => { showAddDialog = false; resetNewApp(); }}>
    <div class="bg-[var(--bg-card)] rounded-xl border border-[var(--border)] w-full max-w-4xl p-5 animate-fadeIn max-h-[90vh] overflow-auto">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-semibold text-[var(--text-primary)]">
          {dialogMode === 'edit' ? 'Edit Application' : 'Add Application'}
        </h3>
        <button 
          class="p-1 rounded hover:bg-[var(--bg-hover)] text-[var(--text-muted)]"
          on:click={() => { showAddDialog = false; resetNewApp(); }}
        >
          <X size={20} />
        </button>
      </div>
      
      <!-- Grid Layout -->
      <div class="grid grid-cols-2 gap-6">
        <!-- Left Column -->
        <div class="space-y-4">
          <!-- App Name -->
          <div>
            <label class="block text-sm text-[var(--text-secondary)] mb-1" for="app-name">App Name</label>
            <input
              id="app-name"
              type="text"
              class="w-full bg-[var(--bg-elevated)] border border-[var(--border)] rounded-lg px-3 py-2 text-[var(--text-primary)] placeholder-[var(--text-muted)]"
              bind:value={newApp.display_name}
              placeholder="Auto-filled from .exe"
            />
            {#if dialogMode === 'edit'}
              <p class="text-xs text-[var(--text-muted)] mt-1">ID: {newApp.app_name} (cannot be changed)</p>
            {/if}
          </div>

          <!-- App Type Toggle -->
          <div>
            <p class="block text-sm text-[var(--text-secondary)] mb-2">App Type</p>
            <div class="grid grid-cols-2 gap-2">
              <button
                class="p-2.5 rounded-lg border-2 text-left transition-all
                       {newApp.app_type === 'vscode' 
                         ? 'border-[var(--primary)] bg-[var(--primary-dim)]' 
                         : 'border-[var(--border)] hover:border-[var(--border-hover)]'}"
                on:click={() => setAppType('vscode')}
              >
                <div class="flex items-center gap-2">
                  <div class="w-3 h-3 rounded-full border-2 flex items-center justify-center
                              {newApp.app_type === 'vscode' ? 'border-[var(--primary)]' : 'border-[var(--text-muted)]'}">
                    {#if newApp.app_type === 'vscode'}
                      <div class="w-1.5 h-1.5 rounded-full bg-[var(--primary)]"></div>
                    {/if}
                  </div>
                  <span class="text-sm font-medium text-[var(--text-primary)]">VSCode Preset</span>
                </div>
              </button>
              <button
                class="p-2.5 rounded-lg border-2 text-left transition-all
                       {newApp.app_type === 'custom' 
                         ? 'border-[var(--primary)] bg-[var(--primary-dim)]' 
                         : 'border-[var(--border)] hover:border-[var(--border-hover)]'}"
                on:click={() => setAppType('custom')}
              >
                <div class="flex items-center gap-2">
                  <div class="w-3 h-3 rounded-full border-2 flex items-center justify-center
                              {newApp.app_type === 'custom' ? 'border-[var(--primary)]' : 'border-[var(--text-muted)]'}">
                    {#if newApp.app_type === 'custom'}
                      <div class="w-1.5 h-1.5 rounded-full bg-[var(--primary)]"></div>
                    {/if}
                  </div>
                  <span class="text-sm font-medium text-[var(--text-primary)]">Custom</span>
                </div>
              </button>
            </div>
          </div>

          <!-- Executable -->
          <div>
            <label class="block text-sm text-[var(--text-secondary)] mb-1" for="exe-path">Executable *</label>
            <div class="flex gap-2">
              <input
                id="exe-path"
                type="text"
                class="flex-1 bg-[var(--bg-hover)] border border-[var(--border)] rounded-lg px-3 py-2 text-[var(--text-primary)] placeholder-[var(--text-muted)] text-sm"
                bind:value={newApp.exe_path}
                placeholder="Select .exe file"
                readonly
              />
              <button 
                class="px-3 py-2 rounded-lg font-medium bg-[var(--bg-hover)] hover:bg-[var(--border)] border border-[var(--border)] text-[var(--text-secondary)] transition-all text-sm"
                on:click={selectExe}
              >
                Browse
              </button>
            </div>
          </div>

          <!-- Data Folder -->
          <div>
            <label class="block text-sm text-[var(--text-secondary)] mb-1" for="data-path">Data Folder *</label>
            <div class="flex gap-2">
              <input
                id="data-path"
                type="text"
                class="flex-1 bg-[var(--bg-hover)] border border-[var(--border)] rounded-lg px-3 py-2 text-[var(--text-primary)] placeholder-[var(--text-muted)] text-sm"
                bind:value={newApp.data_path}
                placeholder={getDataPathHint() || 'AppData/Roaming/...'}
                readonly
              />
              <button 
                class="px-3 py-2 rounded-lg font-medium bg-[var(--bg-hover)] hover:bg-[var(--border)] border border-[var(--border)] text-[var(--text-secondary)] transition-all text-sm"
                on:click={selectDataFolder}
              >
                Browse
              </button>
            </div>
            {#if getDataPathHint()}
              <p class="text-xs text-[var(--text-muted)] mt-1">Hint: {getDataPathHint()}</p>
            {/if}
          </div>

          <!-- Additional Folders (moved under Data Folder) -->
          <div class="bg-[var(--bg-elevated)] rounded-xl border border-[var(--border)] p-2.5">
            <div class="flex items-center gap-2 mb-1">
              <span>📁</span>
              <div>
                <p class="text-sm text-[var(--text-primary)] font-semibold">Additional Folders</p>
                <p class="text-xs text-[var(--text-muted)]">Also backed up & restored (e.g., {getAdditionalFolderExample()})</p>
              </div>
            </div>
            <div id="extra-folders" class="space-y-1.5 max-h-20 overflow-auto pr-1">
              {#each newApp.addon_paths as path}
                <div class="flex items-center gap-2 bg-[var(--bg-card)] border border-[var(--border)] rounded-lg px-3 py-2 text-xs">
                  <span class="flex-1 truncate text-[var(--text-secondary)] font-mono" title={path}>{path}</span>
                  <button class="p-1 rounded text-[var(--danger)] hover:text-[var(--danger)]/80 hover:bg-[var(--bg-hover)]" on:click={() => removeAddonFolder(path)} title="Remove">
                    <X size={14} />
                  </button>
                </div>
              {/each}
            </div>
            <button
              class="w-full mt-2 px-3 py-1.5 rounded-lg text-sm bg-[var(--bg-hover)] hover:bg-[var(--border)] border border-[var(--border)] border-dashed text-[var(--text-secondary)] transition-all"
              on:click={addAddonFolder}
            >
              + Add Folder
            </button>
          </div>
        </div>

        <!-- Right Column: Backup Items -->
        <div class="space-y-4">
          <div class="bg-[var(--bg-elevated)] rounded-xl border border-[var(--border)] overflow-hidden min-h-[280px]">
            <div class="px-3.5 py-2.5 border-b border-[var(--border)] bg-[var(--bg-card)]">
              <div class="flex items-center justify-between gap-3">
                <p class="text-sm font-semibold text-[var(--text-primary)]">📦 Backup Items</p>
                <p class="text-xs text-[var(--text-muted)]">
                  {newApp.backup_items.filter(i => i.enabled).length}/{newApp.backup_items.length}
                </p>
              </div>
              <p class="text-xs text-[var(--text-muted)] mt-0.5">Choose what gets backed up & restored</p>
            </div>

            <div class="p-2">
              <div class="max-h-[200px] overflow-auto pr-1 space-y-1">
                {#if newApp.backup_items.length === 0}
                  <p class="text-sm text-[var(--text-muted)] text-center py-4">No backup items yet.</p>
                {/if}
                {#each newApp.backup_items as item, index}
                  <div
                    class="flex items-start gap-2 p-1.5 rounded-lg border border-[var(--border)] bg-[var(--bg-card)] hover:border-[var(--border-hover)] transition-colors
                           {item.enabled ? '' : 'opacity-60'}"
                  >
                    <button
                      class="mt-0.5 w-5 h-5 rounded-md border flex items-center justify-center transition-all flex-shrink-0
                             {item.enabled
                               ? 'bg-[var(--primary)] border-[var(--primary)]'
                               : 'border-[var(--border)] hover:border-[var(--text-muted)]'}"
                      on:click={() => toggleBackupItem(index)}
                      title={item.enabled ? 'Enabled' : 'Disabled'}
                    >
                      {#if item.enabled}
                        <Check size={12} class="text-white" />
                      {/if}
                    </button>

                    <div class="flex-1 min-w-0">
                      <p class="text-xs text-[var(--text-primary)] font-mono truncate" title={item.path}>{item.path}</p>
                      <p class="text-xs text-[var(--text-muted)] truncate" title={item.description}>{item.description}</p>
                    </div>

                    <div class="flex items-center gap-2 flex-shrink-0">
                      <span class="text-[10px] px-2 py-0.5 rounded-full {item.optional ? 'bg-[var(--bg-hover)] text-[var(--text-muted)]' : 'bg-[var(--warning)]/20 text-[var(--warning)]'}">
                        {item.optional ? 'Optional' : 'Required'}
                      </span>
                      {#if newApp.app_type === 'custom' || !vscodePresetItems.find(p => p.path === item.path)}
                        <button
                          class="p-1 rounded text-[var(--text-muted)] hover:text-[var(--danger)] hover:bg-[var(--bg-hover)]"
                          on:click={() => removeBackupItem(index)}
                          title="Remove"
                        >
                          <X size={14} />
                        </button>
                      {/if}
                    </div>
                  </div>
                {/each}
              </div>

              <!-- Helper text for Custom apps with no items selected -->
              {#if newApp.app_type === 'custom' && !newApp.backup_items.some(item => item.enabled)}
                <p class="text-xs text-[var(--text-muted)] text-center py-2 mt-3 bg-[var(--bg-hover)] rounded-lg">
                  No items selected = only Additional Folders will be backed up
                </p>
              {/if}

              <!-- Add Custom Item -->
              <div class="mt-1.5 pt-1.5 border-t border-[var(--border)]">
                <p class="text-xs text-[var(--text-secondary)] mb-1">Add custom item</p>
                <div class="grid grid-cols-2 gap-2">
                  <input
                    type="text"
                    class="w-full bg-[var(--bg-hover)] border border-[var(--border)] rounded-lg px-3 py-1.5 text-xs text-[var(--text-primary)] placeholder-[var(--text-muted)]"
                    placeholder="Folder/file path"
                    bind:value={customItemPath}
                  />
                  <input
                    type="text"
                    class="w-full bg-[var(--bg-hover)] border border-[var(--border)] rounded-lg px-3 py-1.5 text-xs text-[var(--text-primary)] placeholder-[var(--text-muted)]"
                    placeholder="Description"
                    bind:value={customItemDesc}
                  />
                </div>
                <div class="flex justify-end mt-2">
                  <button
                    class="px-3 py-1.5 rounded-lg text-xs font-medium bg-[var(--primary)] hover:bg-[var(--primary-light)] hover:text-black text-white transition-all"
                    on:click={addCustomBackupItem}
                  >
                    Add Item
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="flex justify-end gap-3 mt-6 pt-4 border-t border-[var(--border)]">
        <button 
          class="px-4 py-2 rounded-lg font-medium bg-[var(--bg-hover)] hover:bg-[var(--border)] border border-[var(--border)] text-[var(--text-secondary)] transition-all"
          on:click={() => { showAddDialog = false; resetNewApp(); }}
        >
          Cancel
        </button>
        <button 
          class="px-4 py-2 rounded-lg font-medium bg-[var(--primary)] hover:bg-[var(--primary-light)] hover:text-black text-white transition-all"
          on:click={saveNewApp}
        >
          Save
        </button>
      </div>
    </div>
  </div>
{/if}
