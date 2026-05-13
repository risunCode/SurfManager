<script>
  import { onMount, onDestroy } from 'svelte';
  import { RotateCcw, Database, Settings, FileText, Info, Github, User, Sliders, Clock } from 'lucide-svelte';
  import { APP_VERSION } from './lib/version.js';
  import ResetTab from './lib/ResetTab.svelte';
  import SessionsTab from './lib/SessionsTab.svelte';
  import ConfigTab from './lib/ConfigTab.svelte';
  import NotesTab from './lib/NotesTab.svelte';
  import SettingsTab from './lib/SettingsTab.svelte';
  import AboutTab from './lib/AboutTab.svelte';
  import Toast from './lib/Toast.svelte';
  import ConfirmModal from './lib/ConfirmModal.svelte';
  import { theme } from './lib/stores/theme.js';
  import { settings } from './lib/stores/settings.js';
  import { GetCurrentUser, GetPlatformInfo, GetActiveApps, IsAppRunning, LogMessage, EventsOn } from './lib/api.js';

  let activeTab = 'reset';
  let currentUser = '';
  let platform = '';
  let progress = { percent: 0, message: 'Ready' };
  let logs = [];
  let configShowAddDialog = false;
  
  // Realtime clock
  let currentTime = '';
  let clockInterval;

  // Global running apps detection
  let globalRunningAppsStatus = {};     // { appKey: boolean }
  let globalRunningCheckInterval;      // Interval for checking running status

  const baseTabs = [
    { id: 'reset', label: 'Reset', icon: RotateCcw },
    { id: 'sessions', label: 'Sessions', icon: Database },
    { id: 'config', label: 'Config', icon: Settings },
    { id: 'notes', label: 'Notes', icon: FileText },
    { id: 'settings', label: 'Settings', icon: Sliders },
    { id: 'about', label: 'About', icon: Info },
  ];
  let tabs = baseTabs;

  function updateClock() {
    const now = new Date();
    currentTime = now.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit',
      second: '2-digit',
      hour12: false 
    });
  }

  let handleWindowError;
  let handleUnhandledRejection;

  onMount(async () => {
    // Initialize theme
    theme.init();
    
    // Start clock
    updateClock();
    clockInterval = setInterval(updateClock, 1000);

    // Start global running apps detection
    startGlobalRunningAppsDetection();

    // Restore last tab if enabled
    if ($settings.rememberLastTab && $settings.lastActiveTab) {
      activeTab = $settings.lastActiveTab;
    }

    try {
      currentUser = await GetCurrentUser();
      const info = await GetPlatformInfo();
      platform = info.platform;
    } catch (e) {
      console.error(e);
    }

    EventsOn('progress', (data) => {
      progress = data;
    });

    EventsOn('log', (msg) => {
      const maxLogs = $settings.logRetention || 100;
      logs = [...logs.slice(-(maxLogs - 1)), msg];
    });

    handleWindowError = (event) => {
      const message = event?.error?.stack || event?.message || String(event);
      LogMessage(`[FrontendError] ${message}`);
    };
    handleUnhandledRejection = (event) => {
      const reason = event?.reason;
      const message = reason?.stack || reason?.message || JSON.stringify(reason);
      LogMessage(`[UnhandledRejection] ${message}`);
    };
    window.addEventListener('error', handleWindowError);
    window.addEventListener('unhandledrejection', handleUnhandledRejection);

    // Initialize tabs based on settings
    refreshTabs();
  });

  onDestroy(() => {
    if (clockInterval) clearInterval(clockInterval);
    if (globalRunningCheckInterval) clearInterval(globalRunningCheckInterval);
    if (handleWindowError) window.removeEventListener('error', handleWindowError);
    if (handleUnhandledRejection) window.removeEventListener('unhandledrejection', handleUnhandledRejection);
  });

  $: refreshTabs();

  function refreshTabs() {
    const allowNotes = $settings.enableNotepad;
    const computed = allowNotes ? baseTabs : baseTabs.filter(t => t.id !== 'notes');
    tabs = computed;
    // If current tab is notes but disabled, fallback to reset
    if (!allowNotes && activeTab === 'notes') {
      activeTab = 'reset';
    }
  }

  // Global running apps detection functions
  async function startGlobalRunningAppsDetection() {
    // Initial check
    await updateGlobalRunningAppsStatus();
    
    // Set up interval for periodic checks
    globalRunningCheckInterval = setInterval(async () => {
      await updateGlobalRunningAppsStatus();
    }, 3000); // Check every 3 seconds
  }

  async function updateGlobalRunningAppsStatus() {
    try {
      const activeApps = await GetActiveApps();
      const newStatus = {};
      
      for (const app of activeApps) {
        newStatus[app.app_name] = await IsAppRunning(app.app_name);
      }
      
      // Only update if status changed to avoid unnecessary re-renders
      const hasChanges = JSON.stringify(globalRunningAppsStatus) !== JSON.stringify(newStatus);
      if (hasChanges) {
        globalRunningAppsStatus = newStatus;
      }
    } catch (e) {
      console.error('Error updating global running apps status:', e);
    }
  }

  // Save active tab when changed
  $: if (activeTab && $settings.rememberLastTab) {
    settings.update('lastActiveTab', activeTab);
  }

  function openGithub() {
    window.open('https://github.com/risunCode/SurfManager', '_blank');
  }

  function handleNavigate(event) {
    const { tab, action } = event.detail;
    activeTab = tab;
    
    // Handle specific actions
    if (tab === 'config' && action === 'addApp') {
      // Small delay to ensure tab is rendered
      setTimeout(() => {
        configShowAddDialog = true;
      }, 100);
    }
  }
