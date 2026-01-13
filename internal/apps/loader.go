// Package apps provides application configuration loading and management.
//
// This module loads app configurations dynamically from JSON files
// in the ~/.surfmanager/AppConfigs/ folder. Apps can be enabled/disabled via 'active' flag.
package apps

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"sync"
)

// AppConfig represents the configuration for an application.
// Note: The skip_data_folder field was removed in v2.1.0. Existing configs with this field
// will load successfully (Go's JSON unmarshaling ignores unknown fields by default).
type AppConfig struct {
	AppName     string       `json:"app_name"`
	DisplayName string       `json:"display_name"`
	Version     string       `json:"version"`
	Active      bool         `json:"active"`
	Description string       `json:"description"`
	Paths       AppPaths     `json:"paths"`
	BackupItems []BackupItem `json:"backup_items"`
	AddonPaths  []string     `json:"addon_backup_paths"`
}

// AppPaths contains the various paths associated with an application.
type AppPaths struct {
	DataPaths   []string `json:"data_paths"`
	ExePaths    []string `json:"exe_paths"`
	ResetFolder string   `json:"reset_folder"`
}

// BackupItem represents a single item to be backed up.
type BackupItem struct {
	Type        string `json:"type"`
	Path        string `json:"path"`
	Description string `json:"description"`
	Optional    bool   `json:"optional"`
}

// ConfigLoader handles loading and caching of application configurations.
type ConfigLoader struct {
	configDir   string
	loadedApps  map[string]*AppConfig
	activeCache []string
	mu          sync.RWMutex
}

// Global instance and initialization
var (
	globalLoader *ConfigLoader
	once         sync.Once
)

// NewConfigLoader creates a new ConfigLoader instance.
func NewConfigLoader() (*ConfigLoader, error) {
	homeDir, err := os.UserHomeDir()
	if err != nil {
		return nil, fmt.Errorf("failed to get home directory: %w", err)
	}

	configDir := filepath.Join(homeDir, ".surfmanager", "AppConfigs")

	loader := &ConfigLoader{
		configDir:  configDir,
		loadedApps: make(map[string]*AppConfig),
	}

	if err := loader.ensureConfigDir(); err != nil {
		return nil, err
	}

	return loader, nil
}

// GetLoader returns the global ConfigLoader instance, initializing it if necessary.
func GetLoader() (*ConfigLoader, error) {
	var initErr error
	once.Do(func() {
		globalLoader, initErr = NewConfigLoader()
		if initErr == nil {
			initErr = globalLoader.LoadAllConfigs()
		}
	})
	if initErr != nil {
		return nil, initErr
	}
	return globalLoader, nil
}

// ensureConfigDir ensures the AppConfigs directory exists.
func (cl *ConfigLoader) ensureConfigDir() error {
	return os.MkdirAll(cl.configDir, 0755)
}

// LoadAllConfigs loads all JSON configs from the AppConfigs folder.
func (cl *ConfigLoader) LoadAllConfigs() error {
	cl.mu.Lock()
	defer cl.mu.Unlock()

	// Clear existing data
	cl.loadedApps = make(map[string]*AppConfig)
	cl.activeCache = nil

	// Check if directory exists
	if _, err := os.Stat(cl.configDir); os.IsNotExist(err) {
		return nil // No configs to load
	}

	// Read all JSON files
	entries, err := os.ReadDir(cl.configDir)
	if err != nil {
		return fmt.Errorf("failed to read config directory: %w", err)
	}

	for _, entry := range entries {
		if entry.IsDir() || !strings.HasSuffix(strings.ToLower(entry.Name()), ".json") {
			continue
		}

		filePath := filepath.Join(cl.configDir, entry.Name())
		config, err := cl.loadConfigFile(filePath)
		if err != nil {
			fmt.Fprintf(os.Stderr, "WARNING: Failed to load %s: %v\n", entry.Name(), err)
			continue
		}

		if config.AppName == "" {
			fmt.Fprintf(os.Stderr, "WARNING: Config file %s missing 'app_name', skipping\n", entry.Name())
			continue
		}

		// Store with lowercase key for consistency
		cl.loadedApps[strings.ToLower(config.AppName)] = config
	}

	return nil
}

