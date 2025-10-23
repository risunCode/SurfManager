"""Main entry point for SurfManager application."""
import sys
import time
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from gui.splash_screen import SplashScreen
from gui.main_window import MainWindow

# Hide console window on Windows
if sys.platform == 'win32':
    import ctypes
    ctypes.windll.kernel32.GetConsoleWindow.restype = ctypes.c_void_p
    hwnd = ctypes.windll.kernel32.GetConsoleWindow()
    if hwnd:
        ctypes.windll.user32.ShowWindow(hwnd, 0)  # 0 = SW_HIDE


def main():
    """Initialize and run the application."""
    app = QApplication(sys.argv)
    app.setApplicationName("SurfManager")
    app.setOrganizationName("SurfManager")
    
    # Show splash screen
    splash = SplashScreen()
    splash.show()
    app.processEvents()
    
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
    window = MainWindow()
    
    splash.set_message("Ready!")
    app.processEvents()
    
    # Finish splash and show main window
    QTimer.singleShot(500, lambda: splash.finish_loading(window))
    QTimer.singleShot(500, window.show)
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
