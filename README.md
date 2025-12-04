# SurfManager

> A simple program for managing IDE and extension data, including login credentials, account switching, workspaces, and more.

[![Version](https://img.shields.io/badge/version-5.2.0-brightgreen.svg)](https://github.com/risunCode/SurfManager)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-blue.svg)](https://github.com/risunCode/SurfManager)
[![Python](https://img.shields.io/badge/python-3.8+-yellow.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

<img width="1398" height="885" alt="SurfManager Screenshot" src="https://github.com/user-attachments/assets/82268ac2-c360-40c0-866a-c87a2db9aba5" />
 
## Showcase

https://github.com/user-attachments/assets/7621f048-3fe6-4299-bf19-29fa92522626
> I forget to tell, right click action is avaible on account manager :V

## 👋 Welcome to SurfManager!

SurfManager is a handy tool designed to help developers effortlessly manage session data for their IDE applications. Whether you're backing up, restoring, keeping things tidy, or seamlessly switching between different accounts and workspaces, SurfManager offers a clean, cross-platform solution to keep your workflow smooth.

## ✨ Key Features

- **Account Switching** - Seamlessly switch between different IDE accounts
- **Multi-Account Management** - Manage multiple user profiles and credentials
- **Session Backup & Restore** - Save and restore your IDE workspace states
- **Cross-Platform Support** - Works on Windows, macOS, and Linux
- **Data Organization** - Keep your IDE extensions and settings organized
- **Workspace Management** - Handle multiple project workspaces efficiently


## ✨ Cool Features You'll Love

### 🔄 Easy Session Management
*   **Create & Restore** backups with custom names – no more lost work!
*   **Batch Operations** to handle multiple sessions at once.
*   **Search & Filter** through your saved sessions in a snap.
*   **Auto-Backup** kicks in before any reset, just in case.

### 🚀 Smart & Speedy Operations
*   **Real-time Detection** of running apps, with auto-close for smooth operations.
*   **Intelligent Caching** for lightning-fast performance.
*   **Auto-detects** your installed applications.
*   **Quick Access** to application folders when you need them.

## 💡 Why SurfManager?

Managing multiple development environments can be challenging. Whether you're working on different projects, testing various configurations, or maintaining separate workspace setups, keeping track of different IDE sessions and their associated data quickly becomes complex.

SurfManager was created to simplify this workflow. Modern development tools store a wealth of session data - from workspace configurations and extension settings to authentication states and user preferences. Manually managing these across different setups is time-consuming and error-prone.

SurfManager streamlines this entire process. With just a few clicks, you can:
- **Switch between configurations** instantly by managing complete session data
- **Backup your current setup** before making changes
- **Restore previous states** without losing your carefully crafted environment
- **Organize multiple profiles** for different projects or workflows
- **Maintain clean IDE environments** across various use cases

What started as a solution for efficient workspace management has evolved into a comprehensive session manager that helps developers maintain organized, reproducible development environments - perfect for testing new setups, managing multiple projects, or simply keeping your development workflow clean and efficient.

> **⚠️ Important Note:** SurfManager is provided as a development workflow management tool. Users are responsible for ensuring their usage complies with all applicable software licenses and Terms of Service. The developers assume no liability for how this tool is used.

## 🚀 Fast Installation/Usage

### 📦 Option 1: Download Pre-built Release (Recommended)

**For Windows Users:**
1. Visit our [Releases Page](https://github.com/risunCode/SurfManager/releases)
2. Download the latest `SurfManager-Windows.exe`
3. Run the executable directly - no installation required!
 
### 🔧 Option 2: Manual Build from Source

**Prerequisites:**
- Python 3.8+ installed
- Git installed

**Build Instructions:**

```bash
# Clone the repository
git clone https://github.com/risunCode/SurfManager.git
cd SurfManager

# Install dependencies
pip install -r requirements.txt

# Run from source
python main.py

# OR use our cross-platform launcher (Linux/macOS)
./Launcher.sh
```

> **⚠️ Important Note:** Due to platform-specific dependencies and PyQt6 requirements, Windows builds cannot generate executables for macOS or Linux. Each platform must be built on its respective operating system for optimal compatibility.
> **⚠️ Disclaimer:** This build process has not been tested at all for macOS and Linux.

**Platform-Specific Build Notes:**
- **Windows**: Can only build Windows executables
- **macOS**: Can only build macOS executables (requires Xcode command line tools)
- **Linux**: Can only build Linux executables (may require additional PyQt6 system packages)


## 📖 How to Use SurfManager

### 🎯 Getting Started
1. **Launch SurfManager** - Run the application using one of the installation methods above
2. **First-Time Setup** - The app will automatically detect your installed IDEs (or you can configure them manually)
3. **Main Dashboard** - Navigate through the clean, intuitive interface

### 🔄 Setting Up Multiple Accounts (The Main Use Case!)

> **Note:** SurfManager saves complete IDE session data including account credentials, workspace configurations, and extension login states.

**First Account:**
1. **Login to your IDE** - Use your first account credentials in the IDE application
2. **Configure Your Workspace** - Set up your workspace, install extensions, and login to any extension services
3. **Save the Session** - In SurfManager, select the app and click "Create Backup" with a meaningful name (e.g., "Account-1")
4. **Done!** - Your complete session (account, workspace, and extension logins) is now saved

**Adding More Accounts:**
1. **Reset the Application** - Use SurfManager's reset function to clear the current session
2. **Login with Another Account** - Open your IDE and login with a different account
3. **Setup New Environment** - Configure workspace and extension logins for this account
4. **Save New Session** - Create another backup in SurfManager (e.g., "Account-2")
5. **Repeat** - Add as many accounts as you need!

**Switching Between Accounts:**
1. **Browse Your Backups** - See all your saved account sessions in the backup list
2. **Select & Restore** - Choose the account you want to use and click "Restore Session"
3. **Launch IDE** - Open your IDE and you're logged in with that account, complete with all workspace settings and extension logins! 🎉

### 🔍 Other Features
- **Search Function** - Quickly find specific backups by name
- **Batch Operations** - Manage multiple sessions at once
- **Auto-Close Detection** - SurfManager automatically closes running IDE instances when needed
- **Application Folders** - Quick access to your IDE's data directories

## ⚠️ Limitations

### 🔒 Windows User-Specific Sessions
**Saved sessions are tied to the Windows user account that created them.** You cannot transfer backup sessions between different Windows users (e.g., from User A to User B).

**Why this limitation exists:**
- Windows uses user-specific encryption for application credentials and authentication tokens
- Session data (including the `DIPS` file and other authentication databases) are encrypted with the current user's Windows credentials
- When restored on a different Windows user account, these encrypted credentials cannot be decrypted, causing authentication to fail

**What this means:**
- ✅ You can switch between multiple accounts **on the same Windows user**
- ❌ You cannot copy backups to another Windows user account and expect them to work
- ✅ Each Windows user must create and manage their own session backups

> **Tip:** If you need to use multiple IDE accounts across different Windows users, each Windows user should set up their own SurfManager backups independently.

## 🆕 What's New in This Build

### 🔥 Latest Updates (v5.2.0 - Released 11/24/2025)
- **Code Architecture Optimization** - Comprehensive redundancy elimination across 7 major categories
- **Improved Maintainability** - Reduced code duplication by 10-15% (~265 lines eliminated)
- **Centralized Path Management** - Single source of truth for all path operations
- **Unified Dialog System** - Consolidated confirmation dialogs with consistent behavior
- **Performance Enhancement** - Cached platform detection eliminates repeated system calls
- **Better Code Organization** - Clear ownership patterns for utilities, paths, and operations
- **Enhanced Reliability** - Consistent error handling across directory creation and file operations

### 🔄 Previous Updates (v5.1.2)
- **Initial Cross-Platform Support** - Basic compatibility framework for macOS, and Linux (untested on macOS/Linux)
- **Intelligent Process Detection** - Real-time detection of running applications with automatic closure
- **Advanced Caching System** - Lightning-fast performance with intelligent caching mechanisms
- **Batch Operation Support** - Handle multiple sessions simultaneously for increased productivity
- **Auto-Backup Protection** - Automatic backup creation before any reset operations
- **Improved Search & Filter** - Enhanced search functionality to quickly locate specific sessions


## 🤝 Want to Contribute?

We love contributions! Whether it's reporting a bug, suggesting a new feature, or diving into the code, your input helps make SurfManager even better.

### How to Contribute

```bash
# 1. Fork the repository on GitHub.
# 2. Create a new feature branch for your changes.
git checkout -b feature/my-awesome-feature

# 3. Commit your changes with a clear message.
git commit -m 'Add my awesome feature'

# 4. Push your changes to your branch.
git push origin feature/my-awesome-feature

# 5. Open a Pull Request on our GitHub repo!
```

### Areas Where You Can Help

| Area | Description |
|------|-------------|
| **Platform Support** | Help us improve Linux and macOS support! |
| **App Support** | Suggest or help add support for more applications. |
| **Documentation** | Make our docs and guides even clearer. |
| **Bug Fixes** | Help us find and squash those pesky bugs! |
| **UI/UX** | Share your ideas for design enhancements. |

## ⚖️ Disclaimer

> SurfManager is a community-driven development tool, built by developers, for developers. It's here to help you manage your coding environments more efficiently.

### Important Notes:

*   ⚠️ **Always** back up important data before performing reset operations.
*   📜 **Follow** the Terms of Service of any applications you're managing.
*   ✅ This tool is for **legitimate development workflow management**.
*   🔒 **Use responsibly** and in accordance with applicable laws.

> **Disclaimer:** We're not responsible for how you choose to use this tool. By using SurfManager, you're joining a community that values clean workflows and efficient tooling.

## 📄 License

SurfManager is open-source under the MIT License. See the [LICENSE](LICENSE) file for all the details.

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

<div align="center">
Built with ❤️ by risuncode and community
</div>
