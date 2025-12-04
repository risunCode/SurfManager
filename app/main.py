"""Main entry point for SurfManager."""
import sys
import os

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QIcon
from app.gui.splash import SplashScreen
from app.gui.main_window import MainWindow
from app import __version__
from app.core.config import debug_print, is_debug_mode

SHOW_TERMINAL = os.environ.get('SURFMANAGER_SHOW_TERMINAL', 'NO').upper() == 'YES'

# Hide console on Windows
if sys.platform == 'win32' and not SHOW_TERMINAL:
    try:
        import ctypes
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 0)
    except:
        pass

debug_print(f"SurfManager v{__version__} starting...")


def main():
    try:
        app = QApplication(sys.argv)
        app.setApplicationName("SurfManager")
        app.setApplicationVersion(__version__)
        
        # Set application icon (cross-platform)
        app_dir = os.path.dirname(__file__)
        if sys.platform == 'darwin':
            icon_file = "app.icns"
        elif sys.platform == 'win32':
            icon_file = "app.ico"
        else:
            icon_file = "app.png"
        
        icon_path = os.path.join(app_dir, "icons", icon_file)
        # Fallback to .ico if platform-specific icon not found
        if not os.path.exists(icon_path):
            icon_path = os.path.join(app_dir, "icons", "app.ico")
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))
        
        splash = SplashScreen()
        splash.show()
        app.processEvents()
        
        splash.set_message("Loading...")
        splash.progress = 50
        app.processEvents()
        
        window = MainWindow()
        
        splash.set_message("Ready!")
        splash.progress = 100
        app.processEvents()
        
        def show():
            splash.finish_loading(window)
            window.show()
        
        QTimer.singleShot(300, show)  # Faster transition
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"FATAL: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
