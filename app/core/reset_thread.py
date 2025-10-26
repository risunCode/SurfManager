"""Reset thread for application data cleaning - Simplified version."""
import os
import sys
import time
import json
import shutil
from pathlib import Path
from PyQt6.QtCore import QThread, pyqtSignal
from typing import Optional, Dict
from app.core.path_utils import get_resource_path


class ResetThread(QThread):
    """Background thread for reset operations with detailed logging."""
    progress = pyqtSignal(str)
    progress_percent = pyqtSignal(int)  # Emit percentage for progress bar
    finished = pyqtSignal(bool, str)
    
    def __init__(self, app_manager, app_name: str):
        super().__init__()
        self.app_manager = app_manager
        self.app_name = app_name
        self.reset_config = self._load_reset_config()
    
    def _load_reset_config(self) -> Dict:
        """Load reset configuration from reset.json."""
        try:
            config_path = get_resource_path('app/config/reset.json')
            
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load reset.json: {e}")
            return {}
    
    def _expand_path(self, path_template: str) -> str:
        """Expand environment variables in path template."""
        expanded = os.path.expandvars(path_template)
        return expanded.replace('/', os.sep)
    
    def run(self):
        """Execute the reset operation - simplified version."""
        try:
            # Get app info
            app_info = self.app_manager.get_app_info(self.app_name)
            if not app_info or not app_info["installed"]:
                self.finished.emit(False, "Application not found")
                return
            
            # Get reset folder from config
            app_config = self.reset_config.get(self.app_name.lower(), {})
            reset_folder = app_config.get('reset_folder')
            
            if not reset_folder:
                self.finished.emit(False, "Reset folder not configured")
                return
            
            # Expand environment variables (like %USERPROFILE%)
            reset_folder = self._expand_path(reset_folder)
            reset_path = Path(reset_folder)
            
            # Phase 1: Starting
            self._emit_progress("Starting", f"Starting reset for {self.app_name}", 0)
            
            # Phase 2: Kill app processes (always, even if not detected as running)
            # This prevents "file in use" errors when app was launched from SurfManager
            self._emit_progress("Closing", f"Killing {app_info['display_name']} processes...", 10)
            success, msg = self.app_manager.kill_app_process(self.app_name)
            
            # Log the result but continue even if kill fails (app might not be running)
            if success or "not running" in msg.lower():
                self._emit_progress("Closing", msg, 15)
            else:
                self._emit_progress("Closing", f"Warning: {msg}", 15)
            
            # Wait for processes to fully terminate
            time.sleep(3)
            
            # Phase 3: Delete reset folder
            self._emit_progress("Deleting", f"Deleting folder: {reset_folder}", 30)
            
            if reset_path.exists():
                try:
                    shutil.rmtree(reset_path, ignore_errors=False)
                    self._emit_progress("Deleting", "Folder deleted successfully", 60)
                except Exception as e:
                    self._emit_progress("Deleting", f"Error deleting folder: {e}", 60)
                    self.finished.emit(False, f"Failed to delete folder: {str(e)}")
                    return
            else:
                self._emit_progress("Deleting", "Folder does not exist, skipping...", 60)
            
            # Phase 4: Recreate folder
            self._emit_progress("Recreating", f"Recreating folder: {reset_folder}", 80)
            try:
                reset_path.mkdir(parents=True, exist_ok=True)
                self._emit_progress("Recreating", "Folder recreated successfully", 90)
            except Exception as e:
                self._emit_progress("Recreating", f"Warning: Could not recreate folder: {e}", 90)
            
            # Complete - No need to reset device IDs since folder was deleted
            self._emit_progress("Complete", "Reset completed successfully!", 100)
            self.finished.emit(True, "Reset completed successfully")
            
        except Exception as e:
            self.finished.emit(False, f"Reset failed: {str(e)}")
    
    def _emit_progress(self, phase: str, message: str, percentage: int):
        """Emit formatted progress message."""
        # Emit message for log
        self.progress.emit(message)
        # Emit percentage for progress bar
        self.progress_percent.emit(percentage)

