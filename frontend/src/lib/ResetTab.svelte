<script>
  import { onMount, createEventDispatcher } from 'svelte';
  import { FolderOpen, RotateCcw, Fingerprint, Play, RefreshCw, Plus, HardDrive, Database, Trash2, XCircle } from 'lucide-svelte';
  import { GetActiveApps, CheckAppInstalled, GetAppDataPath, ResetApp, GenerateNewID, LaunchApp, OpenAppFolder, IsAppRunning, GetSessions, KillApp, ResetAddonData, GetApp } from '../../wailsjs/go/main/App.js';
  import { confirm } from './ConfirmModal.svelte';
  import { settings } from './stores/settings.js';

  export let logs = [];
  
  const dispatch = createEventDispatcher();

  let apps = [];
  let selectedApp = null;
  let loading = false;
  let sessionCount = 0;
  let addonCount = 0;
  
  // Store counts for each app in the list
  let appCounts = {};

  $: autoBackup = $settings.autoBackup;

  onMount(loadApps);

  async function loadApps() {
    loading = true;
    try {
      const activeApps = await GetActiveApps();
      apps = await Promise.all((activeApps || []).map(async (app) => {
        const installed = await CheckAppInstalled(app.app_name);
        const dataPath = await GetAppDataPath(app.app_name);
        const running = await IsAppRunning(app.app_name);
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
  
  async function loadAppCounts() {
    const counts = {};
    for (const app of apps) {
      try {
        // Get regular sessions (not including auto-backups)
        const sessions = await GetSessions(app.app_name, false);
        const sessionCount = sessions?.length || 0;
        
        // Get auto-backups by getting all sessions and filtering
        const allSessions = await GetSessions(app.app_name, true);
        const autoBackupCount = (allSessions?.length || 0) - sessionCount;
        
        // Get addon count from app config
        const fullConfig = await GetApp(app.app_name);
        const addonCount = fullConfig?.addon_backup_paths?.length || 0;
        
        counts[app.app_name] = { sessionCount, autoBackupCount, addonCount };
      } catch (e) {
        counts[app.app_name] = { sessionCount: 0, autoBackupCount: 0, addonCount: 0 };
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
      const sessions = await GetSessions(app.app_name, false);
      sessionCount = sessions?.length || 0;
    } catch (e) {
      sessionCount = 0;
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

  async function handleReset() {
    if (!selectedApp) return;
    
    if ($settings.confirmBeforeReset) {
      const confirmed = await confirm.reset(selectedApp.display_name, autoBackup);
      if (!confirmed) return;
    }
    
    log(`[Reset] Starting ${selectedApp.display_name}...`);
    try {
      await ResetApp(selectedApp.app_name, autoBackup, $settings.skipCloseApp);
      log(`[Reset] ${selectedApp.display_name} complete!`);
      await loadApps();
    } catch (e) {
      log(`[Reset] Error: ${e}`);
    }
  }

  async function handleNewID() {
    if (!selectedApp) return;
    
    log(`[NewID] Generating for ${selectedApp.display_name}...`);
    try {
      const count = await GenerateNewID(selectedApp.app_name);
      log(`[NewID] Updated ${count} keys`);
    } catch (e) {
      log(`[NewID] Error: ${e}`);
    }
  }

  async function handleLaunch() {
    if (!selectedApp) return;
    
    try {
      await LaunchApp(selectedApp.app_name);
      log(`Launched ${selectedApp.display_name}`);
    } catch (e) {
      log(`Error launching: ${e}`);
    }
  }

  async function handleKillApp() {
    if (!selectedApp) return;
    
    log(`[Kill] Stopping ${selectedApp.display_name}...`);
    try {
      await KillApp(selectedApp.app_name);
      log(`[Kill] ${selectedApp.display_name} stopped`);
      await loadApps();
    } catch (e) {
      log(`[Kill] Error: ${e}`);
    }
  }

  async function handleResetAddon() {
    if (!selectedApp || addonCount === 0) return;
    
    if ($settings.confirmBeforeReset) {
      const confirmed = await confirm({
        title: 'Reset Addon Data',
        message: `Delete all ${addonCount} addon folder(s) for ${selectedApp.display_name}?`,
        confirmText: 'Delete',
        danger: true
      });
      if (!confirmed) return;
    }
    
    log(`[ResetAddon] Deleting addon folders for ${selectedApp.display_name}...`);
    try {
      await ResetAddonData(selectedApp.app_name, $settings.skipCloseApp);
      log(`[ResetAddon] ${selectedApp.display_name} addon data deleted!`);
      await loadApps();
    } catch (e) {
      log(`[ResetAddon] Error: ${e}`);
    }
  }

  async function handleOpenFolder() {
    if (!selectedApp) return;
    
    try {
      await OpenAppFolder(selectedApp.app_name);
    } catch (e) {
      log(`Error opening folder: ${e}`);
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
            <!-- Badges for counts -->
            <div class="flex items-center gap-1 flex-shrink-0">
              {#if appCounts[app.app_name]?.sessionCount > 0}
                <span class="px-1.5 py-0.5 text-[10px] font-medium rounded bg-[var(--primary)]/20 text-[var(--primary)]" title="Sessions">
                  {appCounts[app.app_name].sessionCount}
                </span>
              {/if}
              {#if appCounts[app.app_name]?.autoBackupCount > 0}
                <span class="px-1.5 py-0.5 text-[10px] font-medium rounded bg-[var(--success)]/20 text-[var(--success)]" title="Auto-backups">
                  {appCounts[app.app_name].autoBackupCount}
                </span>
              {/if}
              {#if appCounts[app.app_name]?.addonCount > 0}
                <span class="px-1.5 py-0.5 text-[10px] font-medium rounded bg-[var(--warning)]/20 text-[var(--warning)]" title="Addons">
                  {appCounts[app.app_name].addonCount}
                </span>
              {/if}
            </div>
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
          <div class="flex items-center justify-between mb-3">
            <div>
              <h3 class="text-xl font-bold text-[var(--text-primary)]">{selectedApp.display_name}</h3>
              <div class="flex items-center gap-2 mt-0.5">
                <span 
                  class="w-2 h-2 rounded-full"
                  style="background-color: {getStatusColor(selectedApp)}"
                ></span>
                <span class="text-xs" style="color: {getStatusColor(selectedApp)}">{getStatusText(selectedApp)}</span>
              </div>
            </div>
          </div>

          <!-- Path -->
          <div class="mb-4">
            <span class="text-xs text-[var(--text-muted)] block mb-1">Data Path</span>
            <p class="text-xs text-[var(--text-secondary)] font-mono bg-[var(--bg-card)] px-3 py-1.5 rounded-lg truncate" title={selectedApp.dataPath || 'Not found'}>
              {selectedApp.dataPath || 'Data folder not found'}
            </p>
          </div>

          <!-- Action Buttons - 2 rows, 3 columns -->
          <div class="grid grid-cols-3 gap-2">
            <button
              class="flex items-center justify-center gap-2 px-4 py-3 rounded-lg bg-[var(--bg-card)] border border-[var(--border)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-[var(--primary)] transition-all disabled:opacity-30 disabled:cursor-not-allowed"
              on:click={handleOpenFolder}
              disabled={!selectedApp.dataPath}
              title="Open data folder"
            >
              <FolderOpen size={18} />
              <span class="text-xs font-medium">Folder</span>
            </button>
            <button
              class="flex items-center justify-center gap-2 px-4 py-3 rounded-lg bg-[var(--bg-card)] border border-[var(--border)] text-[var(--text-secondary)] hover:text-[var(--danger)] hover:border-[var(--danger)] transition-all disabled:opacity-30 disabled:cursor-not-allowed"
              on:click={handleReset}
              disabled={!selectedApp.dataPath}
              title="Reset all app data"
            >
              <RotateCcw size={18} />
              <span class="text-xs font-medium">Reset</span>
            </button>
            {#if addonCount > 0}
              <button
                class="flex items-center justify-center gap-2 px-4 py-3 rounded-lg bg-[var(--bg-card)] border border-[var(--border)] text-[var(--text-secondary)] hover:text-[var(--warning)] hover:border-[var(--warning)] transition-all"
                on:click={handleResetAddon}
                title="Delete addon folders ({addonCount})"
              >
                <Trash2 size={18} />
                <span class="text-xs font-medium">Addons</span>
              </button>
            {:else}
              <button
                class="flex items-center justify-center gap-2 px-4 py-3 rounded-lg bg-[var(--bg-card)] border border-[var(--border)] text-[var(--text-secondary)] hover:text-[var(--warning)] hover:border-[var(--warning)] transition-all disabled:opacity-30 disabled:cursor-not-allowed"
                on:click={handleNewID}
                disabled={!selectedApp.dataPath}
                title="Generate new machine ID"
              >
                <Fingerprint size={18} />
                <span class="text-xs font-medium">NewID</span>
              </button>
            {/if}
            {#if addonCount > 0}
              <button
                class="flex items-center justify-center gap-2 px-4 py-3 rounded-lg bg-[var(--bg-card)] border border-[var(--border)] text-[var(--text-secondary)] hover:text-[var(--warning)] hover:border-[var(--warning)] transition-all disabled:opacity-30 disabled:cursor-not-allowed"
                on:click={handleNewID}
                disabled={!selectedApp.dataPath}
                title="Generate new machine ID"
              >
                <Fingerprint size={18} />
                <span class="text-xs font-medium">NewID</span>
              </button>
            {/if}
            <button
              class="flex items-center justify-center gap-2 px-4 py-3 rounded-lg bg-[var(--bg-card)] border border-[var(--border)] text-[var(--text-secondary)] hover:text-[var(--danger)] hover:border-[var(--danger)] transition-all disabled:opacity-30 disabled:cursor-not-allowed"
              on:click={handleKillApp}
              disabled={!selectedApp.running}
              title="Force close app"
            >
              <XCircle size={18} />
              <span class="text-xs font-medium">Kill</span>
            </button>
            <button
              class="flex items-center justify-center gap-2 px-4 py-3 rounded-lg bg-[var(--bg-card)] border border-[var(--border)] text-[var(--text-secondary)] hover:text-[var(--success)] hover:border-[var(--success)] transition-all disabled:opacity-30 disabled:cursor-not-allowed"
              on:click={handleLaunch}
              disabled={!selectedApp.installed}
              title="Launch app"
            >
              <Play size={18} />
              <span class="text-xs font-medium">Launch</span>
            </button>
          </div>

          <!-- Stats -->
          <div class="flex items-center gap-6 mt-4 pt-4 border-t border-[var(--border)]">
            <div class="flex items-center gap-2">
              <Database size={14} class="text-[var(--text-muted)]" />
              <div>
                <span class="text-[10px] text-[var(--text-muted)] block">Sessions</span>
                <span class="text-xs font-medium text-[var(--text-primary)]">{sessionCount} backup(s)</span>
              </div>
            </div>
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

        <!-- Log Output -->
        <div class="flex-1 min-h-[120px] bg-[var(--bg-elevated)] rounded-xl border border-[var(--border)] flex flex-col overflow-hidden">
          <div class="flex items-center justify-between px-4 py-2 border-b border-[var(--border)]">
            <span class="text-sm text-[var(--text-secondary)]">Log Output</span>
            <button class="text-xs text-[var(--text-muted)] hover:text-[var(--text-secondary)]" on:click={clearLogs}>Clear</button>
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
