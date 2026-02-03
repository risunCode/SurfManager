package backup

import (
	"os"
	"path/filepath"
	"testing"
)

// TestCreateBackup_AddonOnly tests that CreateBackup skips data folder when addonOnly=true
func TestCreateBackup_AddonOnly(t *testing.T) {
	// Create temporary directories for testing
	tempDir := t.TempDir()
	documentsPath := filepath.Join(tempDir, "Documents")
	sourcePath := filepath.Join(tempDir, "source")
	addonPath := filepath.Join(tempDir, "addon")

	// Create source directory with test files
	if err := os.MkdirAll(sourcePath, 0755); err != nil {
		t.Fatalf("Failed to create source directory: %v", err)
	}
	if err := os.WriteFile(filepath.Join(sourcePath, "data.txt"), []byte("test data"), 0644); err != nil {
		t.Fatalf("Failed to create test file: %v", err)
	}

	// Create addon directory with test files
	if err := os.MkdirAll(addonPath, 0755); err != nil {
		t.Fatalf("Failed to create addon directory: %v", err)
	}
	if err := os.WriteFile(filepath.Join(addonPath, "addon.txt"), []byte("test addon"), 0644); err != nil {
		t.Fatalf("Failed to create addon file: %v", err)
	}

	// Create backup manager
	manager := NewManager(documentsPath)

	// Test 1: Full backup (addonOnly=false)
	t.Run("FullBackup", func(t *testing.T) {
		backupItems := []BackupItem{
			{Path: "data.txt", Optional: false},
		}
		addonPaths := []string{addonPath}

		err := manager.CreateBackup("testapp", "full-session", sourcePath, backupItems, addonPaths, false, nil)
		if err != nil {
			t.Fatalf("CreateBackup failed: %v", err)
		}

		// Verify data file was backed up
		dataBackupPath := filepath.Join(manager.GetBackupPath(), "testapp", "full-session", "data.txt")
		if _, err := os.Stat(dataBackupPath); os.IsNotExist(err) {
			t.Error("Data file was not backed up in full backup mode")
		}

		// Verify addon was backed up
		addonBackupPath := filepath.Join(manager.GetBackupPath(), "testapp", "full-session", "_addons", filepath.Base(addonPath), "addon.txt")
		if _, err := os.Stat(addonBackupPath); os.IsNotExist(err) {
			t.Error("Addon file was not backed up in full backup mode")
		}
	})

	// Test 2: Addon-only backup (addonOnly=true)
	t.Run("AddonOnlyBackup", func(t *testing.T) {
		backupItems := []BackupItem{
			{Path: "data.txt", Optional: false},
		}
		addonPaths := []string{addonPath}

		err := manager.CreateBackup("testapp", "addon-session", sourcePath, backupItems, addonPaths, true, nil)
		if err != nil {
			t.Fatalf("CreateBackup failed: %v", err)
		}

		// Verify data file was NOT backed up
		dataBackupPath := filepath.Join(manager.GetBackupPath(), "testapp", "addon-session", "data.txt")
		if _, err := os.Stat(dataBackupPath); !os.IsNotExist(err) {
			t.Error("Data file should not be backed up in addon-only mode")
		}

		// Verify addon was backed up
		addonBackupPath := filepath.Join(manager.GetBackupPath(), "testapp", "addon-session", "_addons", filepath.Base(addonPath), "addon.txt")
		if _, err := os.Stat(addonBackupPath); os.IsNotExist(err) {
			t.Error("Addon file was not backed up in addon-only mode")
		}
	})

	// Test 3: Addon-only backup with no addons
	t.Run("AddonOnlyBackupNoAddons", func(t *testing.T) {
		backupItems := []BackupItem{
			{Path: "data.txt", Optional: false},
		}
		addonPaths := []string{} // No addons

		err := manager.CreateBackup("testapp", "addon-no-addons", sourcePath, backupItems, addonPaths, true, nil)
		if err != nil {
			t.Fatalf("CreateBackup failed: %v", err)
		}

		// Verify data file was NOT backed up
		dataBackupPath := filepath.Join(manager.GetBackupPath(), "testapp", "addon-no-addons", "data.txt")
		if _, err := os.Stat(dataBackupPath); !os.IsNotExist(err) {
			t.Error("Data file should not be backed up in addon-only mode")
		}

		// Verify backup folder was created (even if empty)
		backupFolder := filepath.Join(manager.GetBackupPath(), "testapp", "addon-no-addons")
		if _, err := os.Stat(backupFolder); os.IsNotExist(err) {
			t.Error("Backup folder should be created even with no addons")
		}
	})
}

