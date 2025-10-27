"""Unified core utilities for SurfManager - Combines constants, utils, messages, and operations."""
import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Callable, Optional, Tuple


# ============================================================================
# DEBUG UTILITIES (must be defined first to avoid circular dependencies)
# ============================================================================

def is_debug_mode() -> bool:
    """Check if running in debug mode."""
    if os.environ.get('SURFMANAGER_DEBUG', '').upper() == 'TRUE':
        return True
    return sys.executable.endswith('python.exe')


def debug_print(message: str):
    """Print debug message with timestamp."""
    if is_debug_mode():
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        try:
            print(f"[{timestamp}] {message}")
        except UnicodeEncodeError:
            safe_message = message.encode('ascii', 'ignore').decode('ascii')
            print(f"[{timestamp}] {safe_message}")


# ============================================================================
# PATH UTILITIES (must be defined before ConfigLoader)
# ============================================================================

def get_resource_path(relative_path: str) -> Path:
    """Get absolute path to resource, works for dev and PyInstaller."""
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
        return Path(base_path) / relative_path
    else:
        current_file = Path(__file__)
        project_root = current_file.parents[2]
        return project_root / relative_path


def open_folder_in_explorer(folder_path: str) -> bool:
    """Open folder in Windows Explorer."""
    try:
        subprocess.Popen(['explorer', folder_path])
        return True
    except Exception:
        return False


def ensure_directory(directory_path: str) -> bool:
    """Ensure directory exists, create if not."""
    try:
        os.makedirs(directory_path, exist_ok=True)
        return True
    except Exception:
        return False


# ============================================================================
# JSON CONFIG LOADER
# ============================================================================

class ConfigLoader:
    """Load configuration from JSON files."""
    _config_cache = {}
    _message_cache = {}
    
    @classmethod
    def load_app_config(cls) -> Dict[str, Any]:
        """Load app metadata from JSON."""
        if 'app_config' not in cls._config_cache:
            try:
                config_path = get_resource_path('app/config/app_metadata.json')
                with open(config_path, 'r', encoding='utf-8') as f:
                    cls._config_cache['app_config'] = json.load(f)
            except Exception as e:
                debug_print(f"Error loading app config: {e}")
                # Fallback to minimal defaults
                cls._config_cache['app_config'] = {
                    "apps": {
                        "windsurf": {"display_name": "Windsurf", "color": "#14ffec"},
                        "cursor": {"display_name": "Cursor", "color": "#2196F3"},
                        "claude": {"display_name": "Claude", "color": "#9C27B0"}
                    },
                    "window": {"min_width": 700, "min_height": 500}
                }
        return cls._config_cache['app_config']
    
    @classmethod
    def load_messages(cls) -> Dict[str, Dict[str, str]]:
        """Load messages from JSON."""
        if 'messages' not in cls._message_cache:
            try:
                msg_path = get_resource_path('app/config/messages.json')
                with open(msg_path, 'r', encoding='utf-8') as f:
                    cls._message_cache['messages'] = json.load(f)
            except Exception as e:
                debug_print(f"Error loading messages: {e}")
                # Fallback to minimal messages
                cls._message_cache['messages'] = {
                    "errors": {"unknown_error": "❌ Error: {error}"},
                    "success": {"completed": "✅ Operation completed"},
                    "info": {"loading": "⏳ Loading..."}
                }
        return cls._message_cache['messages']


# ============================================================================
# CONSTANTS (from JSON config)
# ============================================================================