// loadConfigFile loads a single config file from disk.
func (cl *ConfigLoader) loadConfigFile(filePath string) (*AppConfig, error) {
	data, err := os.ReadFile(filePath)
	if err != nil {
		return nil, fmt.Errorf("failed to read file: %w", err)
	}

	var config AppConfig
	if err := json.Unmarshal(data, &config); err != nil {
		return nil, fmt.Errorf("failed to parse JSON: %w", err)
	}

	return &config, nil
}

// GetApp returns the configuration for a specific app.
// Returns nil if the app is not found.
func (cl *ConfigLoader) GetApp(appName string) *AppConfig {
	cl.mu.RLock()
	defer cl.mu.RUnlock()

	return cl.loadedApps[strings.ToLower(appName)]
}

// GetActiveApps returns a list of all active (enabled) app configurations.
func (cl *ConfigLoader) GetActiveApps() []AppConfig {
	cl.mu.RLock()
	defer cl.mu.RUnlock()

	var activeApps []AppConfig
	for _, config := range cl.loadedApps {
		if config.Active {
			activeApps = append(activeApps, *config)
		}
	}
	return activeApps
}

// GetAllApps returns a list of all loaded app configurations.
func (cl *ConfigLoader) GetAllApps() []AppConfig {
	cl.mu.RLock()
	defer cl.mu.RUnlock()

	apps := make([]AppConfig, 0, len(cl.loadedApps))
	for _, config := range cl.loadedApps {
		apps = append(apps, *config)
	}
	return apps
}

// GetActiveAppNames returns a list of active app names (cached).
func (cl *ConfigLoader) GetActiveAppNames() []string {
	cl.mu.Lock()
	defer cl.mu.Unlock()

	if cl.activeCache == nil {
		cl.activeCache = make([]string, 0)
		for name, config := range cl.loadedApps {
			if config.Active {
				cl.activeCache = append(cl.activeCache, name)
			}
		}
	}
	return cl.activeCache
}

// GetAllAppNames returns a list of all loaded app names.
func (cl *ConfigLoader) GetAllAppNames() []string {
	cl.mu.RLock()
	defer cl.mu.RUnlock()

	names := make([]string, 0, len(cl.loadedApps))
	for name := range cl.loadedApps {
		names = append(names, name)
	}
	return names
}

// IsAppActive checks if an app is active (enabled).
func (cl *ConfigLoader) IsAppActive(appName string) bool {
	config := cl.GetApp(appName)
	if config == nil {
		return false
	}
	return config.Active
}

// Reload reloads all configurations from disk.
func (cl *ConfigLoader) Reload() error {
	return cl.LoadAllConfigs()
}

// SaveConfig saves an app configuration to disk.
func (cl *ConfigLoader) SaveConfig(config AppConfig) error {
	if config.AppName == "" {
		return fmt.Errorf("app_name is required")
	}

	cl.mu.Lock()
	defer cl.mu.Unlock()

	// Ensure config directory exists
	if err := cl.ensureConfigDir(); err != nil {
		return err
	}

	// Create filename from app name
	filename := strings.ToLower(config.AppName) + ".json"
	filePath := filepath.Join(cl.configDir, filename)

	// Marshal config to JSON with indentation
	data, err := json.MarshalIndent(config, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal config: %w", err)
	}

	// Write to file
	if err := os.WriteFile(filePath, data, 0644); err != nil {
		return fmt.Errorf("failed to write config file: %w", err)
	}

	// Update cache
	cl.loadedApps[strings.ToLower(config.AppName)] = &config
	cl.activeCache = nil // Invalidate cache

	return nil
}

// DeleteConfig removes an app configuration from disk and cache.
func (cl *ConfigLoader) DeleteConfig(appName string) error {
	if appName == "" {
		return fmt.Errorf("app_name is required")
	}

	cl.mu.Lock()
	defer cl.mu.Unlock()

	lowerName := strings.ToLower(appName)

	// Check if config exists
	if _, exists := cl.loadedApps[lowerName]; !exists {
		return fmt.Errorf("app config '%s' not found", appName)
	}

	// Delete file
	filename := lowerName + ".json"
	filePath := filepath.Join(cl.configDir, filename)

	if err := os.Remove(filePath); err != nil && !os.IsNotExist(err) {
		return fmt.Errorf("failed to delete config file: %w", err)
	}

	// Remove from cache
	delete(cl.loadedApps, lowerName)
	cl.activeCache = nil // Invalidate cache

	return nil
}

