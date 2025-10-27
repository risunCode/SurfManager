"""Main entry point for SurfManager application - Optimized version."""
import sys
import os
from pathlib import Path

# Fix Windows console encoding for emoji support
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except (AttributeError, ValueError):
        pass  # Not all environments support reconfigure

# Add the parent directory to Python path for imports
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QIcon
from app.gui.splash_screen import SplashScreen
from app.gui.main_window import MainWindow
from app import __version__
from app.core.core_utils import debug_print, is_debug_mode
from app.core.config_manager import ConfigManager
from app.core.logger import get_logger, log_info, log_error, log_critical
from datetime import datetime

# Build configuration
BUILD_TYPE = os.environ.get('SURFMANAGER_BUILD_TYPE', 'DEV')
SHOW_TERMINAL = os.environ.get('SURFMANAGER_SHOW_TERMINAL', 'NO').upper() == 'YES'
IS_FROZEN = getattr(sys, 'frozen', False)

# Hide console window on Windows for stable builds
if sys.platform == 'win32' and not SHOW_TERMINAL and BUILD_TYPE == 'STABLE':
    try:
        import ctypes
        ctypes.windll.kernel32.GetConsoleWindow.restype = ctypes.c_void_p
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 0)  # 0 = SW_HIDE
    except Exception:
        pass

# Initialize logger
logger = get_logger()
log_info(f"SurfManager v{__version__} starting...")
log_info(f"Build type: {BUILD_TYPE}")
log_info(f"Frozen: {IS_FROZEN}")
log_info(f"Debug mode: {is_debug_mode()}")
log_info(f"Show terminal: {SHOW_TERMINAL}")

debug_print(f"[DEBUG] SurfManager v{__version__} starting...")
debug_print(f"[DEBUG] Build type: {BUILD_TYPE}")
debug_print(f"[DEBUG] Frozen: {IS_FROZEN}")
debug_print(f"[DEBUG] Debug mode: {is_debug_mode()}")
debug_print(f"[DEBUG] Show terminal: {SHOW_TERMINAL}")



def main():
    """Initialize and run the application."""
    try:
        # Initialize configuration
        config = ConfigManager()
        
        debug_print("[DEBUG] Initializing QApplication...")
        
        # Enable High DPI scaling (PyQt6 handles this automatically)
        # Qt.AA_EnableHighDpiScaling is deprecated and automatic in Qt6
        os.environ['QT_ENABLE_HIGHDPI_SCALING'] = '1'
        
        app = QApplication(sys.argv)
        app.setApplicationName("SurfManager")
        app.setApplicationVersion(__version__)
        app.setOrganizationName("SurfManager")
        
        # Set application icon
        icon_path = current_dir / 'icons' / 'app_icon.ico'
        if icon_path.exists():
            app.setWindowIcon(QIcon(str(icon_path)))
        
        debug_print("[DEBUG] QApplication initialized")
        
        # Show splash screen
        splash = None
        if config.get('show_splash', True):
            debug_print("[DEBUG] Creating splash screen...")
            splash = SplashScreen()
            splash.show()
            app.processEvents()
            debug_print("[DEBUG] Splash screen shown")
        else:
            debug_print("[DEBUG] Splash screen disabled")
        
        # Loading steps
        if splash:
            splash.set_message("Loading configuration...")
            splash.progress = 20
            app.processEvents()
            
            splash.set_message("Initializing core modules...")
            splash.progress = 40
            app.processEvents()
        
        # Initialize core modules
        from app.core.app_manager import AppManager
        from app.core.backup_manager import BackupManager
        from app.core.id_manager import IdManager
        
        app_manager = AppManager()
        backup_manager = BackupManager()
        id_manager = IdManager()
        
        if splash:
            splash.set_message("Creating main window...")
            splash.progress = 60
            app.processEvents()
        
        debug_print("[DEBUG] Creating main window...")
        window = MainWindow(app_manager, backup_manager, id_manager, config)
        debug_print("[DEBUG] Main window created")
        
        if splash:
            splash.set_message("Scanning applications...")
            splash.progress = 80
            app.processEvents()
        
        # Scan for applications
        app_manager.scan_applications()
        
        if splash:
            splash.set_message("Ready!")
            splash.progress = 100
            app.processEvents()
        
        # Close splash and show main window
        def show_main_window():
            if splash:
                splash.finish_loading(window)
            window.show()
            
            # Restore window state
            if config.get('window_state.maximized', False):
                window.showMaximized()
            else:
                width = config.get('window_state.width', 900)
                height = config.get('window_state.height', 600)
                window.resize(width, height)
                window.move(app.primaryScreen().availableGeometry().center() - window.rect().center())
            
            debug_print("[DEBUG] Main window shown")
        
        # Show window after a short delay
        delay = 500 if splash else 0
        QTimer.singleShot(delay, show_main_window)
        
        debug_print("[DEBUG] Starting application event loop...")
        exit_code = app.exec()
        
        # Save window state before exit
        if window:
            config.set('window_state.maximized', window.isMaximized())
            if not window.isMaximized():
                config.set('window_state.width', window.width())
                config.set('window_state.height', window.height())
        
        debug_print(f"[DEBUG] Application event loop exited with code: {exit_code}")
        debug_print("[DEBUG] Application shutting down...")
        sys.exit(exit_code)
        
    except Exception as e:
        error_msg = f"FATAL ERROR: Application failed to start: {e}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        
        # Log critical error
        log_critical(error_msg, exc_info=True)
        
        # Try to show error dialog if QApplication exists
        try:
            from PyQt6.QtWidgets import QMessageBox
            if QApplication.instance():
                QMessageBox.critical(None, "Startup Error", 
                    f"SurfManager failed to start:\n\n{str(e)}\n\nCheck console for details.")
        except Exception:
            pass  # If dialog fails, rely on console/log output
        
        # Log to file
        try:
            log_dir = Path.home() / ".surfmanager" / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / f"crash_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(f"{error_msg}\n\n")
                traceback.print_exc(file=f)
        except (OSError, PermissionError):
            pass  # Cannot write log file
        
        sys.exit(1)


if __name__ == "__main__":
    main()
