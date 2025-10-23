# 🏄 SurfManager

**Advanced Application Data Manager**

Created by: **risunCode**  
GitHub: [github.com/risuncode](https://github.com/risuncode)

## 📋 Overview

SurfManager is a powerful Windows application for managing application data, user profiles, and system processes. It provides a clean, modern interface for safely resetting application data with automatic backups and managing multiple user accounts.

## ✨ Features

- 🔄 **Data Reset & Cleanup** - Safely clean application data with automatic backups
- 👤 **Account Management** - Switch between multiple user profiles easily  
- 🔍 **Auto Detection** - Automatically finds installed applications
- 💾 **Backup System** - Creates backups before any data operations
- ⚡ **Process Control** - Monitor and manage running processes
- 🎨 **Modern UI** - Clean, dark theme with intuitive design
- 🛡️ **Safe Operations** - All operations include safety checks
- 📊 **Real-time Status** - Live updates on operation progress

## 🚀 Quick Start

### Option 1: Use Pre-built Executable
1. Download `SurfManager.exe` from releases
2. Run the executable (no installation required)
3. Grant administrator permissions when prompted

### Option 2: Build from Source
1. Clone the repository
2. Run `build_app_windows.cmd`
3. Find the executable in `dist/SurfManager.exe`

## 🔧 Building

### Prerequisites
- Windows 10/11 (64-bit)
- Python 3.8+ (for building from source)

### Build Instructions
```cmd
# Clone the repository
git clone https://github.com/risuncode/SurfManager.git
cd SurfManager

# Run the build script
build_app_windows.cmd
```

The build script will:
- Create a virtual environment
- Install dependencies
- Build an optimized executable
- Output to `dist/SurfManager.exe`

### Build Optimizations
The build process includes several optimizations to keep the executable size under 10MB:
- Excludes unused PyQt6 modules
- Removes unnecessary standard library modules
- Strips debug symbols
- Uses optimized PyInstaller configuration

## 💻 System Requirements

- **Operating System:** Windows 10/11 (64-bit)
- **Memory:** 4 GB RAM minimum
- **Storage:** 50 MB free space
- **Dependencies:** None (standalone executable)
- **Permissions:** Administrator rights for some operations

## 📚 Usage

### Reset Data Tab
- Select applications to reset
- Create automatic backups
- Monitor reset progress
- View operation logs

### Account Manager Tab
- Manage multiple user profiles
- Switch between accounts
- Import/export account data
- Session management

### Info Tab
- View documentation
- Creator information
- System requirements
- Feature overview

## 🛡️ Safety Features

- **Automatic Backups:** All operations create backups before making changes
- **Process Detection:** Warns if target applications are running
- **Confirmation Dialogs:** Requires confirmation for destructive operations
- **Rollback Support:** Can restore from backups if needed

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## 📄 License

This project is open source. See the repository for license details.

## 📞 Support

- **GitHub Issues:** [Report bugs or request features](https://github.com/risuncode/SurfManager/issues)
- **GitHub Profile:** [github.com/risuncode](https://github.com/risuncode)

---

**Made with ❤️ by risunCode**
