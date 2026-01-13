// Package main provides the Wails binding layer that connects the frontend to all backend modules.
package main

import (
	"archive/zip"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
	"time"

	"surfmanager/internal/apps"
	"surfmanager/internal/backup"
	"surfmanager/internal/config"
	"surfmanager/internal/process"

	wailsRuntime "github.com/wailsapp/wails/v2/pkg/runtime"
)

// Note represents a user note with metadata.
type Note struct {
	ID        string `json:"id"`
	Title     string `json:"title"`
	Content   string `json:"content"`
	CreatedAt string `json:"created_at"`
	UpdatedAt string `json:"updated_at"`
}

// App struct holds all backend managers and provides Wails-bound methods.
type App struct {
	ctx     context.Context
	config  *config.Manager
	process *process.Killer
	backup  *backup.Manager
	apps    *apps.ConfigLoader
}

// NewApp creates a new App application struct.
func NewApp() *App {
	return &App{}
}

// startup is called when the app starts. Initializes all managers.
func (a *App) startup(ctx context.Context) {
	a.ctx = ctx
	a.config = config.GetManager()

	if err := a.config.EnsureSurfManagerDirs(); err != nil {
		fmt.Printf("Warning: Failed to create SurfManager directories: %v\n", err)
	}

	a.process = process.NewKiller(func(msg string) {
		fmt.Println(msg)
		wailsRuntime.EventsEmit(ctx, "log", msg)
	})

	a.backup = backup.NewManager(a.config.GetDocumentsDir())

	var err error
	a.apps, err = apps.NewConfigLoader()
	if err != nil {
		fmt.Printf("Warning: Failed to initialize apps loader: %v\n", err)
	} else {
		if err := a.apps.LoadAllConfigs(); err != nil {
			fmt.Printf("Warning: Failed to load app configs: %v\n", err)
		}
	}
}

// ============================================================================
// Platform Info
// ============================================================================

// GetPlatformInfo returns platform information
func (a *App) GetPlatformInfo() map[string]string {
	return a.config.GetPlatformInfo()
}

// GetCurrentUser returns the current username
func (a *App) GetCurrentUser() string {
	return a.config.GetCurrentUser()
}

// ============================================================================
// App Configuration Methods
// ============================================================================

// GetApps returns all configured applications
func (a *App) GetApps() []apps.AppConfig {
	if a.apps == nil {
		return []apps.AppConfig{}
	}
	return a.apps.GetAllApps()
}

// GetActiveApps returns only active applications
func (a *App) GetActiveApps() []apps.AppConfig {
	if a.apps == nil {
		return []apps.AppConfig{}
	}
	return a.apps.GetActiveApps()
}

// GetApp returns a specific app configuration
func (a *App) GetApp(appKey string) *apps.AppConfig {
	if a.apps == nil {
		return nil
	}
	return a.apps.GetApp(appKey)
}

// SaveApp saves an app configuration
func (a *App) SaveApp(config apps.AppConfig) error {
	if a.apps == nil {
		return fmt.Errorf("apps loader not initialized")
	}
	return a.apps.SaveConfig(config)
}

// DeleteApp removes an app configuration
func (a *App) DeleteApp(appKey string) error {
	if a.apps == nil {
		return fmt.Errorf("apps loader not initialized")
	}
	return a.apps.DeleteConfig(appKey)
}

// ToggleApp toggles the active state of an app
func (a *App) ToggleApp(appKey string) error {
	if a.apps == nil {
		return fmt.Errorf("apps loader not initialized")
	}
	return a.apps.ToggleActive(appKey)
}

// ReloadApps reloads all app configurations from disk
func (a *App) ReloadApps() error {
	if a.apps == nil {
		return fmt.Errorf("apps loader not initialized")
	}
	return a.apps.Reload()
}

// CheckAppInstalled checks if an app is installed by verifying exe paths
func (a *App) CheckAppInstalled(appKey string) bool {
	cfg := a.GetApp(appKey)
	if cfg == nil {
		return false
	}
	for _, exePath := range cfg.Paths.ExePaths {
		if _, err := os.Stat(exePath); err == nil {
			return true
		}
	}
	return false
}

// GetAppDataPath returns the first existing data path for an app
func (a *App) GetAppDataPath(appKey string) string {
	cfg := a.GetApp(appKey)
	if cfg == nil {
		return ""
	}
	for _, dataPath := range cfg.Paths.DataPaths {
		if _, err := os.Stat(dataPath); err == nil {
			return dataPath
		}
	}
	return ""
}

// ============================================================================
// Reset Data Methods
// ============================================================================

