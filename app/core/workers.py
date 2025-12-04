"""Background workers for long-running operations.

Prevents UI freeze during backup, restore, and reset operations.
"""
import os
import shutil
from PyQt6.QtCore import QObject, QThread, pyqtSignal


class BackupWorker(QObject):
    """Worker for backup operations in background thread."""
    
    # Signals
    progress = pyqtSignal(int, str)  # (percentage, message)
    log = pyqtSignal(str)  # log message
    finished = pyqtSignal(bool, str)  # (success, message)
    
    def __init__(self, source_path: str, backup_folder: str, backup_items: list, addon_paths: list = None):
        super().__init__()
        self.source_path = source_path
        self.backup_folder = backup_folder
        self.backup_items = backup_items
        self.addon_paths = addon_paths or []
        self._cancelled = False
    
    def cancel(self):
        """Cancel the operation."""
        self._cancelled = True
    
    def run(self):
        """Execute backup operation."""
        try:
            os.makedirs(self.backup_folder, exist_ok=True)
            
            if self.backup_items:
                # Use specific backup items
                total_items = len(self.backup_items)
                self.log.emit(f"Backing up {total_items} items...")
                
                for i, item in enumerate(self.backup_items):
                    if self._cancelled:
                        self.finished.emit(False, "Cancelled")
                        return
                    
                    item_path = item.get('path', '')
                    if not item_path:
                        continue
                    
                    src = os.path.join(self.source_path, item_path)
                    dst = os.path.join(self.backup_folder, item_path)
                    
                    if os.path.exists(src):
                        if os.path.isdir(src):
                            os.makedirs(os.path.dirname(dst) if '/' in item_path else self.backup_folder, exist_ok=True)
                            shutil.copytree(src, dst, dirs_exist_ok=True)
                        else:
                            os.makedirs(os.path.dirname(dst) if '/' in item_path else self.backup_folder, exist_ok=True)
                            shutil.copy2(src, dst)
                        self.log.emit(f"  [OK] {item_path}")
                    elif not item.get('optional', False):
                        self.log.emit(f"  [SKIP] {item_path} (not found)")
                    
                    progress = 30 + int((i + 1) / total_items * 50)
                    self.progress.emit(progress, f"Copying {item_path}...")
            else:
                # Fallback: copy all
                items = os.listdir(self.source_path)
                total_items = len(items)
                self.log.emit(f"Backing up {total_items} items (full)...")
                
                for i, item in enumerate(items):
                    if self._cancelled:
                        self.finished.emit(False, "Cancelled")
                        return
                    
                    src = os.path.join(self.source_path, item)
                    dst = os.path.join(self.backup_folder, item)
                    if os.path.isdir(src):
                        shutil.copytree(src, dst, dirs_exist_ok=True)
                    else:
                        shutil.copy2(src, dst)
                    
                    progress = 30 + int((i + 1) / total_items * 50)
                    self.progress.emit(progress, f"Copying {item}...")
            
            # Backup addon folders
            if self.addon_paths:
                self.log.emit(f"Backing up {len(self.addon_paths)} addon folder(s)...")
                addon_backup_dir = os.path.join(self.backup_folder, "_addons")
                os.makedirs(addon_backup_dir, exist_ok=True)
                
                for j, addon_path in enumerate(self.addon_paths):
                    if self._cancelled:
                        self.finished.emit(False, "Cancelled")
                        return
                    
                    if os.path.exists(addon_path):
                        addon_name = os.path.basename(addon_path)
                        addon_dst = os.path.join(addon_backup_dir, addon_name)
                        try:
                            if os.path.isdir(addon_path):
                                shutil.copytree(addon_path, addon_dst, dirs_exist_ok=True)
                            else:
                                shutil.copy2(addon_path, addon_dst)
                            self.log.emit(f"  [OK] Addon: {addon_name}")
                        except Exception as e:
                            self.log.emit(f"  [FAIL] Addon: {addon_name} - {e}")
                    
                    progress = 80 + int((j + 1) / len(self.addon_paths) * 15)
                    self.progress.emit(progress, f"Addon: {addon_name}...")
            
            self.progress.emit(100, "Backup complete!")
            self.finished.emit(True, "Backup complete")
            
        except Exception as e:
            self.finished.emit(False, str(e))


