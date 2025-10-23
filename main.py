"""Main entry point for SurfManager application."""
import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from gui.splash_screen import SplashScreen
from gui.main_window import MainWindow

# Read configuration from environment variables
DEBUG_MODE = os.environ.get('SURFMANAGER_DEBUG', 'NO').upper() == 'YES'
SHOW_TERMINAL = os.environ.get('SURFMANAGER_SHOW_TERMINAL', 'NO').upper() == 'YES'

def debug_print(message):
    """Print debug message only if DEBUG_MODE is enabled."""
    if DEBUG_MODE:
        print(message)

# Hide console window on Windows (unless SHOW_TERMINAL is YES)
if sys.platform == 'win32' and not SHOW_TERMINAL:
    try:
        import ctypes
        ctypes.windll.kernel32.GetConsoleWindow.restype = ctypes.c_void_p
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 0)  # 0 = SW_HIDE
    except Exception:
        pass  # Silently fail if console hiding doesn't work

debug_print("[DEBUG] Application starting...")
debug_print(f"[DEBUG] Debug mode: {DEBUG_MODE}")
debug_print(f"[DEBUG] Show terminal: {SHOW_TERMINAL}")


def main():
    """Initialize and run the application."""
    debug_print("[DEBUG] Initializing QApplication...")
    app = QApplication(sys.argv)
    app.setApplicationName("SurfManager")
    app.setOrganizationName("SurfManager")
    debug_print("[DEBUG] QApplication initialized")
    
    # Show splash screen
    debug_print("[DEBUG] Creating splash screen...")
    splash = SplashScreen()
    splash.show()
    app.processEvents()
    debug_print("[DEBUG] Splash screen shown")
    
    # Simulate loading steps
    splash.set_message("Loading configuration...")
    app.processEvents()
    QTimer.singleShot(500, lambda: None)
    app.processEvents()
    
    splash.set_message("Initializing components...")
    app.processEvents()
    QTimer.singleShot(300, lambda: None)
    app.processEvents()
    
    splash.set_message("Scanning applications...")
    app.processEvents()
    
    # Create main window
    debug_print("[DEBUG] Creating main window...")
    window = MainWindow()
    debug_print("[DEBUG] Main window created")
    
    splash.set_message("Ready!")
    app.processEvents()
    
    # Finish splash and show main window
    debug_print("[DEBUG] Setting up timers for splash finish and window show...")
    QTimer.singleShot(500, lambda: splash.finish_loading(window))
    QTimer.singleShot(500, window.show)
    
    debug_print("[DEBUG] Starting application event loop...")
    exit_code = app.exec()
    debug_print(f"[DEBUG] Application event loop exited with code: {exit_code}")
    debug_print("[DEBUG] Application shutting down...")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
