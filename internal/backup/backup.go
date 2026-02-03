// Package backup handles session backup, restore, and management operations.
// It provides functionality for creating, restoring, and managing session backups
// for applications managed by SurfManager.
package backup

import (
	"encoding/json"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"time"
)

// Session represents a backup session with metadata.
type Session struct {
	Name     string    `json:"name"`
	App      string    `json:"app"`
	Size     int64     `json:"size"`
	Created  time.Time `json:"created"`
	Modified time.Time `json:"modified"`
	IsActive bool      `json:"is_active"`
	IsAuto   bool      `json:"is_auto"`
}

// BackupItem represents an item to be backed up with optional flag.
type BackupItem struct {
	Path     string `json:"path"`
	Optional bool   `json:"optional,omitempty"`
}

// BackupProgress represents progress information during backup/restore operations.
type BackupProgress struct {
	Percent int
	Message string
}

// ProgressCallback is a function type for progress updates.
type ProgressCallback func(progress BackupProgress)

// Manager handles backup operations and session management.
type Manager struct {
	documentsPath string
	backupPath    string
	autoBackupPath string
}

// NewManager creates a new backup manager with the specified documents path.
func NewManager(documentsPath string) *Manager {
	return &Manager{
		documentsPath:  documentsPath,
		backupPath:     filepath.Join(documentsPath, "SurfManager", "backup"),
		autoBackupPath: filepath.Join(documentsPath, "SurfManager", "auto-backups"),
	}
}

// GetBackupPath returns the base backup path.
func (m *Manager) GetBackupPath() string {
	return m.backupPath
}

// GetAutoBackupPath returns the auto-backup path.
func (m *Manager) GetAutoBackupPath() string {
	return m.autoBackupPath
}

// GetSessions returns all sessions for an app, optionally including auto-backups.
func (m *Manager) GetSessions(appKey string, includeAuto bool) ([]Session, error) {
	var sessions []Session
	appKey = strings.ToLower(appKey)

	// Get manual sessions
	manualSessions, err := m.getManualSessions(appKey)
	if err != nil {
		return nil, fmt.Errorf("failed to get manual sessions: %w", err)
	}
	sessions = append(sessions, manualSessions...)

	// Get auto-backups if requested
	if includeAuto {
		autoSessions, err := m.getAutoSessions(appKey)
		if err != nil {
			return nil, fmt.Errorf("failed to get auto sessions: %w", err)
		}
		sessions = append(sessions, autoSessions...)
	}

	// Sort by created time (newest first)
	sort.Slice(sessions, func(i, j int) bool {
		return sessions[i].Created.After(sessions[j].Created)
	})

	return sessions, nil
}

// getManualSessions retrieves manual backup sessions for an app.
func (m *Manager) getManualSessions(appKey string) ([]Session, error) {
	var sessions []Session
	appFolder := filepath.Join(m.backupPath, appKey)

	if _, err := os.Stat(appFolder); os.IsNotExist(err) {
		return sessions, nil
	}

	entries, err := os.ReadDir(appFolder)
	if err != nil {
		return nil, err
	}

	activeSession := m.GetActiveSession(appKey)

	for _, entry := range entries {
		if !entry.IsDir() {
			continue
		}

		name := entry.Name()
		// Skip auto-backups and hidden files
		if strings.HasPrefix(name, "auto-") || strings.HasPrefix(name, ".") {
			continue
		}

		sessionPath := filepath.Join(appFolder, name)
		info, err := entry.Info()
		if err != nil {
			continue
		}

		size, _ := m.calculateDirSize(sessionPath)

		session := Session{
			Name:     name,
			App:      appKey,
			Size:     size,
			Created:  info.ModTime(),
			Modified: info.ModTime(),
			IsActive: name == activeSession,
			IsAuto:   false,
		}
		sessions = append(sessions, session)
	}

	return sessions, nil
}