// BenchmarkCopyFile benchmarks the file copy performance with different file sizes
func BenchmarkCopyFile(b *testing.B) {
	// Test with different file sizes
	sizes := []struct {
		name string
		size int64
	}{
		{"1MB", 1024 * 1024},
		{"10MB", 10 * 1024 * 1024},
		{"100MB", 100 * 1024 * 1024},
	}

	for _, size := range sizes {
		b.Run(size.name, func(b *testing.B) {
			// Create temporary directories
			tempDir := b.TempDir()
			srcFile := filepath.Join(tempDir, "source.dat")
			
			// Create a test file with the specified size
			data := make([]byte, size.size)
			if err := os.WriteFile(srcFile, data, 0644); err != nil {
				b.Fatalf("Failed to create test file: %v", err)
			}

			b.ResetTimer()
			b.SetBytes(size.size)

			for i := 0; i < b.N; i++ {
				dstFile := filepath.Join(tempDir, filepath.Base(srcFile)+".copy")
				if err := copyFile(srcFile, dstFile); err != nil {
					b.Fatalf("copyFile failed: %v", err)
				}
				// Clean up destination file for next iteration
				os.Remove(dstFile)
			}
		})
	}
}

// TestCopyFilePreservesPermissions tests that file permissions are preserved
func TestCopyFilePreservesPermissions(t *testing.T) {
	tempDir := t.TempDir()
	srcFile := filepath.Join(tempDir, "source.txt")
	dstFile := filepath.Join(tempDir, "dest.txt")

	// Create source file with specific permissions
	if err := os.WriteFile(srcFile, []byte("test data"), 0600); err != nil {
		t.Fatalf("Failed to create source file: %v", err)
	}

	// Copy the file
	if err := copyFile(srcFile, dstFile); err != nil {
		t.Fatalf("copyFile failed: %v", err)
	}

	// Check that permissions are preserved
	srcInfo, err := os.Stat(srcFile)
	if err != nil {
		t.Fatalf("Failed to stat source file: %v", err)
	}

	dstInfo, err := os.Stat(dstFile)
	if err != nil {
		t.Fatalf("Failed to stat destination file: %v", err)
	}

	if srcInfo.Mode() != dstInfo.Mode() {
		t.Errorf("File permissions not preserved: source=%v, dest=%v", srcInfo.Mode(), dstInfo.Mode())
	}
}

// TestCopyFileContent tests that file content is copied correctly
func TestCopyFileContent(t *testing.T) {
	tempDir := t.TempDir()
	srcFile := filepath.Join(tempDir, "source.txt")
	dstFile := filepath.Join(tempDir, "dest.txt")

	testData := []byte("This is test data for file copy verification")
	
	// Create source file
	if err := os.WriteFile(srcFile, testData, 0644); err != nil {
		t.Fatalf("Failed to create source file: %v", err)
	}

	// Copy the file
	if err := copyFile(srcFile, dstFile); err != nil {
		t.Fatalf("copyFile failed: %v", err)
	}

	// Verify content
	copiedData, err := os.ReadFile(dstFile)
	if err != nil {
		t.Fatalf("Failed to read destination file: %v", err)
	}

	if string(copiedData) != string(testData) {
		t.Errorf("File content mismatch: expected %q, got %q", testData, copiedData)
	}
}
