# SurfManager v3.0.0-rs

> **Advanced Session & Data Manager for Development Tools**

[![Version](https://img.shields.io/badge/version-3.0.0--rs-brightgreen.svg)](https://github.com/risunCode/SurfManager)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-blue.svg)](https://github.com/risunCode/SurfManager)
[![Rust](https://img.shields.io/badge/rust-1.70+-orange.svg)](https://www.rust-lang.org/)
[![Tauri](https://img.shields.io/badge/tauri-v2-blue.svg)](https://tauri.app/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

## 👋 Welcome to SurfManager!

**SurfManager** is a modern solution for managing session data of development tools like VS Code, Cursor, Windsurf, and similar applications. Built with Rust + Tauri v2 + Svelte for maximum performance, minimal memory usage, and a beautiful native UI.

Perfect for developers who need to:
- 🔄 Switch between multiple sessions/profiles effortlessly
- 💾 Backup workspace settings before experimenting
- 🚀 Maintain organized development workflows
- 🛡️ Have a safety net for important configurations

---

## 📸 Screenshots

<table>
  <tr>
    <td><img src="https://github.com/user-attachments/assets/84270f82-f69c-4697-a9bd-715dbd9aa4db" alt="Reset Data" width="400"/></td>
    <td><img src="https://github.com/user-attachments/assets/4da88062-ed39-4f31-b953-38ac97e2d1e0" alt="Sessions" width="400"/></td>
  </tr>
  <tr>
    <td><img src="https://github.com/user-attachments/assets/aeacc874-2d86-453f-86d1-97b2214c807a" alt="Config App" width="400"/></td>
    <td><img src="https://github.com/user-attachments/assets/ba163263-f275-444a-adf5-3d49cdc9bae0" alt="Notes" width="400"/></td>
  </tr>
  <tr>
    <td><img src="https://github.com/user-attachments/assets/7bb1bfc6-d2ae-407c-bbd1-5e76f58a2067" alt="Settings" width="400"/></td>
    <td><img src="https://github.com/user-attachments/assets/347d989d-2df7-49d0-a8e3-b77e772cc5a7" alt="About" width="400"/></td>
  </tr>
</table>

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| **📱 Session Management** | Backup, restore, and manage multiple app sessions |
| **🔄 Profile Switching** | Switch between different sessions/profiles in seconds |
| **🛠️ Smart App Close** | Auto-close running apps before operations (optional) |
| **📊 Progress Tracking** | Real-time progress bars for all operations |
| **🔍 Search & Filter** | Quick search through sessions and auto-backups |
| **💾 Auto-Backup** | Automatic backup before reset operations |
| **🎨 Theme System** | Dark, Solarized Dark, and Solarized Light themes |
| **⚙️ Customizable Settings** | Persistent settings for personalized experience |
| **📝 Custom App Config** | VSCode preset or fully custom backup items |
| **✏️ Edit App Config** | Edit existing app configurations via UI |

### 🚀 What's New in v3.0.0-rs

- **Complete Backend Rewrite** - Rust + Tauri v2 (from Go + Wails v2)
- **60% Less Memory** - ~4MB RAM (from ~10MB with Go)
- **Zero GC Overhead** - No garbage collection pauses
- **Native WebView** - Uses system WebView (no bundled Chromium)
- **Type-Safe IPC** - Tauri's command system with serde serialization
- **Async Operations** - Tokio runtime for non-blocking file operations
- **Optimized Builds** - LTO, strip, and single codegen unit

### 🚀 Previous Highlights (v2.x)

- **3-5x Faster Backup/Restore** - Parallel file copying using all CPU cores
- **Instant Session Listing** - Cached metadata eliminates slow directory scans
- **Theme System** - Dark, Solarized Dark, and Solarized Light themes
- **Customizable Backups** - Choose exactly what to backup
- **Additional Folders** - Backup extra directories (e.g., ~/.aws, ~/.ssh)

---

## 📁 App Data Locations

SurfManager manages app data stored in platform-specific locations:

| Platform | App Data (Config) | App Data (Local) | Example Apps |
|----------|-------------------|------------------|--------------|
| **Windows** | `%APPDATA%` (`C:\Users\{user}\AppData\Roaming`) | `%LOCALAPPDATA%` (`C:\Users\{user}\AppData\Local`) | `Roaming\Code`, `Roaming\Cursor` |
| **macOS** | `~/Library/Application Support` | `~/Library/Application Support` | `Application Support/Code` |
| **Linux** | `~/.config` | `~/.local/share` | `~/.config/Code`, `~/.config/Cursor` |

### SurfManager Storage Locations

| Data | Windows | macOS | Linux |
|------|---------|-------|-------|
| **Backups** | `Documents\SurfManager\backup` | `~/Documents/SurfManager/backup` | `~/Documents/SurfManager/backup` |
| **Auto-Backups** | `Documents\SurfManager\auto-backups` | `~/Documents/SurfManager/auto-backups` | `~/Documents/SurfManager/auto-backups` |
| **Notes** | `Documents\SurfManager\notes` | `~/Documents/SurfManager/notes` | `~/Documents/SurfManager/notes` |
| **App Configs** | `~\.surfmanager\AppConfigs` | `~/.surfmanager/AppConfigs` | `~/.surfmanager/AppConfigs` |

---

## 📖 How to Use

### Quick Start

**Step 1: Setup First Account**
1. Login to your IDE (VS Code/Cursor/Windsurf)
2. Configure your workspace, install extensions
3. Open SurfManager → Sessions → New Backup
4. Enter session name (e.g., "work-account")

**Step 2: Add More Accounts**
1. Go to Reset tab → Click Reset on your app
2. Login with different credentials in your IDE
3. Create another backup (e.g., "personal-account")

**Step 3: Switch Between Accounts**
1. Go to Sessions tab
2. Restore the session
3. Launch your IDE - you're logged in! 🎉

### Tips

- **Right-click** anywhere for context menus
- **CTRL+Click** rows to select multiple items
- **Enable "Skip Close App"** if you want to backup while app is running
- **Use descriptive names** like "work-main", "personal-dev"

---

## ⚠️ Limitations

### Platform-Specific

**Windows User Isolation**
Sessions are tied to the Windows user account. You cannot transfer backups between different Windows users due to encryption.

- ✅ Switch accounts on the same Windows user
- ❌ Copy backups to another Windows user
- ✅ Each Windows user creates their own backups

---

## � Installation

### Download Pre-built Release (Recommended)

1. Visit [Releases Page](https://github.com/risunCode/SurfManager/releases)
2. Download for your platform:
   - Windows: `SurfManager-windows-amd64.exe`
   - macOS: `SurfManager-darwin-amd64.zip` or `SurfManager-darwin-arm64.zip` (extract and run `.app`)
   - Linux: `SurfManager-linux-amd64`
3. Run directly - no installation required!

---

## � Building from Source

### Prerequisites (All Platforms)

- **Rust 1.70+** - [Install via rustup](https://rustup.rs/)
- **Node.js 18+** - [Download](https://nodejs.org/)
- **Tauri CLI** - Install with: `cargo install tauri-cli`

### Windows

```powershell
# Install prerequisites
# 1. Install Rust from https://rustup.rs/
# 2. Install Node.js from https://nodejs.org/
# 3. Install Visual Studio Build Tools (C++ workload)
# 4. WebView2 is pre-installed on Windows 10/11

# Install Tauri CLI
cargo install tauri-cli

# Clone and build
git clone https://github.com/risunCode/SurfManager.git
cd SurfManager
cd frontend && npm install && cd ..

# Development mode
cargo tauri dev

# Build for production
cargo tauri build
# Output: src-tauri/target/release/bundle/msi/*.msi
# Output: src-tauri/target/release/bundle/nsis/*-setup.exe
```

### macOS

```bash
# Install prerequisites via Homebrew:
brew install rustup node
rustup-init

# Install Xcode Command Line Tools
xcode-select --install

# Install Tauri CLI
cargo install tauri-cli

# Clone and build
git clone https://github.com/risunCode/SurfManager.git
cd SurfManager
cd frontend && npm install && cd ..

# Development mode
cargo tauri dev

# Build for production
cargo tauri build
# Output: src-tauri/target/release/bundle/dmg/*.dmg
```

### Linux (Ubuntu/Debian)

```bash
# Install prerequisites
sudo apt update
sudo apt install -y build-essential libwebkit2gtk-4.1-dev libssl-dev libgtk-3-dev libayatana-appindicator3-dev librsvg2-dev

# Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env

# Install Tauri CLI
cargo install tauri-cli

# Clone and build
git clone https://github.com/risunCode/SurfManager.git
cd SurfManager
cd frontend && npm install && cd ..

# Development mode
cargo tauri dev

# Build for production
cargo tauri build
# Output: src-tauri/target/release/bundle/deb/*.deb
# Output: src-tauri/target/release/bundle/appimage/*.AppImage
```

### Linux (Fedora/RHEL)

```bash
# Install prerequisites
sudo dnf install -y webkit2gtk4.1-devel openssl-devel gtk3-devel libappindicator-gtk3-devel librsvg2-devel

# Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env

# Install Tauri CLI
cargo install tauri-cli

# Clone and build
git clone https://github.com/risunCode/SurfManager.git
cd SurfManager
cd frontend && npm install && cd ..
cargo tauri build
```

### Linux (Arch)

```bash
# Install prerequisites
sudo pacman -S webkit2gtk-4.1 base-devel openssl gtk3 libappindicator-gtk3 librsvg

# Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env

# Install Tauri CLI
cargo install tauri-cli

# Clone and build
git clone https://github.com/risunCode/SurfManager.git
cd SurfManager
cd frontend && npm install && cd ..
cargo tauri build
```

### Verify Installation

```bash
rustc --version
cargo tauri --version
```

This will check if Rust and Tauri CLI are installed correctly.

---

## 🚀 Building with GitHub Actions (Recommended)

The easiest way to build for all platforms is using GitHub Actions. No need to install anything locally!

### Quick Start

1. **Fork the repository**
   - Go to [github.com/risunCode/SurfManager](https://github.com/risunCode/SurfManager)
   - Click "Fork" button (top right)

2. **Enable GitHub Actions**
   - Go to your forked repo → "Actions" tab
   - Click "I understand my workflows, go ahead and enable them"

3. **Run the build**
   - Go to "Actions" → "Build SurfManager"
   - Click "Run workflow" dropdown
   - Select platform:
     - `all` - Build for Windows, Linux, macOS (Intel & Apple Silicon)
     - `windows-amd64` - Windows 64-bit only
     - `linux-amd64` - Linux 64-bit only
     - `macos-amd64` - macOS Intel only
     - `macos-arm64` - macOS Apple Silicon only
   - Click "Run workflow"

4. **Download artifacts**
   - Wait for build to complete (~5-10 minutes)
   - Click on the completed workflow run
   - Download artifacts from the bottom of the page

### Creating a Release

To automatically create a GitHub Release with all binaries:

```bash
# Tag your version
git tag v2.0.0
git push origin v2.0.0
```

This will:
- Build for all 4 platforms automatically
- Create a GitHub Release
- Attach all binaries to the release

### Build Outputs

| Platform | Output File | Architecture |
|----------|-------------|--------------|
| Windows | `SurfManager-windows-amd64.exe` | 64-bit Intel/AMD |
| Linux | `SurfManager-linux-amd64` | 64-bit Intel/AMD |
| macOS | `SurfManager-darwin-amd64.zip` (.app inside) | Intel Mac |
| macOS | `SurfManager-darwin-arm64.zip` (.app inside) | Apple Silicon (M1/M2/M3) |

---

## 🆘 Help Wanted: Linux & macOS Compatibility

**We need your help!** SurfManager is primarily developed and tested on Windows. We need contributors to help with:

### Linux
- [ ] Test app data path detection (`~/.config`, `~/.local/share`)
- [ ] Test VSCode/Cursor data locations
- [ ] Verify file dialogs work correctly
- [ ] Test process detection and termination
- [ ] Package for different distributions (AppImage, Flatpak, Snap)

### macOS
- [ ] Test app data path detection (`~/Library/Application Support`)
- [ ] Test VSCode/Cursor data locations  
- [ ] Verify `.app` bundle selection works
- [ ] Test process detection and termination
- [ ] Code signing and notarization

### How to Contribute

1. Fork the repository
2. Test on your Linux/macOS machine
3. Report issues with detailed logs
4. Submit PRs for fixes

**Even just testing and reporting issues helps a lot!** 🙏
 
---

## 🤝 Contributing

We welcome contributions! Whether it's bug reports, feature suggestions, or code contributions.

```bash
git checkout -b feature/awesome-feature
git commit -m 'Add awesome feature'
git push origin feature/awesome-feature
# Open a Pull Request
```

---

## 📄 License

SurfManager is open-source under the MIT License.

---

## 🙏 Credits

**Built with ❤️ by risunCode**

**Technologies:** Rust, Tauri v2, Svelte, TailwindCSS, Lucide Icons

---

<div align="center">

**SurfManager v3.0.0-rs**

*Making development workflows smoother, one session at a time*

[⭐ Star on GitHub](https://github.com/risunCode/SurfManager) | [🐛 Report Issues](https://github.com/risunCode/SurfManager/issues) | [💡 Suggest Features](https://github.com/risunCode/SurfManager/discussions)

</div>
