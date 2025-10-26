# SurfManager - Changelog

Complete version history from v1.0.0 to v2.0.0

---

## Version 2.0.0 - Minimal Build Edition (2025-10-25)

### 🎯 Major Optimization

#### Dependency Reduction
- **✅ Removed pywin32** - Eliminated unused Windows COM dependencies (~8 MB saved)
- **✅ Kept pygame** - Retained for multi-format audio support (OGG, MP3, WAV)
- **✅ Minimal Dependencies** - Only 4 core packages (PyQt6, pygame, psutil, pyinstaller)

#### Build Size Optimization
- **Aggressive Module Exclusion** - Excludes 20+ unnecessary modules (matplotlib, numpy, pandas, scipy, PIL, tkinter, sqlite3, email, http.server, xmlrpc, etc.)
- **Binary Stripping** - Removes debug symbols with `--strip` flag
- **Optimized Logging** - Minimal logging level (WARN) for stable builds
- **Expected Size** - ~60-70 MB (down from ~100 MB in v1.0.0)

#### Audio System Overhaul
- **✅ Individual Action Sounds** - Setiap button punya config audio sendiri
- **✅ First-Then-Random Mode** - First play: specific sound, subsequent: random
- **✅ Config-Based Audio** - Semua audio 100% dari config file
- **❌ Removed** - `play_success_sound()` method (tidak dipakai)
- **❌ Removed** - Audio dari Account Tab (tidak diperlukan)

#### Audio Config Structure
```json
{
  "sounds": {
    "startup": { "filename": "trimakasih-pak-jokowi.mp3" },
    "reset_windsurf": {
      "first_play": "hey-antek-antek-asing-prabowo.mp3",
      "subsequent_play": "random",
      "exclude": ["startup.ogg"]
    },
    "reset_cursor": { ... },
    "reset_claude": { ... },
    "clear_data": { ... },
    "cleanup": { ... },
    "generate_new_id": { ... },
    "open_folder": { ... }
  }
}
```

#### Code Improvements
- **Removed unused imports** - win32com imports dihapus dari build config
- **Cleaned up audio_manager.py** - Removed deprecated methods
- **Updated window_reset.py** - Semua audio calls pakai `play_action_sound()`
- **Streamlined requirements.txt** - Hanya 4 dependencies

### 📦 Final Dependencies
```txt
PyQt6==6.7.0          # GUI Framework
pygame==2.6.1         # Multi-format audio
psutil==5.9.8         # Process management
pyinstaller==6.3.0    # Build tool
```

### 🚀 Performance Impact
- ✅ **30-40% smaller** executable size
- ✅ **Faster startup** (fewer modules to load)
- ✅ **Lower memory** footprint
- ✅ **Same functionality** maintained

### 📝 Documentation Updates
- ✅ Updated README.md to v2.0.0
- ✅ Updated CHANGELOG.md with complete history
- ✅ Updated documentation tab with changelog
- ✅ Updated all version strings to 2.0.0

### 🔄 Breaking Changes
- **None** - Fully backward compatible with v1.5.0
- Audio config structure changed (but auto-migrates)

### 🐛 Bug Fixes
- ✅ Fixed audio not playing correctly (wrong method calls)
- ✅ Fixed audio config not being used properly
- ✅ Removed unused audio_manager from AccountTab

---

## Version 1.5.0 - Optimized Edition (2025-10-25)

### 🎉 Major Changes

#### Core Refactoring
- **Unified Build System** - Merged `build_stable.py` and `build_debug.py` into single `build_installer.py`
- **Optimized Scripts** - Reduced from 6 scripts to 3 (50% reduction)
- **Module Integration** - Integrated DeviceIdManager into ResetThread for better efficiency
- **Singleton Pattern** - ConfigManager now uses singleton pattern for better performance

#### New Features
- **User-Defined Backup Names** - Backup naming format: `appname-userdefine-timestamp`
- **Centralized Launcher** - Complete menu system (`Launcher.cmd`)
- **Build Configurations** - Support for Stable (no console) and Debug (with console) builds
- **Portable Installation** - Single EXE with installation prompt
- **Desktop Shortcuts** - Automatic shortcut creation on installation

### 🔧 Bug Fixes

#### Critical Fixes
- ✅ Fixed `AA_EnableHighDpiScaling` AttributeError (Qt6 compatibility)
- ✅ Fixed `ConfigManager.get_path()` → Changed to `get()`
- ✅ Fixed `AppManager.kill_app_process()` missing method
- ✅ Fixed `AppManager.launch_application()` missing method
- ✅ Fixed `ConfigManager.get_backup_files()` removed non-existent call
- ✅ Fixed Unicode/Emoji encoding issues on Windows console
- ✅ Fixed ResetTab constructor signature mismatch
- ✅ Fixed version consistency across all files (v1.5.0)

