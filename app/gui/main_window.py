"""Main window GUI for SurfManager - Optimized version."""
import os
import webbrowser
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, 
    QStatusBar, QPushButton, QMessageBox, QLabel, QMenu
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QMutex, QMutexLocker
from PyQt6.QtGui import QIcon, QShortcut, QKeySequence
import threading
from app.core.audio_manager import AudioManager
from app.core.core_utils import (
    debug_print,
    WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT, WINDOW_DEFAULT_WIDTH, WINDOW_DEFAULT_HEIGHT,
    USER_BUTTON_MIN_WIDTH, USER_BUTTON_MAX_HEIGHT,
    GITHUB_BUTTON_WIDTH, GITHUB_BUTTON_HEIGHT,
    USER_LIST_REFRESH_DELAY_MS, REFRESH_SCAN_DELAY_MS,
    SPLASH_DELAY_MS, SCAN_DELAY_MS,
    get_constants
)
from app.gui.splash_screen import SplashScreen
from app.gui.window_reset import ResetTab
from app.gui.window_account import AccountTab
from app.gui.window_advanced import AdvancedTab
from app.gui.theme import COMPACT_DARK_STYLE
from app import __version__


class ScanThread(QThread):
    """Background thread for scanning applications."""
    finished = pyqtSignal(dict)
    progress = pyqtSignal(str)
    
    def __init__(self, app_manager, force_rescan=False):
        super().__init__()
        self.app_manager = app_manager
        self.force_rescan = force_rescan
    
    def run(self):
        if self.force_rescan:
            self.progress.emit("Scanning for installed applications...")
        else:
            self.progress.emit("Checking application status...")
        apps = self.app_manager.scan_applications(force_rescan=self.force_rescan)
        self.finished.emit(apps)