// getAutoSessions retrieves auto-backup sessions for an app.
func (m *Manager) getAutoSessions(appKey string) ([]Session, error) {
	var sessions []Session
	appFolder := filepath.Join(m.autoBackupPath, appKey)

	if _, err := os.Stat(appFolder); os.IsNotExist(err) {
		return sessions, nil
	}

	entries, err := os.ReadDir(appFolder)
	if err != nil {
		return nil, err
	}

	for _, entry := range entries {
		if !entry.IsDir() {
			continue
		}

		name := entry.Name()
		// Only include auto-backups
		if !strings.HasPrefix(name, "auto-") {
			continue
		}

		sessionPath := filepath.Join(appFolder, name)
		info, err := entry.Info()
		if err != nil {
			continue
		}

		size, _ := m.calculateDirSize(sessionPath)

		session := Session{
			Name:     name,
			App:      appKey,
			Size:     size,
			Created:  info.ModTime(),
			Modified: info.ModTime(),
			IsActive: false,
			IsAuto:   true,
		}
		sessions = append(sessions, session)
	}

	return sessions, nil
}

// CreateBackup creates a backup of app data to a session folder.
func (m *Manager) CreateBackup(appKey, sessionName string, sourcePath string, backupItems []BackupItem, addonPaths []string, addonOnly bool, progressCb ProgressCallback) error {
	appKey = strings.ToLower(appKey)
	backupFolder := filepath.Join(m.backupPath, appKey, sessionName)

	// Create backup directory
	if err := os.MkdirAll(backupFolder, 0755); err != nil {
		return fmt.Errorf("failed to create backup folder: %w", err)
	}

	if progressCb != nil {
		progressCb(BackupProgress{Percent: 10, Message: "Starting backup..."})
	}

	// Backup items - only backup specific items if defined and not addonOnly mode
	// When addonOnly=true, skip backing up the data folder entirely
	if !addonOnly && len(backupItems) > 0 {
		if err := m.backupSpecificItems(sourcePath, backupFolder, backupItems, progressCb); err != nil {
			return err
		}
	}
	// NOTE: If backupItems is empty or addonOnly=true, we intentionally skip backing up the data folder

	// Backup addon folders
	if len(addonPaths) > 0 {
		if err := m.backupAddons(backupFolder, addonPaths, progressCb); err != nil {
			return err
		}
	}

	// Save metadata
	if err := m.saveBackupMetadata(backupFolder, appKey, sessionName); err != nil {
		// Non-fatal error, just log
	}

	if progressCb != nil {
		progressCb(BackupProgress{Percent: 100, Message: "Backup complete!"})
	}

	return nil
}

// backupSpecificItems backs up specific items from the backup configuration.
func (m *Manager) backupSpecificItems(sourcePath, backupFolder string, items []BackupItem, progressCb ProgressCallback) error {
	totalItems := len(items)

	for i, item := range items {
		if item.Path == "" {
			continue
		}

		src := filepath.Join(sourcePath, item.Path)
		dst := filepath.Join(backupFolder, item.Path)

		if _, err := os.Stat(src); os.IsNotExist(err) {
			if !item.Optional {
				// Log skip for non-optional items
			}
			continue
		}

		// Ensure parent directory exists
		if err := os.MkdirAll(filepath.Dir(dst), 0755); err != nil {
			return fmt.Errorf("failed to create directory for %s: %w", item.Path, err)
		}

		info, err := os.Stat(src)
		if err != nil {
			continue
		}

		if info.IsDir() {
			if err := copyDir(src, dst); err != nil {
				return fmt.Errorf("failed to copy directory %s: %w", item.Path, err)
			}
		} else {
			if err := copyFile(src, dst); err != nil {
				return fmt.Errorf("failed to copy file %s: %w", item.Path, err)
			}
		}

		if progressCb != nil {
			progress := 30 + int(float64(i+1)/float64(totalItems)*50)
			progressCb(BackupProgress{Percent: progress, Message: fmt.Sprintf("Copying %s...", item.Path)})
		}
	}

	return nil
}

// backupAllItems backs up all items from the source directory.
func (m *Manager) backupAllItems(sourcePath, backupFolder string, progressCb ProgressCallback) error {
	entries, err := os.ReadDir(sourcePath)
	if err != nil {
		return fmt.Errorf("failed to read source directory: %w", err)
	}

	totalItems := len(entries)

	for i, entry := range entries {
		src := filepath.Join(sourcePath, entry.Name())
		dst := filepath.Join(backupFolder, entry.Name())

		if entry.IsDir() {
			if err := copyDir(src, dst); err != nil {
				return fmt.Errorf("failed to copy directory %s: %w", entry.Name(), err)
			}
		} else {
			if err := copyFile(src, dst); err != nil {
				return fmt.Errorf("failed to copy file %s: %w", entry.Name(), err)
			}
		}

		if progressCb != nil {
			progress := 30 + int(float64(i+1)/float64(totalItems)*50)
			progressCb(BackupProgress{Percent: progress, Message: fmt.Sprintf("Copying %s...", entry.Name())})
		}
	}

	return nil
}

