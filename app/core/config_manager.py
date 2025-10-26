"""Configuration manager for SurfManager application - Optimized version."""
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Union
from app.core.path_utils import get_resource_path


class ConfigManager:
    """Manages application configuration and settings."""
    
    # Singleton instance
    _instance = None
    _config = None
    
    def __new__(cls, *args, **kwargs):
        """Ensure singleton pattern."""
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the configuration manager (only once)."""
        # Only initialize once
        if ConfigManager._config is not None:
            return
            
        if config_path:
            self.config_path = Path(config_path)
        else:
            # Default config location
            self.config_path = self._get_config_path()
        
        ConfigManager._config = self._load_config()
    
    def _get_config_path(self) -> Path:
        """Get appropriate config path based on environment."""
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            # Use ProgramData for installed version
            return Path(os.environ.get('PROGRAMDATA', 'C:\\ProgramData')) / 'SurfManager' / 'config.json'
        else:
            # Development mode - use local config
            return Path.home() / ".surfmanager" / "config.json"
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return self._get_default_config()
        else:
            # Create default config
            config = self._get_default_config()
            self.save_config(config)
            return config
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "version": "2.0.0",
            "theme": "dark",
            "auto_backup": True,
            "compress_backups": True,
            "backup_location": str(Path.home() / "Documents" / "SurfManager" / "Backups"),
            "debug_mode": os.environ.get('SURFMANAGER_DEBUG', '0') == '1',
            "show_splash": True,
            "play_sounds": True,
            "check_updates": True,
            "auto_close_apps": True,
            "telemetry_enabled": True,
            "language": "en",
            "window_state": {
                "maximized": False,
                "width": 900,
                "height": 600
            }
        }
    
    @property
    def config(self) -> Dict[str, Any]:
        """Get current configuration."""
        return ConfigManager._config
    
    def save_config(self, config: Optional[Dict[str, Any]] = None):
        """Save configuration to file."""
        if config:
            ConfigManager._config = config
        
        # Ensure directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save config
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(ConfigManager._config, f, indent=2)
        except Exception as e:
            print(f"Failed to save config: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value (supports nested keys with dot notation)."""
        # Support nested keys like "window_state.width"
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """Set configuration value (supports nested keys with dot notation)."""
        keys = key.split('.')
        config = self.config
        
        # Navigate to nested location
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set the value
        config[keys[-1]] = value
        self.save_config()
    
    def update(self, updates: Dict[str, Any]):
        """Update multiple configuration values."""
        ConfigManager._config.update(updates)
        self.save_config()
    
    def reset_to_defaults(self):
        """Reset configuration to defaults."""
        ConfigManager._config = self._get_default_config()
        self.save_config()
    
    def export_config(self, export_path: str) -> bool:
        """Export configuration to file."""
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
            return True
        except Exception:
            return False
    
    def import_config(self, import_path: str) -> bool:
        """Import configuration from file."""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                ConfigManager._config = json.load(f)
            self.save_config()
            return True
        except Exception:
            return False
    
    def get_restore_files(self, app_name: str, file_type: str = 'backup_items') -> list:
        """Get list of files to restore for an application.
        
        Args:
            app_name: Name of the application (windsurf, cursor, claude)
            file_type: Type of files to get ('backup_items' or 'session_files')
            
        Returns:
            List of file/folder names to restore
        """
        try:
            config_path = get_resource_path('app/config/reset.json')
            
            with open(config_path, 'r', encoding='utf-8') as f:
                reset_config = json.load(f)
            
            app_config = reset_config.get(app_name.lower(), {})
            # Both file types use backup_items for now
            return app_config.get('backup_items', [])
        except Exception as e:
            print(f"Warning: Could not load restore files: {e}")
            return []
