"""Path utilities for SurfManager - Handle PyInstaller bundled paths."""
import os
import sys
import subprocess
from pathlib import Path


def get_resource_path(relative_path: str) -> Path:
    """Get absolute path to resource, works for dev and PyInstaller.
    
    Args:
        relative_path: Relative path from project root (e.g., 'app/config/reset.json')
        
    Returns:
        Absolute Path object
    """
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        base_path = sys._MEIPASS
        return Path(base_path) / relative_path
    else:
        # Running as script - get project root
        current_file = Path(__file__)
        project_root = current_file.parents[2]  # Go up 2 levels from app/core/
        return project_root / relative_path


def open_folder_in_explorer(folder_path: str) -> bool:
    """Open folder in Windows Explorer.
    
    Args:
        folder_path: Path to folder to open
        
    Returns:
        True if successful, False otherwise
    """
    try:
        if not os.path.exists(folder_path):
            return False
        
        # Use Popen to avoid blocking
        subprocess.Popen(['explorer', folder_path])
        return True
    except Exception:
        return False


def ensure_directory(directory_path: str) -> bool:
    """Ensure directory exists, create if not.
    
    Args:
        directory_path: Path to directory
        
    Returns:
        True if directory exists or was created, False on error
    """
    try:
        os.makedirs(directory_path, exist_ok=True)
        return True
    except Exception:
        return False