class RestoreWorker(QObject):
    """Worker for restore operations in background thread."""
    
    # Signals
    progress = pyqtSignal(int, str)
    log = pyqtSignal(str)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, backup_folder: str, target_path: str, addon_paths: list = None):
        super().__init__()
        self.backup_folder = backup_folder
        self.target_path = target_path
        self.addon_paths = addon_paths or []
        self._cancelled = False
    
    def cancel(self):
        self._cancelled = True
    
    def run(self):
        """Execute restore operation."""
        try:
            # Remove existing data
            self.progress.emit(10, "Removing existing data...")
            if os.path.exists(self.target_path):
                for item in os.listdir(self.target_path):
                    if self._cancelled:
                        self.finished.emit(False, "Cancelled")
                        return
                    
                    item_path = os.path.join(self.target_path, item)
                    try:
                        if os.path.isdir(item_path):
                            shutil.rmtree(item_path)
                        else:
                            os.remove(item_path)
                    except PermissionError:
                        self.log.emit(f"  [WARN] Cannot delete: {item}")
            
            # Copy backup data
            self.progress.emit(30, "Restoring data...")
            items = [f for f in os.listdir(self.backup_folder) if f != "_addons"]
            total_items = len(items)
            
            for i, item in enumerate(items):
                if self._cancelled:
                    self.finished.emit(False, "Cancelled")
                    return
                
                src = os.path.join(self.backup_folder, item)
                dst = os.path.join(self.target_path, item)
                
                if os.path.isdir(src):
                    shutil.copytree(src, dst, dirs_exist_ok=True)
                else:
                    shutil.copy2(src, dst)
                
                progress = 30 + int((i + 1) / total_items * 50)
                self.progress.emit(progress, f"Restoring {item}...")
            
            # Restore addon folders
            addon_backup_dir = os.path.join(self.backup_folder, "_addons")
            if os.path.exists(addon_backup_dir) and self.addon_paths:
                self.log.emit(f"Restoring {len(self.addon_paths)} addon folder(s)...")
                
                for j, addon_path in enumerate(self.addon_paths):
                    if self._cancelled:
                        self.finished.emit(False, "Cancelled")
                        return
                    
                    addon_name = os.path.basename(addon_path)
                    addon_src = os.path.join(addon_backup_dir, addon_name)
                    
                    if os.path.exists(addon_src):
                        try:
                            if os.path.exists(addon_path):
                                shutil.rmtree(addon_path)
                            
                            if os.path.isdir(addon_src):
                                shutil.copytree(addon_src, addon_path)
                            else:
                                os.makedirs(os.path.dirname(addon_path), exist_ok=True)
                                shutil.copy2(addon_src, addon_path)
                            
                            self.log.emit(f"  [OK] Addon restored: {addon_name}")
                        except Exception as e:
                            self.log.emit(f"  [FAIL] Addon: {addon_name} - {e}")
                    
                    progress = 80 + int((j + 1) / len(self.addon_paths) * 15)
                    self.progress.emit(progress, f"Addon: {addon_name}...")
            
            self.progress.emit(100, "Restore complete!")
            self.finished.emit(True, "Restore complete")
            
        except Exception as e:
            self.finished.emit(False, str(e))


def run_in_thread(worker: QObject) -> QThread:
    """Helper to run a worker in a background thread."""
    thread = QThread()
    worker.moveToThread(thread)
    
    # Connect signals
    thread.started.connect(worker.run)
    worker.finished.connect(thread.quit)
    worker.finished.connect(worker.deleteLater)
    thread.finished.connect(thread.deleteLater)
    
    return thread