// ToggleActive toggles the active state of an app configuration.
func (cl *ConfigLoader) ToggleActive(appName string) error {
	if appName == "" {
		return fmt.Errorf("app_name is required")
	}

	cl.mu.Lock()
	defer cl.mu.Unlock()

	lowerName := strings.ToLower(appName)

	config, exists := cl.loadedApps[lowerName]
	if !exists {
		return fmt.Errorf("app config '%s' not found", appName)
	}

	// Toggle active state
	config.Active = !config.Active

	// Save to disk
	filename := lowerName + ".json"
	filePath := filepath.Join(cl.configDir, filename)

	data, err := json.MarshalIndent(config, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal config: %w", err)
	}

	if err := os.WriteFile(filePath, data, 0644); err != nil {
		return fmt.Errorf("failed to write config file: %w", err)
	}

	// Invalidate cache
	cl.activeCache = nil

	return nil
}

// SetActive sets the active state of an app configuration.
func (cl *ConfigLoader) SetActive(appName string, active bool) error {
	if appName == "" {
		return fmt.Errorf("app_name is required")
	}

	cl.mu.Lock()
	defer cl.mu.Unlock()

	lowerName := strings.ToLower(appName)

	config, exists := cl.loadedApps[lowerName]
	if !exists {
		return fmt.Errorf("app config '%s' not found", appName)
	}

	// Set active state
	config.Active = active

	// Save to disk
	filename := lowerName + ".json"
	filePath := filepath.Join(cl.configDir, filename)

	data, err := json.MarshalIndent(config, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal config: %w", err)
	}

	if err := os.WriteFile(filePath, data, 0644); err != nil {
		return fmt.Errorf("failed to write config file: %w", err)
	}

	// Invalidate cache
	cl.activeCache = nil

	return nil
}

// GetConfigDir returns the path to the config directory.
func (cl *ConfigLoader) GetConfigDir() string {
	return cl.configDir
}

// Count returns the number of loaded app configurations.
func (cl *ConfigLoader) Count() int {
	cl.mu.RLock()
	defer cl.mu.RUnlock()
	return len(cl.loadedApps)
}

// ActiveCount returns the number of active app configurations.
func (cl *ConfigLoader) ActiveCount() int {
	cl.mu.RLock()
	defer cl.mu.RUnlock()

	count := 0
	for _, config := range cl.loadedApps {
		if config.Active {
			count++
		}
	}
	return count
}

// Package-level convenience functions

// LoadAllConfigs loads all configs using the global loader.
func LoadAllConfigs() error {
	loader, err := GetLoader()
	if err != nil {
		return err
	}
	return loader.LoadAllConfigs()
}

// GetApp returns an app config using the global loader.
func GetApp(appName string) *AppConfig {
	loader, err := GetLoader()
	if err != nil {
		return nil
	}
	return loader.GetApp(appName)
}

// GetActiveApps returns active apps using the global loader.
func GetActiveApps() []AppConfig {
	loader, err := GetLoader()
	if err != nil {
		return nil
	}
	return loader.GetActiveApps()
}

// GetAllApps returns all apps using the global loader.
func GetAllApps() []AppConfig {
	loader, err := GetLoader()
	if err != nil {
		return nil
	}
	return loader.GetAllApps()
}

// Reload reloads configs using the global loader.
func Reload() error {
	loader, err := GetLoader()
	if err != nil {
		return err
	}
	return loader.Reload()
}

// SaveConfig saves a config using the global loader.
func SaveConfig(config AppConfig) error {
	loader, err := GetLoader()
	if err != nil {
		return err
	}
	return loader.SaveConfig(config)
}

// DeleteConfig deletes a config using the global loader.
func DeleteConfig(appName string) error {
	loader, err := GetLoader()
	if err != nil {
		return err
	}
	return loader.DeleteConfig(appName)
}

// ToggleActive toggles active state using the global loader.
func ToggleActive(appName string) error {
	loader, err := GetLoader()
	if err != nil {
		return err
	}
	return loader.ToggleActive(appName)
}
