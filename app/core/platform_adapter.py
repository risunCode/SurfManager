"""Cross-platform path resolution for SurfManager.

Supports: Windows, Linux, macOS
Handles: Path detection, user directories, app data locations
"""
import platform
import os
from pathlib import Path
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class PlatformPaths:
    """Cross-platform path configuration."""
    home_dir: Path
    app_data: Path
    app_config: Path
    documents: Path
    downloads: Path
    desktop: Optional[Path] = None
    
    def __post_init__(self):
        if self.desktop is None:
            self.desktop = self.home_dir / "Desktop"


class PlatformAdapter:
    """Cross-platform adapter for path resolution."""
    
    def __init__(self):
        self.system = platform.system()
        self.current_user = os.getenv('USER') or os.getenv('USERNAME') or 'user'
    
    def get_platform_paths(self, username: str = None) -> PlatformPaths:
        """Get platform-specific paths for a user."""
        if username:
            home = self._get_user_home(username)
        else:
            home = Path.home()
        
        if self.system == "Windows":
            return self._get_windows_paths(home)
        elif self.system == "Darwin":
            return self._get_macos_paths(home)
        else:  # Linux
            return self._get_linux_paths(home)
    
    def _get_user_home(self, username: str) -> Path:
        """Get home directory for a specific user."""
        if self.system == "Windows":
            return Path(f"C:/Users/{username}")
        elif self.system == "Darwin":
            return Path(f"/Users/{username}")
        else:  # Linux
            return Path(f"/home/{username}")
    
    def _get_windows_paths(self, home: Path) -> PlatformPaths:
        """Get Windows-specific paths."""
        return PlatformPaths(
            home_dir=home,
            app_data=home / "AppData" / "Local",
            app_config=home / "AppData" / "Roaming",
            documents=home / "Documents",
            downloads=home / "Downloads",
            desktop=home / "Desktop"
        )
    
    def _get_linux_paths(self, home: Path) -> PlatformPaths:
        """Get Linux-specific paths."""
        return PlatformPaths(
            home_dir=home,
            app_data=home / ".local" / "share",
            app_config=home / ".config",
            documents=home / "Documents",
            downloads=home / "Downloads",
            desktop=home / "Desktop"
        )
    
    def _get_macos_paths(self, home: Path) -> PlatformPaths:
        """Get macOS-specific paths."""
        return PlatformPaths(
            home_dir=home,
            app_data=home / "Library" / "Application Support",
            app_config=home / "Library" / "Application Support",
            documents=home / "Documents",
            downloads=home / "Downloads",
            desktop=home / "Desktop"
        )
    
    def get_app_data_dir(self, app_name: str, username: str = None) -> Path:
        """Get application data directory."""
        paths = self.get_platform_paths(username)
        return paths.app_data / app_name
    
    def get_app_config_dir(self, app_name: str, username: str = None) -> Path:
        """Get application config directory."""
        paths = self.get_platform_paths(username)
        return paths.app_config / app_name
    
    def get_documents_dir(self, username: str = None) -> Path:
        """Get documents directory."""
        paths = self.get_platform_paths(username)
        return paths.documents
    
    def expand_user_path(self, path: str, username: str = None) -> Path:
        """Expand user path (~ notation)."""
        path_obj = Path(path)
        
        if str(path).startswith('~'):
            if username:
                home = self._get_user_home(username)
            else:
                home = Path.home()
            
            # Remove ~ and join with home
            relative_path = str(path)[2:]  # Remove ~/
            if relative_path.startswith('/') or relative_path.startswith('\\'):
                relative_path = relative_path[1:]
            return home / relative_path
        
        return path_obj
    
    def normalize_path(self, path: str) -> Path:
        """Normalize path for current platform."""
        path_obj = Path(path)
        
        # Convert to absolute path if relative
        if not path_obj.is_absolute():
            path_obj = Path.cwd() / path_obj
        
        # Resolve path (handles .. and .)
        return path_obj.resolve()
    
    def get_app_dir(self, app_name: str = "SurfManager", username: str = None) -> Path:
        """Get application root directory in Documents."""
        docs = self.get_documents_dir(username)
        return docs / app_name
    
    def get_backup_dir(self, app_name: str = "SurfManager", username: str = None) -> Path:
        """Get backup directory for the application."""
        return self.get_app_dir(app_name, username) / "backup"
    
    def get_session_dir(self, app_name: str = "SurfManager", username: str = None) -> Path:
        """Get session directory for the application."""
        return self.get_backup_dir(app_name, username) / "sessions"
    
    def get_auto_backup_dir(self, app_name: str, username: str = None) -> Path:
        """Get auto-backup directory for an app."""
        return self.get_app_dir(app_name, username) / "auto-backup"
    
    # Platform detection helpers
    def is_windows(self) -> bool:
        return self.system == "Windows"
    
    def is_linux(self) -> bool:
        return self.system == "Linux"
    
    def is_macos(self) -> bool:
        return self.system == "Darwin"
    
    def get_platform_info(self) -> Dict[str, str]:
        """Get platform information."""
        return {
            'system': self.system,
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'python': platform.python_version()
        }
    
    def get_path_separator(self) -> str:
        """Get OS-specific path separator."""
        return os.sep
    
    def get_executable_extension(self) -> str:
        """Get executable file extension for the platform."""
        return ".exe" if self.is_windows() else ""
    
    def get_config_extension(self) -> str:
        """Get config file extension for the platform."""
        return ".ini" if self.is_windows() else ".conf"


# Singleton instance
_adapter_instance = None


def get_platform_adapter() -> PlatformAdapter:
    """Get singleton platform adapter instance."""
    global _adapter_instance
    if _adapter_instance is None:
        _adapter_instance = PlatformAdapter()
    return _adapter_instance


# Convenience functions
def get_current_platform() -> str:
    """Get current platform name."""
    return platform.system()


def is_supported_platform() -> bool:
    """Check if current platform is supported."""
    return get_current_platform() in ["Windows", "Linux", "Darwin"]


def get_app_data_dir(app_name: str, username: str = None) -> Path:
    """Convenience function to get app data directory."""
    return get_platform_adapter().get_app_data_dir(app_name, username)


def get_app_config_dir(app_name: str, username: str = None) -> Path:
    """Convenience function to get app config directory."""
    return get_platform_adapter().get_app_config_dir(app_name, username)


def get_documents_dir(username: str = None) -> Path:
    """Convenience function to get documents directory."""
    return get_platform_adapter().get_documents_dir(username)


def get_backup_dir(app_name: str = "SurfManager", username: str = None) -> Path:
    """Convenience function to get backup directory."""
    return get_platform_adapter().get_backup_dir(app_name, username)


def expand_user_path(path: str, username: str = None) -> Path:
    """Convenience function to expand user path."""
    return get_platform_adapter().expand_user_path(path, username)
