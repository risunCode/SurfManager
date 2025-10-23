"""Application detection and process management."""
import os
import sys
import subprocess
import psutil
import json
from typing import Dict, Optional, Tuple

# Debug mode configuration
DEBUG_MODE = os.environ.get('SURFMANAGER_DEBUG', 'NO').upper() == 'YES'

def debug_print(message):
    """Print debug message only if DEBUG_MODE is enabled."""
    if DEBUG_MODE:
        print(message)


class AppManager:
    """Manages application detection, process monitoring, and installation checks."""
    
    def __init__(self, config_path: str = "config/config.json"):
        """Initialize AppManager with configuration."""
        self.config = self._load_config(config_path)
        self.detected_apps: Dict[str, Dict] = {}
        
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from JSON file."""
        try:
            # Handle PyInstaller bundled path
            if getattr(sys, 'frozen', False):
                # Running as compiled executable
                base_path = sys._MEIPASS
                config_path = os.path.join(base_path, config_path)
                debug_print(f"[DEBUG] Running as executable, config path: {config_path}")
            else:
                # Running as script
                debug_print(f"[DEBUG] Running as script, config path: {config_path}")
            
            debug_print(f"[DEBUG] Loading config from: {config_path}")
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                debug_print(f"[DEBUG] Config loaded successfully")
                return config
        except Exception as e:
            print(f"Error loading config: {e}")
            debug_print(f"[DEBUG] Config load failed: {e}")
            import traceback
            traceback.print_exc()
            return {"applications": {}}
    
    def expand_path(self, path_template: str) -> str:
        """Expand environment variables in path template."""
        # Expand environment variables
        expanded = os.path.expandvars(path_template)
        # Normalize path separators for Windows
        expanded = expanded.replace('/', '\\')
        debug_print(f"[DEBUG] Path expansion: {path_template} -> {expanded}")
        return expanded
    
    def scan_applications(self) -> Dict[str, Dict]:
        """Scan for installed applications and their paths."""
        return self.detect_installations()
    
    def detect_installations(self) -> Dict[str, Dict]:
        """Detect installed applications and their paths."""
        self.detected_apps = {}
        
        for app_name, app_config in self.config.get("applications", {}).items():
            debug_print(f"[DEBUG] Detecting {app_name}...")
            app_info = {
                "name": app_name,
                "display_name": app_config.get("display_name", app_name),
                "installed": False,
                "path": None,
                "size": 0,
                "running": False
            }
            
            # Check each possible data path
            data_paths = app_config.get("data_paths", [])
            debug_print(f"[DEBUG] Checking {len(data_paths)} possible paths for {app_name}")
            for path_template in data_paths:
                expanded_path = self.expand_path(path_template)
                debug_print(f"[DEBUG] Checking if path exists: {expanded_path}")
                if os.path.exists(expanded_path):
                    debug_print(f"[DEBUG] [OK] Found {app_name} at: {expanded_path}")
                    app_info["installed"] = True
                    app_info["path"] = expanded_path
                    app_info["size"] = self._get_directory_size(expanded_path)
                    break
                else:
                    debug_print(f"[DEBUG] [X] Path not found: {expanded_path}")
            
            if not app_info["installed"]:
                debug_print(f"[DEBUG] {app_name} not detected in any configured path")
            
            # Check if process is running
            if app_info["installed"]:
                app_info["running"] = self.is_app_running(app_name)
                debug_print(f"[DEBUG] {app_name} running: {app_info['running']}")
            
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
        debug_print(f"[DEBUG] AppManager.launch_application called for: {app_name}")
        app_info = self.get_app_info(app_name)
        debug_print(f"[DEBUG] App info: {app_info}")
        if not app_info or not app_info.get("installed", False):
            debug_print(f"[DEBUG] App not found or not installed")
            return False, f"Application {app_name} not found or not installed"
        
        try:
            # Get exe paths from config
            app_config = self.config.get("applications", {}).get(app_name, {})
            exe_paths = app_config.get("exe_paths", [])
            debug_print(f"[DEBUG] Configured exe_paths: {exe_paths}")
            
            # Try each configured executable path
            for exe_path_template in exe_paths:
                exe_path = self.expand_path(exe_path_template)
                debug_print(f"[DEBUG] Checking exe path: {exe_path}")
                if os.path.exists(exe_path):
                    debug_print(f"[DEBUG] Found executable at: {exe_path}")
                    # Launch without admin privileges using subprocess
                    debug_print(f"[DEBUG] Launching process...")
                    subprocess.Popen([exe_path], creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
                    debug_print(f"[DEBUG] Process launched successfully")
                    return True, f"Launched {app_info.get('display_name', app_name)}"
                else:
                    debug_print(f"[DEBUG] Exe path does not exist: {exe_path}")
            
            # Fallback: try common executable names in data path
            app_path = app_info.get("path", "")
            debug_print(f"[DEBUG] Trying fallback with app_path: {app_path}")
            if app_path and os.path.exists(app_path):
                # Look for common executable patterns
                common_exes = [
                    f"{app_name}.exe",
                    f"{app_name.lower()}.exe",
                    f"{app_name.title()}.exe"
                ]
                debug_print(f"[DEBUG] Checking common exe names: {common_exes}")
                
                for exe_name in common_exes:
                    exe_full_path = os.path.join(app_path, exe_name)
                    debug_print(f"[DEBUG] Checking fallback exe: {exe_full_path}")
                    if os.path.exists(exe_full_path):
                        debug_print(f"[DEBUG] Found fallback executable at: {exe_full_path}")
                        subprocess.Popen([exe_full_path], creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
                        debug_print(f"[DEBUG] Fallback process launched successfully")
                        return True, f"Launched {app_info.get('display_name', app_name)}"
            
            debug_print(f"[DEBUG] No executable found for {app_name}")
            return False, f"Could not find executable for {app_name}"
            
        except Exception as e:
            debug_print(f"[DEBUG] Exception in launch_application: {str(e)}")
            if DEBUG_MODE:
                import traceback
                traceback.print_exc()
            return False, f"Failed to launch {app_name}: {str(e)}"
