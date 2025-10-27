"""Configuration manager for SurfManager application - Optimized version."""
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional
from app.core.core_utils import get_resource_path


class ConfigManager:
    """Manages application configuration and settings."""
    
    # Singleton instance
    _instance = None
    _config = None
    _initialized = False
    
    def __new__(cls, *args, **kwargs):
        """Ensure singleton pattern."""
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the configuration manager (only once)."""
        # Only initialize once
        if ConfigManager._initialized:
            return
        
        ConfigManager._initialized = True
            
        if config_path:
            self.config_path = Path(config_path)
        else:
            # Default config location
            self.config_path = self._get_config_path()
        
        ConfigManager._config = self._load_config()
    
    def _get_config_path(self) -> Path:
        """Get appropriate config path based on environment.
        
        Always uses user home directory for per-user configuration.
        This ensures each Windows user has their own config.
        """
        # Always use user home directory (both dev and frozen mode)
        return Path.home() / ".surfmanager" / "config.json"
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default.
        
        User config at ~/.surfmanager/config.json takes priority.
        Falls back to defaults if config doesn't exist or is corrupted.
        """
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # Validate config structure
                    if not isinstance(config, dict):
                        raise ValueError("Config must be a dictionary")
                    print(f"✓ Loaded user config from: {self.config_path}")
                    return config
            except json.JSONDecodeError as e:
                print(f"WARNING: Config file corrupted ({e}). Creating backup and using defaults.")
                # Backup corrupted config
                try:
                    backup_path = self.config_path.with_suffix('.json.backup')
                    self.config_path.rename(backup_path)
                    print(f"Corrupted config backed up to: {backup_path}")
                except Exception as backup_error:
                    print(f"Failed to backup corrupted config: {backup_error}")
                return self._get_default_config()
            except Exception as e:
                print(f"WARNING: Failed to load config ({e}). Using defaults.")
                return self._get_default_config()
        else:
            # Create default config
            print(f"✓ Creating new user config at: {self.config_path}")
            config = self._get_default_config()
            try:
                self.save_config(config)
            except Exception as e:
                print(f"WARNING: Failed to save default config: {e}")
            return config
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "app_name": "SurfManager",
            "version": "2.0.0",
            "theme": "dark",
            "compress_backups": True,
            "backup_location": str(Path.home() / "Documents" / "SurfManager" / "Backups"),
            "current_user": None,
            "auto_close_apps": True,
            "play_sounds": True,
            "show_splash": True,
            "language": "en",
            "debug_mode": os.environ.get('SURFMANAGER_DEBUG', '0') == '1',
            "detected_apps": {},
            "multi_user": {
                "current_selected_user": None,
                "available_users": {},
                "user_paths": {}
            },
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
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"ERROR: Failed to create config directory: {e}")
            raise
        
        # Save config with atomic write (write to temp, then rename)
        temp_path = self.config_path.with_suffix('.json.tmp')
        try:
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(ConfigManager._config, f, indent=2)
            
            # Atomic rename
            temp_path.replace(self.config_path)
        except Exception as e:
            print(f"ERROR: Failed to save config: {e}")
            # Clean up temp file
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except (OSError, PermissionError):
                    pass  # Temp file cleanup failed
            raise
    
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
        """Reset configuration to defaults and clear AppData config."""
        import shutil
        
        # Delete entire .surfmanager folder to clear all user data
        appdata_dir = self.config_path.parent
        if appdata_dir.exists():
            try:
                shutil.rmtree(appdata_dir)
                print(f"Deleted AppData config: {appdata_dir}")
            except Exception as e:
                print(f"Warning: Could not delete AppData config: {e}")
        
        # Reset in-memory config to defaults
        ConfigManager._config = self._get_default_config()
        
        # Save fresh config (will recreate .surfmanager folder)
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
    