// backupAddons backs up addon folders to the _addons subdirectory.
func (m *Manager) backupAddons(backupFolder string, addonPaths []string, progressCb ProgressCallback) error {
	addonBackupDir := filepath.Join(backupFolder, "_addons")
	if err := os.MkdirAll(addonBackupDir, 0755); err != nil {
		return fmt.Errorf("failed to create addon backup directory: %w", err)
	}

	for i, addonPath := range addonPaths {
		if _, err := os.Stat(addonPath); os.IsNotExist(err) {
			continue
		}

		addonName := filepath.Base(addonPath)
		addonDst := filepath.Join(addonBackupDir, addonName)

		info, err := os.Stat(addonPath)
		if err != nil {
			continue
		}

		if info.IsDir() {
			if err := copyDir(addonPath, addonDst); err != nil {
				// Log error but continue
				continue
			}
		} else {
			if err := copyFile(addonPath, addonDst); err != nil {
				continue
			}
		}

		if progressCb != nil {
			progress := 80 + int(float64(i+1)/float64(len(addonPaths))*15)
			progressCb(BackupProgress{Percent: progress, Message: fmt.Sprintf("Addon: %s...", addonName)})
		}
	}

	return nil
}

// RestoreBackup restores a backup session to the target path.
func (m *Manager) RestoreBackup(appKey, sessionName string, targetPath string, addonPaths []string, progressCb ProgressCallback) error {
	appKey = strings.ToLower(appKey)
	backupFolder := filepath.Join(m.backupPath, appKey, sessionName)

	// Check if backup exists
	if _, err := os.Stat(backupFolder); os.IsNotExist(err) {
		return fmt.Errorf("backup not found: %s", sessionName)
	}

	// Check if there are any backup items (excluding _addons)
	entries, err := os.ReadDir(backupFolder)
	if err != nil {
		return fmt.Errorf("failed to read backup folder: %w", err)
	}

	// Filter out _addons directory and metadata files
	var items []os.DirEntry
	for _, entry := range entries {
		if entry.Name() != "_addons" && !strings.HasPrefix(entry.Name(), ".") {
			items = append(items, entry)
		}
	}

	// Only clear and restore targetPath if there are backup items
	// This prevents clearing AppData when only addon_paths (like .aws) are configured
	if len(items) > 0 {
		if progressCb != nil {
			progressCb(BackupProgress{Percent: 10, Message: "Removing existing data..."})
		}

		// Remove existing data in target path
		if err := m.clearTargetPath(targetPath); err != nil {
			return fmt.Errorf("failed to clear target path: %w", err)
		}

		if progressCb != nil {
			progressCb(BackupProgress{Percent: 30, Message: "Restoring data..."})
		}

		totalItems := len(items)
		for i, entry := range items {
			src := filepath.Join(backupFolder, entry.Name())
			dst := filepath.Join(targetPath, entry.Name())

			if entry.IsDir() {
				if err := copyDir(src, dst); err != nil {
					return fmt.Errorf("failed to restore directory %s: %w", entry.Name(), err)
				}
			} else {
				if err := copyFile(src, dst); err != nil {
					return fmt.Errorf("failed to restore file %s: %w", entry.Name(), err)
				}
			}

			if progressCb != nil {
				progress := 30 + int(float64(i+1)/float64(totalItems)*50)
				progressCb(BackupProgress{Percent: progress, Message: fmt.Sprintf("Restoring %s...", entry.Name())})
			}
		}
	} else {
		if progressCb != nil {
			progressCb(BackupProgress{Percent: 50, Message: "No main data to restore, processing addons..."})
		}
	}

	// Restore addon folders
	if len(addonPaths) > 0 {
		if err := m.restoreAddons(backupFolder, addonPaths, progressCb); err != nil {
			// Log error but don't fail the restore
		}
	}

	if progressCb != nil {
		progressCb(BackupProgress{Percent: 100, Message: "Restore complete!"})
	}

	return nil
}

