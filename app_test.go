package main

import (
	"encoding/json"
	"os"
	"path/filepath"
	"testing"

	"surfmanager/internal/apps"
)

// TestCalculateBackupSize tests the CalculateBackupSize method
func TestCalculateBackupSize(t *testing.T) {
	// Create a temporary directory for testing
	tempDir := t.TempDir()

	// Create test data structure
	dataPath := filepath.Join(tempDir, "testapp", "data")
	addonPath := filepath.Join(tempDir, "testapp", "addon")
	configDir := filepath.Join(tempDir, ".surfmanager", "AppConfigs")

	// Create directories
	if err := os.MkdirAll(dataPath, 0755); err != nil {
		t.Fatalf("Failed to create data path: %v", err)
	}
	if err := os.MkdirAll(addonPath, 0755); err != nil {
		t.Fatalf("Failed to create addon path: %v", err)
	}
	if err := os.MkdirAll(configDir, 0755); err != nil {
		t.Fatalf("Failed to create config dir: %v", err)
	}

	// Create test files with known sizes
	testFile1 := filepath.Join(dataPath, "test1.txt")
	testFile2 := filepath.Join(dataPath, "test2.txt")
	addonFile := filepath.Join(addonPath, "addon.txt")

	// Write files with specific sizes
	data1 := make([]byte, 1024)      // 1 KB
	data2 := make([]byte, 2048)      // 2 KB
	addonData := make([]byte, 512)   // 512 B

	if err := os.WriteFile(testFile1, data1, 0644); err != nil {
		t.Fatalf("Failed to write test file 1: %v", err)
	}
	if err := os.WriteFile(testFile2, data2, 0644); err != nil {
		t.Fatalf("Failed to write test file 2: %v", err)
	}
	if err := os.WriteFile(addonFile, addonData, 0644); err != nil {
		t.Fatalf("Failed to write addon file: %v", err)
	}

	// Create app config file
	appConfig := map[string]interface{}{
		"app_name":     "testapp",
		"display_name": "Test App",
		"version":      "1.0",
		"active":       true,
		"description":  "Test application",
		"paths": map[string]interface{}{
			"data_paths": []string{dataPath},
			"exe_paths":  []string{},
		},
		"backup_items": []map[string]interface{}{
			{"type": "file", "path": "test1.txt", "description": "Test file 1", "optional": false},
			{"type": "file", "path": "test2.txt", "description": "Test file 2", "optional": false},
		},
		"addon_backup_paths": []string{addonPath},
	}

	configData, err := json.MarshalIndent(appConfig, "", "  ")
	if err != nil {
		t.Fatalf("Failed to marshal config: %v", err)
	}

	configFile := filepath.Join(configDir, "testapp.json")
	if err := os.WriteFile(configFile, configData, 0644); err != nil {
		t.Fatalf("Failed to write config file: %v", err)
	}

	// Set HOME to temp directory so ConfigLoader uses our test config
	oldHome := os.Getenv("HOME")
	if oldHome == "" {
		oldHome = os.Getenv("USERPROFILE") // Windows
	}
	defer func() {
		if oldHome != "" {
			os.Setenv("HOME", oldHome)
			os.Setenv("USERPROFILE", oldHome)
		}
	}()
	os.Setenv("HOME", tempDir)
	os.Setenv("USERPROFILE", tempDir)

	// Create app instance - this will load configs from our temp directory
	app := NewApp()
	
	// Initialize apps loader manually
	var appsErr error
	app.apps, appsErr = apps.NewConfigLoader()
	if appsErr != nil {
		t.Fatalf("Failed to create config loader: %v", appsErr)
	}
	if appsErr = app.apps.LoadAllConfigs(); appsErr != nil {
		t.Fatalf("Failed to load configs: %v", appsErr)
	}

	// Test with includeData = true
	t.Run("IncludeData", func(t *testing.T) {
		result, err := app.CalculateBackupSize("testapp", true)
		if err != nil {
			t.Fatalf("CalculateBackupSize failed: %v", err)
		}

		// Verify result structure
		if result["total_size"] == nil {
			t.Error("total_size is missing")
		}
		if result["data_size"] == nil {
			t.Error("data_size is missing")
		}
		if result["addon_size"] == nil {
			t.Error("addon_size is missing")
		}

		// Verify sizes
		dataSize := result["data_size"].(int64)
		addonSize := result["addon_size"].(int64)
		totalSize := result["total_size"].(int64)

		expectedDataSize := int64(1024 + 2048) // 3 KB
		expectedAddonSize := int64(512)        // 512 B
		expectedTotalSize := expectedDataSize + expectedAddonSize

		if dataSize != expectedDataSize {
			t.Errorf("Expected data_size %d, got %d", expectedDataSize, dataSize)
		}
		if addonSize != expectedAddonSize {
			t.Errorf("Expected addon_size %d, got %d", expectedAddonSize, addonSize)
		}
		if totalSize != expectedTotalSize {
			t.Errorf("Expected total_size %d, got %d", expectedTotalSize, totalSize)
		}

		// Verify formatted strings exist and are non-empty
		if result["total_size_formatted"] == nil || result["total_size_formatted"].(string) == "" {
			t.Error("total_size_formatted is missing or empty")
		}
		if result["data_size_formatted"] == nil || result["data_size_formatted"].(string) == "" {
			t.Error("data_size_formatted is missing or empty")
		}
		if result["addon_size_formatted"] == nil || result["addon_size_formatted"].(string) == "" {
			t.Error("addon_size_formatted is missing or empty")
		}

		t.Logf("Sizes: data=%s, addon=%s, total=%s",
			result["data_size_formatted"],
			result["addon_size_formatted"],
			result["total_size_formatted"])
	})

	// Test with includeData = false
	t.Run("ExcludeData", func(t *testing.T) {
		result, err := app.CalculateBackupSize("testapp", false)
		if err != nil {
			t.Fatalf("CalculateBackupSize failed: %v", err)
		}

		// Verify sizes
		dataSize := result["data_size"].(int64)
		addonSize := result["addon_size"].(int64)
		totalSize := result["total_size"].(int64)

		expectedAddonSize := int64(512) // 512 B

		if dataSize != 0 {
			t.Errorf("Expected data_size 0, got %d", dataSize)
		}
		if addonSize != expectedAddonSize {
			t.Errorf("Expected addon_size %d, got %d", expectedAddonSize, addonSize)
		}
		if totalSize != expectedAddonSize {
			t.Errorf("Expected total_size %d, got %d", expectedAddonSize, totalSize)
		}
	})

	// Test with non-existent app
	t.Run("NonExistentApp", func(t *testing.T) {
		_, err := app.CalculateBackupSize("nonexistent", true)
		if err == nil {
			t.Error("Expected error for non-existent app, got nil")
		}
	})
}

