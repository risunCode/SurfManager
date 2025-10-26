"""Unified ID and Telemetry Manager for SurfManager.

This module combines device ID management and telemetry tracking into a single,
powerful manager that handles:
- Device ID generation and reset
- Machine ID management
- Telemetry tracking
- Usage statistics
- Backup and restore of IDs
"""
import json
import os
import uuid
import hashlib
import platform
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple, List


class IdManager:
    """Unified manager for device IDs and telemetry."""
    
    def __init__(self, telemetry_file: Optional[str] = None):
        """Initialize the IdManager.
        
        Args:
            telemetry_file: Optional path to telemetry file. If None, uses default.
        """
        self.system = platform.system()
        self.home = Path.home()
        self.supported_apps = self._get_supported_apps()
        
        # Telemetry setup
        if telemetry_file:
            self.telemetry_file = Path(telemetry_file)
        else:
            self.telemetry_file = self.home / "Documents" / "SurfManager" / "telemetry.json"
        
        self._ensure_telemetry_file()
    
    def _get_supported_apps(self) -> Dict:
        """Get configuration for supported applications."""
        return {
            'windsurf': {
                'name': 'Windsurf',
                'storage_path': self._get_vscode_path('Windsurf'),
                'machine_id_path': self._get_machine_id_path('Windsurf'),
                'telemetry_keys': [
                    'telemetry.machineId',
                    'telemetry.macMachineId',
                    'telemetry.devDeviceId'
                ]
            },
            'cursor': {
                'name': 'Cursor',
                'storage_path': self._get_vscode_path('Cursor'),
                'machine_id_path': self._get_machine_id_path('Cursor'),
                'telemetry_keys': [
                    'telemetry.machineId',
                    'telemetry.macMachineId',
                    'telemetry.devDeviceId'
                ]
            },
            'vscode': {
                'name': 'VS Code',
                'storage_path': self._get_vscode_path('Code'),
                'machine_id_path': self._get_machine_id_path('Code'),
                'telemetry_keys': [
                    'telemetry.machineId',
                    'telemetry.macMachineId',
                    'telemetry.devDeviceId'
                ]
            }
        }
    
    def _get_vscode_path(self, app_name: str) -> Path:
        """Get VS Code-based app storage path."""
        if self.system == 'Windows':
            return self.home / 'AppData' / 'Roaming' / app_name / 'User' / 'globalStorage' / 'storage.json'
        elif self.system == 'Darwin':  # macOS
            return self.home / 'Library' / 'Application Support' / app_name / 'User' / 'globalStorage' / 'storage.json'
        else:  # Linux
            return self.home / '.config' / app_name / 'User' / 'globalStorage' / 'storage.json'
    
    def _get_machine_id_path(self, app_name: str) -> Path:
        """Get machine ID file path."""
        if self.system == 'Windows':
            return self.home / 'AppData' / 'Roaming' / app_name / 'machineid'
        elif self.system == 'Darwin':  # macOS
            return self.home / 'Library' / 'Application Support' / app_name / 'machineid'
        else:  # Linux
            return self.home / '.config' / app_name / 'machineid'
    
    # ==================== DEVICE ID MANAGEMENT ====================
    
    def generate_device_id(self) -> str:
        """Generate a new random device ID."""
        return str(uuid.uuid4()).replace('-', '')
    
    def get_current_device_ids(self, app_key: str) -> Dict[str, Optional[str]]:
        """Get current device IDs for an application.
        
        Args:
            app_key: Application key (windsurf, cursor, vscode)
            
        Returns:
            Dictionary of current device IDs
        """
        if app_key not in self.supported_apps:
            raise ValueError(f"Unsupported application: {app_key}")
        
        app_config = self.supported_apps[app_key]
        result = {}
        
        # Get machine ID
        machine_id_path = app_config['machine_id_path']
        if machine_id_path.exists():
            try:
                result['machine_id'] = machine_id_path.read_text().strip()
            except Exception:
                result['machine_id'] = None
        else:
            result['machine_id'] = None
        
        # Get telemetry IDs from storage.json
        storage_path = app_config['storage_path']
        if storage_path.exists():
            try:
                with open(storage_path, 'r', encoding='utf-8') as f:
                    storage_data = json.load(f)
                    
                for key in app_config['telemetry_keys']:
                    result[key] = storage_data.get(key)
            except Exception:
                for key in app_config['telemetry_keys']:
                    result[key] = None
        else:
            for key in app_config['telemetry_keys']:
                result[key] = None
        
        return result
    
    def reset_device_ids(self, app_key: str, backup: bool = True) -> Tuple[bool, str, Optional[Dict]]:
        """Reset device IDs for an application.
        
        Args:
            app_key: Application key (windsurf, cursor, vscode)
            backup: Whether to backup current IDs before reset
            
        Returns:
            Tuple of (success, message, new_ids)
        """
        if app_key not in self.supported_apps:
            return False, f"Unsupported application: {app_key}", None
        
        app_config = self.supported_apps[app_key]
        new_ids = {}
        
        try:
            # Backup current IDs if requested
            if backup:
                self.backup_device_ids(app_key)
            
            # Generate new device ID
            new_device_id = self.generate_device_id()
            new_ids['device_id'] = new_device_id
            
            # Update machine ID file
            machine_id_path = app_config['machine_id_path']
            if machine_id_path.parent.exists():
                machine_id_path.write_text(new_device_id)
                new_ids['machine_id'] = new_device_id
            
            # Update storage.json
            storage_path = app_config['storage_path']
            if storage_path.exists():
                # Read existing data
                with open(storage_path, 'r', encoding='utf-8') as f:
                    storage_data = json.load(f)
                
                # Update telemetry keys
                for key in app_config['telemetry_keys']:
                    storage_data[key] = new_device_id
                    new_ids[key] = new_device_id
                
                # Write updated data
                with open(storage_path, 'w', encoding='utf-8') as f:
                    json.dump(storage_data, f, indent=2)
            
            # Track in telemetry
            self.track_id_reset(app_key, True, new_ids)
            
            return True, "Device IDs reset successfully", new_ids
            
        except Exception as e:
            self.track_id_reset(app_key, False, {'error': str(e)})
            return False, f"Failed to reset device IDs: {str(e)}", None
    
    def backup_device_ids(self, app_key: str) -> Tuple[bool, str, Optional[Dict]]:
        """Backup current device IDs for an application.
        
        Args:
            app_key: Application key (windsurf, cursor, vscode)
            
        Returns:
            Tuple of (success, backup_file_path, current_ids)
        """
        if app_key not in self.supported_apps:
            return False, f"Unsupported application: {app_key}", None
        
        try:
            current_ids = self.get_current_device_ids(app_key)
            
            # Save to backup file
            backup_dir = self.home / 'Documents' / 'SurfManager' / 'DeviceID_Backups'
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = backup_dir / f"{app_key}_deviceids_{timestamp}.json"
            
            backup_data = {
                'app': app_key,
                'timestamp': timestamp,
                'ids': current_ids
            }
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2)
            
            return True, str(backup_file), current_ids
            
        except Exception as e:
            return False, f"Failed to backup device IDs: {str(e)}", None
    
    def restore_device_ids(self, app_key: str, backup_file: str) -> Tuple[bool, str]:
        """Restore device IDs from backup.
        
        Args:
            app_key: Application key (windsurf, cursor, vscode)
            backup_file: Path to backup file
            
        Returns:
            Tuple of (success, message)
        """
        if app_key not in self.supported_apps:
            return False, f"Unsupported application: {app_key}"
        
        app_config = self.supported_apps[app_key]
        
        try:
            # Read backup file
            with open(backup_file, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            if backup_data['app'] != app_key:
                return False, "Backup file is for a different application"
            
            ids = backup_data['ids']
            
            # Restore machine ID
            if ids.get('machine_id'):
                machine_id_path = app_config['machine_id_path']
                if machine_id_path.parent.exists():
                    machine_id_path.write_text(ids['machine_id'])
            
            # Restore storage.json IDs
            storage_path = app_config['storage_path']
            if storage_path.exists():
                with open(storage_path, 'r', encoding='utf-8') as f:
                    storage_data = json.load(f)
                
                for key in app_config['telemetry_keys']:
                    if key in ids and ids[key]:
                        storage_data[key] = ids[key]
                
                with open(storage_path, 'w', encoding='utf-8') as f:
                    json.dump(storage_data, f, indent=2)
            
            return True, "Device IDs restored successfully"
            
        except Exception as e:
            return False, f"Failed to restore device IDs: {str(e)}"
    
    # ==================== TELEMETRY MANAGEMENT ====================
    
    def _ensure_telemetry_file(self):
        """Ensure telemetry file and directory exist."""
        try:
            self.telemetry_file.parent.mkdir(parents=True, exist_ok=True)
            
            if not self.telemetry_file.exists():
                self._create_default_telemetry()
                
        except Exception as e:
            print(f"Failed to initialize telemetry: {e}")
    
    def _create_default_telemetry(self):
        """Create default telemetry structure."""
        default_data = {
            "version": "1.0",
            "created": datetime.now().isoformat(),
            "device_id": self._generate_system_device_id(),
            "usage_stats": {},
            "id_reset_history": [],
            "error_log": [],
            "preferences": {
                "auto_backup": True,
                "telemetry_enabled": True
            }
        }
        
        self._save_telemetry(default_data)
    
    def _generate_system_device_id(self) -> str:
        """Generate unique device ID based on system info."""
        # Combine system info for unique ID
        system_info = f"{platform.node()}-{platform.system()}-{platform.machine()}"
        return hashlib.sha256(system_info.encode()).hexdigest()[:16]
    
    def _load_telemetry(self) -> Dict:
        """Load telemetry data from file."""
        try:
            if self.telemetry_file.exists():
                with open(self.telemetry_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
        
        return {}
    
    def _save_telemetry(self, data: Dict):
        """Save telemetry data to file."""
        try:
            with open(self.telemetry_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            print(f"Failed to save telemetry: {e}")
    
    def track_id_reset(self, app_name: str, success: bool, details: Optional[Dict] = None):
        """Track ID reset operation.
        
        Args:
            app_name: Application name
            success: Whether the reset was successful
            details: Additional details about the reset
        """
        data = self._load_telemetry()
        
        if "id_reset_history" not in data:
            data["id_reset_history"] = []
        
        reset_entry = {
            "app": app_name,
            "timestamp": datetime.now().isoformat(),
            "success": success,
            "details": details or {}
        }
        
        data["id_reset_history"].append(reset_entry)
        
        # Keep only last 50 entries
        data["id_reset_history"] = data["id_reset_history"][-50:]
        
        # Also update usage stats
        self.track_app_usage(app_name, "id_reset")
        
        self._save_telemetry(data)
    
    def track_app_usage(self, app_name: str, action: str):
        """Track application usage.
        
        Args:
            app_name: Application name
            action: Action performed (id_reset, backup, etc.)
        """
        data = self._load_telemetry()
        
        if "usage_stats" not in data:
            data["usage_stats"] = {}
        
        if app_name not in data["usage_stats"]:
            data["usage_stats"][app_name] = {
                "total_id_resets": 0,
                "last_id_reset": None,
                "actions": []
            }
        
        app_stats = data["usage_stats"][app_name]
        
        # Update based on action
        if action == "id_reset":
            app_stats["total_id_resets"] += 1
            app_stats["last_id_reset"] = datetime.now().isoformat()
        
        # Add to action history (keep last 10)
        app_stats["actions"].append({
            "action": action,
            "timestamp": datetime.now().isoformat()
        })
        app_stats["actions"] = app_stats["actions"][-10:]
        
        self._save_telemetry(data)
    
    def track_error(self, error_type: str, error_msg: str, context: Optional[Dict] = None):
        """Track error occurrence.
        
        Args:
            error_type: Type of error
            error_msg: Error message
            context: Additional context
        """
        data = self._load_telemetry()
        
        if "error_log" not in data:
            data["error_log"] = []
        
        error_entry = {
            "type": error_type,
            "message": error_msg,
            "timestamp": datetime.now().isoformat(),
            "context": context or {}
        }
        
        data["error_log"].append(error_entry)
        
        # Keep only last 100 errors
        data["error_log"] = data["error_log"][-100:]
        
        self._save_telemetry(data)
    
    def get_app_stats(self, app_name: str) -> Dict:
        """Get usage statistics for an application.
        
        Args:
            app_name: Application name
            
        Returns:
            Dictionary of usage statistics
        """
        data = self._load_telemetry()
        return data.get("usage_stats", {}).get(app_name, {})
    
    def get_id_reset_history(self, app_name: Optional[str] = None) -> List:
        """Get ID reset history, optionally filtered by app.
        
        Args:
            app_name: Optional application name to filter by
            
        Returns:
            List of reset history entries
        """
        data = self._load_telemetry()
        history = data.get("id_reset_history", [])
        
        if app_name:
            return [h for h in history if h.get("app") == app_name]
        
        return history
    
    def get_summary(self) -> Dict:
        """Get telemetry summary.
        
        Returns:
            Dictionary with summary statistics
        """
        data = self._load_telemetry()
        
        summary = {
            "device_id": data.get("device_id", "unknown"),
            "total_apps_tracked": len(data.get("usage_stats", {})),
            "total_id_resets": sum(
                stats.get("total_id_resets", 0) 
                for stats in data.get("usage_stats", {}).values()
            ),
            "recent_errors": len(data.get("error_log", [])),
            "telemetry_created": data.get("created", "unknown")
        }
        
        return summary
    
    def clear_telemetry(self):
        """Clear all telemetry data (reset to defaults)."""
        self._create_default_telemetry()
    
    def export_telemetry(self, export_path: str) -> Tuple[bool, str]:
        """Export telemetry data to file.
        
        Args:
            export_path: Path to export file
            
        Returns:
            Tuple of (success, message/path)
        """
        try:
            data = self._load_telemetry()
            
            export_file = Path(export_path)
            export_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
            
            return True, str(export_file)
            
        except Exception as e:
            return False, str(e)
