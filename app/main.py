"""Main entry point for SurfManager application - Optimized version."""
import sys
import os
import argparse
from pathlib import Path

# Fix Windows console encoding for emoji support
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

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
from app.core.debug_utils import debug_print, is_debug_mode
from app.core.config_manager import ConfigManager

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

debug_print(f"[DEBUG] SurfManager v{__version__} starting...")
debug_print(f"[DEBUG] Build type: {BUILD_TYPE}")
debug_print(f"[DEBUG] Frozen: {IS_FROZEN}")
debug_print(f"[DEBUG] Debug mode: {is_debug_mode()}")
debug_print(f"[DEBUG] Show terminal: {SHOW_TERMINAL}")

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='SurfManager - Advanced Reset Tool')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--no-splash', action='store_true', help='Skip splash screen')
    parser.add_argument('--test', action='store_true', help='Run in test mode')
    parser.add_argument('--config', type=str, help='Path to config file')
    return parser.parse_args()


def main():
    """Initialize and run the application."""
    try:
        # Parse command line arguments
        args = parse_arguments()
        
        # Initialize configuration
        config = ConfigManager(args.config if args.config else None)
        
        # Override debug mode if specified
        if args.debug:
            os.environ['SURFMANAGER_DEBUG'] = '1'
            config.set('debug_mode', True)
        
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
        
        # Show splash screen (unless disabled)
        splash = None
        if not args.no_splash and config.get('show_splash', True):
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
        window.test_mode = args.test
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
        print(f"FATAL ERROR: Application failed to start: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