// ResetApp resets an application's data with optional auto-backup
func (a *App) ResetApp(appKey string, autoBackup bool, skipClose bool) error {
	cfg := a.GetApp(appKey)
	if cfg == nil {
		return fmt.Errorf("app not found: %s", appKey)
	}

	dataPath := a.GetAppDataPath(appKey)
	if dataPath == "" {
		return fmt.Errorf("no data folder found for %s", cfg.DisplayName)
	}

	// Get process names from exe paths
	var processNames []string
	for _, exePath := range cfg.Paths.ExePaths {
		processNames = append(processNames, filepath.Base(exePath))
	}

	// Smart close the app (unless skipClose is true)
	if !skipClose && len(processNames) > 0 {
		wailsRuntime.EventsEmit(a.ctx, "progress", map[string]interface{}{
			"percent": 5,
			"message": fmt.Sprintf("Closing %s...", cfg.DisplayName),
		})
		if err := a.process.SmartClose(cfg.DisplayName, processNames); err != nil {
			return fmt.Errorf("failed to close %s: %w", cfg.DisplayName, err)
		}
	}

	// Create auto-backup if enabled (includes addon folders)
	if autoBackup {
		wailsRuntime.EventsEmit(a.ctx, "progress", map[string]interface{}{
			"percent": 20,
			"message": "Creating auto-backup...",
		})
		if err := a.backup.CreateAutoBackup(appKey, dataPath, func(p backup.BackupProgress) {
			wailsRuntime.EventsEmit(a.ctx, "progress", map[string]interface{}{
				"percent": 20 + p.Percent/5,
				"message": p.Message,
			})
		}); err != nil {
			wailsRuntime.EventsEmit(a.ctx, "log", fmt.Sprintf("[AutoBackup] Failed: %v", err))
		}
	}

	// Only delete data folder if there are backup items configured
	// (meaning user wants to manage this folder)
	shouldResetDataFolder := len(cfg.BackupItems) > 0

	if shouldResetDataFolder {
		// Delete data folder
		wailsRuntime.EventsEmit(a.ctx, "progress", map[string]interface{}{
			"percent": 50,
			"message": fmt.Sprintf("Deleting %s data...", cfg.DisplayName),
		})

		if err := os.RemoveAll(dataPath); err != nil {
			return fmt.Errorf("failed to delete data: %w", err)
		}

		// Recreate empty folder
		if err := os.MkdirAll(dataPath, 0755); err != nil {
			return fmt.Errorf("failed to recreate folder: %w", err)
		}
	} else {
		wailsRuntime.EventsEmit(a.ctx, "progress", map[string]interface{}{
			"percent": 50,
			"message": "Skipping data folder (no backup items configured)...",
		})
	}

	// Delete addon folders if configured
	if len(cfg.AddonPaths) > 0 {
		wailsRuntime.EventsEmit(a.ctx, "progress", map[string]interface{}{
			"percent": 80,
			"message": "Deleting additional folders...",
		})

		for _, addonPath := range cfg.AddonPaths {
			if _, err := os.Stat(addonPath); err == nil {
				if err := os.RemoveAll(addonPath); err != nil {
					wailsRuntime.EventsEmit(a.ctx, "log", fmt.Sprintf("[Reset] Failed to delete addon folder %s: %v", addonPath, err))
				}
			}
		}
	}

	wailsRuntime.EventsEmit(a.ctx, "progress", map[string]interface{}{
		"percent": 100,
		"message": "Reset complete!",
	})

	return nil
}

