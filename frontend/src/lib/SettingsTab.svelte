<script>
  import { settings } from './stores/settings.js';
  import { 
    Settings, Cog, Database,
    ChevronRight, FolderOpen,
    Bell, Power
  } from 'lucide-svelte';
  import { OpenBackupFolder } from './api.js';
  import ThemeSelector from './ThemeSelector.svelte';
  import SettingToggle from './SettingToggle.svelte';

  let activeSection = 'general';
  

  const sections = [
    { id: 'general', label: 'General', icon: Settings },
    { id: 'notifications', label: 'Notifications', icon: Bell },
    { id: 'startup', label: 'Startup', icon: Power },
    { id: 'behavior', label: 'Behavior', icon: Cog },
    { id: 'sessions', label: 'Sessions', icon: Database },
  ];

  function toggle(key) {
    settings.update(key, !$settings[key]);
    if (key === 'enableNotepad') {
      // Restart UI to apply tab visibility immediately
      setTimeout(() => window.location.reload(), 150);
    }
  }

  function updateSetting(key, value) {
    settings.update(key, value);
  }

  // Open backup folder
  async function handleOpenBackupFolder() {
    try {
      await OpenBackupFolder();
    } catch (e) {
      alert(`Error: ${e}`);
    }
  }
  
</script>

