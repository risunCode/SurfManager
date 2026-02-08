<script>
  import { onMount } from 'svelte';
  import { Plus, RefreshCw, Search, CheckSquare, FolderOpen, Trash2, RotateCcw, Package, Play, AlertTriangle, Loader2 } from 'lucide-svelte';
  import { GetActiveApps, GetApp, GetAllSessions, CreateBackup, RestoreBackup, RestoreAddonOnly, CheckSessionHasAddons, DeleteSession, SetActiveSession, OpenSessionFolder, CountAutoBackups, LaunchApp, CalculateBackupSize, KillApp } from '../../wailsjs/go/main/App.js';
  import { confirm } from './ConfirmModal.svelte';
  import { toast } from './Toast.svelte';
  import { settings } from './stores/settings.js';

  export let logs = [];
  export let globalRunningAppsStatus = {};

  let apps = [];
  let sessions = [];
  let filter = 'all';
  let search = '';
  let showAuto = false;
  let autoBackupCount = 0;
  let loading = false;
  let selectedSessions = new Set();

  // Loading states for actions
  let loadingCreateBackup = false;
  let loadingRestore = {};      // { sessionKey: boolean }
  let loadingDelete = {};       // { sessionKey: boolean }
  let loadingKillCreate = false;

  let showNewDialog = false;
  let newBackupApp = '';
  let newBackupName = '';
  let newBackupAppRunning = false;      // Is selected app running?
  let backupSizeInfo = null;            // Size calculation result
  let backupType = 'full';              // 'full' or 'addon'

  // Context menu state
  let contextMenu = { show: false, x: 0, y: 0, session: null, appRunning: false, hasAddons: false };

  onMount(() => {
    showAuto = $settings.showAutoBackups;
    // Restore last selected app filter from settings
    const lastSelectedApp = $settings.lastSelectedAppSession;
    filter = lastSelectedApp || 'all';
    if ($settings.autoRefreshSessionsOnLaunch) {
      loadData();
    } else {
      loadData();
    }

    // Close context menu on click outside
    const handleClick = () => contextMenu.show = false;
    window.addEventListener('click', handleClick);

    return () => {
      window.removeEventListener('click', handleClick);
    };
  });

  async function loadData() {
    loading = true;
    try {
      apps = (await GetActiveApps()) || [];
      // Sort apps alphabetically by display_name
      apps = apps.sort((a, b) => a.display_name.localeCompare(b.display_name));
      sessions = (await GetAllSessions(showAuto)) || [];
      autoBackupCount = await CountAutoBackups();
      
      // Validate that saved filter app still exists, fallback to 'all' if not
      if (filter !== 'all') {
        const appExists = apps.some(app => app.app_name.toLowerCase() === filter.toLowerCase());
        if (!appExists) {
          filter = 'all';
          settings.update('lastSelectedAppSession', 'all');
        }
      }
    } catch (e) {
      log(`Error: ${e}`);
    }
    loading = false;
  }

  // Persist filter selection when it changes
  function handleFilterChange(newFilter) {
    filter = newFilter;
    settings.update('lastSelectedAppSession', newFilter);
  }

  function log(msg) {
    const time = new Date().toLocaleTimeString();
    logs = [...logs.slice(-99), `[${time}] ${msg}`];
  }

  function handleWindowKeydown(e) {
    if (e.key === 'Escape' && showNewDialog) {
      showNewDialog = false;
    }
  }

  let newBackupSizeKey = '';
  $: if (showNewDialog && newBackupApp) {
    const nextKey = `${newBackupApp}|${backupType}`;
    if (nextKey !== newBackupSizeKey) {
      newBackupSizeKey = nextKey;
      updateBackupSize();
    }
  }

  async function updateBackupSize() {
    if (!newBackupApp) return;
    
    try {
      const running = await isAppRunning(newBackupApp);
      newBackupAppRunning = running;
      
      const includeData = backupType === 'full';
      const sizeInfo = await CalculateBackupSize(newBackupApp, includeData);
      backupSizeInfo = sizeInfo;
    } catch (e) {
      backupSizeInfo = null;
    }
  }

  async function handleKillAndCreateBackup() {
    if (!newBackupApp || !newBackupName.trim() || loadingKillCreate) {
      toast.error('Please enter session name');
      return;
    }

    loadingKillCreate = true;
    try {
      await killAppSilently(newBackupApp);
    } catch (e) {
      loadingKillCreate = false;
      return;
    }

    // After killing, proceed with the selected backup type
    const addonOnly = backupType === 'addon';

    // Best-effort refresh size (avoid stale "running" state)
    newBackupAppRunning = false;
    try {
      backupSizeInfo = await CalculateBackupSize(newBackupApp, !addonOnly);
    } catch (e) {
      // ignore
    }

    log(`Creating ${addonOnly ? 'addon-only' : 'full'} backup: ${newBackupApp}/${newBackupName}...`);
    try {
      await CreateBackup(newBackupApp, newBackupName.trim(), addonOnly);
      toast.success('Backup created successfully');
      showNewDialog = false;
      await loadData();
    } catch (e) {
      log(`Error: ${e}`);
      toast.error(`Backup failed: ${e}`);
    } finally {
      loadingKillCreate = false;
    }
  }

  $: filteredSessions = (sessions || []).filter(s => {
    if (filter !== 'all' && s.app.toLowerCase() !== filter.toLowerCase()) return false;
    if (search && !s.name.toLowerCase().includes(search.toLowerCase())) return false;
    if (showAuto && !s.is_auto) return false;
    if (!showAuto && s.is_auto) return false;
    return true;
  });

  async function openNewDialog() {
    if (apps.length === 0) {
      alert('No apps configured. Add apps in Config tab first.');
      return;
    }
    newBackupApp = apps[0]?.app_name || '';
    newBackupName = '';
    backupType = 'full';
    
    // Calculate size and check running state
    await updateBackupSize();
    
    showNewDialog = true;
  }

  async function handleCreateBackup() {
    if (!newBackupApp || !newBackupName.trim() || loadingCreateBackup) {
      toast.error('Please enter session name');
      return;
    }

    // Determine if addon-only backup
    const addonOnly = newBackupAppRunning || backupType === 'addon';

    loadingCreateBackup = true;
    log(`Creating ${addonOnly ? 'addon-only' : 'full'} backup: ${newBackupApp}/${newBackupName}...`);

    try {
      await CreateBackup(newBackupApp, newBackupName.trim(), addonOnly);
      toast.success('Backup created successfully');
      showNewDialog = false;
      await loadData();
    } catch (e) {
      log(`Error: ${e}`);
      toast.error(`Backup failed: ${e}`);
    } finally {
      loadingCreateBackup = false;
    }
  }

  async function handleRestore(session) {
    const sessionKey = `${session.app}/${session.name}`;
    if (loadingRestore[sessionKey]) return;

    const running = await isAppRunning(session.app);
    if (running) {
      const appConfig = await GetApp(session.app);
      const confirmed = await confirm({
        title: `${appConfig.display_name} is Running`,
        message: 'The app must be closed before restoring.\n\nKill the app and continue?',
        confirmText: 'Kill App and Continue',
        danger: true
      });
      if (!confirmed) return;
      loadingRestore = { ...loadingRestore, [sessionKey]: true };
      try {
        await killAppSilently(session.app);
      } catch (e) {
        const override = await confirm({
          title: `${appConfig.display_name} still running`,
          message: 'We could not close the app automatically. If you already closed it, continue without closing step.',
          confirmText: "I've closed the app",
          cancelText: 'Cancel',
          danger: true
        });
        if (!override) {
          loadingRestore = { ...loadingRestore, [sessionKey]: false };
          return;
        }
      }
    } else {
      loadingRestore = { ...loadingRestore, [sessionKey]: true };
    }

    log(`Restoring session: ${session.name}...`);
    try {
      await RestoreBackup(session.app, session.name, false);
      toast.success('Session restored successfully');
      await loadData();
      loadingRestore = { ...loadingRestore, [sessionKey]: false };
      await promptLaunchIfAllowed(session.app);
    } catch (e) {
      const msg = e?.toString?.() || '';
      if (msg.toLowerCase().includes('failed to close')) {
        const appConfig = await GetApp(session.app);
        const override = await confirm({
          title: `${appConfig.display_name} still running`,
          message: 'We could not close the app automatically. If you already closed it, continue without closing step.',
          confirmText: "I've closed the app",
          cancelText: 'Cancel',
          danger: true
        });
        if (override) {
          await RestoreBackup(session.app, session.name, true);
          toast.success('Session restored successfully');
          await loadData();
          loadingRestore = { ...loadingRestore, [sessionKey]: false };
          await promptLaunchIfAllowed(session.app);
          return;
        }
      }
      log(`Error: ${e}`);
      toast.error(`Restore failed: ${e}`);
      loadingRestore = { ...loadingRestore, [sessionKey]: false };
    }
  }

  async function handleRestoreAddonOnly(session) {
    // Addon restore works even if app is running
    
    const appConfig = await GetApp(session.app);
    const addonPaths = appConfig?.addon_backup_paths || [];
    const addonList = addonPaths.map(p => `• ${p}`).join('\n');

    const confirmed = await confirm({
      title: 'Restore Addon Folders Only',
      message: `Restore addon folders from "${session.name}"?\n\nThis will restore:\n${addonList}`,
      confirmText: 'Restore Addons'
    });
    if (!confirmed) return;
    
    log(`Restoring addon folders from ${session.name}...`);
    try {
      await RestoreAddonOnly(session.app, session.name, false);
      toast.success('Addon folders restored successfully');
      await loadData();
    } catch (e) {
      log(`Error: ${e}`);
      toast.error(`Addon restore failed: ${e}`);
    }
  }

  async function handleDelete(session) {
    const sessionKey = `${session.app}/${session.name}`;
    if (loadingDelete[sessionKey]) return;

    if ($settings.confirmBeforeDelete) {
      const confirmed = await confirm.delete(session.name);
      if (!confirmed) return;
    }

    loadingDelete = { ...loadingDelete, [sessionKey]: true };
    try {
      await DeleteSession(session.app, session.name);
      log(`Deleted: ${session.name}`);
      selectedSessions.delete(`${session.app}/${session.name}`);
      selectedSessions = selectedSessions;
      await loadData();
    } catch (e) {
      log(`Error: ${e}`);
    } finally {
      loadingDelete = { ...loadingDelete, [sessionKey]: false };
    }
  }

  async function handleSetActive(session) {
    try {
      await SetActiveSession(session.app, session.name);
      log(`Set active: ${session.name}`);
      await loadData();
    } catch (e) {
      log(`Error: ${e}`);
    }
  }

  async function handleOpenFolder(session) {
    try {
      await OpenSessionFolder(session.app, session.name);
    } catch (e) {
      log(`Error: ${e}`);
    }
  }

  async function handleLaunchApp(session) {
    try {
      await LaunchApp(session.app);
      log(`Launched: ${session.app}`);
    } catch (e) {
      log(`Error launching app: ${e}`);
      alert(`Error launching app: ${e}`);
    }
  }

  function formatSize(bytes) {
    if (!bytes) return '0 B';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }

  function formatDate(dateStr) {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  // Selection handling with CTRL+Click
  function handleRowClick(event, session) {
    const key = `${session.app}/${session.name}`;
    
    if (event.ctrlKey || event.metaKey) {
      // CTRL+Click: toggle selection
      if (selectedSessions.has(key)) {
        selectedSessions.delete(key);
      } else {
        selectedSessions.add(key);
      }
      selectedSessions = selectedSessions;
    }
  }

  function selectAll() {
    if (selectedSessions.size === filteredSessions.length) {
      // Deselect all
      selectedSessions = new Set();
    } else {
      // Select all
      selectedSessions = new Set(filteredSessions.map(s => `${s.app}/${s.name}`));
    }
  }

  async function deleteSelected() {
    if (selectedSessions.size === 0) return;
    
    if ($settings.confirmBeforeDelete) {
      const confirmed = await confirm.bulkDelete(selectedSessions.size);
      if (!confirmed) return;
    }

    for (const key of selectedSessions) {
      const [app, name] = key.split('/');
      try {
        await DeleteSession(app, name);
        log(`Deleted: ${name}`);
      } catch (e) {
        log(`Error deleting ${name}: ${e}`);
      }
    }
    selectedSessions = new Set();
    await loadData();
  }

  // Context menu
  async function handleContextMenu(event, session) {
    event.preventDefault();
    
    // Check if app is running
    const running = await isAppRunning(session.app);
    
    // Check if session has addons
    const hasAddons = await CheckSessionHasAddons(session.app, session.name);
    
    // Clamp to viewport so the menu never overflows
    const menuWidth = 220;
    const menuHeight = 260; // approximate height of menu content
    const padding = 8;
    const maxX = Math.max(padding, (window.innerWidth || 0) - menuWidth - padding);
    const maxY = Math.max(padding, (window.innerHeight || 0) - menuHeight - padding);
    const nextX = Math.min(event.clientX, maxX);
    const nextY = Math.min(event.clientY, maxY);

    contextMenu = {
      show: true,
      x: Math.max(padding, nextX),
      y: Math.max(padding, nextY),
      session,
      appRunning: running,
      hasAddons
    };
  }

  function closeContextMenu() {
    contextMenu.show = false;
  }

  function isAppRunning(appKey) {
    if (globalRunningAppsStatus && Object.prototype.hasOwnProperty.call(globalRunningAppsStatus, appKey)) {
      return Promise.resolve(!!globalRunningAppsStatus[appKey]);
    }
    // Fallback: no status yet, assume not running
    return Promise.resolve(false);
  }

  async function killAppSilently(appKey) {
    try {
      const appConfig = await GetApp(appKey);
      log(`[Kill] Stopping ${appConfig.display_name}...`);
      await KillApp(appKey);
      await new Promise(r => setTimeout(r, 400));
      log(`[Kill] ${appConfig.display_name} closed`);
    } catch (e) {
      log(`Error stopping app: ${e}`);
      toast.error(`Failed to close app: ${e}`);
      throw e;
    }
  }

  async function promptLaunchIfAllowed(appKey) {
    if ($settings.dontAskStartAfterComplete) return;
    const appConfig = await GetApp(appKey);
    const confirmed = await confirm({
      title: 'Launch App?',
      message: `Restore completed for ${appConfig.display_name}.\n\nStart the app now?`,
      confirmText: 'Launch',
    });
    if (confirmed) {
      try {
        await LaunchApp(appKey);
        toast.success(`${appConfig.display_name} launched`, 2000);
      } catch (e) {
        toast.error(`Failed to launch: ${e}`);
      }
    }
  }
</script>

<svelte:window on:keydown={handleWindowKeydown} />

<div class="h-full flex flex-col gap-4 animate-fadeIn">
  <!-- Header -->
  <div class="flex items-center justify-between flex-wrap gap-4">
    <div class="flex items-center gap-3">
      <h2 class="text-xl font-semibold text-[var(--text-primary)]">Sessions</h2>
      <button 
        class="px-4 py-2 rounded-lg font-medium bg-[var(--primary)] hover:bg-[var(--primary-light)] hover:text-black text-white transition-all flex items-center gap-2 text-sm"
        on:click={openNewDialog}
      >
        <Plus size={16} />
        New Backup
      </button>
    </div>
    
    <div class="flex items-center gap-3 flex-wrap">
      <div class="relative">
        <Search size={16} class="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)]" />
        <input
          type="text"
          placeholder="Search..."
          class="bg-[var(--bg-hover)] border border-[var(--border)] rounded-lg pl-9 pr-3 py-1.5 text-sm text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:border-[var(--primary)] focus:outline-none w-36"
          bind:value={search}
        />
      </div>

      <button
        class="px-3 py-1.5 rounded-lg text-sm font-medium transition-all border
               {showAuto 
                 ? 'bg-[var(--warning)]/20 text-[var(--warning)] border-[var(--warning)]' 
                 : 'bg-[var(--bg-hover)] text-[var(--text-muted)] border-[var(--border)]'}"
        on:click={() => { showAuto = !showAuto; loadData(); }}
      >
        Auto-Backup ({autoBackupCount})
      </button>

      <button 
        class="p-2 rounded-lg text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)] transition-colors"
        on:click={loadData} 
        title="Refresh"
      >
        <RefreshCw size={18} class={loading ? 'animate-spin' : ''} />
      </button>
    </div>
  </div>

  <!-- Selection Actions Bar -->
  <div class="flex items-center gap-3">
    <select 
      class="bg-[var(--bg-hover)] border border-[var(--border)] rounded-lg px-3 py-1.5 text-sm text-[var(--text-primary)] focus:border-[var(--primary)] focus:outline-none"
      bind:value={filter}
      on:change={(e) => handleFilterChange(e.target.value)}
    >
      <option value="all">All Apps</option>
      {#each apps as app}
        <option value={app.app_name}>{app.display_name}</option>
      {/each}
    </select>

    <button 
      class="px-3 py-1.5 rounded-lg text-sm font-medium bg-[var(--bg-hover)] hover:bg-[var(--border)] border border-[var(--border)] text-[var(--text-secondary)] transition-all flex items-center gap-2"
      on:click={selectAll}
      title="Select All (or CTRL+Click rows)"
    >
      <CheckSquare size={14} />
      {selectedSessions.size === filteredSessions.length && filteredSessions.length > 0 ? 'Deselect All' : 'Select All'}
    </button>
    
    {#if selectedSessions.size > 0}
      <button 
        class="px-3 py-1.5 rounded-lg text-sm font-medium bg-[var(--danger)]/20 hover:bg-[var(--danger)]/30 text-[var(--danger)] border border-[var(--danger)]/30 transition-all"
        on:click={deleteSelected}
      >
        Delete Selected ({selectedSessions.size})
      </button>
    {/if}

    <span class="text-sm text-[var(--text-muted)] ml-auto">
      {filteredSessions.length} session(s)
    </span>
  </div>

  <!-- Sessions Table -->
  <div class="flex-1 bg-[var(--bg-elevated)] rounded-xl border border-[var(--border)] overflow-hidden">
    <div class="overflow-auto h-full">
      <table class="w-full">
        <thead class="bg-[var(--bg-card)] sticky top-0">
          <tr class="text-left text-xs text-[var(--text-secondary)]">
            <th class="p-3 w-12">#</th>
            <th class="p-3">App</th>
            <th class="p-3">Session Name</th>
            <th class="p-3">Size</th>
            <th class="p-3">Created</th>
            <th class="p-3">Status</th>
            <th class="p-3 text-right">Actions</th>
          </tr>
        </thead>
        <tbody>
          {#if filteredSessions.length === 0}
            <tr>
              <td colspan="7" class="p-8 text-center text-[var(--text-muted)]">
                {showAuto ? 'No auto-backups found' : 'No sessions found'}
              </td>
            </tr>
          {/if}
          {#each filteredSessions as session, index}
            {@const key = `${session.app}/${session.name}`}
            {@const isSelected = selectedSessions.has(key)}
            <tr 
              class="border-b border-[var(--border)] transition-colors cursor-pointer
                     {isSelected ? 'bg-[var(--primary-dim)]' : 'hover:bg-[var(--bg-card)]'}"
              on:click={(e) => handleRowClick(e, session)}
              on:contextmenu={(e) => handleContextMenu(e, session)}
            >
              <td class="p-3 text-[var(--text-muted)] text-sm">{index + 1}</td>
              <td class="p-3">
                <span class="font-medium text-[var(--text-primary)] capitalize">{session.app}</span>
              </td>
              <td class="p-3 text-[var(--text-secondary)]">{session.name}</td>
              <td class="p-3 text-[var(--text-muted)] text-sm">{formatSize(session.size)}</td>
              <td class="p-3 text-[var(--text-muted)] text-sm">{formatDate(session.created)}</td>
              <td class="p-3">
                {#if session.corrupted}
                  <span class="px-2 py-0.5 rounded-full text-xs font-medium bg-[var(--danger)]/20 text-[var(--danger)] inline-flex items-center gap-1">
                    <AlertTriangle size={12} />
                    Corrupted
                  </span>
                {:else if session.is_auto}
                  <span class="px-2 py-0.5 rounded-full text-xs font-medium bg-[var(--warning)]/20 text-[var(--warning)]">Auto</span>
                {:else if session.is_active}
                  <span class="px-2 py-0.5 rounded-full text-xs font-medium bg-[var(--success)]/20 text-[var(--success)]">Active</span>
                {:else}
                  <span class="px-2 py-0.5 rounded-full text-xs font-medium bg-[var(--bg-hover)] text-[var(--text-muted)]">Ready</span>
                {/if}
              </td>
              <td class="p-3">
                <div class="flex items-center justify-end gap-2">
                  <button
                    class="px-2 py-1 rounded text-xs font-medium text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)] transition-colors flex items-center gap-1"
                    on:click|stopPropagation={() => handleOpenFolder(session)}
                  >
                    <FolderOpen size={12} />
                    Folder
                  </button>
                  <button
                    class="px-2 py-1 rounded text-xs font-medium text-[var(--text-secondary)] hover:text-[var(--danger)] hover:bg-[var(--bg-hover)] transition-colors flex items-center gap-1 disabled:opacity-50 disabled:cursor-not-allowed"
                    on:click|stopPropagation={() => handleDelete(session)}
                    disabled={loadingDelete[`${session.app}/${session.name}`]}
                  >
                    {#if loadingDelete[`${session.app}/${session.name}`]}
                      <Loader2 size={12} class="animate-spin" />
                      Deleting...
                    {:else}
                      <Trash2 size={12} />
                      Delete
                    {/if}
                  </button>
                </div>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  </div>

  <!-- Help text -->
  <p class="text-xs text-[var(--text-muted)]">
    💡 Tip: CTRL+Click to select multiple rows, or right-click for quick actions
  </p>
</div>

<!-- Context Menu -->
{#if contextMenu.show}
  <div 
    class="fixed bg-[var(--bg-card)] border border-[var(--border)] rounded-lg shadow-xl py-1 z-50 min-w-[180px]"
    style="left: {contextMenu.x}px; top: {contextMenu.y}px"
    role="menu"
    on:click|stopPropagation
    on:keydown={(e) => { if (e.key === 'Escape') closeContextMenu(); }}
  >
    <!-- Full Restore: Always clickable -->
    <button
      class="w-full px-4 py-2 text-left text-sm text-[var(--text-secondary)] hover:bg-[var(--bg-hover)] hover:text-[var(--primary)] transition-colors flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
      on:click={() => { handleRestore(contextMenu.session); closeContextMenu(); }}
      disabled={loadingRestore[`${contextMenu.session?.app}/${contextMenu.session?.name}`]}
    >
      {#if loadingRestore[`${contextMenu.session?.app}/${contextMenu.session?.name}`]}
        <Loader2 size={14} class="animate-spin" />
        Restoring...
      {:else}
        <RotateCcw size={14} />
        Restore Session
      {/if}
    </button>

    <!-- Restore Addon Only: Enabled only if session has addons -->
    {#if contextMenu.hasAddons}
      <button
        class="w-full px-4 py-2 text-left text-sm text-[var(--text-secondary)] hover:bg-[var(--bg-hover)] hover:text-[var(--success)] transition-colors flex items-center gap-2"
        on:click={() => { handleRestoreAddonOnly(contextMenu.session); closeContextMenu(); }}
      >
        <Package size={14} />
        Restore Addon Only
      </button>
    {:else}
      <button
        class="w-full px-4 py-2 text-left text-sm text-[var(--text-muted)] cursor-not-allowed opacity-50 transition-colors flex items-center gap-2"
        disabled
        title="No addon folders in this session"
      >
        <Package size={14} />
        Restore Addon Only
        <span class="ml-auto text-xs text-[var(--text-muted)]">(No addons)</span>
      </button>
    {/if}

    <div class="border-t border-[var(--border)] my-1"></div>

    <button
      class="w-full px-4 py-2 text-left text-sm text-[var(--text-secondary)] hover:bg-[var(--bg-hover)] hover:text-[var(--text-primary)] transition-colors flex items-center gap-2"
      on:click={() => { handleOpenFolder(contextMenu.session); closeContextMenu(); }}
    >
      <FolderOpen size={14} />
      Open Folder
    </button>
    <button
      class="w-full px-4 py-2 text-left text-sm text-[var(--text-secondary)] hover:bg-[var(--bg-hover)] hover:text-[var(--success)] transition-colors flex items-center gap-2"
      on:click={() => { handleLaunchApp(contextMenu.session); closeContextMenu(); }}
    >
      <Play size={14} />
      Launch App
    </button>
    <div class="border-t border-[var(--border)] my-1"></div>
    <button
      class="w-full px-4 py-2 text-left text-sm text-[var(--danger)] hover:bg-[var(--danger)]/10 transition-colors flex items-center gap-2"
      on:click={() => { handleDelete(contextMenu.session); closeContextMenu(); }}
    >
      <Trash2 size={14} />
      Delete Session
    </button>
  </div>
{/if}

<!-- New Backup Dialog -->
{#if showNewDialog}
  <div class="fixed inset-0 bg-black/60 flex items-center justify-center z-50" role="dialog" aria-modal="true" on:click|self={() => showNewDialog = false} on:keydown={(e) => { if (e.key === 'Escape') showNewDialog = false; }}>
    <div class="bg-[var(--bg-card)] rounded-xl border border-[var(--border)] w-full max-w-2xl p-6 animate-fadeIn">
      <h3 class="text-lg font-semibold text-[var(--text-primary)] mb-4">Create New Backup</h3>
      
      <div class="space-y-4">
        <!-- App Running Warning -->
        {#if newBackupAppRunning}
          <div class="bg-[var(--warning)]/10 rounded-lg p-3">
            <div class="flex items-start gap-2">
              <span class="text-[var(--warning)] text-lg">⚠</span>
              <div class="flex-1">
                <p class="text-sm font-medium text-[var(--warning)] mb-1">App is Running</p>
                <p class="text-xs text-[var(--text-secondary)]">
                  Choose backup type. For Full Backup, click "Kill and Continue" to close the app and proceed.
                </p>
              </div>
            </div>
          </div>
        {/if}

        <div class="grid gap-4 md:grid-cols-2">
          <div class="space-y-4">
            <div>
              <label class="block text-sm text-[var(--text-secondary)] mb-1" for="new-backup-app">Application</label>
              <select 
                class="w-full bg-[var(--bg-hover)] border border-[var(--border)] rounded-lg px-3 py-2 text-[var(--text-primary)] focus:border-[var(--primary)] focus:outline-none"
                id="new-backup-app"
                bind:value={newBackupApp}
                on:change={updateBackupSize}
              >
                {#each apps as app}
                  <option value={app.app_name}>{app.display_name}</option>
                {/each}
              </select>
            </div>

            <div>
              <label class="block text-sm text-[var(--text-secondary)] mb-1" for="new-backup-name">Session Name</label>
              <input
                type="text"
                class="w-full bg-[var(--bg-hover)] border border-[var(--border)] rounded-lg px-3 py-2 text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:border-[var(--primary)] focus:outline-none"
                placeholder="e.g., work-main, personal"
                id="new-backup-name"
                bind:value={newBackupName}
              />
            </div>
          </div>

          <div class="space-y-4">
            <!-- Backup Size -->
            {#if backupSizeInfo}
              <div>
                <p class="block text-sm text-[var(--text-secondary)] mb-2">Backup Size</p>
                <div class="bg-[var(--bg-hover)] border border-[var(--border)] rounded-lg p-3 space-y-1.5">
                  {#if backupType === 'full' && backupSizeInfo.data_size > 0}
                    <div class="flex justify-between text-sm">
                      <span class="text-[var(--text-secondary)]">Data:</span>
                      <span class="text-[var(--text-primary)] font-medium">{backupSizeInfo.data_size_formatted}</span>
                    </div>
                  {/if}
                  {#if backupSizeInfo.addon_size > 0}
                    <div class="flex justify-between text-sm">
                      <span class="text-[var(--text-secondary)]">Addons:</span>
                      <span class="text-[var(--text-primary)] font-medium">{backupSizeInfo.addon_size_formatted}</span>
                    </div>
                  {/if}
                  <div class="border-t border-[var(--border)] pt-1.5 mt-1.5">
                    <div class="flex justify-between text-sm">
                      <span class="text-[var(--text-secondary)] font-medium">Total:</span>
                      <span class="text-[var(--text-primary)] font-semibold">{backupSizeInfo.total_size_formatted}</span>
                    </div>
                  </div>
                </div>
              </div>
            {/if}

            <!-- Backup Type Selection -->
            <div>
              <label class="block text-sm text-[var(--text-secondary)] mb-2">Backup Type</label>
              <div class="grid gap-2 sm:grid-cols-2">
                <label class="flex items-start gap-3 p-3 bg-[var(--bg-hover)] border border-[var(--border)] rounded-lg cursor-pointer hover:border-[var(--primary)] transition-colors">
                  <input
                    type="radio"
                    name="backupType"
                    value="full"
                    bind:group={backupType}
                    class="mt-0.5"
                  />
                  <div class="flex-1">
                    <div class="text-sm font-medium text-[var(--text-primary)]">Full Backup</div>
                    <div class="text-xs text-[var(--text-muted)] mt-0.5">Backup all data and addon folders</div>
                  </div>
                </label>
                
                <label class="flex items-start gap-3 p-3 bg-[var(--bg-hover)] border border-[var(--border)] rounded-lg cursor-pointer hover:border-[var(--primary)] transition-colors">
                  <input
                    type="radio"
                    name="backupType"
                    value="addon"
                    bind:group={backupType}
                    class="mt-0.5"
                  />
                  <div class="flex-1">
                    <div class="text-sm font-medium text-[var(--text-primary)]">Addon Only</div>
                    <div class="text-xs text-[var(--text-muted)] mt-0.5">Backup only addon folders</div>
                  </div>
                </label>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="flex justify-end gap-3 mt-6">
        <button
          class="px-4 py-2 rounded-lg font-medium bg-[var(--bg-hover)] hover:bg-[var(--border)] border border-[var(--border)] text-[var(--text-secondary)] transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          on:click={() => showNewDialog = false}
          disabled={loadingCreateBackup || loadingKillCreate}
        >
          Cancel
        </button>
        {#if newBackupAppRunning}
          <button
            class="px-4 py-2 rounded-lg font-medium bg-[var(--danger)] hover:bg-[var(--danger)]/80 text-white transition-all flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            on:click={handleKillAndCreateBackup}
            disabled={loadingKillCreate}
          >
            {#if loadingKillCreate}
              <Loader2 size={16} class="animate-spin" />
              Processing...
            {:else}
              Kill and Continue Create Backup
            {/if}
          </button>
        {:else}
          <button
            class="px-4 py-2 rounded-lg font-medium bg-[var(--primary)] hover:bg-[var(--primary-light)] hover:text-black text-white transition-all flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            on:click={handleCreateBackup}
            disabled={loadingCreateBackup}
          >
            {#if loadingCreateBackup}
              <Loader2 size={16} class="animate-spin" />
              Creating...
            {:else}
              Create Backup
            {/if}
          </button>
        {/if}
      </div>
    </div>
  </div>
{/if}