// RestoreAccountOnly restores only the auth state file (state.vscdb) for quick account switch
func (m *Manager) RestoreAccountOnly(appKey, sessionName string, targetPath string, progressCb ProgressCallback) error {
	appKey = strings.ToLower(appKey)
	backupFolder := filepath.Join(m.backupPath, appKey, sessionName)

	// Check if backup exists
	if _, err := os.Stat(backupFolder); os.IsNotExist(err) {
		return fmt.Errorf("backup not found: %s", sessionName)
	}

	// The auth state file path
	authFile := "User/globalStorage/state.vscdb"
	srcFile := filepath.Join(backupFolder, authFile)
	dstFile := filepath.Join(targetPath, authFile)

	// Check if auth file exists in backup
	if _, err := os.Stat(srcFile); os.IsNotExist(err) {
		return fmt.Errorf("auth state file not found in backup: %s", authFile)
	}

	if progressCb != nil {
		progressCb(BackupProgress{Percent: 30, Message: "Removing existing auth state..."})
	}

	// Remove existing auth file
	if _, err := os.Stat(dstFile); err == nil {
		if err := os.Remove(dstFile); err != nil {
			return fmt.Errorf("failed to remove existing auth file: %w", err)
		}
	}

	// Ensure destination directory exists
	if err := os.MkdirAll(filepath.Dir(dstFile), 0755); err != nil {
		return fmt.Errorf("failed to create directory: %w", err)
	}

	if progressCb != nil {
		progressCb(BackupProgress{Percent: 60, Message: "Copying auth state..."})
	}

	// Copy auth file
	if err := copyFile(srcFile, dstFile); err != nil {
		return fmt.Errorf("failed to copy auth file: %w", err)
	}

	if progressCb != nil {
		progressCb(BackupProgress{Percent: 100, Message: "Account switched!"})
	}

	return nil
}

// clearTargetPath removes all contents from the target path.
func (m *Manager) clearTargetPath(targetPath string) error {
	if _, err := os.Stat(targetPath); os.IsNotExist(err) {
		return os.MkdirAll(targetPath, 0755)
	}

	entries, err := os.ReadDir(targetPath)
	if err != nil {
		return err
	}

	var lastErr error
	for _, entry := range entries {
		itemPath := filepath.Join(targetPath, entry.Name())
		if entry.IsDir() {
			if err := os.RemoveAll(itemPath); err != nil {
				fmt.Printf("Warning: Failed to remove directory %s: %v\n", itemPath, err)
				lastErr = err
			}
		} else {
			if err := os.Remove(itemPath); err != nil {
				fmt.Printf("Warning: Failed to remove file %s: %v\n", itemPath, err)
				lastErr = err
			}
		}
	}

	// Return last error if any occurred, but we still tried to clean up everything
	if lastErr != nil {
		return fmt.Errorf("some items could not be removed: %w", lastErr)
	}

	return nil
}

// restoreAddons restores addon folders from the backup.
func (m *Manager) restoreAddons(backupFolder string, addonPaths []string, progressCb ProgressCallback) error {
	addonBackupDir := filepath.Join(backupFolder, "_addons")
	if _, err := os.Stat(addonBackupDir); os.IsNotExist(err) {
		return nil // No addons to restore
	}

	for i, addonPath := range addonPaths {
		addonName := filepath.Base(addonPath)
		addonSrc := filepath.Join(addonBackupDir, addonName)

		if _, err := os.Stat(addonSrc); os.IsNotExist(err) {
			continue
		}

		// Remove existing addon - don't wait if it fails, just continue
		if _, err := os.Stat(addonPath); err == nil {
			// Try to remove, but don't block on errors (file might not be locked)
			if err := os.RemoveAll(addonPath); err != nil {
				// Log but continue - the copy might still work or partially work
				fmt.Printf("Warning: Could not fully remove %s: %v (continuing anyway)\n", addonPath, err)
			}
		}

		// Ensure parent directory exists
		if err := os.MkdirAll(filepath.Dir(addonPath), 0755); err != nil {
			fmt.Printf("Warning: Could not create parent dir for %s: %v\n", addonPath, err)
			continue
		}

		info, err := os.Stat(addonSrc)
		if err != nil {
			continue
		}

		if info.IsDir() {
			if err := copyDir(addonSrc, addonPath); err != nil {
				fmt.Printf("Warning: Could not restore addon %s: %v\n", addonName, err)
				continue
			}
		} else {
			if err := copyFile(addonSrc, addonPath); err != nil {
				fmt.Printf("Warning: Could not restore addon file %s: %v\n", addonName, err)
				continue
			}
		}

		if progressCb != nil {
			progress := 80 + int(float64(i+1)/float64(len(addonPaths))*15)
			progressCb(BackupProgress{Percent: progress, Message: fmt.Sprintf("Addon: %s...", addonName)})
		}
	}

	return nil
}

