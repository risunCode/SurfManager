"""Application configurations - Dynamic loading from JSON files.

This module loads app configurations dynamically from JSON files
in the AppConfigs folder. Apps can be enabled/disabled via 'active' flag.
"""
import json
from pathlib import Path
from typing import Dict, Any, List


class DynamicConfigLoader:
    """Loads application configurations dynamically from JSON files."""
    
    def __init__(self):
        self.config_dir = Path.home() / ".surfmanager" / "AppConfigs"
        self.loaded_apps = {}
        self._active_cache = None  # Cache for active apps
        self._ensure_config_dir()
    
    def _ensure_config_dir(self):
        """Ensure AppConfigs directory exists."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
    
    def load_all_configs(self) -> Dict[str, Any]:
        """Load all JSON configs from AppConfigs folder.
        
        Returns:
            Dictionary of app configurations
        """
        self.loaded_apps = {}
        self._active_cache = None  # Clear cache on reload
        
        if not self.config_dir.exists():
            return {}
        
        # Load all JSON files
        for json_file in self.config_dir.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                app_name = config.get('app_name')
                if not app_name:
                    print(f"WARNING: Config file {json_file.name} missing 'app_name', skipping")
                    continue
                
                # Add to loaded apps (use lowercase key for consistency)
                self.loaded_apps[app_name.lower()] = config
                
            except json.JSONDecodeError as e:
                print(f"ERROR: Failed to parse {json_file.name}: {e}")
            except Exception as e:
                print(f"ERROR: Failed to load {json_file.name}: {e}")
        
        return self.loaded_apps
    
    def get_app_config(self, app_name: str) -> Dict[str, Any]:
        """Get configuration for specific app.
        
        Args:
            app_name: Application name
            
        Returns:
            App configuration dictionary or empty dict if not found
        """
        return self.loaded_apps.get(app_name.lower(), {})
    
    def get_app_list(self) -> List[str]:
        """Get list of all loaded application names.
        
        Returns:
            List of app names
        """
        return list(self.loaded_apps.keys())
    
    def get_active_apps(self) -> List[str]:
        """Get list of active (enabled) application names (cached).
        
        Returns:
            List of active app names
        """
        if self._active_cache is None:
            self._active_cache = [
                name for name, config in self.loaded_apps.items()
                if config.get('active', True)
            ]
        return self._active_cache
    
    def is_app_active(self, app_name: str) -> bool:
        """Check if app is active (enabled).
        
        Args:
            app_name: Application name
            
        Returns:
            True if active, False if inactive
        """
        config = self.get_app_config(app_name)
        return config.get('active', True)
    
    def reload(self):
        """Reload all configurations from disk."""
        return self.load_all_configs()


# Global instance
_config_loader = None


def get_config_loader() -> DynamicConfigLoader:
    """Get the global config loader instance.
    
    Returns:
        DynamicConfigLoader instance
    """
    global _config_loader
    if _config_loader is None:
        _config_loader = DynamicConfigLoader()
        _config_loader.load_all_configs()
    return _config_loader


def reload_configs():
    """Reload all configurations from disk."""
    loader = get_config_loader()
    loader.reload()


def get_app_list() -> List[str]:
    """Get list of all app names.
    
    Returns:
        List of app names
    """
    loader = get_config_loader()
    return loader.get_app_list()


def get_active_apps() -> List[str]:
    """Get list of active app names only.
    
    Returns:
        List of active app names
    """
    loader = get_config_loader()
    return loader.get_active_apps()


def get_app(app_name: str) -> Dict[str, Any]:
    """Get specific app configuration.
    
    Args:
        app_name: Application name
        
    Returns:
        App configuration or empty dict
    """
    loader = get_config_loader()
    return loader.get_app_config(app_name)


def is_active(app_name: str) -> bool:
    """Check if app is active.
    
    Args:
        app_name: Application name
        
    Returns:
        True if active
    """
    loader = get_config_loader()
    return loader.is_app_active(app_name)
