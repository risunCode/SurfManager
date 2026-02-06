# Changelog

All notable changes to SurfManager will be documented in this file.

## [2.5.0] - 2026-02-07

### Summary

Major performance optimization release with loading animations. Backup/restore operations are now 3-5x faster, session listing is instant, and all action buttons now show loading feedback.

### ✨ New Features

**Loading Animations**
- All action buttons now display a spinning loader during operations
- Dynamic button text shows current state (e.g., "Resetting...", "Creating...", "Deleting...")
- Buttons are disabled during loading to prevent double-clicks

**Reset Tab Loading States**
- Reset button: spinner + "Resetting..." during reset operation
- Addons button: spinner + "Deleting..." during addon folder deletion
- New ID button: spinner + "Generating..." during machine ID generation
- Kill button: spinner + "Stopping..." during app termination
- Launch button: spinner + "Launching..." during app launch

**Sessions Tab Loading States**
- Create Backup button: spinner + "Creating..." during backup creation
- Kill and Continue button: spinner + "Processing..." during kill + backup
- Restore Session (context menu): spinner + "Restoring..." during restore
- Delete button (per row): spinner + "Deleting..." during session deletion

**Config Tab Loading States**
- Save button: spinner + "Saving..." during app configuration save
- Delete button: spinner during app deletion
- Active/Inactive toggle: spinner during status change

### 🚀 Performance Improvements

**Parallel File Copying**
- Backup and restore now use a worker pool with all available CPU cores
- Each worker uses optimized 4MB I/O buffers for maximum throughput
- File operations run concurrently instead of sequentially

**Streaming Hash Computation**
- Files are hashed while being copied using `io.TeeReader`
- Eliminates the previous double-read pattern (copy then hash)
- Reduces I/O by 50% during backup operations

**Cached Metadata**
- Session size and file count now stored in `.backup_meta.json`
- Session listing no longer walks directory trees to calculate size
- Session list loads instantly regardless of backup size

**Lazy Hash Verification**
- Hash verification removed from session listing (was blocking UI)
- New on-demand `VerifySessionIntegrity` API for explicit integrity checks
- Corrupted status no longer computed at list time

### ✨ New Features

**Backend**
- Added `VerifySessionIntegrity(appKey, sessionName)` API for on-demand backup verification
- Enhanced metadata schema with `hash_version`, `size`, and `file_count` fields
- New v2 hash algorithm matching streaming computation

### 📝 Technical Changes

**New Types**
- `CopyJob` - represents a file copy operation with source, destination, and relative path
- `FileCopyResult` - holds copy result including size, hash, and error status
- `BackupMetadata` - full metadata structure with cached values

**New Functions**
- `copyFileStreaming()` - copies files while computing SHA256 in single pass
- `copyWithWorkerPool()` - parallel file copying with worker pool
- `collectCopyJobs*()` - job collection helpers for items and addons
- `computeHashFromResults()` - aggregate hash from sorted file results
- `readBackupMetadataFull()` - reads full metadata including cached size
- `computeBackupHashV2()` - v2 hash algorithm for new backups

### 🔄 Backwards Compatibility

- Old backups without cached size fall back to directory walk
- Old hash format (v1) automatically detected and verified correctly
- No migration required - old backups work seamlessly

## [2.2.1] - 2026-02-05

### Summary (vs 2.2.0)

This release focuses on simplifying the product surface area and making backup/restore flows clearer.

### 🗑️ Removed Features

- Removed "Restore Account Only" (Sessions UI + backend API)
- Removed "Beep on completion" setting
- Removed Settings > Management section (Import/Export/Reset UI)

### ✨ Improvements

**Sessions**
- Create New Backup: when the app is running, the primary action becomes "Kill and Continue Create Backup"
- Backup size now recalculates based on selected Backup Type (Full vs Addon Only)
- Running warning text updated to match the new kill-and-continue flow
- Sessions context menu simplified (removed account-only restore)

**Config**
- Add Application modal refined (more compact layout, reduced scrolling)
- VSCode preset backup items updated to core data layout (Roaming/Code) and marked as required
- Additional Folders hint example is now app-relevant (e.g., ~/.vscode)

## [2.2.0] - 2026-02-05

### ✨ New Features

**Reliability & Safety**
- Context menu in Sessions tab is now clamped to the viewport so it never overflows off-screen
- Manual override prompts when auto-close fails on reset/restore/addon restore, so you can proceed after closing apps yourself
- Corrupted backup detection now surfaces a badge in Sessions and a count in Reset tab stats

**Configuration & Platform Help**
- Added platform-aware data path hints for Windows/macOS/Linux in Config and Reset tabs

**Observability**
- Frontend crash/unhandled rejection events are logged to backend log file
- Reset tab now lets you download logs directly from the UI

**Settings & Behavior**
- Settings can be exported/imported per section with a preview of incoming keys
- Startup actions: remember last tab and auto-refresh Sessions on launch; defaults updated for smoother startup
- Notification controls: mute non-critical toasts, toggle toast sound