// GenerateNewID generates new machine IDs for an app
func (a *App) GenerateNewID(appKey string) (int, error) {
	cfg := a.GetApp(appKey)
	if cfg == nil {
		return 0, fmt.Errorf("app not found: %s", appKey)
	}

	dataPath := a.GetAppDataPath(appKey)
	if dataPath == "" {
		return 0, fmt.Errorf("no data folder found for %s", cfg.DisplayName)
	}

	// Validate and clean the data path
	dataPath = filepath.Clean(dataPath)
	absDataPath, err := filepath.Abs(dataPath)
	if err != nil {
		return 0, fmt.Errorf("invalid data path: %w", err)
	}

	newMachineID := generateUUID()
	newSessionID := generateUUID()
	updatedCount := 0

	err = filepath.Walk(absDataPath, func(path string, info os.FileInfo, err error) error {
		if err != nil || info.IsDir() || !strings.HasSuffix(info.Name(), ".json") {
			return nil
		}

		// Validate that the path is within the expected data directory
		cleanPath := filepath.Clean(path)
		if !strings.HasPrefix(cleanPath, absDataPath) {
			return nil // Skip files outside the data directory
		}

		data, err := os.ReadFile(path)
		if err != nil {
			return nil
		}

		var jsonData map[string]interface{}
		if err := json.Unmarshal(data, &jsonData); err != nil {
			return nil
		}

		modified := false
		if _, ok := jsonData["machineId"]; ok {
			jsonData["machineId"] = newMachineID
			modified = true
			updatedCount++
		}
		if _, ok := jsonData["telemetry.machineId"]; ok {
			jsonData["telemetry.machineId"] = newMachineID
			modified = true
			updatedCount++
		}
		if _, ok := jsonData["sessionId"]; ok {
			jsonData["sessionId"] = newSessionID
			modified = true
			updatedCount++
		}

		// Force add to storage.json
		if info.Name() == "storage.json" {
			if _, ok := jsonData["machineId"]; !ok {
				jsonData["machineId"] = newMachineID
				jsonData["telemetry.machineId"] = newMachineID
				modified = true
				updatedCount += 2
			}
		}

		if modified {
			newData, err := json.MarshalIndent(jsonData, "", "  ")
			if err == nil {
				if writeErr := os.WriteFile(path, newData, 0644); writeErr != nil {
					fmt.Printf("Warning: Failed to write %s: %v\n", path, writeErr)
				}
			}
		}

		return nil
	})

	return updatedCount, err
}

// LaunchApp launches an application
func (a *App) LaunchApp(appKey string) error {
	cfg := a.GetApp(appKey)
	if cfg == nil {
		return fmt.Errorf("app not found: %s", appKey)
	}

	for _, exePath := range cfg.Paths.ExePaths {
		if _, err := os.Stat(exePath); err == nil {
			cmd := exec.Command(exePath)
			return cmd.Start()
		}
	}

	return fmt.Errorf("executable not found for %s", cfg.DisplayName)
}

// OpenFolder opens a folder in the file explorer
func (a *App) OpenFolder(path string) error {
	var cmd *exec.Cmd
	switch runtime.GOOS {
	case "windows":
		// Convert forward slashes to backslashes for Windows Explorer
		path = strings.ReplaceAll(path, "/", "\\")
		cmd = exec.Command("explorer", path)
	case "darwin":
		cmd = exec.Command("open", path)
	default:
		cmd = exec.Command("xdg-open", path)
	}
	return cmd.Start()
}

// OpenURL opens a URL in the user's default browser (not WebView)
func (a *App) OpenURL(url string) error {
	var cmd *exec.Cmd
	switch runtime.GOOS {
	case "windows":
		cmd = exec.Command("rundll32", "url.dll,FileProtocolHandler", url)
	case "darwin":
		cmd = exec.Command("open", url)
	default:
		cmd = exec.Command("xdg-open", url)
	}
	return cmd.Start()
}

// OpenAppFolder opens the app's data folder
func (a *App) OpenAppFolder(appKey string) error {
	dataPath := a.GetAppDataPath(appKey)
	if dataPath == "" {
		return fmt.Errorf("no data folder found")
	}
	return a.OpenFolder(dataPath)
}

// KillApp kills all processes for an app
func (a *App) KillApp(appKey string) error {
	cfg := a.GetApp(appKey)
	if cfg == nil {
		return fmt.Errorf("app not found: %s", appKey)
	}

	var processNames []string
	for _, exePath := range cfg.Paths.ExePaths {
		processNames = append(processNames, filepath.Base(exePath))
	}

	if len(processNames) == 0 {
		return nil
	}

	return a.process.SmartClose(cfg.DisplayName, processNames)
}

// ResetAddonData resets only the addon folders for an app
func (a *App) ResetAddonData(appKey string, skipClose bool) error {
	cfg := a.GetApp(appKey)
	if cfg == nil {
		return fmt.Errorf("app not found: %s", appKey)
	}

	if len(cfg.AddonPaths) == 0 {
		return fmt.Errorf("no addon folders configured for %s", cfg.DisplayName)
	}

	// Get process names from exe paths
	var processNames []string
	for _, exePath := range cfg.Paths.ExePaths {
		processNames = append(processNames, filepath.Base(exePath))
	}

	// Smart close the app (unless skipClose is true)
	if !skipClose && len(processNames) > 0 {
		wailsRuntime.EventsEmit(a.ctx, "progress", map[string]interface{}{
			"percent": 10,
			"message": fmt.Sprintf("Closing %s...", cfg.DisplayName),
		})
		if err := a.process.SmartClose(cfg.DisplayName, processNames); err != nil {
			return fmt.Errorf("failed to close %s: %w", cfg.DisplayName, err)
		}
	}

	wailsRuntime.EventsEmit(a.ctx, "progress", map[string]interface{}{
		"percent": 30,
		"message": "Deleting addon folders...",
	})

	deletedCount := 0
	for i, addonPath := range cfg.AddonPaths {
		if _, err := os.Stat(addonPath); err == nil {
			if err := os.RemoveAll(addonPath); err != nil {
				wailsRuntime.EventsEmit(a.ctx, "log", fmt.Sprintf("[ResetAddon] Failed to delete %s: %v", addonPath, err))
			} else {
				deletedCount++
			}
		}
		// Progress update
		progress := 30 + int(float64(i+1)/float64(len(cfg.AddonPaths))*60)
		wailsRuntime.EventsEmit(a.ctx, "progress", map[string]interface{}{
			"percent": progress,
			"message": fmt.Sprintf("Deleted: %s", filepath.Base(addonPath)),
		})
	}

	wailsRuntime.EventsEmit(a.ctx, "progress", map[string]interface{}{
		"percent": 100,
		"message": fmt.Sprintf("Reset complete! Deleted %d addon folder(s)", deletedCount),
	})

	return nil
}

