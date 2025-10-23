"""Backup management and data cleaning functionality."""
import os
import shutil
import zipfile
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple


class BackupManager:
    """Manages backup creation and restoration."""
    
    def __init__(self, config_path: str = "config/config.json"):
        """Initialize BackupManager with configuration."""
        self.config = self._load_config(config_path)
        self.backup_base_dir = self._get_backup_directory()
        self._ensure_backup_dir()
    
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from JSON file."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            return {}
    
    def _get_backup_directory(self) -> str:
        """Get backup directory path from config or use default."""
        backup_location = self.config.get("backup_location", "Documents/SurfManager/Backups")
        
        # Expand to absolute path
        if "Documents" in backup_location:
            docs_path = os.path.join(os.path.expanduser("~"), "Documents")
            backup_path = backup_location.replace("Documents", docs_path)
        else:
            backup_path = os.path.expandvars(backup_location)
        
        return backup_path
    
    def _ensure_backup_dir(self):
        """Ensure backup directory exists."""
        os.makedirs(self.backup_base_dir, exist_ok=True)
    
    def get_backup_path(self) -> str:
        """Get the backup directory path."""
        return self.backup_base_dir
    
    def open_backup_folder(self):
        """Open backup folder in Windows Explorer."""
        try:
            os.startfile(self.backup_base_dir)
        except Exception as e:
            print(f"Failed to open backup folder: {e}")
    
    def create_backup(self, source_path: str, app_name: str, backup_folder: str = None) -> Tuple[bool, str]:
        """Create backup of application data."""
        if not os.path.exists(source_path):
            return False, f"Source path does not exist: {source_path}"
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{app_name}_{timestamp}"
        
        # Create app-specific backup folder if specified
        if backup_folder:
            app_backup_dir = os.path.join(self.backup_base_dir, backup_folder)
            os.makedirs(app_backup_dir, exist_ok=True)
        else:
            app_backup_dir = self.backup_base_dir
        
        use_compression = self.config.get("cleaning_options", {}).get("backup_compression", True)
        
        try:
            if use_compression:
                backup_file = os.path.join(app_backup_dir, f"{backup_name}.zip")
                return self._create_compressed_backup(source_path, backup_file)
            else:
                backup_dir = os.path.join(app_backup_dir, backup_name)
                return self._create_directory_backup(source_path, backup_dir)
        except Exception as e:
            return False, f"Backup failed: {str(e)}"
    
    def _create_compressed_backup(self, source_path: str, backup_file: str) -> Tuple[bool, str]:
        """Create compressed ZIP backup."""
        try:
            with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                if os.path.isfile(source_path):
                    zipf.write(source_path, os.path.basename(source_path))
                else:
                    for root, dirs, files in os.walk(source_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, source_path)
                            try:
                                zipf.write(file_path, arcname)
                            except Exception:
                                continue
            
            return True, f"Backup created: {backup_file}"
        except Exception as e:
            return False, f"Compression failed: {str(e)}"
    
    def _create_directory_backup(self, source_path: str, backup_dir: str) -> Tuple[bool, str]:
        """Create directory-based backup."""
        try:
            if os.path.isfile(source_path):
                os.makedirs(backup_dir, exist_ok=True)
                shutil.copy2(source_path, backup_dir)
            else:
                shutil.copytree(source_path, backup_dir, dirs_exist_ok=True)
            
            return True, f"Backup created: {backup_dir}"
        except Exception as e:
            return False, f"Copy failed: {str(e)}"
    
    def list_backups(self) -> list:
        """List all available backups."""
        backups = []
        try:
            for item in os.listdir(self.backup_base_dir):
                item_path = os.path.join(self.backup_base_dir, item)
                stat_info = os.stat(item_path)
                backups.append({
                    "name": item,
                    "path": item_path,
                    "size": stat_info.st_size,
                    "modified": datetime.fromtimestamp(stat_info.st_mtime)
                })
        except Exception as e:
            print(f"Error listing backups: {e}")
        
        return sorted(backups, key=lambda x: x["modified"], reverse=True)
    
    def clean_app_data(self, app_path: str) -> Tuple[bool, str]:
        """Clean application data by removing cache and temporary files."""
        if not os.path.exists(app_path):
            return False, f"Application path does not exist: {app_path}"
        
        try:
            # List of common cache and temporary directories to clean
            cache_dirs = [
                "Cache", "Code Cache", "GPUCache", "CachedData", "CachedExtensions",
                "logs", "blob_storage", "IndexedDB", "Local Storage", "Session Storage",
                "WebStorage", "ShaderCache", "Service Worker"
            ]
            
            cleaned_dirs = 0
            total_size = 0
            
            # Walk through the app directory and clean cache folders
            for root, dirs, files in os.walk(app_path):
                for dir_name in dirs:
                    if dir_name in cache_dirs:
                        dir_path = os.path.join(root, dir_name)
                        # Calculate size before cleaning
                        dir_size = self._get_directory_size(dir_path)
                        total_size += dir_size
                        
                        # Clean directory
                        self._clean_directory(dir_path)
                        cleaned_dirs += 1
            
            # Convert bytes to MB for reporting
            total_size_mb = total_size / (1024 * 1024)
            
            return True, f"Cleaned {cleaned_dirs} cache directories, freed {total_size_mb:.2f} MB"
        except Exception as e:
            return False, f"Cleaning failed: {str(e)}"
    
    def _get_directory_size(self, path: str) -> int:
        """Calculate total size of a directory in bytes."""
        total_size = 0
        for dirpath, _, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if os.path.exists(fp) and os.path.isfile(fp):
                    total_size += os.path.getsize(fp)
        return total_size
    
    def _clean_directory(self, directory: str) -> bool:
        """Clean a directory by removing all contents."""
        try:
            for item in os.listdir(directory):
                path = os.path.join(directory, item)
                if os.path.isfile(path):
                    os.unlink(path)
                elif os.path.isdir(path):
                    shutil.rmtree(path, ignore_errors=True)
            return True
        except Exception:
            return False
    
    def restore_backup(self, backup_path: str, target_path: str) -> Tuple[bool, str]:
        """Restore a backup to the target location."""
        if not os.path.exists(backup_path):
            return False, f"Backup not found: {backup_path}"
        
        if not os.path.exists(target_path):
            return False, f"Target path does not exist: {target_path}"
        
        try:
            # Check if backup is a zip file or directory
            if backup_path.endswith('.zip'):
                return self._restore_from_zip(backup_path, target_path)
            else:
                return self._restore_from_directory(backup_path, target_path)
        except Exception as e:
            return False, f"Restore failed: {str(e)}"
    
    def _restore_from_zip(self, zip_path: str, target_path: str) -> Tuple[bool, str]:
        """Restore from zip backup."""
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(target_path)
            return True, f"Backup restored from: {zip_path}"
        except Exception as e:
            return False, f"Zip extraction failed: {str(e)}"
    
    def _restore_from_directory(self, backup_dir: str, target_path: str) -> Tuple[bool, str]:
        """Restore from directory backup."""
        try:
            if os.path.isfile(backup_dir):
                shutil.copy2(backup_dir, target_path)
            else:
                # Remove existing target and copy backup
                if os.path.exists(target_path):
                    if os.path.isfile(target_path):
                        os.remove(target_path)
                    else:
                        shutil.rmtree(target_path)
                shutil.copytree(backup_dir, target_path)
            
            return True, f"Backup restored from: {backup_dir}"
        except Exception as e:
            return False, f"Directory restore failed: {str(e)}"
