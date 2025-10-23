"""Application detection and process management."""
import os
import psutil
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class AppManager:
    """Manages application detection, process monitoring, and installation checks."""
    
    def __init__(self, config_path: str = "config/config.json"):
        """Initialize AppManager with configuration."""
        self.config = self._load_config(config_path)
        self.detected_apps: Dict[str, Dict] = {}
        
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from JSON file."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            return {"applications": {}}
    
    def expand_path(self, path_template: str) -> str:
        """Expand environment variables in path template."""
        return os.path.expandvars(path_template)
    
    def scan_applications(self) -> Dict[str, Dict]:
        """Scan for installed applications and their paths."""
        return self.detect_installations()
    
    def detect_installations(self) -> Dict[str, Dict]:
        """Detect installed applications and their paths."""
        self.detected_apps = {}
        
        for app_name, app_config in self.config.get("applications", {}).items():
            app_info = {
                "name": app_name,
                "display_name": app_config.get("display_name", app_name),
                "installed": False,
                "path": None,
                "size": 0,
                "running": False
            }
            
            # Check each possible data path
            for path_template in app_config.get("data_paths", []):
                expanded_path = self.expand_path(path_template)
                if os.path.exists(expanded_path):
                    app_info["installed"] = True
                    app_info["path"] = expanded_path
                    app_info["size"] = self._get_directory_size(expanded_path)
                    break
            
            # Check if process is running
            if app_info["installed"]:
                app_info["running"] = self.is_app_running(app_name)
            
            self.detected_apps[app_name] = app_info
        
        return self.detected_apps
    
    def is_app_running(self, app_name: str) -> bool:
        """Check if application process is running."""
        app_config = self.config.get("applications", {}).get(app_name, {})
        process_names = app_config.get("process_names", [])
        
        for proc in psutil.process_iter(['name']):
            try:
                proc_name = proc.info['name']
                if proc_name in process_names:
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return False
    
    def kill_app_process(self, app_name: str) -> Tuple[bool, str]:
        """Kill application process if running."""
        app_config = self.config.get("applications", {}).get(app_name, {})
        process_names = app_config.get("process_names", [])
        killed_count = 0
        
        for proc in psutil.process_iter(['name', 'pid']):
            try:
                proc_name = proc.info['name']
                if proc_name in process_names:
                    proc.kill()
                    killed_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                return False, f"Failed to kill process: {e}"
        
        if killed_count > 0:
            return True, f"Successfully killed {killed_count} process(es)"
        else:
            return True, "No running processes found"
    
    def _get_directory_size(self, path: str) -> int:
        """Calculate total size of directory in bytes."""
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    try:
                        total_size += os.path.getsize(filepath)
                    except (OSError, FileNotFoundError):
                        continue
        except Exception:
            pass
        return total_size
    
    def format_size(self, size_bytes: int) -> str:
        """Format bytes to human-readable size."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"
    
    def get_app_info(self, app_name: str) -> Optional[Dict]:
        """Get information about specific application."""
        return self.detected_apps.get(app_name)
    
    def get_all_apps(self) -> Dict[str, Dict]:
        """Get all detected applications."""
        return self.detected_apps
    
    def launch_application(self, app_name: str) -> Tuple[bool, str]:
        """Launch an application by name."""
        app_info = self.get_app_info(app_name)
        if not app_info or not app_info.get("installed", False):
            return False, f"Application {app_name} not found or not installed"
        
        try:
            # Try to find executable path
            exe_path = app_info.get("exe_path")
            if exe_path and os.path.exists(exe_path):
                os.startfile(exe_path)
                return True, f"Launched {app_info.get('display_name', app_name)}"
            
            # Fallback: try common executable names
            app_path = app_info.get("path", "")
            if app_path and os.path.exists(app_path):
                # Look for common executable patterns
                common_exes = [
                    f"{app_name}.exe",
                    f"{app_name.lower()}.exe",
                    f"{app_name.title()}.exe"
                ]
                
                for exe_name in common_exes:
                    exe_full_path = os.path.join(app_path, exe_name)
                    if os.path.exists(exe_full_path):
                        os.startfile(exe_full_path)
                        return True, f"Launched {app_info.get('display_name', app_name)}"
            
            return False, f"Could not find executable for {app_name}"
            
        except Exception as e:
            return False, f"Failed to launch {app_name}: {str(e)}"