</script>

<!-- Global Components - Dipindahkan ke atas -->
<Toast />
<ConfirmModal />

<main class="h-screen flex bg-[var(--bg-base)]">
  <!-- Sidebar -->
  <aside class="w-[70px] bg-[var(--bg-elevated)] border-r border-[var(--border)] flex flex-col py-3 transition-colors">
    <div class="flex-1 flex flex-col gap-1 px-2">
      {#each tabs as tab}
        <button
          class="flex flex-col items-center gap-1 p-3 rounded-xl cursor-pointer transition-all duration-200
                 {activeTab === tab.id 
                   ? 'bg-[var(--primary-dim)] text-[var(--primary-light)]' 
                   : 'text-[var(--text-muted)] hover:bg-[var(--bg-hover)] hover:text-[var(--text-secondary)]'}"
          on:click={() => activeTab = tab.id}
          title={tab.label}
        >
          <svelte:component this={tab.icon} size={20} />
          <span class="text-[10px] font-medium">{tab.label}</span>
        </button>
      {/each}
    </div>
    
    <div class="px-2 space-y-1">
      <button 
        class="flex flex-col items-center gap-1 p-3 rounded-xl text-[var(--text-muted)] hover:bg-[var(--bg-hover)] hover:text-[var(--text-secondary)] w-full transition-colors"
        on:click={openGithub} 
        title="GitHub"
      >
        <Github size={18} />
      </button>
    </div>
  </aside>

  <!-- Main Content -->
  <div class="flex-1 flex flex-col overflow-hidden">
    <!-- Header -->
    <header class="h-12 bg-[var(--bg-elevated)] border-b border-[var(--border)] flex items-center justify-between px-4 transition-colors">
      <h1 class="text-lg font-semibold text-[var(--text-primary)]">
        SurfManager
        <span class="text-xs text-[var(--text-muted)] ml-2">v{APP_VERSION}</span>
      </h1>
      <div class="flex items-center gap-4 text-sm text-[var(--text-muted)]">
        <span class="flex items-center gap-1.5 px-3 py-1 rounded-full bg-[var(--bg-card)] border border-[var(--border)]">
          <Clock size={14} class="text-[var(--primary)]" />
          <span class="font-mono text-[var(--text-primary)]">{currentTime}</span>
        </span>
        
        <!-- Global Running Apps Indicator -->
        {#if Object.values(globalRunningAppsStatus).some(running => running)}
          <span class="flex items-center gap-1.5 px-3 py-1 rounded-full bg-red-500/20 border border-red-500/30">
            <div class="w-2 h-2 bg-red-400 rounded-full animate-pulse"></div>
            <span class="text-red-400 font-medium">
              {Object.values(globalRunningAppsStatus).filter(running => running).length} Running
            </span>
          </span>
        {/if}
        
        <span class="capitalize">{platform}</span>
        <span class="flex items-center gap-1">
          <User size={14} />
          {currentUser}
        </span>
      </div>
    </header>

    <!-- Content Area -->
    <div class="flex-1 overflow-auto p-4">
      {#if activeTab === 'reset'}
        <ResetTab bind:logs on:navigate={handleNavigate} globalRunningAppsStatus={globalRunningAppsStatus} />
      {:else if activeTab === 'sessions'}
        <SessionsTab bind:logs globalRunningAppsStatus={globalRunningAppsStatus} />
      {:else if activeTab === 'config'}
        <ConfigTab bind:logs bind:showAddDialog={configShowAddDialog} globalRunningAppsStatus={globalRunningAppsStatus} />
      {:else if activeTab === 'notes' && $settings.enableNotepad}
        <NotesTab />
      {:else if activeTab === 'settings'}
        <SettingsTab />
      {:else if activeTab === 'about'}
        <AboutTab />
      {/if}
    </div>

    <!-- Footer -->
    <footer class="h-10 bg-[var(--bg-elevated)] border-t border-[var(--border)] flex items-center gap-4 px-4 text-xs transition-colors">
      <span class="text-[var(--text-muted)] flex-shrink-0">{progress.message}</span>
      <div class="flex-1 h-2 bg-[var(--bg-hover)] rounded-full overflow-hidden">
        <div 
          class="h-full bg-gradient-to-r from-[var(--primary)] to-[var(--primary-light)] transition-all duration-300"
          style="width: {progress.percent}%"
        ></div>
      </div>
      <span class="text-[var(--text-muted)] flex-shrink-0 w-10 text-right">{progress.percent}%</span>
    </footer>
  </div>
</main>