// IsAppRunning checks if an app is currently running
func (a *App) IsAppRunning(appKey string) bool {
	cfg := a.GetApp(appKey)
	if cfg == nil {
		return false
	}

	var processNames []string
	for _, exePath := range cfg.Paths.ExePaths {
		processNames = append(processNames, filepath.Base(exePath))
	}

	return a.process.IsRunning(processNames)
}

// ============================================================================
// Session/Backup Methods
// ============================================================================

// GetSessions returns all sessions for an app
func (a *App) GetSessions(appKey string, includeAuto bool) ([]backup.Session, error) {
	return a.backup.GetSessions(appKey, includeAuto)
}

// GetAllSessions returns sessions for all apps
func (a *App) GetAllSessions(includeAuto bool) ([]backup.Session, error) {
	var allSessions []backup.Session
	apps := a.GetActiveApps()

	for _, app := range apps {
		sessions, err := a.backup.GetSessions(app.AppName, includeAuto)
		if err != nil {
			continue
		}
		allSessions = append(allSessions, sessions...)
	}

	return allSessions, nil
}

// CreateBackup creates a new backup session
func (a *App) CreateBackup(appKey, sessionName string, skipClose bool) error {
	cfg := a.GetApp(appKey)
	if cfg == nil {
		return fmt.Errorf("app not found: %s", appKey)
	}

	dataPath := a.GetAppDataPath(appKey)
	if dataPath == "" {
		return fmt.Errorf("no data folder found for %s", cfg.DisplayName)
	}

	// Check for duplicate
	if a.backup.SessionExists(appKey, sessionName) {
		return fmt.Errorf("session '%s' already exists", sessionName)
	}

	// Smart close the app first (unless skipClose is true)
	var processNames []string
	for _, exePath := range cfg.Paths.ExePaths {
		processNames = append(processNames, filepath.Base(exePath))
	}

	if !skipClose && len(processNames) > 0 {
		wailsRuntime.EventsEmit(a.ctx, "progress", map[string]interface{}{
			"percent": 5,
			"message": fmt.Sprintf("Closing %s...", cfg.DisplayName),
		})
		a.process.SmartClose(cfg.DisplayName, processNames)
	}

	// Convert backup items
	var backupItems []backup.BackupItem
	for _, item := range cfg.BackupItems {
		backupItems = append(backupItems, backup.BackupItem{
			Path:     item.Path,
			Optional: item.Optional,
		})
	}

	// Create backup
	return a.backup.CreateBackup(appKey, sessionName, dataPath, backupItems, cfg.AddonPaths, func(p backup.BackupProgress) {
		wailsRuntime.EventsEmit(a.ctx, "progress", map[string]interface{}{
			"percent": p.Percent,
			"message": p.Message,
		})
	})
}

