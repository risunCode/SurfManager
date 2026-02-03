package main

import (
	"fmt"
	"os"
	"path/filepath"
	"testing"
	"time"

	"surfmanager/internal/apps"
	"surfmanager/internal/backup"
	"surfmanager/internal/config"
)

// TestBackupFlowSimple tests the backup flow without Wails context
func TestBackupFlowSimple(t *testing.T) {
	// Initialize components
	cfg := config.GetManager()
	backupMgr := backup.NewManager(cfg.GetDocumentsDir())
	
	appsLoader, err := apps.NewConfigLoader()
	if err != nil {
		t.Fatalf("Failed to initialize apps loader: %v", err)
	}
	
	if err := appsLoader.LoadAllConfigs(); err != nil {
		t.Fatalf("Failed to load app configs: %v", err)
	}

	// Get first active app for testing
	activeApps := appsLoader.GetActiveApps()
	if len(activeApps) == 0 {
		t.Skip("No active apps configured, skipping test")
	}
	
	testApp := activeApps[0]
	t.Logf("Testing with app: %s (%s)", testApp.AppName, testApp.DisplayName)

	// Test 1: Calculate backup size
	t.Run("CalculateBackupSize", func(t *testing.T) {
		var dataSize int64
		var addonSize int64

		// Get data path
		var dataPath string
		for _, path := range testApp.Paths.DataPaths {
			if _, err := os.Stat(path); err == nil {
				dataPath = path
				break
			}
		}

		// Calculate data folder size
		if dataPath != "" && len(testApp.BackupItems) > 0 {
			for _, item := range testApp.BackupItems {
				itemPath := filepath.Join(dataPath, item.Path)
				
				info, err := os.Stat(itemPath)
				if err != nil {
					if item.Optional || os.IsNotExist(err) {
						continue
					}
					continue
				}

				if info.IsDir() {
					size, err := calculatePathSize(itemPath)
					if err == nil {
						dataSize += size
					}
				} else {
					dataSize += info.Size()
				}
			}
		}

		// Calculate addon folders size
		for _, addonPath := range testApp.AddonPaths {
			if _, err := os.Stat(addonPath); err != nil {
				continue
			}

			size, err := calculatePathSize(addonPath)
			if err == nil {
				addonSize += size
			}
		}

		totalSize := dataSize + addonSize

		t.Logf("✓ Size calculation completed")
		t.Logf("  Data size: %s", backup.FormatSize(dataSize))
		t.Logf("  Addon size: %s", backup.FormatSize(addonSize))
		t.Logf("  Total size: %s", backup.FormatSize(totalSize))

		// Verify sizes are non-negative
		if totalSize < 0 {
			t.Errorf("Total size is negative: %d", totalSize)
		}
	})

	// Test 2: Create addon-only backup
	testSessionName := fmt.Sprintf("test-simple-%d", time.Now().Unix())
	t.Run("CreateBackup_AddonOnly", func(t *testing.T) {
		t.Logf("Creating addon-only backup: %s", testSessionName)
		
		// Get data path
		var dataPath string
		for _, path := range testApp.Paths.DataPaths {
			if _, err := os.Stat(path); err == nil {
				dataPath = path
				break
			}
		}
		
		if dataPath == "" {
			t.Skip("No data path found for app")
		}

		// Create backup with addonOnly=true (no data folder items)
		err := backupMgr.CreateBackup(
			testApp.AppName,
			testSessionName,
			dataPath,
			[]backup.BackupItem{}, // Empty - addon only
			testApp.AddonPaths,
			true, // addonOnly
			func(p backup.BackupProgress) {
				t.Logf("  Progress: %d%% - %s", p.Percent, p.Message)
			},
		)
		
		if err != nil {
			t.Fatalf("CreateBackup failed: %v", err)
		}
		
		t.Logf("✓ Created addon-only backup successfully")
		
		// Verify session exists
		if !backupMgr.SessionExists(testApp.AppName, testSessionName) {
			t.Errorf("Session was not created: %s", testSessionName)
		}
		
		// Check session folder structure
		sessionPath := backupMgr.GetSessionPath(testApp.AppName, testSessionName)
		t.Logf("  Session path: %s", sessionPath)
		
		// Verify session folder exists
		if _, err := os.Stat(sessionPath); os.IsNotExist(err) {
			t.Errorf("Session folder does not exist: %s", sessionPath)
		}
		
		// Check for _addons folder
		addonsPath := filepath.Join(sessionPath, "_addons")
		if _, err := os.Stat(addonsPath); os.IsNotExist(err) {
			t.Logf("  Note: _addons folder not found (app may have no addon paths configured)")
		} else {
			t.Logf("  ✓ _addons folder exists")
			
			// List addon contents
			entries, err := os.ReadDir(addonsPath)
			if err == nil {
				t.Logf("  Addon folders backed up: %d", len(entries))
				for _, entry := range entries {
					t.Logf("    - %s", entry.Name())
				}
			}
		}
		
		// Verify no data folder items were backed up (addon-only mode)
		entries, err := os.ReadDir(sessionPath)
		if err == nil {
			dataItemCount := 0
			for _, entry := range entries {
				name := entry.Name()
				// Skip _addons and metadata files
				if name != "_addons" && len(name) > 0 && name[0] != '.' {
					dataItemCount++
				}
			}
			if dataItemCount > 0 {
				t.Errorf("Found %d data items in addon-only backup (expected 0)", dataItemCount)
			} else {
				t.Logf("  ✓ No data items in addon-only backup (correct)")
			}
		}
	})

	// Test 3: Verify session appears in list
	t.Run("GetSessions", func(t *testing.T) {
		sessions, err := backupMgr.GetSessions(testApp.AppName, false)
		
		if err != nil {
			t.Fatalf("GetSessions failed: %v", err)
		}
		
		t.Logf("✓ Found %d sessions for %s", len(sessions), testApp.AppName)
		
		// Find our test session
		found := false
		for _, session := range sessions {
			if session.Name == testSessionName {
				found = true
				t.Logf("  ✓ Test session found in list")
				t.Logf("    Name: %s", session.Name)
				t.Logf("    Size: %s", backup.FormatSize(session.Size))
				t.Logf("    Created: %s", session.Created.Format("2006-01-02 15:04:05"))
				break
			}
		}
		
		if !found {
			t.Errorf("Test session not found in session list: %s", testSessionName)
		}
	})

	// Test 4: Check session has addons
	t.Run("CheckSessionHasAddons", func(t *testing.T) {
		hasAddons := backupMgr.SessionHasAddons(testApp.AppName, testSessionName)
		t.Logf("✓ Session has addons: %v", hasAddons)
	})

	// Cleanup: Delete test session
	t.Run("Cleanup", func(t *testing.T) {
		err := backupMgr.DeleteSession(testApp.AppName, testSessionName)
		if err != nil {
			t.Errorf("Failed to delete test session: %v", err)
		} else {
			t.Logf("✓ Cleaned up test session: %s", testSessionName)
		}
		
		// Verify deletion
		if backupMgr.SessionExists(testApp.AppName, testSessionName) {
			t.Errorf("Session still exists after deletion: %s", testSessionName)
		}
	})
}

// Helper function to calculate path size
func calculatePathSize(path string) (int64, error) {
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
