// Settings store with localStorage persistence
import { writable, get } from 'svelte/store';
import { APP_VERSION } from '../version.js';

const STORAGE_KEY = 'surfmanager-settings';

const defaultSettings = {
  // General
  theme: 'dark',
  
  // Remember Selected Apps
  lastSelectedAppReset: '',
  lastSelectedAppSession: '',
  
  // Behavior
  confirmBeforeReset: true,
  confirmBeforeDelete: true,
  confirmBeforeRestore: true,
  autoBackup: true,
  skipCloseApp: false,
  
  // Sessions
  showAutoBackups: false,
  defaultSessionFilter: 'all',
  maxAutoBackups: 5,
  
  // Notes (legacy, kept for compatibility)
  autoSaveNotes: false,
  autoSaveDelay: 3000,
  
  // Advanced (legacy, kept for compatibility)
  logRetention: 100,
  
  // Experimental Features
  showRestoreAddonOnly: false,
  experimentalRestoreAccountOnly: false, // Quick account switch (restore only state.vscdb)
};

function createSettingsStore() {
  // Get stored settings or defaults
  let stored = {};
  if (typeof localStorage !== 'undefined') {
    try {
      stored = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
    } catch (e) {
      stored = {};
    }
  }
  
  const initial = { ...defaultSettings, ...stored };
  const { subscribe, set, update } = writable(initial);

  return {
    subscribe,
    set: (settings) => {
      if (typeof localStorage !== 'undefined') {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
      }
      set(settings);
    },
    update: (key, value) => {
      update(s => {
        const newSettings = { ...s, [key]: value };
        if (typeof localStorage !== 'undefined') {
          localStorage.setItem(STORAGE_KEY, JSON.stringify(newSettings));
        }
        return newSettings;
      });
    },
    reset: () => {
      if (typeof localStorage !== 'undefined') {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(defaultSettings));
      }
      set(defaultSettings);
    },
    get: (key) => {
      let current = defaultSettings;
      subscribe(s => current = s)();
      return current[key];
    },
    
    // Export settings to JSON string
    exportSettings: () => {
      const currentSettings = get({ subscribe });
      const exportData = {
        version: APP_VERSION,
        exported_at: new Date().toISOString(),
        settings: {
          // General
          theme: currentSettings.theme,
          
          // Remember Selected Apps
          lastSelectedAppReset: currentSettings.lastSelectedAppReset,
          lastSelectedAppSession: currentSettings.lastSelectedAppSession,
          
          // Behavior
          confirmBeforeReset: currentSettings.confirmBeforeReset,
          confirmBeforeDelete: currentSettings.confirmBeforeDelete,
          confirmBeforeRestore: currentSettings.confirmBeforeRestore,
          autoBackup: currentSettings.autoBackup,
          skipCloseApp: currentSettings.skipCloseApp,
          
          // Sessions
          showAutoBackups: currentSettings.showAutoBackups,
          defaultSessionFilter: currentSettings.defaultSessionFilter,
          maxAutoBackups: currentSettings.maxAutoBackups,
          
          // Notes
          autoSaveNotes: currentSettings.autoSaveNotes,
          autoSaveDelay: currentSettings.autoSaveDelay,
          
          // Advanced
          logRetention: currentSettings.logRetention,
          
          // Experimental
          showRestoreAddonOnly: currentSettings.showRestoreAddonOnly,
          experimentalRestoreAccountOnly: currentSettings.experimentalRestoreAccountOnly,
        }
      };
      return JSON.stringify(exportData, null, 2);
    },
    
    // Import settings from JSON string
    importSettings: (jsonString) => {
      try {
        const importData = JSON.parse(jsonString);
        
        // Validate structure
        if (!importData.settings || typeof importData.settings !== 'object') {
          throw new Error('Invalid settings format: missing settings object');
        }
        
        // Merge with defaults (to handle missing fields)
        const newSettings = { ...defaultSettings };
        
        // Import only known settings
        const validKeys = Object.keys(defaultSettings);
        for (const key of validKeys) {
          if (importData.settings.hasOwnProperty(key)) {
            const value = importData.settings[key];
            // Type validation
            if (typeof value === typeof defaultSettings[key]) {
              newSettings[key] = value;
            }
          }
        }
        
        // Save and apply
        if (typeof localStorage !== 'undefined') {
          localStorage.setItem(STORAGE_KEY, JSON.stringify(newSettings));
        }
        set(newSettings);
        
        return { success: true, message: 'Settings imported successfully' };
      } catch (e) {
        return { success: false, message: `Import failed: ${e.message}` };
      }
    },
    
    // Reset all settings to defaults
    resetSettings: () => {
      const resetData = { ...defaultSettings };
      
      if (typeof localStorage !== 'undefined') {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(resetData));
      }
      set(resetData);
    },
    
    // Get default settings (for preview)
    getDefaults: () => {
      return { ...defaultSettings };
    }
  };
}

export const settings = createSettingsStore();