// RestoreBackup restores a backup session
func (a *App) RestoreBackup(appKey, sessionName string, skipClose bool) error {
	cfg := a.GetApp(appKey)
	if cfg == nil {
		return fmt.Errorf("app not found: %s", appKey)
	}

	dataPath := a.GetAppDataPath(appKey)
	if dataPath == "" {
		// Use first data path as target
		if len(cfg.Paths.DataPaths) > 0 {
			dataPath = cfg.Paths.DataPaths[0]
		} else {
			return fmt.Errorf("no data path configured for %s", cfg.DisplayName)
		}
	}

	// Smart close the app first (unless skipClose is true)
	var processNames []string
	for _, exePath := range cfg.Paths.ExePaths {
		processNames = append(processNames, filepath.Base(exePath))
	}

	if !skipClose && len(processNames) > 0 {
		wailsRuntime.EventsEmit(a.ctx, "progress", map[string]interface{}{
			"percent": 5,
			"message": fmt.Sprintf("Closing %s...", cfg.DisplayName),
		})
		a.process.SmartClose(cfg.DisplayName, processNames)
	}

	// Restore backup
	err := a.backup.RestoreBackup(appKey, sessionName, dataPath, cfg.AddonPaths, func(p backup.BackupProgress) {
		wailsRuntime.EventsEmit(a.ctx, "progress", map[string]interface{}{
			"percent": p.Percent,
			"message": p.Message,
		})
	})

	if err == nil {
		// Set as active session
		a.backup.SetActiveSession(appKey, sessionName)

		// Generate new IDs after successful restore
		count, _ := a.GenerateNewID(appKey)
		wailsRuntime.EventsEmit(a.ctx, "progress", map[string]interface{}{
			"percent": 100,
			"message": fmt.Sprintf("Restore complete! Updated %d ID(s)", count),
		})
	}

	return err
}

// RestoreAccountOnly restores only the auth state file (state.vscdb) for quick account switch
func (a *App) RestoreAccountOnly(appKey, sessionName string) error {
	cfg := a.GetApp(appKey)
	if cfg == nil {
		return fmt.Errorf("app not found: %s", appKey)
	}

	dataPath := a.GetAppDataPath(appKey)
	if dataPath == "" {
		if len(cfg.Paths.DataPaths) > 0 {
			dataPath = cfg.Paths.DataPaths[0]
		} else {
			return fmt.Errorf("no data path configured for %s", cfg.DisplayName)
		}
	}

	// Always close the app first (required for file lock release)
	var processNames []string
	for _, exePath := range cfg.Paths.ExePaths {
		processNames = append(processNames, filepath.Base(exePath))
	}

	if len(processNames) > 0 {
		wailsRuntime.EventsEmit(a.ctx, "progress", map[string]interface{}{
			"percent": 10,
			"message": fmt.Sprintf("Closing %s...", cfg.DisplayName),
		})
		if err := a.process.SmartClose(cfg.DisplayName, processNames); err != nil {
			return fmt.Errorf("failed to close %s: %w", cfg.DisplayName, err)
		}
	}

	// Restore only the auth state file
	wailsRuntime.EventsEmit(a.ctx, "progress", map[string]interface{}{
		"percent": 50,
		"message": "Switching account...",
	})

	err := a.backup.RestoreAccountOnly(appKey, sessionName, dataPath, func(p backup.BackupProgress) {
		wailsRuntime.EventsEmit(a.ctx, "progress", map[string]interface{}{
			"percent": p.Percent,
			"message": p.Message,
		})
	})

	if err == nil {
		// Set as active session after successful restore
		a.backup.SetActiveSession(appKey, sessionName)

		// Generate new IDs after successful restore
		count, _ := a.GenerateNewID(appKey)
		wailsRuntime.EventsEmit(a.ctx, "progress", map[string]interface{}{
			"percent": 100,
			"message": fmt.Sprintf("Account switched! Updated %d ID(s)", count),
		})
	}

	return err
}

// DeleteSession deletes a backup session
func (a *App) DeleteSession(appKey, sessionName string) error {
	return a.backup.DeleteSession(appKey, sessionName)
}

// RenameSession renames a backup session
func (a *App) RenameSession(appKey, oldName, newName string) error {
	return a.backup.RenameSession(appKey, oldName, newName)
}

// SetActiveSession sets the active session for an app
func (a *App) SetActiveSession(appKey, sessionName string) error {
	return a.backup.SetActiveSession(appKey, sessionName)
}

// GetActiveSession returns the active session for an app
func (a *App) GetActiveSession(appKey string) string {
	return a.backup.GetActiveSession(appKey)
}

// OpenSessionFolder opens the session folder in file explorer
func (a *App) OpenSessionFolder(appKey, sessionName string) error {
	path := a.backup.GetSessionPath(appKey, sessionName)
	return a.OpenFolder(path)
}

// CountAutoBackups returns the count of auto-backups
func (a *App) CountAutoBackups() int {
	return a.backup.CountAllAutoBackups()
}

// ClearAllSessions deletes all backup sessions for all apps
func (a *App) ClearAllSessions() (int, error) {
	apps := a.GetActiveApps()
	deletedCount := 0

	for _, app := range apps {
		// Get all sessions including auto-backups
		sessions, err := a.backup.GetSessions(app.AppName, true)
		if err != nil {
			continue
		}

		for _, session := range sessions {
			if err := a.backup.DeleteSession(app.AppName, session.Name); err != nil {
				// Log error but continue with other sessions
				fmt.Printf("Warning: Failed to delete session %s/%s: %v\n", app.AppName, session.Name, err)
			} else {
				deletedCount++
			}
		}
	}

	return deletedCount, nil
}

