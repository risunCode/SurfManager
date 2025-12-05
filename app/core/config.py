"""Configuration and debug utilities for SurfManager."""
import os
import sys
from datetime import datetime
from pathlib import Path
from .platform_adapter import get_platform_adapter

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
        self.adapter = get_platform_adapter()
        self.documents_path = str(self.adapter.get_documents_dir())
        self.surfmanager_path = str(self.adapter.get_app_dir("SurfManager"))
    
    def get_path(self, key: str) -> str:
        """Get path by key."""
        paths = {
            'surfmanager_paths.session_backup': self.surfmanager_path,
            'session_config_file': os.path.join(self.surfmanager_path, "sessions.json"),
            'backup_path': str(self.adapter.get_backup_dir()),
            'session_dir': str(self.adapter.get_session_dir()),
            'auto_backup_dir': str(self.adapter.get_auto_backup_dir("SurfManager")),
        }
        return paths.get(key, "")
    
    def get_platform_path(self, path_type: str, app_name: str = "SurfManager", username: str = None) -> Path:
        """Get platform-specific path."""
        if path_type == "app_data":
            return self.adapter.get_app_data_dir(app_name, username)
        elif path_type == "app_config":
            return self.adapter.get_app_config_dir(app_name, username)
        elif path_type == "documents":
            return self.adapter.get_documents_dir(username)
        elif path_type == "backup":
            return self.adapter.get_backup_dir(app_name, username)
        elif path_type == "session":
            return self.adapter.get_session_dir(app_name, username)
        elif path_type == "auto_backup":
            return self.adapter.get_auto_backup_dir(app_name, username)
        else:
            return Path.cwd()
    
    def expand_user_path(self, path: str, username: str = None) -> Path:
        """Expand user path using platform adapter."""
        return self.adapter.expand_user_path(path, username)
    
    def is_windows(self) -> bool:
        """Check if running on Windows."""
        return self.adapter.is_windows()
    
    def is_linux(self) -> bool:
        """Check if running on Linux."""
        return self.adapter.is_linux()
    
    def is_macos(self) -> bool:
        """Check if running on macOS."""
        return self.adapter.is_macos()
    
    def get_platform_info(self) -> dict:
        """Get platform information."""
        return self.adapter.get_platform_info()
    
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
