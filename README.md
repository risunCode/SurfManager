# SurfManager v2.1.0 - Optimized Edition

Advanced session and data management tool for Windsurf, Cursor, and Claude.

[![Version](https://img.shields.io/badge/version-2.1.0-blue.svg)](https://github.com/risunCode/SurfManager)
[![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)](https://github.com/risunCode/SurfManager)
[![Python](https://img.shields.io/badge/python-3.8+-yellow.svg)](https://www.python.org/)
[![Size](https://img.shields.io/badge/size-~60--70MB-green.svg)](https://github.com/risunCode/SurfManager)

---

## What is SurfManager?

Session and data management tool for development applications like Windsurf, Cursor, and Claude.

**Key Features:**
- Reset application data safely
- Backup and restore sessions
- Generate new device IDs
- Quick folder access
- Audio feedback for actions
- Keyboard shortcuts for productivity

---

## Main Features

### Reset Data Tab
- Auto-detect installed applications (Windsurf, Cursor, Claude)
- Reset application data with automatic backup
- Generate new device IDs
- Cleanup cache and temporary files
- Quick access to application folders
- Keyboard shortcuts: Ctrl+L (clear log), F5 (refresh), Ctrl+M (toggle audio), Ctrl+G (generate ID)

### Account Manager Tab
- Create session backups with custom names
- Restore previous sessions
- Update existing backups
- Session management (rename, delete, set active)
- Multi-app support (Cursor, Windsurf, Claude)
- Search and filter sessions
- Keyboard shortcuts: F5 (refresh), Ctrl+O (open folder), Ctrl+F (search), Ctrl+1/2/3 (quick backup)

### Advanced Settings Tab
- Configure backup locations
- Edit configuration files
- Manage application paths
- Export and import settings


## What's New in v2.1.0

**Code Optimization**
- 10% code reduction through file merging and optimization
- External CSS stylesheets for better maintainability
- JSON-based configuration system
- Eliminated 300+ lines of duplicate code

**Enhanced UX**
- 10 keyboard shortcuts for faster workflow
- Enhanced tooltips with shortcut hints
- Improved UI layout (less clutter, better accessibility)
- Table headers with descriptive tooltips

**Code Quality**
- Fixed all bare except statements (better debugging)
- Specific exception handling throughout
- Improved error logging
- Better maintainability

---

## Installation

**Requirements:**
- Windows 10/11
- Python 3.8+ (for building from source)
- Disk space: ~100 MB

**Pre-built Binary:**
1. Download `SurfManager.exe` from [Releases](https://github.com/risunCode/SurfManager/releases)
2. Run directly, no installation needed

**Build from Source:**
```cmd
git clone https://github.com/risunCode/SurfManager.git
cd SurfManager
setup.bat
python scripts/build_installer.py --type stable
```

---

## Usage

**Reset Application Data:**
1. Open Reset Data tab
2. Click Reset button next to the application
3. Confirm the action (automatic backup will be created)
4. Wait for process to complete

**Create Backup:**
1. Open Account Manager tab
2. Click Backup button for desired app (or use Ctrl+1/2/3)
3. Enter session name
4. Backup saved to Documents/SurfManager/

**Restore Session:**
1. Open Account Manager tab
2. Right-click on session
3. Select Restore Session
4. Application closes and restores data automatically

**Generate New Device ID:**
1. Open Reset Data tab
2. Click Generate ID (or press Ctrl+G)
3. Select application
4. New device ID will be generated

---

## Configuration

**Config Files:**
- app/config/config.json - Main configuration
- app/config/app_metadata.json - Application metadata
- app/config/messages.json - Error and success messages
- app/audio/audio_config.json - Audio settings

**Storage Locations:**
- Session backups: Documents/SurfManager/
- Application data: AppData/Roaming/ (system default)

---

## Building

**Build Options:**
```cmd
python scripts/build_installer.py --type stable  # No console
python scripts/build_installer.py --type debug   # With console 
python scripts/build_installer.py --clean-only   # Clean only
```

**Build Features:**
- Minimal dependencies (3 core packages)
- Aggressive module exclusion
- Binary stripping
- Expected size: 60-70 MB

---

## Dependencies

**Core Packages:**
```txt
PyQt6==6.7.0          # GUI framework
psutil==5.9.8         # Process management  
pyinstaller==6.3.0    # Build tool
```

**Audio:** Native Windows winsound (no external dependency)

**Size History:**
- v1.0.0: ~100 MB
- v1.5.0: ~80 MB
- v2.0.0: ~60-70 MB
- v2.1.0: ~60-70 MB (optimized code, same size)

---

## Keyboard Shortcuts

**Reset Tab:**
- Ctrl+L: Clear log
- F5: Refresh application list
- Ctrl+M: Toggle audio
- Ctrl+G: Generate new device ID

**Account Manager:**
- F5: Refresh session list
- Ctrl+O: Open backup folder
- Ctrl+F: Focus search
- Ctrl+1: Quick backup Cursor
- Ctrl+2: Quick backup Windsurf
- Ctrl+3: Quick backup Claude

---

## Troubleshooting

**Audio not working:**
- Check audio_enabled: true in config
- Verify audio files exist in app/audio/sound/
- Supported formats: WAV only (native Windows)

**Application not detected:**
- Ensure application installed in default location
- Check app/config/config.json for path detection
- Try refreshing with F5

**Build fails:**
- Run setup.bat first
- Ensure Python 3.8+ installed
- Install dependencies: pip install -r requirements.txt

---

## Tips

**Session Backups:**
- Use descriptive names (e.g., "Project-ClientA")
- Backup before major updates
- Test restore with non-critical sessions first
- Clean up old backups periodically

**Performance:**
- Close applications before backup/restore
- Disable audio if needed (Ctrl+M)
- Use debug mode only for troubleshooting

---

## Contributing

Contributions welcome:
1. Fork repository
2. Create feature branch
3. Commit changes
4. Open Pull Request

---

## License

MIT License - see LICENSE file for details

---

## Author

risunCode - [GitHub](https://github.com/risunCode)

---

## Acknowledgments

- PyQt6 GUI framework
- Community contributors

---

**Optimized build, maximum functionality**