// TestCalculateBackupSizeWithOptionalItems tests handling of optional backup items
func TestCalculateBackupSizeWithOptionalItems(t *testing.T) {
	// Create a temporary directory for testing
	tempDir := t.TempDir()

	// Create test data structure
	dataPath := filepath.Join(tempDir, "testapp", "data")
	configDir := filepath.Join(tempDir, ".surfmanager", "AppConfigs")

	// Create directories
	if err := os.MkdirAll(dataPath, 0755); err != nil {
		t.Fatalf("Failed to create data path: %v", err)
	}
	if err := os.MkdirAll(configDir, 0755); err != nil {
		t.Fatalf("Failed to create config dir: %v", err)
	}

	// Create only one of the two files (the required one)
	testFile1 := filepath.Join(dataPath, "required.txt")
	data1 := make([]byte, 1024) // 1 KB

	if err := os.WriteFile(testFile1, data1, 0644); err != nil {
		t.Fatalf("Failed to write test file: %v", err)
	}

	// Create app config with optional item that doesn't exist
	appConfig := map[string]interface{}{
		"app_name":     "testapp",
		"display_name": "Test App",
		"version":      "1.0",
		"active":       true,
		"description":  "Test application",
		"paths": map[string]interface{}{
			"data_paths": []string{dataPath},
			"exe_paths":  []string{},
		},
		"backup_items": []map[string]interface{}{
			{"type": "file", "path": "required.txt", "description": "Required file", "optional": false},
			{"type": "file", "path": "optional.txt", "description": "Optional file", "optional": true},
		},
		"addon_backup_paths": []string{},
	}

	configData, err := json.MarshalIndent(appConfig, "", "  ")
	if err != nil {
		t.Fatalf("Failed to marshal config: %v", err)
	}

	configFile := filepath.Join(configDir, "testapp.json")
	if err := os.WriteFile(configFile, configData, 0644); err != nil {
		t.Fatalf("Failed to write config file: %v", err)
	}

	// Set HOME to temp directory
	oldHome := os.Getenv("HOME")
	if oldHome == "" {
		oldHome = os.Getenv("USERPROFILE")
	}
	defer func() {
		if oldHome != "" {
			os.Setenv("HOME", oldHome)
			os.Setenv("USERPROFILE", oldHome)
		}
	}()
	os.Setenv("HOME", tempDir)
	os.Setenv("USERPROFILE", tempDir)

	// Create app instance
	app := NewApp()
	
	// Initialize apps loader manually
	var appsErr error
	app.apps, appsErr = apps.NewConfigLoader()
	if appsErr != nil {
		t.Fatalf("Failed to create config loader: %v", appsErr)
	}
	if appsErr = app.apps.LoadAllConfigs(); appsErr != nil {
		t.Fatalf("Failed to load configs: %v", appsErr)
	}

	// Test that optional missing files don't cause errors
	result, err := app.CalculateBackupSize("testapp", true)
	if err != nil {
		t.Fatalf("CalculateBackupSize failed: %v", err)
	}

	// Verify only the required file was counted
	dataSize := result["data_size"].(int64)
	expectedDataSize := int64(1024) // Only required.txt

	if dataSize != expectedDataSize {
		t.Errorf("Expected data_size %d, got %d", expectedDataSize, dataSize)
	}
}

// TestCalculatePathSize tests the calculatePathSize helper method
func TestCalculatePathSize(t *testing.T) {
	// Create a temporary directory for testing
	tempDir := t.TempDir()

	// Create test directory structure
	testDir := filepath.Join(tempDir, "testdir")
	subDir := filepath.Join(testDir, "subdir")

	if err := os.MkdirAll(subDir, 0755); err != nil {
		t.Fatalf("Failed to create test directories: %v", err)
	}

	// Create test files
	file1 := filepath.Join(testDir, "file1.txt")
	file2 := filepath.Join(subDir, "file2.txt")

	data1 := make([]byte, 1024) // 1 KB
	data2 := make([]byte, 2048) // 2 KB

	if err := os.WriteFile(file1, data1, 0644); err != nil {
		t.Fatalf("Failed to write file1: %v", err)
	}
	if err := os.WriteFile(file2, data2, 0644); err != nil {
		t.Fatalf("Failed to write file2: %v", err)
	}

	// Test calculatePathSize
	app := NewApp()
	size, err := app.calculatePathSize(testDir)
	if err != nil {
		t.Fatalf("calculatePathSize failed: %v", err)
	}

	expectedSize := int64(1024 + 2048) // 3 KB total
	if size != expectedSize {
		t.Errorf("Expected size %d, got %d", expectedSize, size)
	}
}