def get_constants():
    """Get constants from JSON config."""
    config = ConfigLoader.load_app_config()
    return {
        # Window dimensions
        'WINDOW_MIN_WIDTH': config.get('window', {}).get('min_width', 700),
        'WINDOW_MIN_HEIGHT': config.get('window', {}).get('min_height', 500),
        'WINDOW_DEFAULT_WIDTH': config.get('window', {}).get('default_width', 1200),
        'WINDOW_DEFAULT_HEIGHT': config.get('window', {}).get('default_height', 570),
        
        # Timing constants
        'SPLASH_DELAY_MS': config.get('timing', {}).get('splash_delay_ms', 500),
        'SCAN_DELAY_MS': config.get('timing', {}).get('scan_delay_ms', 500),
        'PROCESS_TIMEOUT_SECONDS': config.get('timing', {}).get('process_timeout_seconds', 10),
        
        # File patterns
        'SKIP_PATTERNS': config.get('skip_patterns', []),
        'RESERVED_NAMES': config.get('reserved_names', []),
        'SIZE_UNITS': config.get('size_units', ['B', 'KB', 'MB', 'GB', 'TB'])
    }

# Legacy constants for backward compatibility
CONSTANTS = get_constants()
WINDOW_MIN_WIDTH = CONSTANTS['WINDOW_MIN_WIDTH']
WINDOW_MIN_HEIGHT = CONSTANTS['WINDOW_MIN_HEIGHT']
WINDOW_DEFAULT_WIDTH = CONSTANTS['WINDOW_DEFAULT_WIDTH']
WINDOW_DEFAULT_HEIGHT = CONSTANTS['WINDOW_DEFAULT_HEIGHT']
ACCOUNT_MANAGER_WIDTH = CONSTANTS['WINDOW_DEFAULT_WIDTH']
ACCOUNT_MANAGER_HEIGHT = CONSTANTS['WINDOW_DEFAULT_HEIGHT']

# Other constants not in JSON
MAX_PATH_LENGTH = 260
MAX_LOG_FILE_SIZE_MB = 5
MAX_LOG_BACKUP_COUNT = 5
SIZE_UNIT_DIVISOR = 1024.0
PROCESS_KILL_TIMEOUT_SECONDS = 10
PROCESS_WAIT_INTERVAL_SECONDS = 0.1
LOG_RETENTION_DAYS = 30

# UI constants (from old constants.py)
USER_BUTTON_MIN_WIDTH = 140
USER_BUTTON_MAX_HEIGHT = 32
GITHUB_BUTTON_WIDTH = 130
GITHUB_BUTTON_HEIGHT = 32
USER_LIST_REFRESH_DELAY_MS = 200
REFRESH_SCAN_DELAY_MS = 100
SPLASH_DELAY_MS = 500
SCAN_DELAY_MS = 500

# Build info
APP_NAME = 'SurfManager'
BUILD_TYPE_DEV = 'DEV'
BUILD_TYPE_STABLE = 'STABLE'


# ============================================================================
# ERROR MESSAGES (from JSON messages)
# ============================================================================

class ErrorMessages:
    """Centralized error messages loaded from JSON."""
    
    @staticmethod
    def format_error(template_key: str, **kwargs) -> str:
        """Format error message from template key."""
        messages = ConfigLoader.load_messages()
        template = messages.get('errors', {}).get(template_key, "❌ Error occurred")
        try:
            return template.format(**kwargs)
        except KeyError:
            return template
    
    @staticmethod
    def get_user_friendly_error(exception: Exception) -> str:
        """Convert exception to user-friendly message."""
        error_str = str(exception).lower()
        
        if 'permission' in error_str or 'access denied' in error_str:
            return ErrorMessages.format_error('permission_denied')
        elif 'no such file' in error_str or 'not found' in error_str:
            return f"❌ File or folder not found: {exception}"
        elif 'no space' in error_str or 'disk full' in error_str:
            return "❌ Insufficient disk space."
        elif 'network' in error_str or 'connection' in error_str:
            return ErrorMessages.format_error('network_error', error=exception)
        else:
            return ErrorMessages.format_error('unknown_error', error=exception)


class SuccessMessages:
    """Success messages loaded from JSON."""
    
    @staticmethod
    def format_success(template_key: str, **kwargs) -> str:
        """Format success message from template key."""
        messages = ConfigLoader.load_messages()
        template = messages.get('success', {}).get(template_key, "✅ Success")
        try:
            return template.format(**kwargs)
        except KeyError:
            return template


