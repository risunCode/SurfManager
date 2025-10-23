"""Main window GUI for SurfManager with modular design."""
import sys
import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QTabWidget, QStatusBar, QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QIcon
from core.app_manager import AppManager
import webbrowser
from core.backup_manager import BackupManager
from gui.window_reset import ResetTab
from gui.window_account import AccountTab
from gui.styles import COMPACT_DARK_STYLE


class ScanThread(QThread):
    """Background thread for scanning applications."""
    finished = pyqtSignal(dict)
    
    def __init__(self, app_manager):
        super().__init__()
        self.app_manager = app_manager
    
    def run(self):
        apps = self.app_manager.scan_applications()
        self.finished.emit(apps)


class MainWindow(QMainWindow):
    """Main application window with modular tabs."""
    
    def __init__(self):
        super().__init__()
        self.app_manager = AppManager()
        self.backup_manager = BackupManager()
        self.detected_apps = {}
        
        self.init_ui()
        self.apply_styles()
        self.scan_applications()
    
    def init_ui(self):
        """Initialize the main window UI."""
        self.setWindowTitle("SurfManager")
        self.setMinimumSize(600, 500)
        self.resize(1000, 650)
        
        # Central widget with tabs
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # Tab widget
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Create modular tabs
        self.reset_tab = ResetTab(
            self.app_manager, 
            self.backup_manager, 
            self.statusBar(), 
            self.log,
            self.scan_applications  # Add refresh callback
        )
        self.tabs.addTab(self.reset_tab, "🔄 Reset Data")
        
        self.account_tab = AccountTab(
            self.app_manager,
            self.log
        )
        self.tabs.addTab(self.account_tab, "👤 Account Manager")
        
        # Add GitHub button to tab bar
        self.add_github_button_to_tabs()
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
    
    def log(self, message: str):
        """Add message to log output."""
        if hasattr(self.reset_tab, 'log_output'):
            self.reset_tab.log_output.append(message)
        print(f"[SurfManager] {message}")
    
    def apply_styles(self):
        """Apply compact dark stylesheet."""
        self.setStyleSheet(COMPACT_DARK_STYLE)
    
    def scan_applications(self):
        """Scan for installed applications."""
        self.status_bar.showMessage("Scanning applications...")
        
        self.scan_thread = ScanThread(self.app_manager)
        self.scan_thread.finished.connect(self.on_scan_finished)
        self.scan_thread.start()
    
    def on_scan_finished(self, apps: dict):
        """Handle scan completion."""
        self.detected_apps = apps
        self.update_app_paths()
        self.status_bar.showMessage("Scan complete", 3000)
        self.log(f"✓ Scan completed - Found {len([a for a in apps.values() if a['installed']])} application(s)")
    
    def update_app_paths(self):
        """Update the application path displays in reset tab."""
        if hasattr(self.reset_tab, 'update_app_paths'):
            self.reset_tab.update_app_paths(self.detected_apps)
    
    def add_github_button_to_tabs(self):
        """Add GitHub button to the right side of tab bar."""
        # Create GitHub button
        github_btn = QPushButton("🔗 SurfManager")
        github_btn.setFixedSize(85, 24)  # Even smaller width
        github_btn.setStyleSheet("""
            QPushButton {
                background-color: #4299e1;
                color: white;
                border: none;
                padding: 4px 3px;
                border-radius: 2px;
                font-weight: bold;
                font-size: 10px;
                margin: 1px;
            }
            QPushButton:hover {
                background-color: #3182ce;
            }
            QPushButton:pressed {
                background-color: #2c5282;
            }
        """)
        github_btn.clicked.connect(self.open_github)
        
        # Add button to tab bar corner
        self.tabs.setCornerWidget(github_btn, Qt.Corner.TopRightCorner)
    
    def open_github(self):
        """Open GitHub repository in browser."""
        try:
            webbrowser.open("https://github.com/risunCode/SurfManager")
        except Exception as e:
            print(f"Error opening GitHub: {e}")
    
    def closeEvent(self, event):
        """Handle window close event."""
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