// DeleteSession deletes a backup session.
func (m *Manager) DeleteSession(appKey, sessionName string) error {
	appKey = strings.ToLower(appKey)

	// Check if it's an auto-backup
	var sessionPath string
	if strings.HasPrefix(sessionName, "auto-") {
		sessionPath = filepath.Join(m.autoBackupPath, appKey, sessionName)
	} else {
		sessionPath = filepath.Join(m.backupPath, appKey, sessionName)
	}

	if _, err := os.Stat(sessionPath); os.IsNotExist(err) {
		return fmt.Errorf("session not found: %s", sessionName)
	}

	// Clear active marker if this session is active
	if m.GetActiveSession(appKey) == sessionName {
		m.clearActiveSession(appKey)
	}

	if err := os.RemoveAll(sessionPath); err != nil {
		return fmt.Errorf("failed to delete session: %w", err)
	}

	return nil
}

// SetActiveSession sets the active session for an app via marker file.
func (m *Manager) SetActiveSession(appKey, sessionName string) error {
	appKey = strings.ToLower(appKey)
	markerFile := filepath.Join(m.backupPath, appKey, ".active")

	// Ensure app directory exists
	if err := os.MkdirAll(filepath.Dir(markerFile), 0755); err != nil {
		return fmt.Errorf("failed to create app directory: %w", err)
	}

	if err := os.WriteFile(markerFile, []byte(sessionName), 0644); err != nil {
		return fmt.Errorf("failed to write active marker: %w", err)
	}

	return nil
}

// GetActiveSession returns the active session name for an app.
func (m *Manager) GetActiveSession(appKey string) string {
	appKey = strings.ToLower(appKey)
	markerFile := filepath.Join(m.backupPath, appKey, ".active")

	data, err := os.ReadFile(markerFile)
	if err != nil {
		return ""
	}

	return strings.TrimSpace(string(data))
}

// clearActiveSession removes the active session marker.
func (m *Manager) clearActiveSession(appKey string) error {
	appKey = strings.ToLower(appKey)
	markerFile := filepath.Join(m.backupPath, appKey, ".active")

	if _, err := os.Stat(markerFile); os.IsNotExist(err) {
		return nil
	}

	return os.Remove(markerFile)
}

// CreateAutoBackup creates an automatic backup before reset operations.
func (m *Manager) CreateAutoBackup(appKey string, sourcePath string, progressCb ProgressCallback) error {
	appKey = strings.ToLower(appKey)

	// Generate timestamp-based name
	timestamp := time.Now().Format("20060102_150405")
	sessionName := fmt.Sprintf("auto-%s", timestamp)

	autoBackupFolder := filepath.Join(m.autoBackupPath, appKey, sessionName)

	// Create auto-backup directory
	if err := os.MkdirAll(autoBackupFolder, 0755); err != nil {
		return fmt.Errorf("failed to create auto-backup folder: %w", err)
	}

	if progressCb != nil {
		progressCb(BackupProgress{Percent: 10, Message: "Creating auto-backup..."})
	}

	// Copy all items from source
	entries, err := os.ReadDir(sourcePath)
	if err != nil {
		return fmt.Errorf("failed to read source directory: %w", err)
	}

	totalItems := len(entries)
	for i, entry := range entries {
		src := filepath.Join(sourcePath, entry.Name())
		dst := filepath.Join(autoBackupFolder, entry.Name())

		if entry.IsDir() {
			if err := copyDir(src, dst); err != nil {
				return fmt.Errorf("failed to copy directory %s: %w", entry.Name(), err)
			}
		} else {
			if err := copyFile(src, dst); err != nil {
				return fmt.Errorf("failed to copy file %s: %w", entry.Name(), err)
			}
		}

		if progressCb != nil {
			progress := 10 + int(float64(i+1)/float64(totalItems)*85)
			progressCb(BackupProgress{Percent: progress, Message: fmt.Sprintf("Auto-backup: %s...", entry.Name())})
		}
	}

	// Cleanup old auto-backups (keep last 5)
	m.cleanupOldAutoBackups(appKey, 5)

	if progressCb != nil {
		progressCb(BackupProgress{Percent: 100, Message: "Auto-backup complete!"})
	}

	return nil
}