# ============================================================================
# APP OPERATIONS (from app_operations.py)
# ============================================================================

class AppOperations:
    """Centralized operations for applications."""
    
    @staticmethod
    def launch_app(app_name: str, detected_apps: dict, log_callback: Callable, 
                   audio_manager: Optional[Any] = None) -> bool:
        """Launch application executable."""
        app_info = detected_apps.get(app_name)
        if not app_info or not app_info.get('installed'):
            log_callback(ErrorMessages.format_error('app_not_found'))
            return False
        
        exe_path = app_info.get('exe_path')
        if not exe_path or not os.path.exists(exe_path):
            log_callback(ErrorMessages.format_error('app_launch_failed', app_name=app_name.title()))
            return False
        
        try:
            subprocess.Popen([exe_path], shell=False)
            log_callback(SuccessMessages.format_success('app_launched', app_name=app_name.title()))
            if audio_manager:
                audio_manager.play_sound('startup')
            return True
        except Exception as e:
            log_callback(f"❌ Failed to launch {app_name.title()}: {e}")
            return False
    
    @staticmethod
    def open_app_folder(app_name: str, detected_apps: dict, log_callback: Callable,
                       audio_manager: Optional[Any] = None) -> bool:
        """Open application data folder."""
        app_info = detected_apps.get(app_name)
        if not app_info or not app_info.get('installed'):
            log_callback(ErrorMessages.format_error('app_not_found'))
            return False
        
        path = app_info['path']
        
        if open_folder_in_explorer(path):
            log_callback(SuccessMessages.format_success('folder_opened', path=path))
            if audio_manager:
                audio_manager.play_action_sound('open_folder')
            return True
        else:
            log_callback(f"❌ Failed to open folder: {path}")
            return False
    
    @staticmethod
    def get_app_display_name(app_name: str) -> str:
        """Get display name for application."""
        config = ConfigLoader.load_app_config()
        app_data = config.get('apps', {}).get(app_name.lower(), {})
        return app_data.get('display_name', app_name.title())
    
    @staticmethod
    def get_app_color(app_name: str) -> str:
        """Get color code for application."""
        config = ConfigLoader.load_app_config()
        app_data = config.get('apps', {}).get(app_name.lower(), {})
        return app_data.get('color', '#888888')


# ============================================================================
# BACKWARD COMPATIBILITY EXPORTS
# ============================================================================

# Export commonly used functions/classes at module level
from_constants = [
    'WINDOW_MIN_WIDTH', 'WINDOW_MIN_HEIGHT', 'WINDOW_DEFAULT_WIDTH', 
    'WINDOW_DEFAULT_HEIGHT', 'ACCOUNT_MANAGER_WIDTH', 'ACCOUNT_MANAGER_HEIGHT',
    'MAX_PATH_LENGTH', 'MAX_LOG_FILE_SIZE_MB', 'LOG_RETENTION_DAYS',
    'SIZE_UNIT_DIVISOR', 'PROCESS_KILL_TIMEOUT_SECONDS',
    'USER_BUTTON_MIN_WIDTH', 'USER_BUTTON_MAX_HEIGHT',
    'GITHUB_BUTTON_WIDTH', 'GITHUB_BUTTON_HEIGHT',
    'USER_LIST_REFRESH_DELAY_MS', 'REFRESH_SCAN_DELAY_MS',
    'SPLASH_DELAY_MS', 'SCAN_DELAY_MS'
]

from_utils = [
    'is_debug_mode', 'debug_print', 'get_resource_path',
    'open_folder_in_explorer', 'ensure_directory'
]

from_messages = [
    'ErrorMessages', 'SuccessMessages'
]

from_operations = [
    'AppOperations'
]

__all__ = from_constants + from_utils + from_messages + from_operations
