# Changelog

All notable changes to SurfManager will be documented in this file.

## [1.0.1] - 2025-12-05

### Fixed
- **Backup Path Structure**: Fixed incorrect backup directory naming
  - Changed from `SurfManagerBackups` to `Documents/SurfManager/backup`
  - Auto-backups now stored in `Documents/SurfManager/auto-backup`
  - Notes stored in `Documents/SurfManager/notes`
  - Cleaner and more organized folder structure

### Improved
- **Auto-Backup Toggle Button**: Better UX with badge counter
  - Shows `Show Auto-Backup (N)` with count of available backups
  - Changes to `← Back to Sessions` when active for clarity
  - Real-time badge update on refresh
- **Reset Data Tab Sync**: Fixed app list not syncing with App Configuration
  - Immediate UI update when toggling apps active/inactive
  - Proper height calculation based on number of programs
  - No more "social distancing" spacing with few programs
- **Session Scanning**: Skip internal folders (sessions, auto-backups) when listing backups

### Technical
- Updated `platform_adapter.py` with new path structure
- Added `get_app_dir()` method for app root directory
- Improved `_update_scroll_height()` for dynamic sizing
- Enhanced `refresh_ui()` with geometry updates and event processing

---

## [1.0.0] - 2025-12-04

### Highlights
**New Redesign, User Friendly, and Fast - No More Freezing!**

### Added
- **Background Threading**: Backup and restore operations now run in background threads
  - No more UI freezing during long operations
  - Real-time progress updates via signals
  - Responsive interface throughout all operations
- **Cross-Platform Support**: New platform adapter for Windows, Linux, and macOS
  - Automatic path detection for each platform
  - User-specific directory resolution
  - Unified API for all platforms
- **Optimized Backup Items**: Reduced from 16+ items to 9 essential files/folders
  - Folders: User, Local Storage, Session Storage, Network
  - Files: Preferences, Local State, DIPS, machineid, languagepacks.json
  - Faster backup/restore with smaller file sizes
- **Duplicate Protection**: Prevents overwriting existing session backups
- **Screenshots**: Added Windows screenshots to README

### Changed
- **Build System**: Fixed PyInstaller configuration
  - Correct icon path resolution
  - Proper hidden imports for PyQt6
  - Size optimization with module exclusions
- **Code Cleanup**: Removed emojis from code, replaced with text alternatives
- **Session Table**: Disabled auto-sorting, maintains creation order
- **Set Active**: Fixed status display for active sessions

### Fixed
- Variable name errors in backup/restore functions
- Filter combo changing after backup (now stays on "All")
- Session active status not displaying correctly
- Unused highlight methods removed

### Technical
- New `app/core/workers.py` with BackupWorker and RestoreWorker classes
- New `app/core/platform_adapter.py` for cross-platform support
- Updated ConfigManager with platform-aware path resolution
- Signal-based progress communication between threads

---

## [0.0.3-beta-windows] - 2025-12-04

### Added
- **Addon Backup Folders**: Optional additional folders to backup (e.g., ~/.aws, ~/.ssh, custom configs)
  - Add extra folders in App Configuration dialog
  - Auto-backup and restore with session data
  - Support for any folder outside main app data path
- **Right-click Tip**: Added visual tip in Sessions tab about right-click options
- **Smart App Close**: ProcessKiller with graceful termination before operations
- **Auto-Backup Protection**: Automatic backup before reset operations
- **Dual View Mode**: Separate views for manual sessions vs auto-backups toggle

### Changed
- **Reset Tab Refresh**: Fixed app list not updating after adding new app in App Configuration
- **Progress Bars**: Now persist final status instead of resetting
- **Session Storage**: Filesystem-based (no more JSON conflicts)
- **Active Session Tracking**: Using marker files for reliability

### Fixed
- Reset Tab not showing newly added apps after refresh
- Auto-backups showing in main session view (now hidden by default)
- File lock errors during restore with retry mechanism
- Process detection with psutil integration

### Technical
- Added `addon_backup_paths` field in app configuration
- Enhanced `_create_backup()` and `_load_session()` for addon support
- Improved `refresh_ui()` in Reset Tab with proper widget cleanup
- Added psutil to requirements.txt

---

## [0.0.2-beta] - 2025-12-04

### Added
- **Session Backup System**: Full backup/restore functionality
  - "New Backup" button in Sessions toolbar
  - Create backup from any configured app
  - Load (restore) session via double-click or right-click
  - Update existing session with current data
- **Reset Data - Action buttons with labels**: `[📁 Folder] [🔄 Reset] [▶ Launch]`
- **Progress bar** in Reset Data tab

### Changed
- **Reset Data Layout**: Actions moved to bottom right (next to progress bar)
- **App Configuration Table**: Dark theme styling with proper borders
- **App Configuration Buttons**: Compact design `[Edit] [Del] [ON/OFF]`
- **Corner buttons**: User info + SurfManager GitHub button with consistent styling
- **Sessions - Applications**: Max 5 visible + "Show more" dialog for additional apps

### Fixed
- Double log output issue (messages appearing twice)
- App Configuration action buttons getting cut off
- Session log timestamp removed for cleaner output

## [0.0.1-beta] - 2025-12-04

### Initial Release
- GUI foundation only (base for v6.0.0)
- Reset Data tab with program list
- Data Management with sub-tabs:
  - Sessions (account manager placeholder)
  - App Configuration (dynamic app loading)
- Enable/Disable apps sync across tabs
- Dark theme UI
- Optimized lazy loading
- Icon caching for performance
