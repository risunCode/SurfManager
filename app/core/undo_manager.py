"""Undo/Redo functionality for destructive operations."""
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass, asdict


@dataclass
class UndoAction:
    """Represents an undoable action."""
    action_type: str  # 'delete', 'reset', 'modify'
    timestamp: str
    app_name: str
    backup_path: str
    original_path: str
    description: str
    metadata: Dict = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)
    
    @staticmethod
    def from_dict(data: Dict) -> 'UndoAction':
        """Create from dictionary."""
        return UndoAction(**data)


class UndoManager:
    """Manages undo/redo operations for destructive actions."""
    
    def __init__(self, max_undo_history: int = 10):
        """Initialize undo manager.
        
        Args:
            max_undo_history: Maximum number of undo actions to keep
        """
        self.max_undo_history = max_undo_history
        self.undo_stack: List[UndoAction] = []
        self.redo_stack: List[UndoAction] = []
        
        # Undo storage location
        self.undo_dir = Path.home() / ".surfmanager" / "undo"
        self.undo_dir.mkdir(parents=True, exist_ok=True)
        
        # Load undo history
        self._load_history()
    
    def _load_history(self):
        """Load undo history from disk."""
        history_file = self.undo_dir / "undo_history.json"
        if history_file.exists():
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.undo_stack = [UndoAction.from_dict(item) for item in data.get('undo', [])]
                    self.redo_stack = [UndoAction.from_dict(item) for item in data.get('redo', [])]
            except Exception as e:
                print(f"Warning: Failed to load undo history: {e}")
    
    def _save_history(self):
        """Save undo history to disk."""
        history_file = self.undo_dir / "undo_history.json"
        try:
            data = {
                'undo': [action.to_dict() for action in self.undo_stack],
                'redo': [action.to_dict() for action in self.redo_stack]
            }
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save undo history: {e}")
    
    def create_backup_before_action(self, action_type: str, app_name: str, 
                                   original_path: str, description: str,
                                   metadata: Optional[Dict] = None) -> Optional[UndoAction]:
        """Create backup before performing destructive action.
        
        Args:
            action_type: Type of action ('delete', 'reset', 'modify')
            app_name: Name of the application
            original_path: Path that will be modified
            description: Human-readable description
            metadata: Optional metadata
            
        Returns:
            UndoAction if successful, None otherwise
        """
        try:
            # Create backup
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{app_name}_{action_type}_{timestamp}"
            backup_path = self.undo_dir / backup_name
            
            # Copy data to backup
            original = Path(original_path)
            if original.exists():
                if original.is_dir():
                    shutil.copytree(original, backup_path, dirs_exist_ok=True)
                else:
                    shutil.copy2(original, backup_path)
                
                # Create undo action
                action = UndoAction(
                    action_type=action_type,
                    timestamp=timestamp,
                    app_name=app_name,
                    backup_path=str(backup_path),
                    original_path=original_path,
                    description=description,
                    metadata=metadata or {}
                )
                
                return action
            else:
                print(f"Warning: Original path doesn't exist: {original_path}")
                return None
                
        except Exception as e:
            print(f"Error creating backup: {e}")
            return None
    
    def push_action(self, action: UndoAction):
        """Push action to undo stack.
        
        Args:
            action: The action to push
        """
        self.undo_stack.append(action)
        
        # Clear redo stack when new action is performed
        self.redo_stack.clear()
        
        # Limit stack size
        if len(self.undo_stack) > self.max_undo_history:
            # Remove oldest action and its backup
            old_action = self.undo_stack.pop(0)
            self._cleanup_backup(old_action.backup_path)
        
        self._save_history()
    
    def can_undo(self) -> bool:
        """Check if undo is available."""
        return len(self.undo_stack) > 0
    
    def can_redo(self) -> bool:
        """Check if redo is available."""
        return len(self.redo_stack) > 0
    
    def undo(self, progress_callback: Optional[Callable] = None) -> tuple[bool, str]:
        """Undo last action.
        
        Args:
            progress_callback: Optional callback for progress updates
            
        Returns:
            Tuple of (success, message)
        """
        if not self.can_undo():
            return False, "No actions to undo"
        
        action = self.undo_stack.pop()
        
        try:
            if progress_callback:
                progress_callback(f"Undoing: {action.description}")
            
            # Restore from backup
            backup_path = Path(action.backup_path)
            original_path = Path(action.original_path)
            
            if not backup_path.exists():
                return False, f"Backup not found: {backup_path}"
            
            # Remove current state
            if original_path.exists():
                if original_path.is_dir():
                    shutil.rmtree(original_path)
                else:
                    original_path.unlink()
            
            # Restore backup
            if backup_path.is_dir():
                shutil.copytree(backup_path, original_path)
            else:
                shutil.copy2(backup_path, original_path)
            
            # Move to redo stack
            self.redo_stack.append(action)
            self._save_history()
            
            if progress_callback:
                progress_callback(f"✅ Undo completed: {action.description}")
            
            return True, f"Undone: {action.description}"
            
        except Exception as e:
            # Restore action to undo stack if failed
            self.undo_stack.append(action)
            return False, f"Undo failed: {e}"
    
    def redo(self, progress_callback: Optional[Callable] = None) -> tuple[bool, str]:
        """Redo last undone action.
        
        Args:
            progress_callback: Optional callback for progress updates
            
        Returns:
            Tuple of (success, message)
        """
        if not self.can_redo():
            return False, "No actions to redo"
        
        action = self.redo_stack.pop()
        
        try:
            if progress_callback:
                progress_callback(f"Redoing: {action.description}")
            
            # Re-apply the action (delete/reset)
            original_path = Path(action.original_path)
            
            if original_path.exists():
                if original_path.is_dir():
                    shutil.rmtree(original_path)
                else:
                    original_path.unlink()
            
            # Move back to undo stack
            self.undo_stack.append(action)
            self._save_history()
            
            if progress_callback:
                progress_callback(f"✅ Redo completed: {action.description}")
            
            return True, f"Redone: {action.description}"
            
        except Exception as e:
            # Restore action to redo stack if failed
            self.redo_stack.append(action)
            return False, f"Redo failed: {e}"
    
    def get_undo_description(self) -> Optional[str]:
        """Get description of action that would be undone."""
        if self.can_undo():
            return self.undo_stack[-1].description
        return None
    
    def get_redo_description(self) -> Optional[str]:
        """Get description of action that would be redone."""
        if self.can_redo():
            return self.redo_stack[-1].description
        return None
    
    def clear_history(self):
        """Clear all undo/redo history and cleanup backups."""
        for action in self.undo_stack + self.redo_stack:
            self._cleanup_backup(action.backup_path)
        
        self.undo_stack.clear()
        self.redo_stack.clear()
        self._save_history()
    
    def _cleanup_backup(self, backup_path: str):
        """Remove backup files.
        
        Args:
            backup_path: Path to backup to remove
        """
        try:
            path = Path(backup_path)
            if path.exists():
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()
        except Exception as e:
            print(f"Warning: Failed to cleanup backup {backup_path}: {e}")
    
    def get_history_size(self) -> int:
        """Get total size of undo history in bytes."""
        total_size = 0
        for action in self.undo_stack + self.redo_stack:
            try:
                path = Path(action.backup_path)
                if path.exists():
                    if path.is_dir():
                        total_size += sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
                    else:
                        total_size += path.stat().st_size
            except Exception:
                pass
        return total_size