class MainWindow(QMainWindow):
    """Main application window with modular tabs."""
    
    def __init__(self, app_manager=None, backup_manager=None, 
                 id_manager=None, config_manager=None):
        super().__init__()
        
        # Core managers (use provided or create new instances)
        from app.core.app_manager import AppManager
        from app.core.backup_manager import BackupManager
        from app.core.id_manager import IdManager
        from app.core.config_manager import ConfigManager
        
        self.app_manager = app_manager or AppManager()
        self.backup_manager = backup_manager or BackupManager()
        self.id_manager = id_manager or IdManager()
        self.config_manager = config_manager or ConfigManager()
        
        # UI managers
        self.audio_manager = AudioManager()
        self.scan_thread = None
        self.test_mode = False
        self.detected_apps = {}
        
        # Thread safety
        self.scan_mutex = QMutex()
        self.detected_apps_lock = threading.Lock()
        
        self.init_ui()
        self.apply_styles()
        self.setup_shortcuts()

        # Trigger initial application scan after UI is ready
        QTimer.singleShot(SPLASH_DELAY_MS, lambda: self.scan_applications(force_rescan=True))
    
    def init_ui(self):
        """Initialize the main window UI."""
        self.setWindowTitle(f"SurfManager v{__version__}")
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        self.resize(WINDOW_DEFAULT_WIDTH, WINDOW_DEFAULT_HEIGHT)
        
        # Set window icon if exists
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'icons', 'surfmanager.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # Central widget with tabs
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # Tab widget
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Create modular tabs with real managers
        self.reset_tab = ResetTab(
            self.app_manager,
            self.statusBar(),
            self.log,
            self.scan_applications,
            self.audio_manager
        )
        self.tabs.addTab(self.reset_tab, "🔄 Reset Data")
        
        self.account_tab = AccountTab(
            self.app_manager,
            self.log
        )
        self.tabs.addTab(self.account_tab, "👤 Account Manager")
        
        self.advanced_tab = AdvancedTab(
            self.app_manager,
            self.log
        )
        self.tabs.addTab(self.advanced_tab, "⚙️ Advanced")
        
        # Add custom tab bar styling with better spacing
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border-top: 2px solid #3d3d3d;
                margin-top: 2px;
            }
            QTabBar::tab {
                padding: 8px 16px;
                margin-right: 2px;
            }
        """)
        
        # Add GitHub button to tab bar
        self.add_corner_widgets_to_tabs()
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
    
    def log(self, message: str):
        """Add message to log output."""
        if hasattr(self, 'reset_tab') and hasattr(self.reset_tab, 'log_output'):
            self.reset_tab.log_output.append(message)
        debug_print(f"[LOG] {message}")
    
    def apply_styles(self):
        """Apply compact dark stylesheet."""
        self.setStyleSheet(COMPACT_DARK_STYLE)
    
    def add_corner_widgets_to_tabs(self):
        """Add user info and GitHub buttons to the right side of tab bar."""
        # Create container widget
        corner_widget = QWidget()
        corner_layout = QHBoxLayout()
        corner_layout.setContentsMargins(0, 0, 5, 0)
        corner_layout.setSpacing(3)
        corner_widget.setLayout(corner_layout)
        
        # User button with menu (more reliable than QComboBox)
        self.user_btn = QPushButton("👤 Loading...")
        self.user_btn.setMinimumWidth(USER_BUTTON_MIN_WIDTH)
        self.user_btn.setMaximumHeight(USER_BUTTON_MAX_HEIGHT)
        self.user_btn.setToolTip("Click to switch Windows user")
        self.user_btn.setStyleSheet("""
            QPushButton {
                background: #4CAF50;
                color: white;
                border: 2px solid #45a049;
                border-radius: 5px;
                padding: 5px 10px;
                font-size: 12px;
                font-weight: bold;
                text-align: center;
            }
            QPushButton:hover {
                background: #5cbf60;
            }
            QPushButton:pressed {
                background: #45a049;
            }
        """)
        self.user_btn.clicked.connect(self.show_user_menu)
        corner_layout.addWidget(self.user_btn)
        
        # Populate user list with delay
        QTimer.singleShot(USER_LIST_REFRESH_DELAY_MS, self.refresh_user_list)
        
        # GitHub button (right)
        github_btn = QPushButton("🔗 SurfManager")
        github_btn.setFixedHeight(GITHUB_BUTTON_HEIGHT)
        github_btn.setFixedWidth(GITHUB_BUTTON_WIDTH)
        github_btn.setStyleSheet("""
            QPushButton {
                background-color: #0d7377;
                color: #ffffff;
                border: 1px solid #0a5a5d;
                padding: 0px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #0f8a8f;
                border: 1px solid #0d7377;
            }
            QPushButton:pressed {
                background-color: #0a5a5d;
            }
        """)
        github_btn.clicked.connect(self.open_github)
        corner_layout.addWidget(github_btn)
        
        # Add container to tab bar corner
        self.tabs.setCornerWidget(corner_widget, Qt.Corner.TopRightCorner)
    
    def refresh_user_list(self):
        """Refresh Windows user list."""
        try:
            import getpass
            import os
            
            debug_print("[DEBUG] Refreshing user list...")
            
            # Get all users from system drive
            system_drive = os.getenv('SystemDrive', 'C:')
            if not system_drive.endswith('\\'):
                system_drive += '\\'
            users_dir = os.path.join(system_drive, 'Users')
            self.all_users = []
            self.current_user = getpass.getuser()
            
            debug_print(f"[DEBUG] Current user: {self.current_user}")
            debug_print(f"[DEBUG] Scanning users directory: {users_dir}")
            
            if os.path.exists(users_dir):
                exclude_dirs = {'Public', 'Default', 'Default User', 'All Users', 'desktop.ini'}
                for item in os.listdir(users_dir):
                    user_path = os.path.join(users_dir, item)
                    debug_print(f"[DEBUG] Checking: {item} - isdir: {os.path.isdir(user_path)}")
                    
                    # Include all user directories
                    if os.path.isdir(user_path) and item not in exclude_dirs:
                        self.all_users.append(item)
                        debug_print(f"[DEBUG] Added user: {item}")
            
            debug_print(f"[DEBUG] Found {len(self.all_users)} users: {self.all_users}")
            
            # Sort: current user first
            self.all_users.sort(key=lambda x: (x.lower() != self.current_user.lower(), x.lower()))
            
            # Update button text
            self.user_btn.setText(f"👤 {self.current_user}")
            
            # Enable/disable button based on user count
            self.user_btn.setEnabled(len(self.all_users) > 0)
                    
        except Exception as e:
            debug_print(f"[DEBUG] Error refreshing user list: {e}")
            self.user_btn.setText("👤 Error")
    
    def show_user_menu(self):
        """Show user selection menu."""
        if not hasattr(self, 'all_users') or not self.all_users:
            return
        
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background: #2d2d2d;
                color: white;
                border: 2px solid #4CAF50;
                padding: 5px;
            }
            QMenu::item {
                padding: 8px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background: #4CAF50;
            }
        """)
        
        for user in self.all_users:
            display_name = f"👤 {user}"
            if user.lower() == self.current_user.lower():
                display_name += " (Current)"
            action = menu.addAction(display_name)
            action.setData(user)
        
        action = menu.exec(self.user_btn.mapToGlobal(self.user_btn.rect().bottomLeft()))
        if action:
            selected_user = action.data()
            self.switch_user(selected_user)
    
    def switch_user(self, username):
        """Switch to different user."""
        try:
            self.current_user = username
            self.user_btn.setText(f"👤 {username}")
            self.log(f"Switched to user: {username}")
            
            # Update config
            self.config_manager.set('current_user', username)
            
            # Trigger app scan
            QTimer.singleShot(REFRESH_SCAN_DELAY_MS, lambda: self.scan_applications(force_rescan=True))
            
        except Exception as e:
            self.log(f"Error switching user: {e}")
    
    def open_github(self):
        """Open GitHub repository in browser."""
        try:
            webbrowser.open("https://github.com/risunCode/SurfManager")
        except Exception as e:
            print(f"Error opening GitHub: {e}")
    
    def setup_shortcuts(self):
        """Setup keyboard shortcuts."""
        # Debug shortcuts (only in debug/test mode)
        if self.config_manager.get('debug_mode', False) or self.test_mode:
            QShortcut(QKeySequence("Ctrl+Shift+D"), self, self.open_debug_panel)
            QShortcut(QKeySequence("Ctrl+Shift+L"), self, self.show_log_viewer)
            QShortcut(QKeySequence("Ctrl+Shift+T"), self, self.run_test_suite)
        
        # Normal shortcuts
        QShortcut(QKeySequence("Ctrl+R"), self, self.scan_applications)
        QShortcut(QKeySequence("F5"), self, self.scan_applications)
        QShortcut(QKeySequence("Ctrl+Q"), self, self.close)
    
    def scan_applications(self, force_rescan=False):
        """Scan for installed applications.
        
        Args:
            force_rescan: If True, perform full rescan. Otherwise just check running status.
        """
        # Thread-safe check for running scan
        locker = QMutexLocker(self.scan_mutex)
        if self.scan_thread and self.scan_thread.isRunning():
            self.log("Scan already in progress...")
            return
        locker.unlock()
        
        # Get selected user
        selected_user = self.current_user if hasattr(self, 'current_user') else None
        
        # Update AppManager with selected user paths
        if selected_user:
            system_drive = os.getenv('SystemDrive', 'C:')
            if not system_drive.endswith('\\'):
                system_drive += '\\'
            user_profile = os.path.join(system_drive, 'Users', selected_user)
            appdata_roaming = os.path.join(user_profile, 'AppData', 'Roaming')
            appdata_local = os.path.join(user_profile, 'AppData', 'Local')
            self.app_manager.set_current_user(selected_user, appdata_roaming, appdata_local)
            
            if force_rescan:
                self.log(f"Scanning applications for user: {selected_user}")
        else:
            if force_rescan:
                self.log("Starting application scan...")
        
        self.status_bar.showMessage("Scanning for applications...")
        
        self.scan_thread = ScanThread(self.app_manager, force_rescan=force_rescan)
        self.scan_thread.progress.connect(self.status_bar.showMessage)
        self.scan_thread.finished.connect(lambda apps: self.on_scan_finished(apps, log_details=force_rescan))
        self.scan_thread.start()
    
    def on_scan_finished(self, apps: dict, log_details: bool = True):
        """Handle scan completion.
        
        Args:
            apps: Dictionary of detected applications
            log_details: If True, log detailed information
        """
        # Thread-safe update of detected apps
        with self.detected_apps_lock:
            self.detected_apps = apps.copy()
        
        # Update tabs with detected apps
        if hasattr(self.reset_tab, 'update_detected_apps'):
            self.reset_tab.update_detected_apps(apps, log_details=log_details)
        
        if hasattr(self.account_tab, 'update_detected_apps'):
            self.account_tab.update_detected_apps(apps)

        # Show essential scan results
        if log_details:
            installed_apps = [name for name, info in apps.items() if info.get('installed', False)]
            if installed_apps:
                self.log(f"Found {len(installed_apps)} installed applications")
            else:
                self.log("No applications detected")

        # Show summary in status bar
        installed_count = sum(1 for app in apps.values() if app.get('installed', False))
        self.status_bar.showMessage(f"Scan complete: {installed_count} apps detected")
    
    def show_log_viewer(self):
        """Show log viewer (test/debug mode only)."""
        self.log("Log viewer: Feature not yet implemented")
    
    def run_test_suite(self):
        """Run test suite (test/debug mode only)."""
        self.log("Test suite: Feature not yet implemented")
    
    def closeEvent(self, event):
        """Handle window close event."""
        # Save window state and configuration
        if self.config_manager:
            self.config_manager.save_config()
        
        # Only show confirmation in non-test mode
        if not self.test_mode:
            reply = QMessageBox.question(
                self, 
                'Exit SurfManager', 
                'Are you sure you want to exit?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