// cleanupOldAutoBackups removes old auto-backups, keeping only the specified count.
func (m *Manager) cleanupOldAutoBackups(appKey string, keepCount int) {
	appFolder := filepath.Join(m.autoBackupPath, appKey)

	entries, err := os.ReadDir(appFolder)
	if err != nil {
		return
	}

	// Filter auto-backups
	var autoBackups []os.DirEntry
	for _, entry := range entries {
		if entry.IsDir() && strings.HasPrefix(entry.Name(), "auto-") {
			autoBackups = append(autoBackups, entry)
		}
	}

	if len(autoBackups) <= keepCount {
		return
	}

	// Sort by name (timestamp-based, so alphabetical = chronological)
	sort.Slice(autoBackups, func(i, j int) bool {
		return autoBackups[i].Name() < autoBackups[j].Name()
	})

	// Remove oldest backups
	toRemove := len(autoBackups) - keepCount
	for i := 0; i < toRemove; i++ {
		path := filepath.Join(appFolder, autoBackups[i].Name())
		os.RemoveAll(path)
	}
}

// RenameSession renames a backup session.
func (m *Manager) RenameSession(appKey, oldName, newName string) error {
	appKey = strings.ToLower(appKey)
	oldPath := filepath.Join(m.backupPath, appKey, oldName)
	newPath := filepath.Join(m.backupPath, appKey, newName)

	if _, err := os.Stat(oldPath); os.IsNotExist(err) {
		return fmt.Errorf("session not found: %s", oldName)
	}

	if _, err := os.Stat(newPath); err == nil {
		return fmt.Errorf("session already exists: %s", newName)
	}

	if err := os.Rename(oldPath, newPath); err != nil {
		return fmt.Errorf("failed to rename session: %w", err)
	}

	// Update active marker if needed
	if m.GetActiveSession(appKey) == oldName {
		m.SetActiveSession(appKey, newName)
	}

	return nil
}

// SessionExists checks if a session exists for an app.
func (m *Manager) SessionExists(appKey, sessionName string) bool {
	appKey = strings.ToLower(appKey)
	sessionPath := filepath.Join(m.backupPath, appKey, sessionName)
	_, err := os.Stat(sessionPath)
	return err == nil
}

// GetSessionPath returns the full path to a session folder.
func (m *Manager) GetSessionPath(appKey, sessionName string) string {
	appKey = strings.ToLower(appKey)
	if strings.HasPrefix(sessionName, "auto-") {
		return filepath.Join(m.autoBackupPath, appKey, sessionName)
	}
	return filepath.Join(m.backupPath, appKey, sessionName)
}

// CountAutoBackups returns the count of auto-backups for an app.
func (m *Manager) CountAutoBackups(appKey string) int {
	appKey = strings.ToLower(appKey)
	appFolder := filepath.Join(m.autoBackupPath, appKey)

	entries, err := os.ReadDir(appFolder)
	if err != nil {
		return 0
	}

	count := 0
	for _, entry := range entries {
		if entry.IsDir() && strings.HasPrefix(entry.Name(), "auto-") {
			count++
		}
	}

	return count
}

// CountAllAutoBackups returns the total count of auto-backups across all apps.
func (m *Manager) CountAllAutoBackups() int {
	if _, err := os.Stat(m.autoBackupPath); os.IsNotExist(err) {
		return 0
	}

	entries, err := os.ReadDir(m.autoBackupPath)
	if err != nil {
		return 0
	}

	total := 0
	for _, entry := range entries {
		if entry.IsDir() {
			total += m.CountAutoBackups(entry.Name())
		}
	}

	return total
}

// saveBackupMetadata saves metadata about the backup.
func (m *Manager) saveBackupMetadata(backupFolder, appKey, sessionName string) error {
	metadata := map[string]interface{}{
		"app":     appKey,
		"session": sessionName,
		"created": time.Now().Format(time.RFC3339),
	}

	data, err := json.MarshalIndent(metadata, "", "  ")
	if err != nil {
		return err
	}

	metadataFile := filepath.Join(backupFolder, ".backup_meta.json")
	return os.WriteFile(metadataFile, data, 0644)
}