#### Minor Fixes
- Fixed path detection for installed vs development mode
- Fixed backup directory creation
- Fixed telemetry file handling
- Improved error messages and logging

### 🚀 New AppManager Methods
- `kill_app_process(app_name)` - Kill application processes
- `launch_application(app_name)` - Launch application executable
- `get_process_info(app_name)` - Get detailed process information

### 🎨 UI Improvements
- Launcher color changed to yellow (0E) for better visibility
- Better error handling with user-friendly messages
- Improved backup naming with user input
- Enhanced session management interface

### 🔒 Security & Stability
- UTF-8 encoding support for all platforms
- Graceful fallback for emoji display on unsupported consoles
- Better error handling throughout the application
- Improved process termination (graceful → forceful)

### 📊 Performance
- Reduced script count by 50%
- Singleton pattern for ConfigManager
- Optimized module imports
- Better memory management

### 🧪 Testing
- Added `test_imports.py` for module testing
- Added `test_detection.py` for app detection testing
- All core modules tested and verified

### 📝 Documentation
- Created comprehensive README
- Added CHANGELOG.md
- Improved inline code documentation
- Better error messages

### 🔄 Breaking Changes
- Backup naming format changed: `app-session-timestamp` → `app-userdefine-timestamp`
- ConfigManager now uses singleton pattern
- Some internal method signatures changed (backward compatible)

### 🐛 Known Issues
- None currently reported

### 📦 Dependencies
- PyQt6==6.7.0
- pygame==2.6.1
- psutil==5.9.8
- pywin32==306 (later removed in v2.0.0)
- pyinstaller==6.3.0

### 🎯 Supported Applications
- ✅ Windsurf
- ✅ Cursor
- ✅ VS Code
- ✅ Claude

---

## Version 1.0.0 - Initial Release (2025-10-20)

### 🎉 Initial Features

#### Core Functionality
- **Application Detection** - Automatic detection of Windsurf, Cursor, VS Code, Claude
- **Reset Operations** - Complete data cleanup with backup support
- **Device ID Management** - Reset and manage device identifiers
- **Backup System** - Create and restore backups with compression
- **Process Management** - Detect and close running applications

#### GUI Features
- **PyQt6 Interface** - Modern, responsive GUI
- **Tab Navigation** - Organized by functionality (Reset, Backup, Account, Documentation)
- **Splash Screen** - Loading screen with progress indicator
- **Dark Theme** - Eye-friendly dark interface
- **Sound Effects** - Audio feedback using pygame

#### Build System
- **PyInstaller Integration** - Single executable builds
- **Separate Scripts** - build_stable.py and build_debug.py
- **Multiple Launchers** - Dedicated scripts for each operation

### 📦 Initial Dependencies
- PyQt6==6.7.0
- pygame==2.6.1
- psutil==5.9.8
- pywin32==306
- pyinstaller==6.3.0

### 🎯 Supported Applications
- Windsurf
- Cursor
- VS Code
- Claude

### 🐛 Known Issues (Fixed in v1.5.0)
- Qt6 compatibility issues with AA_EnableHighDpiScaling
- ConfigManager method inconsistencies
- Missing AppManager methods
- Unicode encoding issues on Windows console
- Multiple build scripts causing confusion

---

## 📊 Version Comparison

| Feature | v1.0.0 | v1.5.0 | v2.0.0 |
|---------|--------|--------|--------|
| **Build Size** | ~100 MB | ~80 MB | ~60-70 MB |
| **Dependencies** | 5 packages | 5 packages | 4 packages |
| **Build Scripts** | 2 separate | 1 unified | 1 unified |
| **Audio System** | Basic | Basic | Advanced (first-then-random) |
| **Module Exclusion** | ~7 modules | ~14 modules | ~20+ modules |
| **Binary Stripping** | ❌ | ❌ | ✅ |
| **Config-Based Audio** | ❌ | ❌ | ✅ |
| **Individual Action Sounds** | ❌ | ❌ | ✅ |

---

## 🔮 Future Plans (v2.1.0+)

- Add more application support (VS Code full support, etc.)
- Implement backup scheduling
- Add cloud backup integration
- Create GUI installer
- Add update checker
- Further size optimizations with UPX compression
- Multi-language support

---

## 📞 Support & Contact

- **GitHub**: [risunCode/SurfManager](https://github.com/risunCode/SurfManager)
- **Issues**: [Report bugs](https://github.com/risunCode/SurfManager/issues)
- **Author**: risunCode

---

**Full Changelog**: https://github.com/risunCode/SurfManager/releases