// BackupAllSessions creates a zip archive of all sessions in the backup folder
func (a *App) BackupAllSessions() (string, error) {
	backupPath := a.backup.GetBackupPath()
	autoBackupPath := a.backup.GetAutoBackupPath()

	// Check if backup folder exists and has content
	if _, err := os.Stat(backupPath); os.IsNotExist(err) {
		return "", fmt.Errorf("no backup folder found")
	}

	// Generate archive filename with timestamp
	timestamp := time.Now().Format("20060102_150405")
	archiveName := fmt.Sprintf("surfmanager-backup-%s.zip", timestamp)

	// Use save dialog to let user choose location
	savePath, err := wailsRuntime.SaveFileDialog(a.ctx, wailsRuntime.SaveDialogOptions{
		Title:           "Save Backup Archive",
		DefaultFilename: archiveName,
		Filters: []wailsRuntime.FileFilter{
			{DisplayName: "ZIP Archive", Pattern: "*.zip"},
		},
	})

	if err != nil {
		return "", fmt.Errorf("failed to open save dialog: %w", err)
	}

	if savePath == "" {
		return "", fmt.Errorf("backup cancelled")
	}

	// Create the zip file
	zipFile, err := os.Create(savePath)
	if err != nil {
		return "", fmt.Errorf("failed to create archive: %w", err)
	}
	defer zipFile.Close()

	zipWriter := zip.NewWriter(zipFile)
	defer zipWriter.Close()

	// Add backup folder contents
	if err := a.addDirToZip(zipWriter, backupPath, "backup"); err != nil {
		return "", fmt.Errorf("failed to add backup folder: %w", err)
	}

	// Add auto-backups folder if it exists
	if _, err := os.Stat(autoBackupPath); err == nil {
		if err := a.addDirToZip(zipWriter, autoBackupPath, "auto-backups"); err != nil {
			return "", fmt.Errorf("failed to add auto-backups folder: %w", err)
		}
	}

	return savePath, nil
}

// addDirToZip recursively adds a directory to a zip archive
func (a *App) addDirToZip(zipWriter *zip.Writer, sourcePath, baseName string) error {
	return filepath.Walk(sourcePath, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return nil // Skip errors
		}

		// Get relative path
		relPath, err := filepath.Rel(sourcePath, path)
		if err != nil {
			return nil
		}

		// Create archive path with base name
		archivePath := filepath.Join(baseName, relPath)
		archivePath = filepath.ToSlash(archivePath) // Use forward slashes in zip

		if info.IsDir() {
			// Add directory entry
			if relPath != "." {
				_, err := zipWriter.Create(archivePath + "/")
				if err != nil {
					return nil
				}
			}
			return nil
		}

		// Skip hidden files
		if strings.HasPrefix(info.Name(), ".") {
			return nil
		}

		// Create file in zip
		writer, err := zipWriter.Create(archivePath)
		if err != nil {
			return nil
		}

		// Open and copy file
		file, err := os.Open(path)
		if err != nil {
			return nil
		}
		defer file.Close()

		_, err = io.Copy(writer, file)
		return nil
	})
}

// ============================================================================
// Notes Methods
// ============================================================================

// GetNotes returns all notes
func (a *App) GetNotes() ([]Note, error) {
	notesDir := a.config.GetNotesDir()
	var notes []Note

	entries, err := os.ReadDir(notesDir)
	if err != nil {
		if os.IsNotExist(err) {
			return notes, nil
		}
		return nil, err
	}

	for _, entry := range entries {
		if entry.IsDir() || !strings.HasSuffix(entry.Name(), ".json") {
			continue
		}

		filePath := filepath.Join(notesDir, entry.Name())
		data, err := os.ReadFile(filePath)
		if err != nil {
			continue
		}

		var note Note
		if err := json.Unmarshal(data, &note); err != nil {
			continue
		}

		note.ID = strings.TrimSuffix(entry.Name(), ".json")
		notes = append(notes, note)
	}

	return notes, nil
}

// GetNote returns a specific note
func (a *App) GetNote(id string) (*Note, error) {
	notesDir := a.config.GetNotesDir()
	filePath := filepath.Join(notesDir, id+".json")

	data, err := os.ReadFile(filePath)
	if err != nil {
		return nil, err
	}

	var note Note
	if err := json.Unmarshal(data, &note); err != nil {
		return nil, err
	}

	note.ID = id
	return &note, nil
}

