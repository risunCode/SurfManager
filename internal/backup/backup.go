// Package backup handles session backup, restore, and management operations.
// It provides functionality for creating, restoring, and managing session backups
// for applications managed by SurfManager.
package backup

import (
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"runtime"
	"sort"
	"strings"
	"sync"
	"time"
)

// validatePath ensures the path is safe and doesn't allow directory traversal
func validatePath(basePath, inputPath string) (string, error) {
	// Clean the input path
	cleanPath := filepath.Clean(inputPath)

	// Join with base path and clean again
	fullPath := filepath.Clean(filepath.Join(basePath, cleanPath))

	// Check if the resulting path is still within the base path
	if !strings.HasPrefix(fullPath, filepath.Clean(basePath)+string(os.PathSeparator)) {
		return "", fmt.Errorf("path traversal detected: %s", inputPath)
	}

	return fullPath, nil
}

// Session represents a backup session with metadata.
type Session struct {
	Name      string `json:"name"`
	App       string `json:"app"`
	Size      int64  `json:"size"`
	Created   string `json:"created"`
	Modified  string `json:"modified"`
	IsActive  bool   `json:"is_active"`
	IsAuto    bool   `json:"is_auto"`
	Corrupted bool   `json:"corrupted,omitempty"`
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

// CopyJob represents a file to be copied.
type CopyJob struct {
	Src     string
	Dst     string
	RelPath string // For progress reporting
}

// FileCopyResult holds the result of a file copy operation.
type FileCopyResult struct {
	RelPath string
	Size    int64
	Hash    string // SHA256 of individual file
	Skipped bool   // True if file unchanged (incremental)
	Err     error
}

// BackupMetadata represents the full metadata stored in .backup_meta.json.
type BackupMetadata struct {
	App         string `json:"app"`
	Session     string `json:"session"`
	Created     string `json:"created"`
	Hash        string `json:"hash"`
	HashVersion int    `json:"hash_version,omitempty"`
	Size        int64  `json:"size,omitempty"`
	FileCount   int    `json:"file_count,omitempty"`
}

// Manager handles backup operations and session management.
type Manager struct {
	documentsPath  string
	backupPath     string
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
		parse := func(s string) time.Time {
			if s == "" {
				return time.Time{}
			}
			t, err := time.Parse(time.RFC3339, s)
			if err != nil {
				return time.Time{}
			}
			return t
		}
		return parse(sessions[i].Created).After(parse(sessions[j].Created))
	})

	return sessions, nil
}

// getManualSessions retrieves manual backup sessions for an app.
// Uses cached metadata for size when available (no hash verification at listing time).
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

		// Read full metadata for cached values
		meta := m.readBackupMetadataFull(sessionPath)

		var size int64
		if meta != nil && meta.Size > 0 {
			size = meta.Size // Use cached size (fast)
		} else {
			size, _ = m.calculateDirSize(sessionPath) // Fallback
		}

		createdAt := info.ModTime()
		if meta != nil && meta.Created != "" {
			if t, parseErr := time.Parse(time.RFC3339, meta.Created); parseErr == nil {
				createdAt = t
			}
		}

		session := Session{
			Name:      name,
			App:       appKey,
			Size:      size,
			Created:   createdAt.Format(time.RFC3339),
			Modified:  info.ModTime().Format(time.RFC3339),
			IsActive:  name == activeSession,
			IsAuto:    false,
			Corrupted: false, // Don't verify at listing time - use lazy verification
		}
		sessions = append(sessions, session)
	}

	return sessions, nil
}

// getAutoSessions retrieves auto-backup sessions for an app.
// Uses cached metadata for size when available (no hash verification at listing time).
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

		// Read full metadata for cached values
		meta := m.readBackupMetadataFull(sessionPath)

		var size int64
		if meta != nil && meta.Size > 0 {
			size = meta.Size // Use cached size (fast)
		} else {
			size, _ = m.calculateDirSize(sessionPath) // Fallback
		}

		createdAt := info.ModTime()
		if meta != nil && meta.Created != "" {
			if t, parseErr := time.Parse(time.RFC3339, meta.Created); parseErr == nil {
				createdAt = t
			}
		}

		session := Session{
			Name:      name,
			App:       appKey,
			Size:      size,
			Created:   createdAt.Format(time.RFC3339),
			Modified:  info.ModTime().Format(time.RFC3339),
			IsActive:  false,
			IsAuto:    true,
			Corrupted: false, // Don't verify at listing time - use lazy verification
		}
		sessions = append(sessions, session)
	}

	return sessions, nil
}

