"""Main window for SurfManager - Optimized loading."""
import os
import getpass
import webbrowser
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QStatusBar, QPushButton, QLabel
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon
import qtawesome as qta

from app.gui.styles import DARK_STYLE, SUB_TAB_STYLE
from app import __app_name__

# Lazy imports - loaded when needed
_ResetTab = None
_AccountTab = None
_AppConfigTab = None
_NotepadTab = None
_AboutTab = None

def _get_reset_tab():
    global _ResetTab
    if _ResetTab is None:
        from app.gui.tab_reset import ResetTab
        _ResetTab = ResetTab
    return _ResetTab

def _get_account_tab():
    global _AccountTab
    if _AccountTab is None:
        from app.gui.tab_account import AccountTab
        _AccountTab = AccountTab
    return _AccountTab

def _get_app_config_tab():
    global _AppConfigTab
    if _AppConfigTab is None:
        from app.gui.tab_app_config import AppConfigTab
        _AppConfigTab = AppConfigTab
    return _AppConfigTab

def _get_notepad_tab():
    global _NotepadTab
    if _NotepadTab is None:
        from app.gui.tab_notepad import NotepadTab
        _NotepadTab = NotepadTab
    return _NotepadTab

def _get_about_tab():
    global _AboutTab
    if _AboutTab is None:
        from app.gui.tab_about import AboutTab
        _AboutTab = AboutTab
    return _AboutTab


class DummyAppManager:
    """Placeholder app manager."""
    def get_app_info(self, name): return {"installed": False, "path": "", "running": False}
    def kill_app_process(self, name): return False, "No functionality"
    def launch_application(self, name): return False, "No functionality"


# Cache icons for reuse
_icon_cache = {}

def _get_icon(name, color):
    """Get cached icon."""
    key = f"{name}_{color}"
    if key not in _icon_cache:
        _icon_cache[key] = qta.icon(name, color=color)
    return _icon_cache[key]


