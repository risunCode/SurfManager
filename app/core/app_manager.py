"""Application detection and process management - Optimized version."""
import os
import sys
import subprocess
import psutil
import json
from pathlib import Path
from typing import Dict, Optional, List, Tuple
from app.core.config_manager import ConfigManager
from app.core.debug_utils import debug_print
from app.core.path_utils import get_resource_path


class AppManager:
    """Manages application detection, process monitoring, and installation checks."""
    
    def __init__(self, config_path: str = "app/config/config.json"):
        """Initialize AppManager with configuration."""
        self.config_manager = ConfigManager()
        self.config_path = config_path
        self.config = self._load_config(config_path)
        self.detected_apps: Dict[str, Dict] = {}
        self._load_detected_apps()
        
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from JSON file."""
        try:
            # Use path_utils for consistent path resolution
            resolved_path = get_resource_path(config_path)
            debug_print(f"[DEBUG] Loading config from: {resolved_path}")
            
            with open(resolved_path, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            debug_print(f"[DEBUG] Config load failed: {e}")
            return {"applications": {}}
    
    def expand_path(self, path_template: str) -> str:
        """Expand environment variables in path template."""
        expanded = os.path.expandvars(path_template)
        return expanded.replace('/', os.sep)
    
    def scan_applications(self, force_rescan: bool = False) -> Dict[str, Dict]:
        """Scan for installed applications.
        
        Args:
            force_rescan: If True, force a full rescan. Otherwise use cached results.
        """
        if not force_rescan and self.detected_apps:
            # Update running status only
            for app_name in self.detected_apps:
                if self.detected_apps[app_name].get("installed"):
                    self.detected_apps[app_name]["running"] = self.is_app_running(app_name)
            return self.detected_apps
        
        return self.detect_installations()
    
    def detect_installations(self) -> Dict[str, Dict]:
        """Detect installed applications and their paths."""
        self.detected_apps = {}
        
        for app_name, app_config in self.config.get("applications", {}).items():
            app_info = self._create_app_info(app_name, app_config)
            
            # Check each possible data path
            for path_template in app_config.get("data_paths", []):
                expanded_path = self.expand_path(path_template)
                if os.path.exists(expanded_path):
                    app_info.update({
                        "installed": True,
                        "path": expanded_path,
                        "size": self._get_directory_size(expanded_path)
                    })
                    break
            
            # Find executable path
            if app_info["installed"]:
                for exe_template in app_config.get("exe_paths", []):
                    exe_path = self.expand_path(exe_template)
                    if os.path.exists(exe_path):
                        app_info["exe_path"] = exe_path
                        break
                
                # Check if process is running
                app_info["running"] = self.is_app_running(app_name)
                
            self.detected_apps[app_name] = app_info
        
        # Save detected apps to config
        self._save_detected_apps()
        return self.detected_apps
    
    def _create_app_info(self, app_name: str, app_config: Dict) -> Dict:
        """Create default app info structure."""
        return {
            "name": app_name,
            "display_name": app_config.get("display_name", app_name),
            "installed": False,
            "path": None,
            "size": 0,
            "running": False
        }
    
    def _get_directory_size(self, path: str) -> int:
        """Calculate total directory size in bytes."""
        try:
            total = 0
            for entry in os.scandir(path):
                if entry.is_file(follow_symlinks=False):
                    total += entry.stat().st_size
                elif entry.is_dir(follow_symlinks=False):
                    total += self._get_directory_size(entry.path)
            return total
        except (OSError, IOError):
            return 0
    
    def is_app_running(self, app_name: str) -> bool:
        """Check if application is running."""
        app_config = self.config.get("applications", {}).get(app_name, {})
        processes = app_config.get("process_names", [])
        
        try:
            for proc in psutil.process_iter(['name']):
                if any(p.lower() in proc.info['name'].lower() for p in processes):
                    return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
            
        return False
    
    def close_application(self, app_name: str, timeout: int = 10) -> Tuple[bool, str]:
        """Close application gracefully, then forcefully if needed."""
        if not self.is_app_running(app_name):
            return True, "Application not running"
        
        app_config = self.config.get("applications", {}).get(app_name, {})
        processes = app_config.get("process_names", [])
        closed_count = 0
        
        try:
            # First try graceful termination
            for proc in psutil.process_iter(['pid', 'name']):
                if any(p.lower() in proc.info['name'].lower() for p in processes):
                    try:
                        proc.terminate()
                        closed_count += 1
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
            
            # Wait for graceful termination
            psutil.wait_procs(
                [p for p in psutil.process_iter() 
                 if any(proc.lower() in p.name().lower() for proc in processes)],
                timeout=timeout
            )
            
            # Force kill if still running
            if self.is_app_running(app_name):
                for proc in psutil.process_iter(['pid', 'name']):
                    if any(p.lower() in proc.info['name'].lower() for p in processes):
                        try:
                            proc.kill()
                            closed_count += 1
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
            
            return not self.is_app_running(app_name), f"Closed {closed_count} processes"
            
        except Exception as e:
            return False, f"Error closing application: {e}"
    
    def get_app_info(self, app_name: str) -> Optional[Dict]:
        """Get information about specific app."""
        if not self.detected_apps:
            self.scan_applications()
        return self.detected_apps.get(app_name)
    
    def get_process_info(self, app_name: str) -> List[Dict]:
        """Get detailed process information for running app."""
        app_config = self.config.get("applications", {}).get(app_name, {})
        processes = app_config.get("process_names", [])
        process_list = []
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'cpu_percent']):
                if any(p.lower() in proc.info['name'].lower() for p in processes):
                    process_list.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'memory': proc.info['memory_info'].rss if proc.info['memory_info'] else 0,
                        'cpu': proc.info['cpu_percent'] or 0
                    })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
            
        return process_list
    
    def kill_app_process(self, app_name: str) -> Tuple[bool, str]:
        """Kill application process - wrapper for close_application()."""
        return self.close_application(app_name)
    
    def _load_detected_apps(self):
        """Load previously detected apps from config."""
        detected = self.config.get("detected_apps", {})
        for app_name, app_data in detected.items():
            if app_data.get("installed"):
                app_config = self.config.get("applications", {}).get(app_name, {})
                self.detected_apps[app_name] = {
                    "name": app_name,
                    "display_name": app_config.get("display_name", app_name),
                    "installed": app_data["installed"],
                    "path": app_data["path"],
                    "exe_path": app_data.get("exe_path", ""),
                    "size": 0,
                    "running": False
                }
    
    def _save_detected_apps(self):
        """Save detected apps to config file."""
        try:
            # Get config file path
            if getattr(sys, 'frozen', False):
                # Don't save in frozen mode
                return
            
            config_path = self.config_path
            if not os.path.isabs(config_path):
                current_dir = Path(__file__).parents[2]
                config_path = current_dir / config_path
            
            # Update detected_apps section
            self.config["detected_apps"] = {}
            for app_name, app_info in self.detected_apps.items():
                self.config["detected_apps"][app_name] = {
                    "installed": app_info.get("installed", False),
                    "path": app_info.get("path", ""),
                    "exe_path": app_info.get("exe_path", "")
                }
            
            # Save to file
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
                
        except Exception as e:
            debug_print(f"[DEBUG] Failed to save detected apps: {e}")