// CreateBackup creates a backup of app data to a session folder.
// Uses parallel file copying with streaming hash computation for optimal performance.
func (m *Manager) CreateBackup(appKey, sessionName string, sourcePath string, backupItems []BackupItem, addonPaths []string, addonOnly bool, progressCb ProgressCallback) error {
	appKey = strings.ToLower(appKey)

	// Validate appKey and sessionName to prevent path traversal
	if strings.Contains(appKey, "..") || strings.Contains(sessionName, "..") {
		return fmt.Errorf("invalid characters in appKey or sessionName")
	}

	backupFolder := filepath.Join(m.backupPath, appKey, sessionName)

	// Create backup directory
	if err := os.MkdirAll(backupFolder, 0755); err != nil {
		return fmt.Errorf("failed to create backup folder: %w", err)
	}

	if progressCb != nil {
		progressCb(BackupProgress{Percent: 5, Message: "Collecting files..."})
	}

	// Collect all copy jobs
	var allJobs []CopyJob

	// Collect backup items jobs (if not addonOnly)
	if !addonOnly && len(backupItems) > 0 {
		itemJobs, err := m.collectCopyJobsFromItems(sourcePath, backupFolder, backupItems)
		if err != nil {
			return err
		}
		allJobs = append(allJobs, itemJobs...)
	}

	// Collect addon jobs
	if len(addonPaths) > 0 {
		addonBackupDir := filepath.Join(backupFolder, "_addons")
		if err := os.MkdirAll(addonBackupDir, 0755); err != nil {
			return fmt.Errorf("failed to create addon backup directory: %w", err)
		}
		addonJobs, err := m.collectCopyJobsFromAddons(addonBackupDir, addonPaths)
		if err != nil {
			return err
		}
		allJobs = append(allJobs, addonJobs...)
	}

	if len(allJobs) == 0 {
		if progressCb != nil {
			progressCb(BackupProgress{Percent: 100, Message: "No files to backup"})
		}
		return nil
	}

	if progressCb != nil {
		progressCb(BackupProgress{Percent: 10, Message: fmt.Sprintf("Copying %d files...", len(allJobs))})
	}

	// Determine worker count (use NumCPU, but cap at reasonable limits)
	workerCount := runtime.NumCPU()
	if workerCount < 2 {
		workerCount = 2
	}
	if workerCount > 16 {
		workerCount = 16
	}

	// Run parallel copy with progress callback that maps to 10-90%
	results, err := m.copyWithWorkerPool(allJobs, workerCount, func(p BackupProgress) {
		if progressCb != nil {
			// Map 0-100% to 10-90%
			mappedPercent := 10 + int(float64(p.Percent)*0.8)
			progressCb(BackupProgress{Percent: mappedPercent, Message: p.Message})
		}
	})
	if err != nil {
		return fmt.Errorf("failed during file copy: %w", err)
	}

	if progressCb != nil {
		progressCb(BackupProgress{Percent: 92, Message: "Computing checksum..."})
	}

	// Aggregate stats from results
	var totalSize int64
	for _, r := range results {
		if r.Err == nil {
			totalSize += r.Size
		}
	}
	hash := computeHashFromResults(results)

	if progressCb != nil {
		progressCb(BackupProgress{Percent: 95, Message: "Saving metadata..."})
	}

	// Save enhanced metadata
	if err := m.saveBackupMetadata(backupFolder, appKey, sessionName, totalSize, len(results), hash); err != nil {
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

		// Validate paths to prevent traversal
		src, err := validatePath(sourcePath, item.Path)
		if err != nil {
			if item.Optional {
				continue // Skip optional items with invalid paths
			}
			return fmt.Errorf("invalid source path for item %s: %w", item.Path, err)
		}

		dst, err := validatePath(backupFolder, item.Path)
		if err != nil {
			return fmt.Errorf("invalid destination path for item %s: %w", item.Path, err)
		}

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
// Uses parallel file copying for optimal performance.
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
			progressCb(BackupProgress{Percent: 5, Message: "Removing existing data..."})
		}

		// Remove existing data in target path
		if err := m.clearTargetPath(targetPath); err != nil {
			return fmt.Errorf("failed to clear target path: %w", err)
		}

		if progressCb != nil {
			progressCb(BackupProgress{Percent: 10, Message: "Collecting files to restore..."})
		}

		// Collect all files from backup items
		var jobs []CopyJob
		for _, entry := range items {
			src := filepath.Join(backupFolder, entry.Name())
			dst := filepath.Join(targetPath, entry.Name())

			if entry.IsDir() {
				// Walk the directory and collect all files
				err := filepath.Walk(src, func(path string, finfo os.FileInfo, walkErr error) error {
					if walkErr != nil || finfo.IsDir() {
						return nil
					}
					relToSrc, _ := filepath.Rel(src, path)
					relPath := filepath.Join(entry.Name(), relToSrc)
					dstPath := filepath.Join(dst, relToSrc)

					jobs = append(jobs, CopyJob{
						Src:     path,
						Dst:     dstPath,
						RelPath: relPath,
					})
					return nil
				})
				if err != nil {
					return fmt.Errorf("failed to collect files from %s: %w", entry.Name(), err)
				}
			} else {
				jobs = append(jobs, CopyJob{
					Src:     src,
					Dst:     dst,
					RelPath: entry.Name(),
				})
			}
		}

		if len(jobs) > 0 {
			if progressCb != nil {
				progressCb(BackupProgress{Percent: 15, Message: fmt.Sprintf("Restoring %d files...", len(jobs))})
			}

			// Determine worker count
			workerCount := runtime.NumCPU()
			if workerCount < 2 {
				workerCount = 2
			}
			if workerCount > 16 {
				workerCount = 16
			}

			// Run parallel copy with progress callback that maps to 15-80%
			_, err := m.copyWithWorkerPool(jobs, workerCount, func(p BackupProgress) {
				if progressCb != nil {
					mappedPercent := 15 + int(float64(p.Percent)*0.65)
					progressCb(BackupProgress{Percent: mappedPercent, Message: p.Message})
				}
			})
			if err != nil {
				return fmt.Errorf("failed during file restore: %w", err)
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
		progressCb(BackupProgress{Percent: 5, Message: "Collecting files for auto-backup..."})
	}

	// Collect all files from source
	jobs, err := m.collectCopyJobs(sourcePath, autoBackupFolder)
	if err != nil {
		return fmt.Errorf("failed to collect files: %w", err)
	}

	if len(jobs) == 0 {
		if progressCb != nil {
			progressCb(BackupProgress{Percent: 100, Message: "No files to backup"})
		}
		return nil
	}

	if progressCb != nil {
		progressCb(BackupProgress{Percent: 10, Message: fmt.Sprintf("Copying %d files...", len(jobs))})
	}

	// Determine worker count
	workerCount := runtime.NumCPU()
	if workerCount < 2 {
		workerCount = 2
	}
	if workerCount > 16 {
		workerCount = 16
	}

	// Run parallel copy with progress callback that maps to 10-90%
	results, err := m.copyWithWorkerPool(jobs, workerCount, func(p BackupProgress) {
		if progressCb != nil {
			mappedPercent := 10 + int(float64(p.Percent)*0.8)
			progressCb(BackupProgress{Percent: mappedPercent, Message: fmt.Sprintf("Auto-backup: %s", p.Message)})
		}
	})
	if err != nil {
		return fmt.Errorf("failed during file copy: %w", err)
	}

	// Aggregate stats and save metadata
	var totalSize int64
	for _, r := range results {
		if r.Err == nil {
			totalSize += r.Size
		}
	}
	hash := computeHashFromResults(results)

	if err := m.saveBackupMetadata(autoBackupFolder, appKey, sessionName, totalSize, len(results), hash); err != nil {
		// Non-fatal error
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

// saveBackupMetadata saves metadata about the backup including cached size and file count.
func (m *Manager) saveBackupMetadata(backupFolder, appKey, sessionName string, size int64, fileCount int, hash string) error {
	metadata := BackupMetadata{
		App:         appKey,
		Session:     sessionName,
		Created:     time.Now().Format(time.RFC3339),
		Hash:        hash,
		HashVersion: 2,
		Size:        size,
		FileCount:   fileCount,
	}

	data, err := json.MarshalIndent(metadata, "", "  ")
	if err != nil {
		return err
	}

	metadataFile := filepath.Join(backupFolder, ".backup_meta.json")
	return os.WriteFile(metadataFile, data, 0644)
}

// saveBackupMetadataLegacy saves metadata using the legacy format (for auto-backups).
func (m *Manager) saveBackupMetadataLegacy(backupFolder, appKey, sessionName string) error {
	hashValue, _ := m.computeBackupHash(backupFolder)

	metadata := map[string]interface{}{
		"app":     appKey,
		"session": sessionName,
		"created": time.Now().Format(time.RFC3339),
		"hash":    hashValue,
	}

	data, err := json.MarshalIndent(metadata, "", "  ")
	if err != nil {
		return err
	}

	metadataFile := filepath.Join(backupFolder, ".backup_meta.json")
	return os.WriteFile(metadataFile, data, 0644)
}

// readBackupMetadata returns created time (if present) and hash
func (m *Manager) readBackupMetadata(backupFolder string) (*time.Time, string) {
	meta := m.readBackupMetadataFull(backupFolder)
	if meta == nil {
		return nil, ""
	}

	var createdPtr *time.Time
	if meta.Created != "" {
		if t, err := time.Parse(time.RFC3339, meta.Created); err == nil {
			createdPtr = &t
		}
	}
	return createdPtr, meta.Hash
}

// readBackupMetadataFull returns the full backup metadata including cached size.
func (m *Manager) readBackupMetadataFull(backupFolder string) *BackupMetadata {
	metadataFile := filepath.Join(backupFolder, ".backup_meta.json")
	data, err := os.ReadFile(metadataFile)
	if err != nil {
		return nil
	}

	var meta BackupMetadata
	if err := json.Unmarshal(data, &meta); err != nil {
		return nil
	}

	return &meta
}

// computeBackupHash computes a deterministic SHA256 hash of all files in the backup folder (excluding metadata)
func (m *Manager) computeBackupHash(backupFolder string) (string, error) {
	hasher := sha256.New()
	var files []string

	// Collect file paths
	filepath.Walk(backupFolder, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return nil
		}
		if info.IsDir() {
			return nil
		}
		// Skip metadata file
		if info.Name() == ".backup_meta.json" {
			return nil
		}
		rel, _ := filepath.Rel(backupFolder, path)
		files = append(files, rel)
		return nil
	})

	sort.Strings(files)

	for _, rel := range files {
		full := filepath.Join(backupFolder, rel)
		data, err := os.ReadFile(full)
		if err != nil {
			continue
		}
		// include filename to keep ordering stable
		hasher.Write([]byte(rel))
		hasher.Write(data)
	}

	return fmt.Sprintf("%x", hasher.Sum(nil)), nil
}

// verifyBackupHash recomputes hash and compares with expected
func (m *Manager) verifyBackupHash(backupFolder, expected string) bool {
	if expected == "" {
		return true
	}
	computed, err := m.computeBackupHash(backupFolder)
	if err != nil {
		return false
	}
	return computed == expected
}

// VerifySessionIntegrity verifies backup integrity on-demand.
// Returns true if the backup is valid, false if corrupted.
func (m *Manager) VerifySessionIntegrity(appKey, sessionName string) (bool, error) {
	backupFolder := m.GetSessionPath(appKey, sessionName)

	if _, err := os.Stat(backupFolder); os.IsNotExist(err) {
		return false, fmt.Errorf("session not found: %s", sessionName)
	}

	meta := m.readBackupMetadataFull(backupFolder)
	if meta == nil || meta.Hash == "" {
		return true, nil // No hash stored, assume valid
	}

	// Check hash version and use appropriate verification
	if meta.HashVersion >= 2 {
		// New hash format: recompute using computeBackupHashV2
		computed, err := m.computeBackupHashV2(backupFolder)
		if err != nil {
			return false, err
		}
		return computed == meta.Hash, nil
	}

	// Legacy hash format
	computed, err := m.computeBackupHash(backupFolder)
	if err != nil {
		return false, err
	}
	return computed == meta.Hash, nil
}

// computeBackupHashV2 computes hash using the new v2 algorithm (matching computeHashFromResults).
func (m *Manager) computeBackupHashV2(backupFolder string) (string, error) {
	var files []string

	// Collect file paths
	filepath.Walk(backupFolder, func(path string, info os.FileInfo, err error) error {
		if err != nil || info.IsDir() {
			return nil
		}
		// Skip metadata file
		if info.Name() == ".backup_meta.json" {
			return nil
		}
		rel, _ := filepath.Rel(backupFolder, path)
		files = append(files, rel)
		return nil
	})

	sort.Strings(files)

	hasher := sha256.New()
	buf := make([]byte, 4*1024*1024) // 4MB buffer

	for _, rel := range files {
		full := filepath.Join(backupFolder, rel)
		f, err := os.Open(full)
		if err != nil {
			continue
		}

		fileHasher := sha256.New()
		_, err = io.CopyBuffer(fileHasher, f, buf)
		f.Close()
		if err != nil {
			continue
		}

		fileHash := fmt.Sprintf("%x", fileHasher.Sum(nil))
		hasher.Write([]byte(rel))
		hasher.Write([]byte(fileHash))
	}

	return fmt.Sprintf("%x", hasher.Sum(nil)), nil
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

// copyFileStreaming copies a file while computing its hash in a single pass.
// Uses io.TeeReader to hash while copying, eliminating double file reads.
func copyFileStreaming(src, dst string, buf []byte) (size int64, hash string, err error) {
	sourceFile, err := os.Open(src)
	if err != nil {
		return 0, "", err
	}
	defer sourceFile.Close()

	sourceInfo, err := sourceFile.Stat()
	if err != nil {
		return 0, "", err
	}

	// Check if destination exists with same size and mtime (incremental skip)
	if dstInfo, dstErr := os.Stat(dst); dstErr == nil {
		if dstInfo.Size() == sourceInfo.Size() && dstInfo.ModTime().Equal(sourceInfo.ModTime()) {
			// File unchanged, compute hash from existing file for consistency
			hasher := sha256.New()
			if _, hashErr := io.CopyBuffer(hasher, sourceFile, buf); hashErr == nil {
				return sourceInfo.Size(), fmt.Sprintf("%x", hasher.Sum(nil)), nil
			}
		}
	}

	// Reset file position after potential hash check
	sourceFile.Seek(0, 0)

	// Ensure destination directory exists
	if err := os.MkdirAll(filepath.Dir(dst), 0755); err != nil {
		return 0, "", err
	}

	destFile, err := os.Create(dst)
	if err != nil {
		return 0, "", err
	}
	defer destFile.Close()

	// Use TeeReader to hash while copying
	hasher := sha256.New()
	teeReader := io.TeeReader(sourceFile, hasher)

	// Copy with provided buffer
	written, err := io.CopyBuffer(destFile, teeReader, buf)
	if err != nil {
		return 0, "", err
	}

	// Preserve file permissions and modification time
	os.Chmod(dst, sourceInfo.Mode())
	os.Chtimes(dst, sourceInfo.ModTime(), sourceInfo.ModTime())

	return written, fmt.Sprintf("%x", hasher.Sum(nil)), nil
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

// copyWithWorkerPool copies files in parallel using a worker pool.
func (m *Manager) copyWithWorkerPool(jobs []CopyJob, workerCount int, progressCb ProgressCallback) ([]FileCopyResult, error) {
	if len(jobs) == 0 {
		return nil, nil
	}

	jobsChan := make(chan CopyJob, len(jobs))
	resultsChan := make(chan FileCopyResult, len(jobs))

	var wg sync.WaitGroup

	// Spawn workers
	for i := 0; i < workerCount; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			// 4MB buffer per worker for optimal I/O performance
			buf := make([]byte, 4*1024*1024)
			for job := range jobsChan {
				size, hash, err := copyFileStreaming(job.Src, job.Dst, buf)
				resultsChan <- FileCopyResult{
					RelPath: job.RelPath,
					Size:    size,
					Hash:    hash,
					Err:     err,
				}
			}
		}()
	}

	// Feed jobs
	go func() {
		for _, job := range jobs {
			jobsChan <- job
		}
		close(jobsChan)
	}()

	// Wait and close results
	go func() {
		wg.Wait()
		close(resultsChan)
	}()

	// Collect results with progress
	var results []FileCopyResult
	completed := 0
	for result := range resultsChan {
		results = append(results, result)
		completed++
		if progressCb != nil {
			percent := int(float64(completed) / float64(len(jobs)) * 100)
			progressCb(BackupProgress{Percent: percent, Message: fmt.Sprintf("Copying %s...", result.RelPath)})
		}
	}

	// Check for errors
	for _, r := range results {
		if r.Err != nil {
			return results, r.Err
		}
	}

	return results, nil
}

// collectCopyJobs walks a directory and collects all files as CopyJobs.
func (m *Manager) collectCopyJobs(srcBase, dstBase string) ([]CopyJob, error) {
	var jobs []CopyJob

	err := filepath.Walk(srcBase, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return nil // Skip errors
		}
		if info.IsDir() {
			return nil
		}
		// Skip metadata files
		if info.Name() == ".backup_meta.json" {
			return nil
		}

		relPath, _ := filepath.Rel(srcBase, path)
		dstPath := filepath.Join(dstBase, relPath)

		jobs = append(jobs, CopyJob{
			Src:     path,
			Dst:     dstPath,
			RelPath: relPath,
		})
		return nil
	})

	return jobs, err
}

