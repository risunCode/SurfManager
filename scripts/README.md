# 📜 Scripts Directory

Build scripts untuk SurfManager project.

---

## 📁 Files

### `build_installer.py`
**Main build script** - Unified build system untuk SurfManager

**Features:**
- ✅ Build stable executable (no console)
- ✅ Build debug executable (with console)
- ✅ Standalone executable support
- ✅ Clean build directories

**Usage:**
```bash
# Default: Stable
python scripts/build_installer.py

# Debug dengan console
python scripts/build_installer.py --type debug

# Build both stable + debug
python scripts/build_installer.py --type both

# Clean only
python scripts/build_installer.py --clean-only

# Help
python scripts/build_installer.py --help
```

**Arguments:**
- `--type {stable,debug,both}` - Build type selection
- `--clean-only` - Only clean build directories

---

### `setup.bat`
Setup script untuk development environment

**Usage:**
```bash
setup.bat
```

---

### `launch_app.cmd`
Launch script untuk development

**Usage:**
```bash
launch_app.cmd
```

---

## 🎯 Quick Reference

### Development Workflow

```bash
# 1. Setup environment (first time)
setup.bat

# 2. Build debug untuk testing
python scripts/build_installer.py --type debug

# 3. Test debug build
output/debug/SurfManager_Debug.exe

# 4. Build stable untuk production
python scripts/build_installer.py --type stable --no-installer

# 5. Build installer untuk release
python scripts/build_installer.py
```

### Production Release

```bash
# Build stable executable
python scripts/build_installer.py --type stable

# Output:
# - output/stable/SurfManager.exe
# - output/stable/README.md
# - output/stable/CHANGELOG.md
```

---

## 📦 Output Structure

```
output/
├── stable/
│   ├── SurfManager.exe              # Stable build (no console)
│   ├── README.md
│   └── CHANGELOG.md
└── debug/
    ├── SurfManager_Debug.exe        # Debug build (with console)
    ├── README.md
    └── CHANGELOG.md
```

---

## 🔧 Configuration

### Build Types

**Stable:**
- No console window (`--windowed`)
- Optimized for production
- Environment: `SURFMANAGER_BUILD_TYPE=STABLE`

**Debug:**
- Console window enabled (`--console`)
- Debug symbols included
- Verbose logging
- Environment: `SURFMANAGER_BUILD_TYPE=DEBUG`

---

## 📚 See Also

- [README.md](../README.md) - Project README
- [Launcher.cmd](../Launcher.cmd) - Main launcher with build menu
