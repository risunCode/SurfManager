# SurfManager
 
> **Advanced Session & Data Manager for Development Tools**

[![Version](https://img.shields.io/badge/version-1.0.0-brightgreen.svg)](https://github.com/risunCode/SurfManager)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-blue.svg)](https://github.com/risunCode/SurfManager)
[![Python](https://img.shields.io/badge/python-3.8+-yellow.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

<div align="center">
  <img src="https://github.com/user-attachments/assets/82268ac2-c360-40c0-866a-c87a2db9aba5" alt="SurfManager Screenshot" width="800"/>
</div>

---

## 👋 Welcome to SurfManager!

**SurfManager** is a modern solution for managing session data of development tools like VS Code, Cursor, Windsurf, and similar applications. With a clean interface and powerful features, SurfManager makes it easy for developers to backup, restore, and switch between multiple accounts seamlessly.

Perfect for developers who need to:
- 🔄 Switch between multiple accounts/profiles effortlessly
- 💾 Backup workspace settings before experimenting
- 🚀 Maintain organized development workflows  
- 🛡️ Have a safety net for important configurations

---

## Screenshots (Windows)

![1 Reset data](https://github.com/user-attachments/assets/e142de68-8491-4c90-bd79-6f8d43446eab)
![2-backup](https://github.com/user-attachments/assets/7b056f6f-228b-403f-b7e9-a72f732a1901)
![3-app config](https://github.com/user-attachments/assets/7864b5cd-aa72-44e5-8874-600c378bd343)
![4-about](https://github.com/user-attachments/assets/42442eaa-70ca-454b-8cb1-9c0e7cfc3b36)

---

## ✨ Features

### 🎯 Core Features

| Feature | Description |
|---------|-------------|
| **📱 Session Management** | Backup, restore, and manage multiple app sessions |
| **🔄 Account Switching** | Switch between different accounts in seconds |
| **🛡️ Smart App Close** | Auto-close running apps before operations to avoid conflicts |
| **📊 Progress Tracking** | Real-time progress bars for all operations |
| **🔍 Search & Filter** | Quick search through sessions and auto-backups |
| **💾 Auto-Backup** | Automatic backup before reset operations |
| **📁 Dual View Mode** | Separate views for manual sessions and auto-backups |
| **⚡ Process Management** | Advanced process management with graceful termination |

### 🚀 Advanced Features

**🎯 Smart Operations**
- **Real-time Process Detection** - Accurately detect running applications
- **Graceful App Termination** - Safely close apps before operations
- **Retry Mechanisms** - Auto-retry for failed operations
- **File Lock Protection** - Handle file conflicts with intelligent retry logic
- **Progress Persistence** - Progress bars don't reset after completion

**📋 Session Management**
- **Filesystem-based Storage** - No more JSON conflicts, direct folder scanning
- **Active Session Tracking** - Mark and track active sessions with marker files
- **Batch Delete Operations** - Delete multiple sessions at once
- **Session Size Display** - Real-time folder size calculation
- **Contextual Actions** - Right-click menus for quick actions

**🔧 Developer Experience**
- **Dynamic App Loading** - Auto-detect installed applications
- **Dark Theme UI** - Beautiful dark interface that's easy on the eyes
- **Keyboard Shortcuts** - Quick access via hotkeys
- **Local Logging** - Per-tab logging for better debugging
- **Configuration Management** - Easy app configuration via GUI

---

## 💡 The Story Behind SurfManager

**The Problem**
Modern developers often work with multiple accounts, different projects, and various configurations. But managing session data for apps like VS Code, Cursor, or Windsurf can be tedious:

- Manual backup-restore is time-consuming and error-prone
- Switching between accounts requires repeated logout-login cycles
- Experimenting with settings risks breaking perfectly tuned configurations
- Authentication data often conflicts when not handled properly

**The Solution**
SurfManager was born from personal developer frustration needing an elegant solution to this problem. What started as a simple script for backing up VS Code settings evolved into a comprehensive session manager that:

- **Automates repetitive tasks** - No more manual backup-restore
- **Prevents data loss** - Smart app close and auto-backup protection
- **Streamlines workflow** - Switch profiles in seconds, not minutes
- **Handles edge cases** - File locks, process conflicts, permission issues

**The Evolution**
From a simple CLI script to a full-featured GUI application with:
- Advanced process management (ProcessKiller)
- Real-time progress tracking
- Filesystem-based storage (reliable)
- Cross-platform compatibility
- Developer-friendly UX

> **⚠️ Disclaimer:** SurfManager is a tool for development workflow management. Users are responsible for complying with software licenses and Terms of Service. Developers are not liable for how this tool is used.

---

## 📖 How to Use SurfManager

### 🎯 Getting Started

#### Main Use Case: Multiple Account Management

**Step 1: Setup First Account**
1. **Login to your IDE** - Use your first account in VS Code/Cursor/etc.
2. **Configure your workspace** - Install extensions, set preferences, login to services
3. **Create backup** - In SurfManager, click an app → enter session name (e.g., "work-account")
4. **Done!** Your complete session is saved

**Step 2: Add More Accounts**
1. **Reset the app** - Use SurfManager's Reset Data tab to clear current session
2. **Login with new account** - Use different credentials in your IDE
3. **Configure new environment** - Set up workspace for this account
4. **Save new session** - Create another backup (e.g., "personal-account")

**Step 3: Switch Between Accounts**
1. **Browse sessions** - View all saved sessions in the Sessions tab
2. **Double-click to restore** - Or right-click → "Load"
3. **Launch your IDE** - You're logged in with that account! 🎉

### 🖱️ Interface Guide

**Sessions Tab:**
- **App buttons** - Click to create new backup
- **Sessions table** - View all saved sessions
- **Right-click menu** - Quick actions (Load, Update, Set Active, Rename, Browse, Delete)
- **Auto-Backups toggle** - Switch between manual sessions and auto-backups
- **Search bar** - Filter sessions by name

**Reset Data Tab:**
- **Reset button** - Clear app data (with auto-backup option)
- **AutoBackup toggle** - Enable/disable automatic backup before reset
- **Launch button** - Open app folder or executable

### 💡 Tips & Tricks

- **Right-click sessions** for quick actions menu
- **Double-click sessions** to restore instantly
- **Toggle Auto-Backups** to view automatic backups separately
- **Use descriptive names** like "work-main", "personal-dev", etc.
- **Enable AutoBackup** before reset operations for safety

---

## ⚠️ Limitations

### 🔒 Platform-Specific Restrictions

**Windows User Isolation**
Sessions are tied to the Windows user account that created them. You cannot transfer backups between different Windows users.

**Why this exists:**
- Windows encrypts app credentials with user-specific keys
- Authentication tokens (like DIPS files) are encrypted per Windows user
- Cross-user session restoration would fail authentication

**What this means:**
- ✅ Switch between accounts **on the same Windows user**
- ❌ Copy backups to another Windows user account
- ✅ Each Windows user must create their own session backups

---

## 🆕 What's New

### 🔥 v1.0.0 - New Redesign, User Friendly, and Fast!

**🚀 No More Freezing!**
- **Background Threading** - Backup and restore run in background threads
- **Responsive UI** - Interface stays smooth during all operations
- **Real-time Progress** - Live updates via signal-based communication

**🌐 Cross-Platform Ready**
- **Platform Adapter** - Automatic path detection for Windows, Linux, macOS
- **Unified API** - Same code works across all platforms

**⚡ Optimized Performance**
- **Smaller Backups** - Reduced from 16+ items to 9 essential files/folders
- **Faster Operations** - Only backup what matters
- **Duplicate Protection** - Prevents overwriting existing sessions

**🛠️ Quality Improvements**
- Fixed build system with proper PyInstaller configuration
- Removed emojis from code for cleaner codebase
- Fixed session active status display
- Session table maintains creation order

### 🔄 Previous Updates (v0.0.2-beta)
- **GUI Foundation** - Modern PyQt6 interface
- **Multi-tab Architecture** - Sessions, Reset Data, App Configuration, About
- **Dynamic App Loading** - Auto-detection of installed applications
- **Dark Theme UI** - Professional dark interface
- **Cross-platform Base** - Framework for Windows/macOS/Linux support

---

## 🚀 Installation & Build

### 📦 Option 1: Download Pre-built Release (Recommended)

**Windows:**
1. Visit the [Releases Page](https://github.com/risunCode/SurfManager/releases)
2. Download `SurfManager-Windows.exe`
3. Run directly - no installation required!

### 🔧 Option 2: Build from Source

**Prerequisites:**
- Python 3.8+
- Git

**Instructions:**
```bash
# Clone repository
git clone https://github.com/risunCode/SurfManager.git
cd SurfManager

# Install dependencies
pip install -r requirements.txt

# Run application
python main.py
```

**Platform Notes:**
- **Windows** - Full support, can build executables
- **macOS** - Framework support (untested)
- **Linux** - Framework support (untested)

---

## 🤝 Contributing

We welcome contributions! Whether it's bug reports, feature suggestions, or code contributions.

### How to Contribute

```bash
# Fork the repository on GitHub
# Create a feature branch
git checkout -b feature/awesome-feature

# Make your changes
git commit -m 'Add awesome feature'

# Push to your fork
git push origin feature/awesome-feature

# Open a Pull Request
```

### Areas for Contribution

| Area | Description |
|------|-------------|
| **Platform Support** | Improve macOS and Linux compatibility |
| **App Support** | Add support for more development tools |
| **Documentation** | Enhance guides and documentation |
| **Bug Fixes** | Help identify and fix issues |
| **UI/UX** | Design improvements and user experience |
| **Testing** | Cross-platform testing and validation |

---

## 📄 License

SurfManager is open-source under the MIT License. See [LICENSE](LICENSE) for details.

```
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.
```

---

## 🙏 Credits

**Built with ❤️ by:**
- **risunCode** - Project Creator & Lead Developer
- **Community Contributors** - Feature suggestions, bug reports, and code contributions

**Special Thanks:**
- PyQt6 team for the amazing GUI framework
- psutil developers for process management capabilities
- All beta testers and early adopters

**Technologies Used:**
- **PyQt6** - Modern GUI framework
- **Python 3.8+** - Core application language
- **psutil** - Process management and system monitoring
- **qtawesome** - Beautiful icons for the interface

---

<div align="center">
  
**SurfManager v1.0.0**

*Making development workflows smoother, one session at a time*

[⭐ Star us on GitHub](https://github.com/risunCode/SurfManager) | [🐛 Report Issues](https://github.com/risunCode/SurfManager/issues) | [💡 Suggest Features](https://github.com/risunCode/SurfManager/discussions)

</div>