// SaveNote saves a note
func (a *App) SaveNote(note Note) error {
	notesDir := a.config.GetNotesDir()
	if err := os.MkdirAll(notesDir, 0755); err != nil {
		return err
	}

	if note.ID == "" {
		note.ID = time.Now().Format("20060102_150405")
		note.CreatedAt = time.Now().Format(time.RFC3339)
	}
	note.UpdatedAt = time.Now().Format("2006-01-02 15:04")

	data, err := json.MarshalIndent(note, "", "  ")
	if err != nil {
		return err
	}

	filePath := filepath.Join(notesDir, note.ID+".json")
	return os.WriteFile(filePath, data, 0644)
}

// DeleteNote deletes a note
func (a *App) DeleteNote(id string) error {
	notesDir := a.config.GetNotesDir()
	filePath := filepath.Join(notesDir, id+".json")
	return os.Remove(filePath)
}

// ============================================================================
// File Dialog Methods
// ============================================================================

// SelectFile opens a file dialog to select a file
func (a *App) SelectFile(title string, filters []string) (string, error) {
	return wailsRuntime.OpenFileDialog(a.ctx, wailsRuntime.OpenDialogOptions{
		Title: title,
		Filters: []wailsRuntime.FileFilter{
			{DisplayName: "Executables", Pattern: "*.exe"},
			{DisplayName: "All Files", Pattern: "*.*"},
		},
	})
}

// SelectFolder opens a folder dialog
func (a *App) SelectFolder(title string) (string, error) {
	return wailsRuntime.OpenDirectoryDialog(a.ctx, wailsRuntime.OpenDialogOptions{
		Title: title,
	})
}

// SelectFolderFromHome opens a folder dialog starting from user home directory
func (a *App) SelectFolderFromHome(title string) (string, error) {
	homeDir, err := os.UserHomeDir()
	if err != nil {
		homeDir = ""
	}
	return wailsRuntime.OpenDirectoryDialog(a.ctx, wailsRuntime.OpenDialogOptions{
		Title:            title,
		DefaultDirectory: homeDir,
	})
}

// SelectFolderFromLocalPrograms opens a folder dialog starting from platform-specific programs directory
func (a *App) SelectFolderFromLocalPrograms(title string) (string, error) {
	var programsDir string
	homeDir, _ := os.UserHomeDir()

	switch runtime.GOOS {
	case "windows":
		localAppData := os.Getenv("LOCALAPPDATA")
		if localAppData == "" {
			localAppData = filepath.Join(homeDir, "AppData", "Local")
		}
		programsDir = filepath.Join(localAppData, "Programs")
		// Fallback to LocalAppData if Programs doesn't exist
		if _, err := os.Stat(programsDir); os.IsNotExist(err) {
			programsDir = localAppData
		}
	case "darwin":
		programsDir = "/Applications"
	default: // Linux
		programsDir = filepath.Join(homeDir, ".local", "bin")
		if _, err := os.Stat(programsDir); os.IsNotExist(err) {
			programsDir = "/usr/bin"
		}
	}

	return wailsRuntime.OpenDirectoryDialog(a.ctx, wailsRuntime.OpenDialogOptions{
		Title:            title,
		DefaultDirectory: programsDir,
	})
}

// SelectFolderFromRoaming opens a folder dialog starting from platform-specific app data directory
func (a *App) SelectFolderFromRoaming(title string) (string, error) {
	var appData string
	homeDir, _ := os.UserHomeDir()

	switch runtime.GOOS {
	case "windows":
		appData = os.Getenv("APPDATA")
		if appData == "" {
			appData = filepath.Join(homeDir, "AppData", "Roaming")
		}
	case "darwin":
		appData = filepath.Join(homeDir, "Library", "Application Support")
	default: // Linux
		appData = filepath.Join(homeDir, ".config")
		if _, err := os.Stat(appData); os.IsNotExist(err) {
			appData = filepath.Join(homeDir, ".local", "share")
		}
	}

	return wailsRuntime.OpenDirectoryDialog(a.ctx, wailsRuntime.OpenDialogOptions{
		Title:            title,
		DefaultDirectory: appData,
	})
}