<div class="h-full flex animate-fadeIn gap-4">
  <!-- Sidebar -->
  <div class="w-48 bg-[var(--bg-elevated)] rounded-xl border border-[var(--border)] p-2 flex flex-col gap-1">
    {#each sections as section}
      <button
        class="w-full flex items-center gap-2 px-3 py-2.5 rounded-lg text-left transition-all
          {activeSection === section.id 
            ? 'bg-[var(--primary)] text-white' 
            : 'hover:bg-[var(--bg-hover)] text-[var(--text-secondary)]'}"
        on:click={() => activeSection = section.id}
      >
        <svelte:component this={section.icon} size={16} />
        <span class="text-sm font-medium">{section.label}</span>
        <ChevronRight size={14} class="ml-auto opacity-50" />
      </button>
    {/each}
  </div>

  <!-- Content -->
  <div class="flex-1 overflow-y-auto">
    {#if activeSection === 'general'}
      <h2 class="text-lg font-semibold mb-4 text-[var(--text-primary)]">General</h2>
      
      <div class="space-y-3">
        <!-- Theme -->
        <div class="flex items-center justify-between p-4 bg-[var(--bg-card)] rounded-lg border border-[var(--border)]">
          <div>
            <p class="font-medium text-[var(--text-primary)]">Theme</p>
            <p class="text-sm text-[var(--text-secondary)]">Choose your preferred color scheme</p>
          </div>
          <ThemeSelector />
        </div>

        <SettingToggle
          label="Enable Notepad"
          description="Show Notes tab and features (UI will reload immediately)"
          checked={$settings.enableNotepad}
          on:change={() => toggle('enableNotepad')}
        />
      </div>

    {:else if activeSection === 'notifications'}
      <h2 class="text-lg font-semibold mb-4 text-[var(--text-primary)]">Notifications</h2>

      <div class="space-y-3">
        <SettingToggle
          label="Mute non-critical toasts"
          description="Only show error toasts"
          checked={$settings.muteToasts}
          on:change={() => toggle('muteToasts')}
        />

        <SettingToggle
          label="Toast sound"
          description="Enable sound for toasts"
          checked={$settings.toastSound}
          on:change={() => toggle('toastSound')}
        />
      </div>

    {:else if activeSection === 'startup'}
      <h2 class="text-lg font-semibold mb-4 text-[var(--text-primary)]">Startup</h2>

      <div class="space-y-3">
        <SettingToggle
          label="Remember last tab"
          description="Restore the last opened tab on startup"
          checked={$settings.rememberLastTab}
          on:change={() => toggle('rememberLastTab')}
        />

        <SettingToggle
          label="Auto refresh sessions on launch"
          description="Refresh Sessions list when app starts"
          checked={$settings.autoRefreshSessionsOnLaunch}
          on:change={() => toggle('autoRefreshSessionsOnLaunch')}
        />
      </div>

    {:else if activeSection === 'behavior'}
      <h2 class="text-lg font-semibold mb-4 text-[var(--text-primary)]">Behavior</h2>
      
      <div class="space-y-3">
        <SettingToggle
          label="Confirm Before Reset"
          description="Show confirmation dialog before resetting app data"
          checked={$settings.confirmBeforeReset}
          on:change={() => toggle('confirmBeforeReset')}
        />

        <SettingToggle
          label="Confirm Before Delete"
          description="Show confirmation dialog before deleting sessions"
          checked={$settings.confirmBeforeDelete}
          on:change={() => toggle('confirmBeforeDelete')}
        />

        <SettingToggle
          label="Confirm Before Restore"
          description="Show confirmation dialog before restoring sessions"
          checked={$settings.confirmBeforeRestore}
          on:change={() => toggle('confirmBeforeRestore')}
        />

        <SettingToggle
          label="Don't ask to start app after restore"
          description="Skip launch prompt after restore completes"
          checked={$settings.dontAskStartAfterComplete}
          on:change={() => toggle('dontAskStartAfterComplete')}
        />

        <SettingToggle
          label="Auto-Backup on Reset"
          description="Automatically create backup before reset operations"
          checked={$settings.autoBackup}
          on:change={() => toggle('autoBackup')}
        />
      </div>

    {:else if activeSection === 'sessions'}
      <h2 class="text-lg font-semibold mb-4 text-[var(--text-primary)]">Sessions</h2>

      <!-- Info Block -->
      <div class="p-4 mb-4 rounded-lg border border-[var(--border)] bg-[var(--bg-card)] space-y-2">
        <div class="flex items-center gap-2 text-[var(--text-primary)] font-semibold">
          <Database size={16} />
          <span>Sessions Backup & Restore</span>
        </div>
        <ul class="text-sm text-[var(--text-secondary)] space-y-1 list-disc list-inside">
          <li>Sessions may expire after weeks/months.</li>
          <li>Sessions are tied to this machine; cannot be transferred PC-to-PC due to Windows cryptography (encrypted data).</li>
        </ul>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-3">
        <div class="space-y-3">
          <SettingToggle
            label="Show Auto-Backups"
            description="Include auto-generated backups in session list by default"
            checked={$settings.showAutoBackups}
            on:change={() => toggle('showAutoBackups')}
          />

          <div class="p-4 bg-[var(--bg-card)] rounded-lg border border-[var(--border)] space-y-3">
            <div>
              <p class="font-medium text-[var(--text-primary)]">Max Auto-Backups</p>
              <p class="text-sm text-[var(--text-secondary)] mb-2">Keep recent auto-backups per app (oldest will be deleted)</p>
              <input 
                type="number" 
                min="1" 
                max="20" 
                value={$settings.maxAutoBackups}
                on:change={(e) => updateSetting('maxAutoBackups', parseInt(e.target.value) || 5)}
                class="w-full bg-[var(--bg-hover)] border border-[var(--border)] rounded-lg px-3 py-2 text-[var(--text-primary)] focus:outline-none focus:border-[var(--primary)]"
              />
            </div>
          </div>
        </div>

        <div class="space-y-3">
          <div class="p-4 bg-[var(--bg-card)] rounded-lg border border-[var(--border)] space-y-2">
            <p class="font-medium text-[var(--text-primary)]">Backup Folder</p>
            <p class="text-sm text-[var(--text-secondary)]">Open the folder where sessions are stored</p>
            <button
              class="w-full p-3 bg-[var(--bg-hover)] hover:bg-[var(--bg-card)] rounded-lg 
                     text-[var(--text-primary)] border border-[var(--border)] transition-colors flex items-center justify-center gap-2"
              on:click={handleOpenBackupFolder}
            >
              <FolderOpen size={16} />
              Open Backup Folder
            </button>
          </div>
        </div>
      </div>

    {/if}
  </div>
</div>
