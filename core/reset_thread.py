"""Reset thread for application data cleaning."""
import os
import time
import shutil
import json
import sqlite3
import uuid
from PyQt6.QtCore import QThread, pyqtSignal


class ResetThread(QThread):
    """Background thread for reset operations with detailed logging."""
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, app_manager, backup_manager, app_name, create_backup, backup_folder=None):
        super().__init__()
        self.app_manager = app_manager
        self.backup_manager = backup_manager
        self.app_name = app_name
        self.create_backup = create_backup
        self.backup_folder = backup_folder
        self.cache_types = [
            "IndexedDB", "Local Storage", "Cache", "Code Cache", 
            "GPUCache", "blob_storage", "logs", "User/workspaceStorage",
            "User/History", "User/logs", "CachedData", "CachedExtensions",
            "ShaderCache", "WebStorage"
        ]
        self.telemetry_keys = [
            "machineId", "deviceId", "telemetryId", "installationId", 
            "anonymousId", "userId", "sessionId", "clientId"
        ]
        self.session_keys = [
            "session", "sessions", "sessionData", "sessionInfo"
        ]
    
    def run(self):
        try:
            # Get app info
            app_info = self.app_manager.get_app_info(self.app_name)
            if not app_info or not app_info["installed"]:
                self.finished.emit(False, "Application not found")
                return
            
            # Phase: Starting
            self.progress.emit(f"INFO:  Phase: , Progress: Starting reset for {self.app_name}, Percentage: 0%")
            
            # Check if running
            if app_info["running"]:
                self.progress.emit(f"INFO:  {app_info['display_name']} is running. Attempting to close...")
                success, msg = self.app_manager.kill_app_process(self.app_name)
                if not success:
                    self.finished.emit(False, f"Failed to close application: {msg}")
                    return
                self.progress.emit(f"INFO:  Application closed successfully")
                
                # Add delay after killing process
                self.progress.emit(f"INFO:  Waiting 3 seconds for processes to fully terminate...")
                time.sleep(3)
            
            # Phase: Analysis
            self.progress.emit(f"INFO:  Phase: , Progress: Analyzing application data, Percentage: 10%")
            
            # Create backup if enabled
            if self.create_backup:
                self.progress.emit(f"INFO:  Creating backup of {app_info['display_name']} data...")
                success, msg = self.backup_manager.create_backup(
                    app_info["path"], 
                    self.app_name,
                    self.backup_folder
                )
                if success:
                    self.progress.emit(f"INFO:  {msg}")
                else:
                    self.finished.emit(False, f"Backup failed: {msg}")
                    return
            
            # Analyze cache
            cache_dirs = self.find_cache_directories(app_info["path"])
            total_size = self.calculate_total_size(cache_dirs)
            self.progress.emit(f"INFO:  Phase: , Progress: Found {len(cache_dirs)} cache types, total size {total_size:.1f} MB, Percentage: 15%")
            
            # Phase: Telemetry
            self.progress.emit(f"INFO:  Phase: telemetry, Progress: Modifying Telemetry ID, Percentage: 20%")
            
            # Find telemetry files
            telemetry_files = self.find_telemetry_files(app_info["path"])
            self.progress.emit(f"INFO:  Phase: telemetry, Progress: Started processing {len(telemetry_files)} identifier files, Percentage: 20%")
            
            # Process telemetry files
            processed = 0
            updated = 0
            deleted = 0
            failed = 0
            
            for i, file_path in enumerate(telemetry_files):
                progress = 22.0 + float(i) * 18.0 / float(len(telemetry_files) + 1)
                self.progress.emit(f"INFO:  Phase: telemetry, Progress: Processing file ({i+1}/{len(telemetry_files)}): {os.path.basename(file_path)}, Percentage: {int(progress)}%")
                
                file_ext = os.path.splitext(file_path)[1].lower()
                if file_ext == '.json':
                    success, updated_count, deleted_count = self.process_json_file(file_path)
                    processed += 1
                    if success:
                        updated += updated_count
                        deleted += deleted_count
                    else:
                        failed += 1
                elif file_ext in ['.vscdb', '.db', '.sqlite', '.sqlite3']:
                    success, updated_count, deleted_count = self.process_sqlite_file(file_path)
                    processed += 1
                    if success:
                        updated += updated_count
                        deleted += deleted_count
                    else:
                        failed += 1
            
            self.progress.emit(f"INFO:  Phase: telemetry, Progress: Telemetry modification complete (Processed: {processed}, Updated: {updated}, Deleted: {deleted}, Failed: {failed}), Percentage: 45%")
            
            # Phase: Database
            self.progress.emit(f"INFO:  Phase: database, Progress: Resetting database, Percentage: 50%")
            
            # Find database files
            db_files = self.find_database_files(app_info["path"])
            self.progress.emit(f"INFO:  Phase: database, Progress: Found {len(db_files)} database files, Percentage: 50%")
            
            # Process database files
            reset_count = 0
            record_count = 0
            
            for i, db_file in enumerate(db_files):
                progress = 50.0 + float(i) * 15.0 / float(len(db_files) + 1)
                self.progress.emit(f"INFO:  Phase: database, Progress: Processing database ({i+1}/{len(db_files)}): {os.path.basename(db_file)}, Percentage: {int(progress)}%")
                
                success, records = self.reset_database(db_file)
                if success:
                    reset_count += 1
                    record_count += records
            
            self.progress.emit(f"INFO:  Phase: database, Progress: Database reset complete (Reset: {reset_count}/{len(db_files)}, Records: {record_count}, Failed: {len(db_files) - reset_count}), Percentage: 65%")
            
            # Phase: Cache
            self.progress.emit(f"INFO:  Phase: cache, Progress: Resetting cache directories, Percentage: 80%")
            self.progress.emit(f"INFO:  Phase: cache, Progress: Searching all cache directories ({len(self.cache_types)} types), Percentage: 80%")
            
            # Search cache directories
            found_cache_dirs = {}
            for i, cache_type in enumerate(self.cache_types):
                progress = 80.0 + float(i) * 1.0 / float(len(self.cache_types))
                self.progress.emit(f"INFO:  Phase: cache, Progress: Searching cache directory: {cache_type}, Percentage: {int(progress)}%")
                
                dirs = self.find_directories_by_name(app_info["path"], cache_type)
                if dirs:
                    found_cache_dirs[cache_type] = dirs
            
            # Reset cache directories
            total_cache_dirs = sum(len(dirs) for dirs in found_cache_dirs.values())
            self.progress.emit(f"INFO:  Phase: cache, Progress: Starting reset of {total_cache_dirs} cache directories, Percentage: 85%")
            
            reset_count = 0
            current_progress = 85
            
            for cache_type, dirs in found_cache_dirs.items():
                self.progress.emit(f"INFO:  Phase: cache, Progress: Reset {cache_type}: Found {len(dirs)} directories, Percentage: {current_progress}%")
                
                for i, dir_path in enumerate(dirs):
                    self.progress.emit(f"INFO:  Phase: cache, Progress: Reset {cache_type} ({i+1}/{len(dirs)}): {os.path.basename(dir_path)}, Percentage: {current_progress}%")
                    self.clean_directory(dir_path)
                    reset_count += 1
                    current_progress += 1
                    if current_progress > 95:
                        current_progress = 95
            
            # Clean app data
            self.progress.emit(f"INFO:  Reset complete: {app_info['display_name']}")
            self.progress.emit(f"INFO:  Phase: cache, Progress: Cache reset complete: Reset {reset_count} directories, freed {total_size:.1f} MB, Percentage: 100%")
            self.progress.emit(f"INFO:  Phase: , Progress: Successfully reset {self.app_name}, Percentage: 100%")
            
            self.finished.emit(True, f"Successfully reset {app_info['display_name']}")
        except Exception as e:
            self.progress.emit(f"ERROR: {str(e)}")
            self.finished.emit(False, f"Error: {str(e)}")
    
    def find_cache_directories(self, app_path):
        """Find cache directories in the application path."""
        result = []
        for cache_type in self.cache_types:
            dirs = self.find_directories_by_name(app_path, cache_type)
            if dirs:
                result.extend(dirs)
        return result
    
    def find_directories_by_name(self, root_path, dir_name):
        """Find directories with a specific name."""
        result = []
        for root, dirs, _ in os.walk(root_path):
            for d in dirs:
                if d == dir_name or d.lower() == dir_name.lower():
                    result.append(os.path.join(root, d))
        return result
    
    def calculate_total_size(self, directories):
        """Calculate total size of directories in MB."""
        total_size = 0
        for directory in directories:
            total_size += self.get_directory_size(directory)
        return total_size / (1024 * 1024)  # Convert to MB
    
    def get_directory_size(self, path):
        """Get directory size in bytes."""
        total_size = 0
        for dirpath, _, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if os.path.exists(fp) and os.path.isfile(fp):
                    total_size += os.path.getsize(fp)
        return total_size
    
    def find_telemetry_files(self, app_path):
        """Find files that might contain telemetry data."""
        result = []
        for root, _, files in os.walk(app_path):
            for file in files:
                if file.endswith(('.json', '.vscdb', '.db', '.sqlite', '.sqlite3')):
                    result.append(os.path.join(root, file))
        return result
    
    def process_json_file(self, file_path):
        """Process JSON file to reset telemetry IDs."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    return False, 0, 0
            
            if not isinstance(data, dict):
                return False, 0, 0
            
            # Generate new IDs
            new_machine_id = str(uuid.uuid4())
            new_session_id = str(uuid.uuid4())
            
            # Process JSON
            updated_keys = 0
            deleted_keys = 0
            modified = False
            
            # Check for telemetry keys
            for key in self.telemetry_keys:
                if key in data:
                    if isinstance(data[key], str):
                        data[key] = new_machine_id
                        updated_keys += 1
                        modified = True
            
            # Check for session keys
            for key in self.session_keys:
                if key in data:
                    del data[key]
                    deleted_keys += 1
                    modified = True
            
            # Process nested objects
            for key, value in data.items():
                if isinstance(value, dict):
                    success, u_keys, d_keys = self.process_nested_json(value, new_machine_id, new_session_id)
                    if success:
                        updated_keys += u_keys
                        deleted_keys += d_keys
                        modified = True
            
            # Write back if modified
            if modified:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
            
            return True, updated_keys, deleted_keys
        except Exception:
            return False, 0, 0
    
    def process_nested_json(self, data, new_machine_id, new_session_id):
        """Process nested JSON objects."""
        updated_keys = 0
        deleted_keys = 0
        modified = False
        
        # Check for telemetry keys
        for key in self.telemetry_keys:
            if key in data:
                if isinstance(data[key], str):
                    data[key] = new_machine_id
                    updated_keys += 1
                    modified = True
        
        # Check for session keys
        for key in self.session_keys:
            if key in data:
                del data[key]
                deleted_keys += 1
                modified = True
        
        # Process nested objects
        for key, value in list(data.items()):
            if isinstance(value, dict):
                success, u_keys, d_keys = self.process_nested_json(value, new_machine_id, new_session_id)
                if success:
                    updated_keys += u_keys
                    deleted_keys += d_keys
                    modified = True
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        success, u_keys, d_keys = self.process_nested_json(item, new_machine_id, new_session_id)
                        if success:
                            updated_keys += u_keys
                            deleted_keys += d_keys
                            modified = True
        
        return modified, updated_keys, deleted_keys
    
    def process_sqlite_file(self, file_path):
        """Process SQLite file to reset telemetry IDs."""
        try:
            conn = sqlite3.connect(file_path)
            cursor = conn.cursor()
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            updated_keys = 0
            deleted_keys = 0
            
            for table in tables:
                table_name = table[0]
                
                # Get columns
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = [column[1] for column in cursor.fetchall()]
                
                # Check for telemetry columns
                for key in self.telemetry_keys:
                    if key in columns:
                        new_id = str(uuid.uuid4())
                        cursor.execute(f"UPDATE {table_name} SET {key} = ? WHERE {key} IS NOT NULL", (new_id,))
                        updated_keys += cursor.rowcount
                
                # Check for session columns
                for key in self.session_keys:
                    if key in columns:
                        cursor.execute(f"DELETE FROM {table_name} WHERE {key} IS NOT NULL")
                        deleted_keys += cursor.rowcount
            
            conn.commit()
            conn.close()
            return True, updated_keys, deleted_keys
        except Exception:
            return False, 0, 0
    
    def find_database_files(self, app_path):
        """Find database files in the application path."""
        result = []
        for root, _, files in os.walk(app_path):
            for file in files:
                if file.endswith(('.vscdb', '.db', '.sqlite', '.sqlite3')):
                    result.append(os.path.join(root, file))
        return result
    
    def reset_database(self, db_path):
        """Reset database tables."""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            record_count = 0
            
            for table in tables:
                table_name = table[0]
                
                # Skip sqlite system tables
                if table_name.startswith('sqlite_'):
                    continue
                
                # Count records
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                record_count += count
                
                # Delete all records
                cursor.execute(f"DELETE FROM {table_name}")
            
            conn.commit()
            conn.close()
            return True, record_count
        except Exception:
            return False, 0
    
    def clean_directory(self, directory):
        """Clean a directory by removing all contents."""
        try:
            for item in os.listdir(directory):
                path = os.path.join(directory, item)
                if os.path.isfile(path):
                    os.unlink(path)
                elif os.path.isdir(path):
                    shutil.rmtree(path)
            return True
        except Exception:
            return False