// SelectExeFromLocalPrograms opens a file dialog for executables starting from platform-specific programs directory
func (a *App) SelectExeFromLocalPrograms(title string) (string, error) {
	var programsDir string
	homeDir, _ := os.UserHomeDir()

	switch runtime.GOOS {
	case "windows":
		localAppData := os.Getenv("LOCALAPPDATA")
		if localAppData == "" {
			localAppData = filepath.Join(homeDir, "AppData", "Local")
		}
		programsDir = filepath.Join(localAppData, "Programs")
		if _, err := os.Stat(programsDir); os.IsNotExist(err) {
			programsDir = localAppData
		}
	case "darwin":
		programsDir = "/Applications"
	default: // Linux
		programsDir = filepath.Join(homeDir, ".local", "bin")
		if _, err := os.Stat(programsDir); os.IsNotExist(err) {
			programsDir = "/usr/bin"
		}
	}

	// Platform-specific file filters
	var filters []wailsRuntime.FileFilter
	switch runtime.GOOS {
	case "windows":
		filters = []wailsRuntime.FileFilter{
			{DisplayName: "Executables", Pattern: "*.exe"},
			{DisplayName: "All Files", Pattern: "*.*"},
		}
	case "darwin":
		filters = []wailsRuntime.FileFilter{
			{DisplayName: "Applications", Pattern: "*.app"},
			{DisplayName: "All Files", Pattern: "*"},
		}
	default: // Linux
		filters = []wailsRuntime.FileFilter{
			{DisplayName: "All Files", Pattern: "*"},
		}
	}

	return wailsRuntime.OpenFileDialog(a.ctx, wailsRuntime.OpenDialogOptions{
		Title:            title,
		DefaultDirectory: programsDir,
		Filters:          filters,
	})
}

// ============================================================================
// Utility Methods
// ============================================================================

// OpenConfigFolder opens the app configs folder
func (a *App) OpenConfigFolder() error {
	if a.apps == nil {
		return fmt.Errorf("apps loader not initialized")
	}
	return a.OpenFolder(a.apps.GetConfigDir())
}

// OpenBackupFolder opens the backup folder
func (a *App) OpenBackupFolder() error {
	return a.OpenFolder(a.backup.GetBackupPath())
}

// FormatSize formats bytes to human readable string
func (a *App) FormatSize(bytes int64) string {
	return backup.FormatSize(bytes)
}

// RestoreAddonOnly restores only the addon folders from a backup session
func (a *App) RestoreAddonOnly(appKey, sessionName string, skipClose bool) error {
	cfg := a.GetApp(appKey)
	if cfg == nil {
		return fmt.Errorf("app not found: %s", appKey)
	}

	if len(cfg.AddonPaths) == 0 {
		return fmt.Errorf("no addon paths configured for %s", cfg.DisplayName)
	}

	// Check if session has _addons folder
	if !a.CheckSessionHasAddons(appKey, sessionName) {
		return fmt.Errorf("session '%s' does not have addon backups", sessionName)
	}

	// Get process names from exe paths
	var processNames []string
	for _, exePath := range cfg.Paths.ExePaths {
		processNames = append(processNames, filepath.Base(exePath))
	}

	// Smart close the app (unless skipClose is true)
	if !skipClose && len(processNames) > 0 {
		wailsRuntime.EventsEmit(a.ctx, "progress", map[string]interface{}{
			"percent": 5,
			"message": fmt.Sprintf("Closing %s...", cfg.DisplayName),
		})
		if err := a.process.SmartClose(cfg.DisplayName, processNames); err != nil {
			return fmt.Errorf("failed to close %s: %w", cfg.DisplayName, err)
		}
	}

	wailsRuntime.EventsEmit(a.ctx, "progress", map[string]interface{}{
		"percent": 20,
		"message": "Restoring addon folders...",
	})

	// Restore only addons from backup
	err := a.backup.RestoreAddonsOnly(appKey, sessionName, cfg.AddonPaths, func(p backup.BackupProgress) {
		wailsRuntime.EventsEmit(a.ctx, "progress", map[string]interface{}{
			"percent": 20 + int(float64(p.Percent)*0.8),
			"message": p.Message,
		})
	})

	if err != nil {
		return err
	}

	// Set as active session after successful restore
	a.backup.SetActiveSession(appKey, sessionName)

	// Generate new IDs after successful restore
	count, _ := a.GenerateNewID(appKey)
	wailsRuntime.EventsEmit(a.ctx, "progress", map[string]interface{}{
		"percent": 100,
		"message": fmt.Sprintf("Addon folders restored! Updated %d ID(s)", count),
	})

	return nil
}

// CheckSessionHasAddons checks if a session has _addons folder
func (a *App) CheckSessionHasAddons(appKey, sessionName string) bool {
	return a.backup.SessionHasAddons(appKey, sessionName)
}

// generateUUID generates a simple UUID
func generateUUID() string {
	return fmt.Sprintf("%08x-%04x-%04x-%04x-%012x",
		time.Now().UnixNano()&0xffffffff,
		time.Now().UnixNano()>>32&0xffff,
		0x4000|time.Now().UnixNano()>>48&0x0fff,
		0x8000|time.Now().UnixNano()>>60&0x3fff,
		time.Now().UnixNano())
}