### 🗑️ Removed Features

- Removed batch "Backup All Sessions" and "Clear All Sessions" actions from Settings

### 🔧 Fixes & Improvements

- Reused process-name collection helper across close/kill/restore paths for consistency
- Default auto-refresh sessions on launch enabled; assorted UI text updates

---

## [2.1.0] - 2026-01-13

### ✨ New Features

**UX Improvements**
- Apps are now sorted alphabetically by display name in Reset Tab and Sessions Tab
- Last selected app is now remembered when navigating between tabs
- Added "Launch App" option to session context menu for quick app launching
- Post-restore launch prompt - option to launch app after successful restore
- Auto-generate new machine IDs after any restore operation (full, addon-only, account-only)
- Session is now marked as active after addon-only or account-only restore

**Bulk Session Management**
- Added "Backup All Sessions" button in Settings - creates a zip archive of all sessions
- Added "Clear All Sessions" button in Settings - deletes all backup sessions with confirmation

**Reset Tab Redesign**
- App name now displayed on the left side of app rows
- Session count, auto-backup count, and addon count badges displayed on the right side
- Improved layout with better information visibility

### 🗑️ Removed Features

- Removed "Remember Last Tab" setting (unused)
- Removed "Debug Mode" setting from Experimental section (unused)
- Removed "Skip Data Folder" feature from app configuration (redundant with Restore Account/Addon Only)

### 🔧 Fixes & Improvements

- Improved selection persistence across tab navigation
- Better fallback handling when persisted app no longer exists in configuration

### 📝 Technical Changes

**Backend**
- Added `ClearAllSessions()` function in app.go
- Added `BackupAllSessions()` function in app.go
- Auto-generate new IDs integrated into all restore functions
- SetActiveSession called after addon-only and account-only restores
- Removed SkipDataFolder field from AppConfig struct

**Frontend**
- Added `lastSelectedAppReset` and `lastSelectedAppSession` to settings store
- Removed `rememberLastTab`, `lastActiveTab`, `debugMode`, `skipDataFolder` from settings
- Updated ResetTab with new layout and badge display
- Added launch prompt modal to SessionsTab
- Added bulk management buttons to SettingsTab

---

## [2.0.2] - 2026-01-04

### ✨ New Features

**Settings Revamp**
- Restructured settings into 4 clear categories: General, Behavior, Sessions, Experimental
- Added Import/Export Settings - backup and restore your SurfManager configuration as JSON
- Added Reset All Settings button to restore defaults
- Moved experimental features to dedicated Experimental section with warning banner

**Restore Addon Only (Experimental)**
- New context menu option in Sessions tab to restore ONLY addon folders (like .aws, .ssh)
- Restores addon folders without touching main app data
- Must be enabled in Settings > Experimental > "Show Restore Addon Only"
- Only appears when app has addon paths configured and session has _addons folder
- Perfect for restoring credentials without affecting app settings

**Reset Tab Enhancements**
- Added "Reset Addon Data" button - delete only addon folders without touching main data
- Added "Kill App" button - force close running apps
- Button layout now uses 2 rows with 3 columns for better organization
- Addon button only appears for apps with configured addon paths
- Kill button only enabled when app is running

**Skip Data Folder Feature**
- New toggle in Config tab for Custom apps: "Skip Data Folder"
- Allows apps to backup/restore ONLY addon folders, skipping main data folder entirely
- Useful for apps where you only want to manage external folders (credentials, configs)

### 🔧 Fixes & Improvements

**UI/UX**
- Fixed toggle switch inconsistency - all toggles now have uniform appearance
- Replaced emoji icons with Lucide icons in context menus for consistency
- Removed "Set as Active" from session context menu (redundant feature)
- Stats section in Reset tab now shows addon folder count when applicable
- Removed placeholder "Last Reset" stat (not implemented)

**Bug Fixes**
- Fixed backup logic: empty BackupItems now correctly skips data folder instead of backing up everything
- Fixed reset logic: respects SkipDataFolder flag and BackupItems configuration
- Fixed field name mismatch: `addon_paths` → `addon_backup_paths` in frontend
- Fixed toggle component using inline styles for reliable positioning

### 📝 Technical Changes

**Backend**
- Added `RestoreAddonOnly()` function in app.go
- Added `CheckSessionHasAddons()` function in app.go
- Added `RestoreAddonsOnly()` method in backup.go
- Added `SessionHasAddons()` method in backup.go
- Added `SkipDataFolder` field to AppConfig struct

**Frontend**
- Complete SettingsTab.svelte revamp with new structure
- Enhanced SessionsTab.svelte with new context menu options
- Updated settings store with export/import/reset functions
- Fixed SettingToggle.svelte component for consistent behavior

---

## [2.0.1] - 2026-01-03

### 🔧 Fixes & Improvements