// collectCopyJobsFromItems collects CopyJobs from specific backup items.
func (m *Manager) collectCopyJobsFromItems(srcBase, dstBase string, items []BackupItem) ([]CopyJob, error) {
	var jobs []CopyJob

	for _, item := range items {
		if item.Path == "" {
			continue
		}

		src, err := validatePath(srcBase, item.Path)
		if err != nil {
			if item.Optional {
				continue
			}
			return nil, fmt.Errorf("invalid source path for item %s: %w", item.Path, err)
		}

		dst, err := validatePath(dstBase, item.Path)
		if err != nil {
			return nil, fmt.Errorf("invalid destination path for item %s: %w", item.Path, err)
		}

		info, err := os.Stat(src)
		if err != nil {
			if item.Optional || os.IsNotExist(err) {
				continue
			}
			return nil, err
		}

		if info.IsDir() {
			// Walk the directory and collect all files
			err := filepath.Walk(src, func(path string, finfo os.FileInfo, walkErr error) error {
				if walkErr != nil || finfo.IsDir() {
					return nil
				}
				relToSrc, _ := filepath.Rel(src, path)
				relPath := filepath.Join(item.Path, relToSrc)
				dstPath := filepath.Join(dst, relToSrc)

				jobs = append(jobs, CopyJob{
					Src:     path,
					Dst:     dstPath,
					RelPath: relPath,
				})
				return nil
			})
			if err != nil {
				return nil, err
			}
		} else {
			jobs = append(jobs, CopyJob{
				Src:     src,
				Dst:     dst,
				RelPath: item.Path,
			})
		}
	}

	return jobs, nil
}