class MainWindow(QMainWindow):
    """Main application window - Optimized."""
    
    def __init__(self):
        super().__init__()
        self._tabs_initialized = False
        self._init_ui()
        self.setStyleSheet(DARK_STYLE)
        # Defer heavy tab loading
        QTimer.singleShot(0, self._init_tabs_deferred)
    
    def _init_ui(self):
        """Initialize UI shell (fast)."""
        self.setWindowTitle(__app_name__)
        self.setMinimumSize(600, 500)
        self.resize(1000, 570)
        
        # Icon
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'icons', 'app.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        central.setLayout(layout)
        
        # Main Tabs (empty, will be filled in deferred init)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Tab styling
        self.tabs.setStyleSheet("QTabWidget::pane { border-top: 2px solid #3d3d3d; margin-top: 2px; } QTabBar::tab { padding: 8px 16px; margin-right: 2px; }")
        
        # Corner widget: User info + GitHub button
        corner_widget = QWidget()
        corner_layout = QHBoxLayout()
        corner_layout.setContentsMargins(0, 0, 6, 0)
        corner_layout.setSpacing(4)
        corner_widget.setLayout(corner_layout)
        
        # Shared style for corner elements
        corner_style = """
            QPushButton {
                color: #aaa;
                font-size: 11px;
                padding: 4px 10px;
                background-color: #2d2d30;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
                border-color: #4d4d4d;
                color: #ccc;
            }
        """
        
        # User info button (clickable label style)
        username = getpass.getuser()
        user_btn = QPushButton(f" {username}")
        user_btn.setIcon(_get_icon('fa5s.user', '#888'))
        user_btn.setToolTip(f"Current user: {username}")
        user_btn.setStyleSheet(corner_style)
        corner_layout.addWidget(user_btn)
        
        # GitHub button (same style, different color accent)
        github_btn = QPushButton(" SurfManager")
        github_btn.setIcon(_get_icon('fa5b.github', '#4fc3f7'))
        github_btn.setToolTip("Visit SurfManager on GitHub")
        github_btn.setStyleSheet("""
            QPushButton {
                color: #aaa;
                font-size: 11px;
                padding: 4px 10px;
                background-color: #2d2d30;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #0d7377;
                border-color: #0d7377;
                color: #fff;
            }
        """)
        github_btn.clicked.connect(lambda: webbrowser.open("https://github.com/risunCode/SurfManager"))
        corner_layout.addWidget(github_btn)
        
        self.tabs.setCornerWidget(corner_widget, Qt.Corner.TopRightCorner)
        
        # Status bar
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Loading...")
    
    def _init_tabs_deferred(self):
        """Initialize tabs after window is shown (deferred for faster startup)."""
        if self._tabs_initialized:
            return
        self._tabs_initialized = True
        
        app_manager = DummyAppManager()
        
        # 1. Reset Data Tab
        ResetTab = _get_reset_tab()
        self.reset_tab = ResetTab(self.statusBar(), self.log)
        self.tabs.addTab(self.reset_tab, _get_icon('fa5s.sync-alt', '#4fc3f7'), "Reset Data")
        
        # 2. Data Management Tab
        self._create_data_management_tab(app_manager)
        
        self.statusBar().showMessage("Ready")
    
    def _create_data_management_tab(self, app_manager):
        """Create Data Management tab with sub-tabs."""
        data_widget = QWidget()
        data_layout = QVBoxLayout()
        data_layout.setContentsMargins(0, 0, 0, 0)
        data_widget.setLayout(data_layout)
        
        # Sub-tabs
        self.data_sub_tabs = QTabWidget()
        self.data_sub_tabs.setTabPosition(QTabWidget.TabPosition.North)
        data_layout.addWidget(self.data_sub_tabs)
        
        # 1. Sessions sub-tab
        AccountTab = _get_account_tab()
        self.account_tab = AccountTab(app_manager, self.log)
        self.data_sub_tabs.addTab(self.account_tab, _get_icon('fa5s.users', '#ce93d8'), "Sessions")
        
        # 2. App Configuration sub-tab
        AppConfigTab = _get_app_config_tab()
        self.app_config_tab = AppConfigTab(self.log)
        self.app_config_tab.apps_changed.connect(self._on_apps_config_changed)
        self.data_sub_tabs.addTab(self.app_config_tab, _get_icon('fa5s.cog', '#4fc3f7'), "App Configuration")
        
        # 3. Notepad sub-tab
        NotepadTab = _get_notepad_tab()
        self.notepad_tab = NotepadTab()
        self.data_sub_tabs.addTab(self.notepad_tab, _get_icon('fa5s.sticky-note', '#FFD54F'), "Notepad")
        
        self.data_sub_tabs.setStyleSheet(SUB_TAB_STYLE)
        self.tabs.addTab(data_widget, _get_icon('fa5s.database', '#ce93d8'), "Data Management")
        
        # 3. About Tab
        AboutTab = _get_about_tab()
        self.about_tab = AboutTab()
        self.tabs.addTab(self.about_tab, _get_icon('fa5s.info-circle', '#888'), "About")
    
    def _on_apps_config_changed(self):
        """Handle app config changes - refresh all tabs that use app configs."""
        self.log("App configurations updated - refreshing all tabs...")
        
        # Refresh Reset Data tab
        if hasattr(self, 'reset_tab') and hasattr(self.reset_tab, 'refresh_ui'):
            self.reset_tab.refresh_ui()
        
        # Refresh Sessions tab (Account tab)
        if hasattr(self, 'account_tab') and hasattr(self.account_tab, 'refresh_ui'):
            self.account_tab.refresh_ui()
    
    def log(self, msg: str):
        if hasattr(self, 'reset_tab') and hasattr(self.reset_tab, 'log_output'):
            self.reset_tab.log_output.append(msg)
        print(f"[SurfManager] {msg}")
    
    def closeEvent(self, event):
        event.accept()
