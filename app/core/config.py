"""Configuration and debug utilities for SurfManager."""
import os
import sys
from datetime import datetime

# Debug utilities
def is_debug_mode() -> bool:
    """Check if running in debug mode."""
    if os.environ.get('SURFMANAGER_DEBUG', '').upper() == 'TRUE':
        return True
    return sys.executable.endswith('python.exe')

def debug_print(message: str):
    """Print debug message if in debug mode."""
    if is_debug_mode():
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] {message}")


class ConfigManager:
    """Configuration manager for paths and settings."""
    
    def __init__(self):
        self.documents_path = os.path.join(os.path.expanduser("~"), "Documents")
        self.surfmanager_path = os.path.join(self.documents_path, "SurfManager")
    
    def get_path(self, key: str) -> str:
        """Get path by key."""
        paths = {
            'surfmanager_paths.session_backup': self.surfmanager_path,
            'session_config_file': os.path.join(self.surfmanager_path, "sessions.json"),
        }
        return paths.get(key, "")
    
    def get_backup_files(self, app_name: str) -> list:
        """Get list of files to backup for an app."""
        return [
            "User/settings.json", "User/keybindings.json", "User/snippets",
            "User/globalStorage/state.vscdb", "User/globalStorage/storage.json",
            "User/workspaceStorage", "Network", "Local State", "Preferences"
        ]
    
    def get_restore_files(self, app_name: str, file_type: str) -> list:
        """Get list of files to restore."""
        return self.get_backup_files(app_name)
