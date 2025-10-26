"""Debug utilities for MinimalSurfGUI."""
import os
import sys
from datetime import datetime

def is_debug_mode() -> bool:
    """Return True if application is running in debug mode."""
    # Check environment variables first
    if os.environ.get('SURFMANAGER_DEBUG', '').upper() == 'TRUE':
        return True
    
    # If not explicitly set, check if running with python or pythonw
    return sys.executable.endswith('python.exe')

def debug_print(message: str):
    """Print debug message if in debug mode."""
    if is_debug_mode():
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        try:
            print(f"[{timestamp}] {message}")
        except UnicodeEncodeError:
            # Fallback for Windows console - remove emojis
            safe_message = message.encode('ascii', 'ignore').decode('ascii')
            print(f"[{timestamp}] {safe_message}")
