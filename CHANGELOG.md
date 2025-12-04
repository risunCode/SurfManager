# Changelog

All notable changes to SurfManager will be documented in this file.

## [0.0.2-beta] - 2024-12-04

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

## [0.0.1-beta] - 2024-12-04

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
