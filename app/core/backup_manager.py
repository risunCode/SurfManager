"""Backup management for application data - Optimized version."""
import os
import sys
import shutil
import json
import zipfile
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from app.core.core_utils import debug_print, get_resource_path
from app.core.path_validator import PathValidator


class BackupManager:
    """Handles backup and restore operations for application data."""
    
    def __init__(self, base_backup_dir: Optional[str] = None):
        """Initialize BackupManager with base backup directory."""
        if base_backup_dir:
            self.base_backup_dir = Path(base_backup_dir)
        else:
            # Default to Documents/SurfManager/Backups
            self.base_backup_dir = Path.home() / "Documents" / "SurfManager" / "Backups"
        
        self._ensure_backup_dir()
        self.reset_config = self._load_reset_config()
    
    def _ensure_backup_dir(self):
        """Ensure backup directory exists."""
        try:
            self.base_backup_dir.mkdir(parents=True, exist_ok=True)
            debug_print(f"[DEBUG] Backup directory ready: {self.base_backup_dir}")
        except Exception as e:
            debug_print(f"[ERROR] Failed to create backup directory: {e}")
    
    def _load_reset_config(self) -> Dict:
        """Load reset configuration from reset.json."""
        try:
            config_path = get_resource_path('app/config/reset.json')
            
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            debug_print(f"[WARNING] Could not load reset.json: {e}")
            return {}
    
    def create_backup(self, source_path: str, app_name: str, 
                     backup_name: Optional[str] = None) -> Tuple[bool, str]:
        """Create backup of application data."""
        try:
            # Validate source path
            is_valid, error, normalized_source = PathValidator.validate_path(
                source_path, must_exist=True
            )
            if not is_valid:
                return False, f"Invalid source path: {error}"
            
            if not normalized_source.exists():
                return False, f"Source path does not exist: {source_path}"
            
            # Generate backup folder name
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = backup_name or f"{app_name}_backup_{timestamp}"
            
            # Sanitize backup name
            backup_name = PathValidator.sanitize_filename(backup_name)
            backup_path = self.base_backup_dir / app_name / backup_name
            
            # Validate backup destination
            is_valid, error = PathValidator.validate_backup_path(str(backup_path))
            if not is_valid:
                return False, f"Invalid backup destination: {error}"
            
            # Check disk space
            source_size = self._estimate_directory_size(normalized_source)
            free_space = self._get_free_disk_space(self.base_backup_dir)
            
            # Require 1.5x source size for safety (compression, metadata, etc.)
            required_space = int(source_size * 1.5)
            if free_space < required_space:
                return False, (f"Insufficient disk space. Required: {self._format_size(required_space)}, "
                             f"Available: {self._format_size(free_space)}")
            
            # Create backup directory
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # Copy data
            total_files = 0
            total_size = 0
            
            for root, dirs, files in os.walk(source_path):
                # Skip unnecessary directories
                dirs[:] = [d for d in dirs if not self._should_skip(d)]
                
                rel_path = os.path.relpath(root, source_path)
                dest_dir = backup_path / rel_path if rel_path != '.' else backup_path
                dest_dir.mkdir(parents=True, exist_ok=True)
                
                for file in files:
                    if self._should_skip(file):
                        continue
                        
                    src_file = Path(root) / file
                    dest_file = dest_dir / file
                    
                    try:
                        shutil.copy2(src_file, dest_file)
                        total_files += 1
                        total_size += src_file.stat().st_size
                    except Exception as e:
                        debug_print(f"[WARNING] Failed to backup {file}: {e}")
            
            # Create backup info
            info = {
                "app_name": app_name,
                "source_path": str(source_path),
                "backup_path": str(backup_path),
                "timestamp": timestamp,
                "total_files": total_files,
                "total_size": total_size,
                "checksum": self._calculate_checksum(backup_path)
            }
            
            info_file = backup_path / "backup_info.json"
            with open(info_file, 'w') as f:
                json.dump(info, f, indent=2)
            
            debug_print(f"[DEBUG] Backup created: {backup_path}")
            return True, str(backup_path)
            
        except Exception as e:
            debug_print(f"[ERROR] Backup failed: {e}")
            return False, str(e)
    
    def create_compressed_backup(self, source_path: str, app_name: str,
                                backup_name: Optional[str] = None,
                                progress_callback=None) -> Tuple[bool, str]:
        """Create compressed backup as ZIP file - only backup specified items."""
        try:
            # Validate source path
            is_valid, error, normalized_source = PathValidator.validate_path(
                source_path, must_exist=True
            )
            if not is_valid:
                return False, f"Invalid source path: {error}"
            
            if not normalized_source.exists():
                return False, f"Source path does not exist: {source_path}"
            
            # Reload config to ensure we have latest backup items
            self.reset_config = self._load_reset_config()
            
            # Get backup items from config
            app_config = self.reset_config.get(app_name.lower(), {})
            backup_items = app_config.get('backup_items', [])
            
            if not backup_items:
                debug_print(f"[WARNING] No backup items specified for {app_name}")
                return False, "No backup items configured"
            
            # Generate backup filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = backup_name or f"{app_name}_backup_{timestamp}"
            backup_dir = self.base_backup_dir / app_name
            backup_dir.mkdir(parents=True, exist_ok=True)
            backup_file = backup_dir / f"{backup_name}.zip"
            
            # Create ZIP archive with only specified items
            source = Path(source_path)
            total_files = 0
            found_items = []
            missing_items = []
            
            if progress_callback:
                progress_callback(f"📦 Scanning {len(backup_items)} items...")
            
            with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for item in backup_items:
                    item_path = source / item
                    
                    if not item_path.exists():
                        debug_print(f"[WARNING] Backup item not found: {item}")
                        missing_items.append(item)
                        if progress_callback:
                            progress_callback(f"⚠️ Not found: {item}")
                        continue
                    
                    # Backup file
                    if item_path.is_file():
                        try:
                            zipf.write(item_path, item)
                            total_files += 1
                            found_items.append(item)
                            debug_print(f"[DEBUG] Backed up file: {item}")
                            if progress_callback:
                                progress_callback(f"✅ Backed up: {item}")
                        except Exception as e:
                            debug_print(f"[WARNING] Failed to backup {item}: {e}")
                            if progress_callback:
                                progress_callback(f"❌ Failed: {item}")
                    
                    # Backup directory
                    elif item_path.is_dir():
                        dir_file_count = 0
                        for root, dirs, files in os.walk(item_path):
                            for file in files:
                                file_path = Path(root) / file
                                arc_name = os.path.relpath(file_path, source)
                                
                                try:
                                    zipf.write(file_path, arc_name)
                                    total_files += 1
                                    dir_file_count += 1
                                except Exception as e:
                                    debug_print(f"[WARNING] Failed to backup {file}: {e}")
                        
                        found_items.append(item)
                        debug_print(f"[DEBUG] Backed up directory: {item} ({dir_file_count} files)")
                        if progress_callback:
                            progress_callback(f"✅ Backed up: {item} ({dir_file_count} files)")
            
            debug_print(f"[DEBUG] Compressed backup created: {backup_file} ({total_files} files)")
            
            # Summary
            if progress_callback:
                progress_callback(f"📊 Summary: {len(found_items)} items backed up, {len(missing_items)} not found")
            
            return True, str(backup_file)
            
        except Exception as e:
            debug_print(f"[ERROR] Compressed backup failed: {e}")
            return False, str(e)
    
    def restore_backup(self, backup_path: str, target_path: str) -> Tuple[bool, str]:
        """Restore backup to target location."""
        try:
            backup_path = Path(backup_path)
            
            # Check if it's a ZIP backup
            if backup_path.suffix == '.zip':
                return self._restore_compressed_backup(backup_path, target_path)
            
            # Regular directory backup
            if not backup_path.exists():
                return False, f"Backup path does not exist: {backup_path}"
            
            # Read backup info
            info_file = backup_path / "backup_info.json"
            if info_file.exists():
                with open(info_file, 'r') as f:
                    info = json.load(f)
                debug_print(f"[DEBUG] Restoring backup from {info['timestamp']}")
            
            # Clear target directory
            if os.path.exists(target_path):
                shutil.rmtree(target_path, ignore_errors=True)
            
            # Copy backup to target
            shutil.copytree(backup_path, target_path, 
                           ignore=shutil.ignore_patterns('backup_info.json'))
            
            debug_print(f"[DEBUG] Backup restored to: {target_path}")
            return True, "Backup restored successfully"
            
        except Exception as e:
            debug_print(f"[ERROR] Restore failed: {e}")
            return False, str(e)
    
    def _restore_compressed_backup(self, backup_file: Path, target_path: str) -> Tuple[bool, str]:
        """Restore compressed backup from ZIP file."""
        try:
            if not backup_file.exists():
                return False, f"Backup file does not exist: {backup_file}"
            
            # Clear target directory
            if os.path.exists(target_path):
                shutil.rmtree(target_path, ignore_errors=True)
            
            # Extract ZIP archive
            with zipfile.ZipFile(backup_file, 'r') as zipf:
                zipf.extractall(target_path)
            
            debug_print(f"[DEBUG] Compressed backup restored to: {target_path}")
            return True, "Backup restored successfully"
            
        except Exception as e:
            debug_print(f"[ERROR] Compressed restore failed: {e}")
            return False, str(e)
    
    def list_backups(self, app_name: str) -> List[Dict]:
        """List all backups for an application."""
        backups = []
        app_backup_dir = self.base_backup_dir / app_name
        
        if not app_backup_dir.exists():
            return backups
        
        # Check for directory backups
        for item in app_backup_dir.iterdir():
            if item.is_dir():
                info_file = item / "backup_info.json"
                if info_file.exists():
                    with open(info_file, 'r') as f:
                        backups.append(json.load(f))
            
            # Check for ZIP backups
            elif item.suffix == '.zip':
                backups.append({
                    "app_name": app_name,
                    "backup_path": str(item),
                    "timestamp": item.stem.split('_')[-2:],
                    "compressed": True,
                    "size": item.stat().st_size
                })
        
        return sorted(backups, key=lambda x: x.get('timestamp', ''), reverse=True)
    
    def delete_backup(self, backup_path: str) -> Tuple[bool, str]:
        """Delete a backup."""
        try:
            backup_path = Path(backup_path)
            
            if backup_path.is_dir():
                shutil.rmtree(backup_path)
            elif backup_path.is_file():
                backup_path.unlink()
            else:
                return False, f"Backup not found: {backup_path}"
            
            debug_print(f"[DEBUG] Backup deleted: {backup_path}")
            return True, "Backup deleted successfully"
            
        except Exception as e:
            debug_print(f"[ERROR] Delete backup failed: {e}")
            return False, str(e)
    
    def _should_skip(self, name: str) -> bool:
        """Check if file/directory should be skipped during backup."""
        skip_patterns = [
            'node_modules', '__pycache__', '.git', '.venv', 'venv',
            '*.tmp', '*.log', '*.cache', 'Temp', 'temp', 'tmp'
        ]
        
        name_lower = name.lower()
        return any(
            pattern.replace('*', '') in name_lower 
            for pattern in skip_patterns
        )
    
    def _calculate_checksum(self, path: Path) -> str:
        """Calculate checksum for backup verification."""
        hasher = hashlib.sha256()
        
        for root, dirs, files in os.walk(path):
            for file in sorted(files):
                file_path = Path(root) / file
                try:
                    with open(file_path, 'rb') as f:
                        while chunk := f.read(8192):
                            hasher.update(chunk)
                except Exception:
                    pass
        
        return hasher.hexdigest()
    
    def _estimate_directory_size(self, path: Path) -> int:
        """Estimate directory size in bytes."""
        total = 0
        try:
            for entry in path.rglob('*'):
                if entry.is_file():
                    try:
                        total += entry.stat().st_size
                    except (OSError, PermissionError):
                        pass
        except Exception as e:
            debug_print(f"[WARNING] Error estimating size: {e}")
        return total
    
    def _get_free_disk_space(self, path: Path) -> int:
        """Get free disk space in bytes."""
        try:
            import shutil
            stat = shutil.disk_usage(path)
            return stat.free
        except Exception as e:
            debug_print(f"[WARNING] Cannot get disk space: {e}")
            return 0
    
    def _format_size(self, size: int) -> str:
        """Format size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} PB"
