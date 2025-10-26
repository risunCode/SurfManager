"""Main window GUI for SurfManager - Optimized version."""
import sys
import os
import webbrowser
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, 
    QStatusBar, QPushButton, QMessageBox, QLabel
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QIcon, QShortcut, QKeySequence
from app.core.audio_manager import AudioManager
from app.core.debug_utils import debug_print
from app.gui.splash_screen import SplashScreen
from app.gui.window_reset import ResetTab
from app.gui.window_account import AccountTab
from app.gui.window_documentation import DocumentationTab
from app.gui.styles import COMPACT_DARK_STYLE
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
        
        self.init_ui()
        self.apply_styles()
        self.setup_shortcuts()
        
        # Start application scan after window is shown (force full scan on startup)
        QTimer.singleShot(100, lambda: self.scan_applications(force_rescan=True))
    
    def init_ui(self):
        """Initialize the main window UI."""
        self.setWindowTitle(f"SurfManager v{__version__}")
        self.setMinimumSize(600, 500)
        self.resize(1000, 570)
        
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
        
        self.documentation_tab = DocumentationTab()
        self.tabs.addTab(self.documentation_tab, "📚 Documentation")
        
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
        """Add GitHub button to the right side of tab bar."""
        # Create container widget
        corner_widget = QWidget()
        corner_layout = QHBoxLayout()
        corner_layout.setContentsMargins(0, 0, 5, 0)
        corner_layout.setSpacing(3)
        corner_widget.setLayout(corner_layout)
        
        # Create SurfManager button (matching tab style, centered text)
        github_btn = QPushButton("🔗 SurfManager")
        github_btn.setFixedHeight(32)
        github_btn.setFixedWidth(130)
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
        if self.scan_thread and self.scan_thread.isRunning():
            self.log("Scan already in progress...")
            return
        
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
        self.detected_apps = apps
        
        # Update tabs with detected apps
        if hasattr(self.reset_tab, 'update_detected_apps'):
            self.reset_tab.update_detected_apps(apps, log_details=log_details)
        if hasattr(self.account_tab, 'update_detected_apps'):
            self.account_tab.update_detected_apps(apps)
        
        # Show summary
        installed_count = sum(1 for app in apps.values() if app.get('installed', False))
        self.status_bar.showMessage(f"Scan complete: {installed_count} apps detected")
        if log_details:
            self.log(f"Application scan completed: {installed_count} apps found")
        
        # Track telemetry
        if self.id_manager:
            self.id_manager.track_app_usage('system', 'scan')
    
    def open_debug_panel(self):
        """Open debug panel (test/debug mode only)."""
        self.log("Debug panel: Feature not yet implemented")
    
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
