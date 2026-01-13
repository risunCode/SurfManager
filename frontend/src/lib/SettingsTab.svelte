<script>
  import { settings } from './stores/settings.js';
  import { theme } from './stores/theme.js';
  import { 
    Settings, Cog, Database, FlaskConical,
    RotateCcw, ChevronRight, Download, Upload, FolderOpen, AlertTriangle, Trash2, Archive
  } from 'lucide-svelte';
  import { OpenBackupFolder, ClearAllSessions, BackupAllSessions } from '../../wailsjs/go/main/App.js';
  import ThemeSelector from './ThemeSelector.svelte';
  import SettingToggle from './SettingToggle.svelte';
  import { confirm } from './ConfirmModal.svelte';
  import { toast } from './Toast.svelte';

  let activeSection = 'general';
  
  // Loading states
  let isClearing = false;
  let isBackingUp = false;

  const sections = [
    { id: 'general', label: 'General', icon: Settings },
    { id: 'behavior', label: 'Behavior', icon: Cog },
    { id: 'sessions', label: 'Sessions', icon: Database },
    { id: 'experimental', label: 'Experimental', icon: FlaskConical },
  ];

  function toggle(key) {
    settings.update(key, !$settings[key]);
  }

  function updateSetting(key, value) {
    settings.update(key, value);
  }

  // Export settings to file
  async function handleExportSettings() {
    try {
      const jsonData = settings.exportSettings();
      const blob = new Blob([jsonData], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `surfmanager-settings-${new Date().toISOString().split('T')[0]}.json`;
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
        const result = settings.importSettings(text);
        if (result.success) {
          alert('Settings imported successfully!');
        } else {
          alert(result.message);
        }
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
  
  // Backup all sessions
  async function handleBackupAllSessions() {
    if (isBackingUp) return;
    
    isBackingUp = true;
    try {
      const archivePath = await BackupAllSessions();
      toast.success(`Backup saved successfully`);
    } catch (e) {
      if (e.toString().includes('cancelled')) {
        // User cancelled, no toast needed
      } else {
        toast.error(`Backup failed: ${e}`);
      }
    } finally {
      isBackingUp = false;
    }
  }
  
  // Clear all sessions
  async function handleClearAllSessions() {
    if (isClearing) return;
    
    const confirmed = await confirm.danger({
      title: 'Clear All Sessions',
      message: 'Are you sure you want to delete ALL backup sessions for ALL apps?\n\nThis action cannot be undone.',
      confirmText: 'Clear All'
    });
    
    if (!confirmed) return;
    
    isClearing = true;
    try {
      const deletedCount = await ClearAllSessions();
      toast.success(`Deleted ${deletedCount} session(s)`);
    } catch (e) {
      toast.error(`Clear failed: ${e}`);
    } finally {
      isClearing = false;
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

        <!-- Settings Management Section -->
        <div class="p-4 bg-[var(--bg-card)] rounded-lg border border-[var(--border)]">
          <p class="font-medium mb-2 text-[var(--text-primary)]">Settings Management</p>
          <p class="text-sm text-[var(--text-secondary)] mb-4">Import, export, or reset your settings</p>
          
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
          label="Auto-Backup on Reset"
          description="Automatically create backup before reset operations"
          checked={$settings.autoBackup}
          on:change={() => toggle('autoBackup')}
        />

        <SettingToggle
          label="Skip Close App"
          description="Don't close target app before reset/backup/restore operations (may cause file lock errors)"
          checked={$settings.skipCloseApp}
          on:change={() => toggle('skipCloseApp')}
        />
      </div>

    {:else if activeSection === 'sessions'}
      <h2 class="text-lg font-semibold mb-4 text-[var(--text-primary)]">Sessions</h2>
      
      <div class="space-y-3">
        <SettingToggle
          label="Show Auto-Backups"
          description="Include auto-generated backups in session list by default"
          checked={$settings.showAutoBackups}
          on:change={() => toggle('showAutoBackups')}
        />

        <div class="p-4 bg-[var(--bg-card)] rounded-lg border border-[var(--border)]">
          <p class="font-medium mb-2 text-[var(--text-primary)]">Max Auto-Backups</p>
          <p class="text-sm text-[var(--text-secondary)] mb-3">
            Maximum number of auto-backups to keep per app (oldest will be deleted)
          </p>
          <input 
            type="number" 
            min="1" 
            max="20" 
            value={$settings.maxAutoBackups}
            on:change={(e) => updateSetting('maxAutoBackups', parseInt(e.target.value) || 5)}
            class="w-full bg-[var(--bg-hover)] border border-[var(--border)] rounded-lg px-3 py-2 text-[var(--text-primary)] focus:outline-none focus:border-[var(--primary)]"
          />
        </div>

        <div class="p-4 bg-[var(--bg-card)] rounded-lg border border-[var(--border)]">
          <p class="font-medium mb-2 text-[var(--text-primary)]">Default Filter</p>
          <p class="text-sm text-[var(--text-secondary)] mb-3">Default app filter when opening Sessions tab</p>
          <select 
            class="w-full bg-[var(--bg-hover)] border border-[var(--border)] rounded-lg px-3 py-2 text-[var(--text-primary)] focus:outline-none focus:border-[var(--primary)]"
            bind:value={$settings.defaultSessionFilter}
            on:change={(e) => updateSetting('defaultSessionFilter', e.target.value)}
          >
            <option value="all">All Apps</option>
            <option value="active">Active Only</option>
          </select>
        </div>

        <!-- Open Backup Folder Button -->
        <button
          class="w-full p-3 bg-[var(--bg-card)] hover:bg-[var(--bg-hover)] rounded-lg 
            transition-colors flex items-center justify-center gap-2 border border-[var(--border)] text-[var(--text-primary)]"
          on:click={handleOpenBackupFolder}
        >
          <FolderOpen size={16} />
          Open Backup Folder
        </button>

        <!-- Bulk Session Management -->
        <div class="p-4 bg-[var(--bg-card)] rounded-lg border border-[var(--border)]">
          <p class="font-medium mb-2 text-[var(--text-primary)]">Bulk Session Management</p>
          <p class="text-sm text-[var(--text-secondary)] mb-4">Backup or clear all sessions at once</p>
          
          <div class="grid grid-cols-2 gap-2">
            <button
              class="p-3 bg-[var(--bg-hover)] hover:bg-[var(--border)] rounded-lg 
                transition-colors flex items-center justify-center gap-2 border border-[var(--border)] text-[var(--text-primary)]
                disabled:opacity-50 disabled:cursor-not-allowed"
              on:click={handleBackupAllSessions}
              disabled={isBackingUp}
            >
              <Archive size={16} />
              {isBackingUp ? 'Backing up...' : 'Backup All'}
            </button>
            
            <button
              class="p-3 bg-[var(--danger)]/10 text-[var(--danger)] rounded-lg 
                hover:bg-[var(--danger)]/20 transition-colors flex items-center justify-center gap-2 border border-[var(--danger)]/30
                disabled:opacity-50 disabled:cursor-not-allowed"
              on:click={handleClearAllSessions}
              disabled={isClearing}
            >
              <Trash2 size={16} />
              {isClearing ? 'Clearing...' : 'Clear All'}
            </button>
          </div>
        </div>
      </div>

    {:else if activeSection === 'experimental'}
      <h2 class="text-lg font-semibold mb-4 text-[var(--text-primary)]">Experimental Features</h2>
      
      <!-- Warning Banner -->
      <div class="p-4 bg-[var(--warning)]/10 border border-[var(--warning)]/30 rounded-lg mb-4 flex items-start gap-3">
        <AlertTriangle size={20} class="text-[var(--warning)] flex-shrink-0 mt-0.5" />
        <div>
          <p class="text-sm font-medium text-[var(--warning)]">Use at your own risk</p>
          <p class="text-sm text-[var(--text-secondary)]">
            These features are experimental and may not work as expected. They may be removed or changed in future versions.
          </p>
        </div>
      </div>

      <div class="space-y-3">
        <SettingToggle
          label="Show Restore Addon Only"
          description="Enable 'Restore Addon Only' option in session context menu. Restores only addon folders (like .aws, .ssh) without touching main data."
          checked={$settings.showRestoreAddonOnly}
          on:change={() => toggle('showRestoreAddonOnly')}
        />

        <SettingToggle
          label="Restore Account Only"
          description="Enable quick account switch in Sessions context menu. Only restores auth state (state.vscdb), preserving extensions and settings."
          checked={$settings.experimentalRestoreAccountOnly}
          on:change={() => toggle('experimentalRestoreAccountOnly')}
        />
      </div>
    {/if}
  </div>
</div>