// calculateDirSize calculates the total size of a directory.
func (m *Manager) calculateDirSize(path string) (int64, error) {
	var size int64

	err := filepath.Walk(path, func(_ string, info os.FileInfo, err error) error {
		if err != nil {
			return nil // Skip errors
		}
		if !info.IsDir() {
			size += info.Size()
		}
		return nil
	})

	return size, err
}

// RestoreAddonsOnly restores only the addon folders from a backup session
func (m *Manager) RestoreAddonsOnly(appKey, sessionName string, addonPaths []string, progressCb ProgressCallback) error {
	appKey = strings.ToLower(appKey)
	backupFolder := m.GetSessionPath(appKey, sessionName)

	// Check if backup exists
	if _, err := os.Stat(backupFolder); os.IsNotExist(err) {
		return fmt.Errorf("backup not found: %s", sessionName)
	}

	// Check if _addons folder exists
	addonBackupDir := filepath.Join(backupFolder, "_addons")
	if _, err := os.Stat(addonBackupDir); os.IsNotExist(err) {
		return fmt.Errorf("no addon backups found in session: %s", sessionName)
	}

	if progressCb != nil {
		progressCb(BackupProgress{Percent: 10, Message: "Restoring addon folders..."})
	}

	// Restore addon folders
	if err := m.restoreAddons(backupFolder, addonPaths, progressCb); err != nil {
		return fmt.Errorf("failed to restore addons: %w", err)
	}

	if progressCb != nil {
		progressCb(BackupProgress{Percent: 100, Message: "Addon folders restored!"})
	}

	return nil
}

// SessionHasAddons checks if a session has _addons folder
func (m *Manager) SessionHasAddons(appKey, sessionName string) bool {
	appKey = strings.ToLower(appKey)
	backupFolder := m.GetSessionPath(appKey, sessionName)
	addonBackupDir := filepath.Join(backupFolder, "_addons")
	
	info, err := os.Stat(addonBackupDir)
	if err != nil {
		return false
	}
	return info.IsDir()
}

// FormatSize formats a byte size to human-readable string.
func FormatSize(bytes int64) string {
	const (
		KB = 1024
		MB = KB * 1024
		GB = MB * 1024
	)

	switch {
	case bytes >= GB:
		return fmt.Sprintf("%.1f GB", float64(bytes)/float64(GB))
	case bytes >= MB:
		return fmt.Sprintf("%.1f MB", float64(bytes)/float64(MB))
	case bytes >= KB:
		return fmt.Sprintf("%.1f KB", float64(bytes)/float64(KB))
	default:
		return fmt.Sprintf("%d B", bytes)
	}
}

// copyFile copies a single file from src to dst using a 1MB buffer for better performance.
func copyFile(src, dst string) error {
	sourceFile, err := os.Open(src)
	if err != nil {
		return err
	}
	defer sourceFile.Close()

	// Get source file info for permissions (reuse to avoid extra stat call)
	sourceInfo, err := sourceFile.Stat()
	if err != nil {
		return err
	}

	// Ensure destination directory exists
	if err := os.MkdirAll(filepath.Dir(dst), 0755); err != nil {
		return err
	}

	destFile, err := os.Create(dst)
	if err != nil {
		return err
	}
	defer destFile.Close()

	// Use 1MB buffer for better performance (32x larger than default 32KB)
	buf := make([]byte, 1024*1024)
	if _, err := io.CopyBuffer(destFile, sourceFile, buf); err != nil {
		return err
	}

	// Preserve file permissions
	return os.Chmod(dst, sourceInfo.Mode())
}

// copyDir recursively copies a directory from src to dst.
func copyDir(src, dst string) error {
	srcInfo, err := os.Stat(src)
	if err != nil {
		return err
	}

	if err := os.MkdirAll(dst, srcInfo.Mode()); err != nil {
		return err
	}

	entries, err := os.ReadDir(src)
	if err != nil {
		return err
	}

	for _, entry := range entries {
		srcPath := filepath.Join(src, entry.Name())
		dstPath := filepath.Join(dst, entry.Name())

		if entry.IsDir() {
			if err := copyDir(srcPath, dstPath); err != nil {
				return err
			}
		} else {
			if err := copyFile(srcPath, dstPath); err != nil {
				return err
			}
		}
	}

	return nil
}
