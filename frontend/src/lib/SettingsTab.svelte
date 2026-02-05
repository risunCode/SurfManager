<script>
  import { settings } from './stores/settings.js';
  import { theme } from './stores/theme.js';
  import { 
    Settings, Cog, Database,
    RotateCcw, ChevronRight, Download, Upload, FolderOpen
  } from 'lucide-svelte';
  import { OpenBackupFolder } from '../../wailsjs/go/main/App.js';
  import ThemeSelector from './ThemeSelector.svelte';
  import SettingToggle from './SettingToggle.svelte';
  import { confirm } from './ConfirmModal.svelte';

  let activeSection = 'general';
  

  const sections = [
    { id: 'general', label: 'General', icon: Settings },
    { id: 'behavior', label: 'Behavior', icon: Cog },
    { id: 'sessions', label: 'Sessions', icon: Database },
  ];

  const settingsSectionOptions = [
    { id: 'all', label: 'All Settings' },
    { id: 'general', label: 'General' },
    { id: 'notifications', label: 'Notifications' },
    { id: 'startup', label: 'Startup' },
    { id: 'behavior', label: 'Behavior' },
    { id: 'sessions', label: 'Sessions' }
  ];

  const settingsSectionKeys = {
    general: ['theme', 'enableNotepad', 'dontAskStartAfterComplete'],
    notifications: ['muteToasts', 'toastSound', 'beepOnComplete'],
    startup: ['rememberLastTab', 'lastActiveTab', 'autoRefreshSessionsOnLaunch'],
    behavior: ['confirmBeforeReset', 'confirmBeforeDelete', 'confirmBeforeRestore', 'autoBackup'],
    sessions: ['showAutoBackups', 'maxAutoBackups']
  };

  let selectedSettingsSection = 'all';

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

  // Export settings to file
  async function handleExportSettings() {
    try {
      let jsonData = '';
      if (selectedSettingsSection === 'all') {
        jsonData = settings.exportSettings();
      } else {
        const keys = settingsSectionKeys[selectedSettingsSection] || [];
        const sectionData = {};
        for (const key of keys) {
          sectionData[key] = $settings[key];
        }
        jsonData = JSON.stringify({
          version: 'partial',
          exported_at: new Date().toISOString(),
          section: selectedSettingsSection,
          settings: sectionData
        }, null, 2);
      }
      const blob = new Blob([jsonData], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      const suffix = selectedSettingsSection === 'all' ? 'all' : selectedSettingsSection;
      a.download = `surfmanager-settings-${suffix}-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (e) {
      alert(`Export failed: ${e.message}`);
    }
  }

  // Import settings from file
  async function handleImportSettings() {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.json';
    input.onchange = async (e) => {
      const file = e.target.files[0];
      if (!file) return;
      
      try {
        const text = await file.text();
        const importData = JSON.parse(text);
        const importSection = importData.section || selectedSettingsSection || 'all';
        const keys = importSection === 'all'
          ? Object.keys(settings.getDefaults())
          : (settingsSectionKeys[importSection] || []);

        const incoming = importData.settings || {};
        const filtered = {};
        for (const key of keys) {
          if (Object.prototype.hasOwnProperty.call(incoming, key) && typeof incoming[key] === typeof settings.getDefaults()[key]) {
            filtered[key] = incoming[key];
          }
        }

        const previewLines = Object.keys(filtered)
          .map((key) => `- ${key}: ${JSON.stringify(filtered[key])}`)
          .join('\n');

        const confirmed = await confirm({
          title: 'Import Settings',
          message: `Section: ${importSection}\n\n${previewLines || 'No valid keys found.'}`,
          confirmText: 'Import',
          cancelText: 'Cancel'
        });
        if (!confirmed) return;
        if (Object.keys(filtered).length === 0) {
          alert('No valid settings to import.');
          return;
        }
        settings.applySettings(filtered);
        alert('Settings imported successfully!');
      } catch (err) {
        alert(`Import failed: ${err.message}`);
      }
    };
    input.click();
  }

  // Reset all settings
  async function handleResetSettings() {
    if (confirm('Reset all settings to default values?\n\nThis cannot be undone.')) {
      settings.resetSettings();
      alert('Settings reset to defaults!');
    }
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

        <SettingToggle
          label="Beep on complete"
          description="Play a short beep when operations finish"
          checked={$settings.beepOnComplete}
          on:change={() => toggle('beepOnComplete')}
        />

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

        <!-- Settings Management Section -->
        <div class="p-4 bg-[var(--bg-card)] rounded-lg border border-[var(--border)]">
          <p class="font-medium mb-2 text-[var(--text-primary)]">Settings Management</p>
          <p class="text-sm text-[var(--text-secondary)] mb-4">Import, export, or reset your settings</p>

          <select
            class="w-full mb-3 bg-[var(--bg-hover)] border border-[var(--border)] rounded-lg px-3 py-2 text-sm text-[var(--text-primary)] focus:outline-none focus:border-[var(--primary)]"
            bind:value={selectedSettingsSection}
          >
            {#each settingsSectionOptions as opt}
              <option value={opt.id}>{opt.label}</option>
            {/each}
          </select>
          
          <div class="grid grid-cols-3 gap-2">
            <button
              class="p-3 bg-[var(--bg-hover)] hover:bg-[var(--border)] rounded-lg 
                transition-colors flex items-center justify-center gap-2 border border-[var(--border)] text-[var(--text-primary)]"
              on:click={handleImportSettings}
            >
              <Upload size={16} />
              Import
            </button>
            
            <button
              class="p-3 bg-[var(--bg-hover)] hover:bg-[var(--border)] rounded-lg 
                transition-colors flex items-center justify-center gap-2 border border-[var(--border)] text-[var(--text-primary)]"
              on:click={handleExportSettings}
            >
              <Download size={16} />
              Export
            </button>
            
            <button
              class="p-3 bg-[var(--danger)]/10 text-[var(--danger)] rounded-lg 
                hover:bg-[var(--danger)]/20 transition-colors flex items-center justify-center gap-2 border border-[var(--danger)]/30"
              on:click={handleResetSettings}
            >
              <RotateCcw size={16} />
              Reset
            </button>
          </div>
        </div>
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