// collectCopyJobsFromAddons collects CopyJobs from addon paths.
func (m *Manager) collectCopyJobsFromAddons(addonBackupDir string, addonPaths []string) ([]CopyJob, error) {
	var jobs []CopyJob

	for _, addonPath := range addonPaths {
		info, err := os.Stat(addonPath)
		if err != nil {
			continue // Skip non-existent paths
		}

		addonName := filepath.Base(addonPath)
		addonDst := filepath.Join(addonBackupDir, addonName)

		if info.IsDir() {
			err := filepath.Walk(addonPath, func(path string, finfo os.FileInfo, walkErr error) error {
				if walkErr != nil || finfo.IsDir() {
					return nil
				}
				relToAddon, _ := filepath.Rel(addonPath, path)
				relPath := filepath.Join("_addons", addonName, relToAddon)
				dstPath := filepath.Join(addonDst, relToAddon)

				jobs = append(jobs, CopyJob{
					Src:     path,
					Dst:     dstPath,
					RelPath: relPath,
				})
				return nil
			})
			if err != nil {
				continue
			}
		} else {
			jobs = append(jobs, CopyJob{
				Src:     addonPath,
				Dst:     addonDst,
				RelPath: filepath.Join("_addons", addonName),
			})
		}
	}

	return jobs, nil
}

// computeHashFromResults computes an aggregate hash from copy results.
// Uses sorted file paths for deterministic ordering.
func computeHashFromResults(results []FileCopyResult) string {
	// Sort by RelPath for deterministic ordering
	sorted := make([]FileCopyResult, len(results))
	copy(sorted, results)
	sort.Slice(sorted, func(i, j int) bool {
		return sorted[i].RelPath < sorted[j].RelPath
	})

	hasher := sha256.New()
	for _, r := range sorted {
		if r.Err == nil && r.Hash != "" {
			hasher.Write([]byte(r.RelPath))
			hasher.Write([]byte(r.Hash))
		}
	}
	return fmt.Sprintf("%x", hasher.Sum(nil))
}
