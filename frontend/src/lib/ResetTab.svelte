<script>
  import { onMount, createEventDispatcher } from 'svelte';
  import { FolderOpen, RotateCcw, Fingerprint, Play, RefreshCw, Plus, Trash2, XCircle, Copy, Database, HardDrive, Download, AlertTriangle, Loader2, Package } from 'lucide-svelte';
  import { GetActiveApps, CheckAppInstalled, GetAppDataPath, ResetApp, ResetAccountOnly, GenerateNewID, LaunchApp, OpenAppFolder, GetSessions, KillApp, ResetAddonData, GetApp, GetPlatformInfo, GetLogs, CreateBackup, CalculateBackupSize } from './api.js';
  import { confirm } from './ConfirmModal.svelte';
  import { toast } from './Toast.svelte';
  import { settings } from './stores/settings.js';

  // Loading states for each action
  let loadingReset = false;
  let loadingNewID = false;
  let loadingKill = false;
  let loadingAddon = false;
  let loadingLaunch = false;
  let showResetModeModal = false;
  let showInstantBackupModal = false;
  let loadingInstantBackup = false;
  let loadingInstantKillBackup = false;

  export let logs = [];
  export let globalRunningAppsStatus = {};
  
  const dispatch = createEventDispatcher();

  let apps = [];
  let selectedApp = null;
  let loading = false;
  let sessionCount = 0;
  let addonCount = 0;
  let corruptedCount = 0;
  let instantBackupName = '';
  let instantBackupType = 'full';
  let instantBackupSizeInfo = null;
  let instantBackupRunning = false;
  let instantBackupSizeKey = '';
  
  // Store counts for each app in the list
  let appCounts = {};
  let platformInfo = {};

  $: autoBackup = $settings.autoBackup;

  onMount(loadApps);
  onMount(async () => {
    try {
      platformInfo = await GetPlatformInfo();
    } catch (e) {
      platformInfo = {};
    }
  });

  async function loadApps() {
    loading = true;
    try {
      const activeApps = await GetActiveApps();
      apps = await Promise.all((activeApps || []).map(async (app) => {
        const installed = await CheckAppInstalled(app.app_name);
        const dataPath = await GetAppDataPath(app.app_name);
        const running = !!globalRunningAppsStatus[app.app_name];
        return { ...app, installed, dataPath, running };
      }));
      
      // Sort apps alphabetically by display_name
      apps = apps.sort((a, b) => a.display_name.localeCompare(b.display_name));
      
      // Load counts for each app in the list
      await loadAppCounts();
      
      // Restore last selected app or fallback to first app
      if (apps.length > 0 && !selectedApp) {
        const lastSelectedAppName = $settings.lastSelectedAppReset;
        const lastSelectedApp = apps.find(app => app.app_name === lastSelectedAppName);
        
        if (lastSelectedApp) {
          selectApp(lastSelectedApp);
        } else {
          // Fallback to first app if saved app doesn't exist
          selectApp(apps[0]);
        }
      }
    } catch (e) {
      log(`Error loading apps: ${e}`);
    }
    loading = false;
  }
  
  // Keep running status in sync with global map
  $: if (apps && Object.keys(globalRunningAppsStatus).length >= 0) {
    apps = apps.map(app => ({ ...app, running: !!globalRunningAppsStatus[app.app_name] }));
  }

  $: if (selectedApp) {
    selectedApp = { ...selectedApp, running: !!globalRunningAppsStatus[selectedApp.app_name] };
  }

  $: if (showInstantBackupModal && selectedApp) {
    const nextKey = `${selectedApp.app_name}|${instantBackupType}`;
    if (nextKey !== instantBackupSizeKey) {
      instantBackupSizeKey = nextKey;
      updateInstantBackupSize();
    }
  }
  
  async function loadAppCounts() {
    const counts = {};
    for (const app of apps) {
      try {
        // Get regular sessions (not including auto-backups)
        const allSessions = await GetSessions(app.app_name, true);
        const sessionCount = (allSessions || []).filter(s => !s.is_auto).length;
        const autoBackupCount = (allSessions?.length || 0) - sessionCount;
        const corruptedCount = (allSessions || []).filter(s => s.corrupted).length;
        
        // Get addon count from app config
        const fullConfig = await GetApp(app.app_name);
        const addonCount = fullConfig?.addon_backup_paths?.length || 0;
        
        counts[app.app_name] = { sessionCount, autoBackupCount, addonCount, corruptedCount };
      } catch (e) {
        counts[app.app_name] = { sessionCount: 0, autoBackupCount: 0, addonCount: 0, corruptedCount: 0 };
      }
    }
    appCounts = counts;
  }

  async function selectApp(app) {
    selectedApp = app;
    
    // Persist selection to settings store
    settings.update('lastSelectedAppReset', app.app_name);
    // Load session count for selected app
    try {
      const allSessions = await GetSessions(app.app_name, true);
      sessionCount = (allSessions || []).filter(s => !s.is_auto).length;
      corruptedCount = (allSessions || []).filter(s => s.corrupted).length;
    } catch (e) {
      sessionCount = 0;
      corruptedCount = 0;
    }
    // Load addon count
    try {
      const fullConfig = await GetApp(app.app_name);
      addonCount = fullConfig?.addon_backup_paths?.length || 0;
    } catch (e) {
      addonCount = 0;
    }
  }

  function log(msg) {
    const time = new Date().toLocaleTimeString();
    logs = [...logs.slice(-99), `[${time}] ${msg}`];
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

  async function handleResetWithOverride(skipClose) {
    if (!selectedApp || loadingReset) return;

    let skipCloseStep = skipClose;
    let alreadyConfirmed = false;

    if (!skipClose && selectedApp.running) {
      const confirmed = await confirm({
        title: 'Reset Confirmation',
        message: `App is running.\n\nKill the app and reset?${autoBackup ? '\n\nAuto-backup will be created first.' : ''}`,
        confirmText: 'Kill and reset',
        cancelText: 'Cancel',
        danger: true
      });
      if (!confirmed) return;

      alreadyConfirmed = true;
      loadingReset = true;
      try {
        log(`[Kill] Stopping ${selectedApp.display_name}...`);
        await KillApp(selectedApp.app_name);
        log(`[Kill] ${selectedApp.display_name} stopped`);
      } catch (e) {
        log(`[Kill] Error: ${e}`);
        toast.error(`Failed to stop app: ${e}`, 5000);
        loadingReset = false;
        return;
      }
      skipCloseStep = true;
    }

    if ($settings.confirmBeforeReset && !alreadyConfirmed) {
      const confirmed = await confirm.reset(selectedApp.display_name, autoBackup);
      if (!confirmed) return;
    }

    loadingReset = true;
    log(`[Reset] Starting ${selectedApp.display_name}...`);
    try {
      await ResetApp(selectedApp.app_name, autoBackup, skipCloseStep);
      log(`[Reset] ${selectedApp.display_name} complete!`);
      toast.success('App data reset successfully', 3000);
      await loadApps();
    } catch (e) {
      const msg = e?.toString?.() || '';
      if (!skipClose && msg.toLowerCase().includes('failed to close')) {
        const override = await confirm({
          title: `${selectedApp.display_name} still running`,
          message: 'We could not close the app automatically. If you already closed it, continue without closing step.',
          confirmText: "I've closed the app",
          cancelText: 'Cancel',
          danger: true
        });
        if (override) {
          loadingReset = false;
          await handleResetWithOverride(true);
          return;
        }
      }
      log(`[Reset] Error: ${e}`);
      toast.error(`Reset failed: ${e}`, 5000);
    } finally {
      loadingReset = false;
    }
  }

  async function handleReset() {
    if (!selectedApp || loadingReset || !selectedApp.dataPath) return;
    showResetModeModal = true;
  }

  async function handleFullReset() {
    showResetModeModal = false;
    await handleResetWithOverride(false);
  }

  async function handleRemoveAccountOnly() {
    showResetModeModal = false;
    if (!selectedApp || loadingReset) return;

    if ($settings.confirmBeforeReset) {
      const confirmed = await confirm({
        title: 'Remove Account Only',
        message: `Remove account files for ${selectedApp.display_name}?\n\nThis will remove:\n- User/globalStorage/state.vscdb\n- User/globalStorage/state.vscdb.backup\n- User/globalStorage/storage.json\n\nAuto-backup will NOT be created.`,
        confirmText: 'Remove Account',
        cancelText: 'Cancel',
        danger: true
      });
      if (!confirmed) return;
    }

    loadingReset = true;
    log(`[RemoveAccount] Starting ${selectedApp.display_name}...`);
    try {
      await ResetAccountOnly(selectedApp.app_name);
      log(`[RemoveAccount] ${selectedApp.display_name} complete!`);
      toast.success('Account data removed successfully', 3000);
      await loadApps();
    } catch (e) {
      log(`[RemoveAccount] Error: ${e}`);
      toast.error(`Remove account failed: ${e}`, 5000);
    } finally {
      loadingReset = false;
    }
  }

  async function updateInstantBackupSize() {
    if (!selectedApp) return;
    try {
      instantBackupRunning = !!selectedApp.running;
      const includeData = instantBackupType === 'full';
      instantBackupSizeInfo = await CalculateBackupSize(selectedApp.app_name, includeData);
    } catch (e) {
      instantBackupSizeInfo = null;
    }
  }

  async function openInstantBackupModal() {
    if (!selectedApp || !selectedApp.dataPath) return;
    instantBackupName = '';
    instantBackupType = 'full';
    await updateInstantBackupSize();
    showInstantBackupModal = true;
  }

  async function handleCreateInstantBackup() {
    if (!selectedApp || !instantBackupName.trim() || loadingInstantBackup) {
      toast.error('Please enter session name');
      return;
    }

    const addonOnly = instantBackupType === 'addon';

    loadingInstantBackup = true;
    log(`Creating ${addonOnly ? 'addon-only' : 'full'} backup: ${selectedApp.app_name}/${instantBackupName}...`);
    try {
      await CreateBackup(selectedApp.app_name, instantBackupName.trim(), addonOnly);
      toast.success('Backup created successfully');
      showInstantBackupModal = false;
      await loadApps();
    } catch (e) {
      log(`Error: ${e}`);
      toast.error(`Backup failed: ${e}`);
    } finally {
      loadingInstantBackup = false;
    }
  }

  async function handleKillAndCreateInstantBackup() {
    if (!selectedApp || !instantBackupName.trim() || loadingInstantKillBackup) {
      toast.error('Please enter session name');
      return;
    }

    loadingInstantKillBackup = true;
    try {
      log(`[Kill] Stopping ${selectedApp.display_name}...`);
      await KillApp(selectedApp.app_name);
      await new Promise(r => setTimeout(r, 400));
      log(`[Kill] ${selectedApp.display_name} closed`);
    } catch (e) {
      loadingInstantKillBackup = false;
      toast.error(`Failed to close app: ${e}`);
      return;
    }

    instantBackupRunning = false;
    try {
      instantBackupSizeInfo = await CalculateBackupSize(selectedApp.app_name, instantBackupType === 'full');
    } catch (e) {
    }

    const addonOnly = instantBackupType === 'addon';
    log(`Creating ${addonOnly ? 'addon-only' : 'full'} backup: ${selectedApp.app_name}/${instantBackupName}...`);
    try {
      await CreateBackup(selectedApp.app_name, instantBackupName.trim(), addonOnly);
      toast.success('Backup created successfully');
      showInstantBackupModal = false;
      await loadApps();
    } catch (e) {
      log(`Error: ${e}`);
      toast.error(`Backup failed: ${e}`);
    } finally {
      loadingInstantKillBackup = false;
    }
  }

  async function handleNewID() {
    if (!selectedApp || loadingNewID) return;

    loadingNewID = true;
    toast.info('Generating new machine ID...');
    log(`[NewID] Generating for ${selectedApp.display_name}...`);
    try {
      const count = await GenerateNewID(selectedApp.app_name);
      log(`[NewID] Updated ${count} keys`);
      toast.success(`New machine ID generated (${count} keys updated)`, 3000);
    } catch (e) {
      log(`[NewID] Error: ${e}`);
      toast.error(`Failed to generate new ID: ${e}`, 5000);
    } finally {
      loadingNewID = false;
    }
  }

  async function handleLaunch() {
    if (!selectedApp || loadingLaunch) return;

    loadingLaunch = true;
    try {
      await LaunchApp(selectedApp.app_name);
      log(`Launched ${selectedApp.display_name}`);
      toast.success(`${selectedApp.display_name} launched successfully`, 3000);
    } catch (e) {
      log(`Error launching: ${e}`);
      toast.error(`Failed to launch app: ${e}`, 5000);
    } finally {
      loadingLaunch = false;
    }
  }

  async function handleKillApp() {
    if (!selectedApp || loadingKill) return;

    loadingKill = true;
    log(`[Kill] Stopping ${selectedApp.display_name}...`);
    try {
      await KillApp(selectedApp.app_name);
      log(`[Kill] ${selectedApp.display_name} stopped`);
      toast.success('App stopped successfully', 3000);
      await loadApps();
    } catch (e) {
      log(`[Kill] Error: ${e}`);
      toast.error(`Failed to stop app: ${e}`, 5000);
    } finally {
      loadingKill = false;
    }
  }

  async function handleResetAddon() {
    if (!selectedApp || addonCount === 0 || loadingAddon) return;

    if ($settings.confirmBeforeReset) {
      const confirmed = await confirm({
        title: 'Reset Addon Data',
        message: `Delete all ${addonCount} addon folder(s) for ${selectedApp.display_name}?`,
        confirmText: 'Delete',
        danger: true
      });
      if (!confirmed) return;
    }

    loadingAddon = true;
    log(`[ResetAddon] Deleting addon folders for ${selectedApp.display_name}...`);
    try {
      await ResetAddonData(selectedApp.app_name, false);
      log(`[ResetAddon] ${selectedApp.display_name} addon data deleted!`);
      toast.success('Addon folders deleted successfully', 3000);
      await loadApps();
    } catch (e) {
      const msg = e?.toString?.() || '';
      if (msg.toLowerCase().includes('failed to close')) {
        const override = await confirm({
          title: `${selectedApp.display_name} still running`,
          message: 'We could not close the app automatically. If you already closed it, continue without closing step.',
          confirmText: "I've closed the app",
          cancelText: 'Cancel',
          danger: true
        });
        if (override) {
          try {
            await ResetAddonData(selectedApp.app_name, true);
            log(`[ResetAddon] ${selectedApp.display_name} addon data deleted!`);
            toast.success('Addon folders deleted successfully', 3000);
            await loadApps();
          } catch (inner) {
            log(`[ResetAddon] Error: ${inner}`);
            toast.error(`Failed to delete addon folders: ${inner}`, 5000);
          } finally {
            loadingAddon = false;
          }
          return;
        }
      }
      log(`[ResetAddon] Error: ${e}`);
      toast.error(`Failed to delete addon folders: ${e}`, 5000);
    } finally {
      loadingAddon = false;
    }
  }

  async function handleDownloadLogs() {
    try {
      const data = await GetLogs();
      const blob = new Blob([data], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `surfmanager-activity-${new Date().toISOString().split('T')[0]}.log`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      toast.success('Log downloaded', 2000);
    } catch (e) {
      toast.error(`Failed to download logs: ${e}`, 4000);
    }
  }

  async function handleOpenFolder() {
    if (!selectedApp) return;
    
    try {
      await OpenAppFolder(selectedApp.app_name);
    } catch (e) {
      log(`Error opening folder: ${e}`);
      toast.error(`Failed to open folder: ${e}`, 5000);
    }
  }

  function clearLogs() {
    logs = [];
  }

  function toggleAutoBackup() {
    settings.update('autoBackup', !autoBackup);
  }

  function getStatusColor(app) {
    if (!app.installed) return 'var(--danger)';
    if (app.running) return 'var(--warning)';
    return 'var(--success)';
  }

  function getStatusText(app) {
    if (!app.installed) return 'Not Found';
    if (app.running) return 'Running';
    return 'Installed';
  }

  function handleAddApp() {
    dispatch('navigate', { tab: 'config', action: 'addApp' });
  }
</script>

<div class="h-full flex flex-col gap-4 animate-fadeIn">
  <!-- Header -->
  <div class="flex items-center justify-between">
    <h2 class="text-xl font-semibold text-[var(--text-primary)]">Reset Data</h2>
    <div class="flex items-center gap-3">
      <button
        class="px-3 py-1.5 rounded-lg text-sm font-medium transition-all border
               {autoBackup 
                 ? 'bg-[var(--success)]/20 text-[var(--success)] border-[var(--success)]' 
                 : 'bg-[var(--bg-hover)] text-[var(--text-muted)] border-[var(--border)]'}"
        on:click={toggleAutoBackup}
      >
        AutoBackup [{autoBackup ? 'ON' : 'OFF'}]
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

  <!-- Split Panel -->
  <div class="flex-1 flex gap-4 min-h-0">
    <!-- Left: App List -->
    <div class="w-64 bg-[var(--bg-elevated)] rounded-xl border border-[var(--border)] flex flex-col overflow-hidden">
      <div class="px-4 py-3 border-b border-[var(--border)]">
        <span class="text-sm font-medium text-[var(--text-secondary)]">APPS</span>
      </div>
      
      <div class="flex-1 overflow-auto p-2 space-y-1">
        {#if apps.length === 0 && !loading}
          <p class="text-center text-[var(--text-muted)] text-sm py-4">No apps configured</p>
        {/if}
        
        {#each apps as app}
          <button
            class="w-full flex items-center gap-2 px-3 py-2.5 rounded-lg text-left transition-all
                   {selectedApp?.app_name === app.app_name 
                     ? 'bg-[var(--primary-dim)] border border-[var(--primary)]/50' 
                     : 'hover:bg-[var(--bg-hover)] border border-transparent'}"
            on:click={() => selectApp(app)}
          >
            <span 
              class="w-2 h-2 rounded-full flex-shrink-0"
              style="background-color: {getStatusColor(app)}"
            ></span>
            <span class="text-sm font-medium text-[var(--text-primary)] truncate flex-1">{app.display_name}</span>
          </button>
        {/each}
      </div>

      <div class="p-2 border-t border-[var(--border)]">
        <button 
          class="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-sm text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)] transition-colors"
          on:click={handleAddApp}
        >
          <Plus size={16} />
          Add App
        </button>
      </div>
    </div>

    <!-- Right: App Details -->
    <div class="flex-1 flex flex-col gap-4 min-h-0">
      {#if selectedApp}
        <!-- App Info Card -->
        <div class="bg-[var(--bg-elevated)] rounded-xl border border-[var(--border)] p-4">
          <div class="flex items-start justify-between gap-4 mb-3">
            <div>
              <h3 class="text-xl font-bold text-[var(--text-primary)]">{selectedApp.display_name}</h3>
              <div class="flex items-center gap-2 mt-0.5">
                <span 
                  class="w-2 h-2 rounded-full"
                  style="background-color: {getStatusColor(selectedApp)}"
                ></span>
                <span class="text-xs" style="color: {getStatusColor(selectedApp)}">{getStatusText(selectedApp)}</span>
              </div>
              {#if getDataPathHint()}
                <p class="text-[10px] text-[var(--text-muted)] mt-1">Hint: {getDataPathHint()}</p>
              {/if}
            </div>

            <div class="flex flex-wrap items-start justify-end gap-4 text-right">
              <div class="flex items-center gap-2">
                <Database size={14} class="text-[var(--text-muted)]" />
                <div>
                  <span class="text-[10px] text-[var(--text-muted)] block">Sessions</span>
                  <span class="text-xs font-medium text-[var(--text-primary)]">{sessionCount} backup(s)</span>
                </div>
              </div>
              {#if corruptedCount > 0}
                <div class="flex items-center gap-2">
                  <AlertTriangle size={14} class="text-[var(--danger)]" />
                  <div>
                    <span class="text-[10px] text-[var(--text-muted)] block">Corrupted</span>
                    <span class="text-xs font-medium text-[var(--danger)]">{corruptedCount} found</span>
                  </div>
                </div>
              {/if}
              <div class="flex items-center gap-2">
                <HardDrive size={14} class="text-[var(--text-muted)]" />
                <div>
                  <span class="text-[10px] text-[var(--text-muted)] block">Auto-Backup</span>
                  <span class="text-xs font-medium text-[var(--text-primary)]">{autoBackup ? 'Enabled' : 'Disabled'}</span>
                </div>
              </div>
              {#if addonCount > 0}
                <div class="flex items-center gap-2">
                  <FolderOpen size={14} class="text-[var(--text-muted)]" />
                  <div>
                    <span class="text-[10px] text-[var(--text-muted)] block">Addons</span>
                    <span class="text-xs font-medium text-[var(--text-primary)]">{addonCount} folder(s)</span>
                  </div>
                </div>
              {/if}
            </div>
          </div>

          <!-- Path -->
          <div class="mb-4">
            <span class="text-xs text-[var(--text-muted)] block mb-1">Data Path</span>
            <div class="flex items-center gap-2">
              <p class="text-xs text-[var(--text-secondary)] font-mono bg-[var(--bg-card)] px-3 py-1.5 rounded-lg truncate flex-1" title={selectedApp.dataPath || 'Not found'}>
                {selectedApp.dataPath || 'Data folder not found'}
              </p>
              <button
                class="p-2 rounded-lg bg-[var(--bg-card)] border border-[var(--border)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-[var(--primary)] transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                on:click={() => {
                  if (!selectedApp.dataPath) return;
                  navigator.clipboard?.writeText(selectedApp.dataPath);
                  toast.success('Path copied to clipboard', 2000);
                }}
                disabled={!selectedApp.dataPath}
                title="Copy path"
              >
                <Copy size={16} />
              </button>
              <button
                class="p-2 rounded-lg bg-[var(--bg-card)] border border-[var(--border)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-[var(--primary)] transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                on:click={handleOpenFolder}
                disabled={!selectedApp.dataPath}
                title="Open data folder"
              >
                <FolderOpen size={16} />
              </button>
            </div>
          </div>

          <!-- Action Buttons -->
          <div class="grid grid-cols-2 gap-2">
            <button
              class="flex items-center justify-center gap-2 px-4 py-3 rounded-lg bg-[var(--bg-card)] border border-[var(--border)] text-[var(--text-secondary)] hover:text-[var(--primary)] hover:border-[var(--primary)] transition-all disabled:opacity-30 disabled:cursor-not-allowed"
              on:click={handleReset}
              disabled={!selectedApp.dataPath || loadingReset}
              title="Reset all app data"
            >
              {#if loadingReset}
                <Loader2 size={18} class="animate-spin" />
              {:else}
                <RotateCcw size={18} />
              {/if}
              <span class="text-xs font-medium">{loadingReset ? 'Resetting...' : 'Reset'}</span>
            </button>

            <button
              class="flex items-center justify-center gap-2 px-4 py-3 rounded-lg bg-[var(--bg-card)] border border-[var(--border)] text-[var(--text-secondary)] hover:text-[var(--success)] hover:border-[var(--success)] transition-all disabled:opacity-30 disabled:cursor-not-allowed"
              on:click={openInstantBackupModal}
              disabled={!selectedApp.dataPath}
              title="Create backup for selected app"
            >
              <Package size={18} />
              <span class="text-xs font-medium">Backup</span>
            </button>

            <button
              class="flex items-center justify-center gap-2 px-4 py-3 rounded-lg bg-[var(--bg-card)] border border-[var(--border)] text-[var(--text-secondary)] hover:text-[var(--warning)] hover:border-[var(--warning)] transition-all disabled:opacity-30 disabled:cursor-not-allowed"
              on:click={handleResetAddon}
              disabled={addonCount === 0 || loadingAddon}
              title={addonCount > 0 ? `Delete addon folders (${addonCount})` : 'No addons configured'}
            >
              {#if loadingAddon}
                <Loader2 size={18} class="animate-spin" />
              {:else}
                <Trash2 size={18} />
              {/if}
              <span class="text-xs font-medium">{loadingAddon ? 'Deleting...' : 'Addons'}</span>
            </button>

            <button
              class="flex items-center justify-center gap-2 px-4 py-3 rounded-lg bg-[var(--bg-card)] border border-[var(--border)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-[var(--primary)] transition-all disabled:opacity-30 disabled:cursor-not-allowed"
              on:click={handleNewID}
              disabled={!selectedApp.dataPath || loadingNewID}
              title="Generate new machine ID"
            >
              {#if loadingNewID}
                <Loader2 size={18} class="animate-spin" />
              {:else}
                <Fingerprint size={18} />
              {/if}
              <span class="text-xs font-medium">{loadingNewID ? 'Generating...' : 'New ID'}</span>
            </button>

            <button
              class="flex items-center justify-center gap-2 px-4 py-3 rounded-lg bg-[var(--bg-card)] border border-[var(--border)] text-[var(--text-secondary)] hover:text-[var(--danger)] hover:border-[var(--danger)] transition-all disabled:opacity-30 disabled:cursor-not-allowed"
              on:click={handleKillApp}
              disabled={!selectedApp.running || loadingKill}
              title="Force close app"
            >
              {#if loadingKill}
                <Loader2 size={18} class="animate-spin" />
              {:else}
                <XCircle size={18} />
              {/if}
              <span class="text-xs font-medium">{loadingKill ? 'Stopping...' : 'Kill'}</span>
            </button>

            <button
              class="flex items-center justify-center gap-2 px-4 py-3 rounded-lg bg-[var(--bg-card)] border border-[var(--border)] text-[var(--text-secondary)] hover:text-[var(--success)] hover:border-[var(--success)] transition-all disabled:opacity-30 disabled:cursor-not-allowed"
              on:click={handleLaunch}
              disabled={!selectedApp.installed || loadingLaunch}
              title="Launch app"
            >
              {#if loadingLaunch}
                <Loader2 size={18} class="animate-spin" />
              {:else}
                <Play size={18} />
              {/if}
              <span class="text-xs font-medium">{loadingLaunch ? 'Launching...' : 'Launch'}</span>
            </button>
          </div>

        </div>

        <!-- Log Output -->
        <div class="flex-1 min-h-[120px] bg-[var(--bg-elevated)] rounded-xl border border-[var(--border)] flex flex-col overflow-hidden">
          <div class="flex items-center justify-between px-4 py-2 border-b border-[var(--border)]">
            <span class="text-sm text-[var(--text-secondary)]">Log Output</span>
            <div class="flex items-center gap-3">
              <button class="text-xs text-[var(--text-muted)] hover:text-[var(--text-secondary)]" on:click={clearLogs}>Clear</button>
              <button class="text-xs text-[var(--text-muted)] hover:text-[var(--text-secondary)] flex items-center gap-1" on:click={handleDownloadLogs}>
                <Download size={12} />
                Download
              </button>
            </div>
          </div>
          <div class="flex-1 overflow-auto p-4 font-mono text-xs text-[var(--text-secondary)] space-y-1">
            {#if logs.length === 0}
              <p class="text-[var(--text-muted)]">Ready</p>
            {/if}
            {#each logs as logItem}
              <p class="leading-relaxed">{logItem}</p>
            {/each}
          </div>
        </div>
      {:else}
        <!-- No App Selected -->
        <div class="flex-1 flex items-center justify-center bg-[var(--bg-elevated)] rounded-xl border border-[var(--border)]">
          <div class="text-center">
            <p class="text-[var(--text-muted)]">Select an app from the list</p>
            <p class="text-sm text-[var(--text-muted)] mt-1">or add a new one in Config tab</p>
          </div>
        </div>
      {/if}
    </div>
  </div>
</div>

{#if showResetModeModal}
  <div
    class="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-[210]"
    role="dialog"
    aria-modal="true"
    on:click|self={() => showResetModeModal = false}
  >
    <div class="bg-[var(--bg-card)] rounded-xl border border-[var(--border)] w-full max-w-lg p-6 shadow-2xl">
      <h3 class="text-lg font-semibold text-[var(--text-primary)] mb-2">Choose Reset Mode</h3>
      <p class="text-sm text-[var(--text-secondary)] mb-5">
        Select which reset operation to run for <span class="text-[var(--text-primary)] font-medium">{selectedApp?.display_name}</span>.
      </p>

      <div class="space-y-3">
        <button
          class="w-full p-4 rounded-lg border border-[var(--border)] bg-[var(--bg-elevated)] hover:border-[var(--danger)]/60 hover:bg-[var(--danger)]/10 transition-colors text-left"
          on:click={handleFullReset}
        >
          <div class="flex items-center gap-2 mb-1">
            <RotateCcw size={16} class="text-[var(--danger)]" />
            <span class="font-semibold text-[var(--text-primary)]">Full Reset</span>
          </div>
          <p class="text-xs text-[var(--text-secondary)]">
            Delete app data folder and addon folders. Auto-backup follows current setting.
          </p>
        </button>

        <button
          class="w-full p-4 rounded-lg border border-[var(--border)] bg-[var(--bg-elevated)] hover:border-[var(--warning)]/60 hover:bg-[var(--warning)]/10 transition-colors text-left"
          on:click={handleRemoveAccountOnly}
        >
          <div class="flex items-center gap-2 mb-1">
            <Trash2 size={16} class="text-[var(--warning)]" />
            <span class="font-semibold text-[var(--text-primary)]">Remove Account Only</span>
          </div>
          <p class="text-xs text-[var(--text-secondary)]">
            Remove only known account files: <code>User/globalStorage/state.vscdb</code>, <code>state.vscdb.backup</code>, and <code>storage.json</code>.
          </p>
        </button>
      </div>

      <div class="flex justify-end mt-6">
        <button
          class="px-4 py-2 rounded-lg font-medium bg-[var(--bg-hover)] hover:bg-[var(--border)] border border-[var(--border)] text-[var(--text-secondary)] transition-all"
          on:click={() => showResetModeModal = false}
        >
          Cancel
        </button>
      </div>
    </div>
  </div>
{/if}

{#if showInstantBackupModal}
  <div class="fixed inset-0 bg-black/60 flex items-center justify-center z-50" role="dialog" aria-modal="true" on:click|self={() => showInstantBackupModal = false} on:keydown={(e) => { if (e.key === 'Escape') showInstantBackupModal = false; }}>
    <div class="bg-[var(--bg-card)] rounded-xl border border-[var(--border)] w-full max-w-2xl p-6 animate-fadeIn">
      <h3 class="text-lg font-semibold text-[var(--text-primary)] mb-1">Instant Backup</h3>
      <p class="text-xs text-[var(--text-secondary)] mb-4">{selectedApp?.display_name}</p>

      <div class="space-y-4">
        {#if instantBackupRunning}
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
              <div class="block text-sm text-[var(--text-secondary)] mb-1">Application</div>
              <div class="w-full bg-[var(--bg-hover)] border border-[var(--border)] rounded-lg px-3 py-2 text-[var(--text-primary)]">
                {selectedApp?.display_name}
              </div>
            </div>

            <div>
              <label class="block text-sm text-[var(--text-secondary)] mb-1" for="instant-backup-name">Session Name</label>
              <input
                type="text"
                class="w-full bg-[var(--bg-hover)] border border-[var(--border)] rounded-lg px-3 py-2 text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:border-[var(--primary)] focus:outline-none"
                placeholder="e.g., work-main, personal"
                id="instant-backup-name"
                bind:value={instantBackupName}
              />
            </div>
          </div>

          <div class="space-y-4">
            {#if instantBackupSizeInfo}
              <div>
                <p class="block text-sm text-[var(--text-secondary)] mb-2">Backup Size</p>
                <div class="bg-[var(--bg-hover)] border border-[var(--border)] rounded-lg p-3 space-y-1.5">
                  {#if instantBackupType === 'full' && instantBackupSizeInfo.data_size > 0}
                    <div class="flex justify-between text-sm">
                      <span class="text-[var(--text-secondary)]">Data:</span>
                      <span class="text-[var(--text-primary)] font-medium">{instantBackupSizeInfo.data_size_formatted}</span>
                    </div>
                  {/if}
                  {#if instantBackupSizeInfo.addon_size > 0}
                    <div class="flex justify-between text-sm">
                      <span class="text-[var(--text-secondary)]">Addons:</span>
                      <span class="text-[var(--text-primary)] font-medium">{instantBackupSizeInfo.addon_size_formatted}</span>
                    </div>
                  {/if}
                  <div class="border-t border-[var(--border)] pt-1.5 mt-1.5">
                    <div class="flex justify-between text-sm">
                      <span class="text-[var(--text-secondary)] font-medium">Total:</span>
                      <span class="text-[var(--text-primary)] font-semibold">{instantBackupSizeInfo.total_size_formatted}</span>
                    </div>
                  </div>
                </div>
              </div>
            {/if}

            <div>
              <div class="block text-sm text-[var(--text-secondary)] mb-2">Backup Type</div>
              <div class="grid gap-2 sm:grid-cols-2">
                <label class="flex items-start gap-3 p-3 bg-[var(--bg-hover)] border border-[var(--border)] rounded-lg cursor-pointer hover:border-[var(--primary)] transition-colors">
                  <input
                    type="radio"
                    name="instantBackupType"
                    value="full"
                    bind:group={instantBackupType}
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
                    name="instantBackupType"
                    value="addon"
                    bind:group={instantBackupType}
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
          on:click={() => showInstantBackupModal = false}
          disabled={loadingInstantBackup || loadingInstantKillBackup}
        >
          Cancel
        </button>
        {#if instantBackupRunning}
          <button
            class="px-4 py-2 rounded-lg font-medium bg-[var(--danger)] hover:bg-[var(--danger)]/80 text-white transition-all flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            on:click={handleKillAndCreateInstantBackup}
            disabled={loadingInstantKillBackup}
          >
            {#if loadingInstantKillBackup}
              <Loader2 size={16} class="animate-spin" />
              Processing...
            {:else}
              Kill and Continue Create Backup
            {/if}
          </button>
        {:else}
          <button
            class="px-4 py-2 rounded-lg font-medium bg-[var(--primary)] hover:bg-[var(--primary-light)] hover:text-black text-white transition-all flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            on:click={handleCreateInstantBackup}
            disabled={loadingInstantBackup}
          >
            {#if loadingInstantBackup}
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