**GitHub Actions Workflow**
- Fixed invalid workflow file error on `build.yml`
- Resolved `matrix` context not accessible at job-level `if` condition
- Added step-level platform filtering for manual workflow dispatch
- Now properly supports selective platform builds (windows/linux/macos)

**Settings UX Improvement**
- Renamed "Skip Close App" to "Keep App Running" for better clarity
- Updated description to be more intuitive
- Toggle ON = app stays running during backup/restore/reset
- Toggle OFF = app will be closed before operations

---

## [2.0.0] - 2025-12-06

### 🚀 Complete Rewrite - Go + Wails + Svelte

**SurfManager v2.0** is a complete rewrite from Python/PyQt6 to Go + Wails + Svelte + TailwindCSS for better performance, smaller binary size, and modern UI.

### ✨ New Features

**🎨 Theme System**
- Dark theme (default)
- Solarized Dark theme
- Solarized Light theme
- Theme persistence across sessions

**⚙️ Settings System**
- Comprehensive settings with categories: Appearance, Behavior, Sessions, Notes, Advanced
- All settings persistent via localStorage
- New "Skip Close App" option - perform operations without closing target app
- Auto-backup toggle
- Confirmation dialogs (customizable)
- Remember last active tab

**🖥️ UI Improvements**
- JetBrains Mono font for better readability
- Realtime clock display in header
- Custom confirmation modals (no more browser alerts)
- Right-click context menus throughout the app
- CTRL+Click multi-selection in Sessions tab
- Split panel design for Reset tab
- Grid layout for Add App dialog
- Text selection disabled (native app feel)

**📝 Notes Tab**
- Create and manage notes
- Auto-save option
- Markdown support

**🔧 Config Tab Enhancements**
- VSCode Preset vs Custom app type
- Customizable backup items (choose what to backup)
- Additional folders support (backup extra directories)
- Smart file dialogs with default directories:
  - Executable: Opens from `AppData/Local/Programs`
  - Data Folder: Opens from `AppData/Roaming`
  - Additional Folders: Opens from user home
- Right-click context menu (Set Active, Edit JSON, Open Folder, Delete)

**📊 Sessions Tab Enhancements**
- Index number column
- App filter dropdown
- CTRL+Click selection (no checkboxes)
- Right-click context menu (Restore, Set Active, Open Folder, Delete)
- Icon + text action buttons

**🔄 Reset Tab Redesign**
- Split panel layout (Pro style)
- Left panel: App list with status indicators
- Right panel: App details, actions, stats
- Session count, Last Reset, Auto-Backup status
- Add App button navigates to Config tab

### 🛠️ Technical Changes

- **Framework**: Go + Wails v2 (from Python + PyQt6)
- **Frontend**: Svelte + TailwindCSS + Vite
- **Binary Size**: ~15MB (from 40+MB)
- **Startup Time**: <0.5s (from ~1s)
- **Memory Usage**: Significantly reduced
- **Cross-platform**: Windows, macOS, Linux support

### 📦 Migration Notes

- Settings are stored in localStorage (browser-based)
- App configs stored in `~/.surfmanager/AppConfigs/`
- Backups stored in `Documents/SurfManager/backup/`
- Notes stored in `Documents/SurfManager/notes/`

---

## [1.0.1] - 2025-12-05

### Fixed
- **Backup Path Structure**: Fixed incorrect backup directory naming
  - Changed from `SurfManagerBackups` to `Documents/SurfManager/backup`
  - Auto-backups now stored in `Documents/SurfManager/auto-backup`
  - Notes stored in `Documents/SurfManager/notes`

### Improved
- **Auto-Backup Toggle Button**: Better UX with badge counter
- **Reset Data Tab Sync**: Fixed app list not syncing with App Configuration
- **Session Scanning**: Skip internal folders when listing backups

---

## [1.0.0] - 2025-12-04

### Highlights
**New Redesign, User Friendly, and Fast - No More Freezing!**

### Added
- **Background Threading**: No more UI freezing during operations
- **Cross-Platform Support**: Windows, Linux, and macOS
- **Optimized Backup Items**: Reduced to 9 essential files/folders
- **Duplicate Protection**: Prevents overwriting existing sessions

### Fixed
- Variable name errors in backup/restore functions
- Filter combo changing after backup
- Session active status not displaying correctly

---

## [0.0.3-beta-windows] - 2025-12-04

### Added
- **Addon Backup Folders**: Optional additional folders to backup
- **Smart App Close**: Graceful termination before operations
- **Auto-Backup Protection**: Automatic backup before reset
- **Dual View Mode**: Separate views for manual sessions vs auto-backups

---

## [0.0.2-beta] - 2025-12-04

### Added
- **Session Backup System**: Full backup/restore functionality
- **Progress bar** in Reset Data tab

---

## [0.0.1-beta] - 2025-12-04

### Initial Release
- GUI foundation (PyQt6)
- Reset Data tab with program list
- Sessions and App Configuration tabs
- Dark theme UI
