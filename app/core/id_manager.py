"""Simple ID Manager for Windows - SurfManager."""
import json
import uuid
import os
from typing import Dict, Optional, Tuple


class IdManager:
    """Simple Windows-focused ID Manager."""
    
    def __init__(self):
        """Initialize ID Manager."""
        self.appdata_roaming = os.getenv('APPDATA')
    
    def get_current_device_ids(self, app_name: str) -> Dict:
        """Get current device IDs for an app.
        
        Args:
            app_name: App name (cursor, windsurf, claude)
            
        Returns:
            Dictionary with current IDs
        """
        storage_path = self._get_storage_path(app_name)
        
        if not storage_path or not os.path.exists(storage_path):
            return {}
        
        try:
            with open(storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return {
                'telemetry.machineId': data.get('telemetry.machineId'),
                'telemetry.macMachineId': data.get('telemetry.macMachineId'),
                'telemetry.devDeviceId': data.get('telemetry.devDeviceId')
            }
        except (json.JSONDecodeError, KeyError, OSError):
            return {}  # Storage file is invalid or missing
    
    def reset_device_ids(self, app_name: str, backup: bool = False) -> Tuple[bool, str, Optional[Dict]]:
        """Reset device IDs for an app.
        
        Args:
            app_name: App name (cursor, windsurf, claude)
            backup: Whether to backup (deprecated, kept for compatibility)
            
        Returns:
            Tuple of (success, message, new_ids)
        """
        storage_path = self._get_storage_path(app_name)
        
        if not storage_path:
            return False, f"Unsupported app: {app_name}", None
        
        if not os.path.exists(storage_path):
            return False, f"Storage file not found for {app_name}", None
        
        try:
            # Generate new ID
            new_id = str(uuid.uuid4())
            
            # Read current data
            with open(storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Update IDs
            data['telemetry.machineId'] = new_id
            data['telemetry.macMachineId'] = new_id
            data['telemetry.devDeviceId'] = new_id
            
            # Save
            with open(storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            new_ids = {
                'telemetry.machineId': new_id,
                'telemetry.macMachineId': new_id,
                'telemetry.devDeviceId': new_id
            }
            
            return True, "Device IDs reset successfully", new_ids
            
        except Exception as e:
            return False, f"Failed to reset IDs: {str(e)}", None
    
    def _get_storage_path(self, app_name: str) -> Optional[str]:
        """Get storage.json path for app.
        
        Args:
            app_name: App name
            
        Returns:
            Path to storage.json or None
        """
        paths = {
            'cursor': os.path.join(self.appdata_roaming, 'Cursor', 'User', 'globalStorage', 'storage.json'),
            'windsurf': os.path.join(self.appdata_roaming, 'Windsurf', 'User', 'globalStorage', 'storage.json'),
            'claude': None  # Claude doesn't use this structure
        }
        
        return paths.get(app_name.lower())
