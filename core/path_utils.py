"""Path utilities for PyInstaller compatibility."""
import sys
import os


def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller.
    
    Args:
        relative_path (str): Path relative to the application root
        
    Returns:
        str: Absolute path to the resource
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        # Running in development mode
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)


def get_app_dir():
    """Get the application directory.
    
    Returns:
        str: Path to the application directory
    """
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller executable
        return os.path.dirname(sys.executable)
    else:
        # Running in development mode
        return os.path.dirname(os.path.abspath(__file__))


def is_frozen():
    """Check if running as PyInstaller executable.
    
    Returns:
        bool: True if running as executable, False if in development
    """
    return getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')


def get_config_path():
    """Get path to config directory.
    
    Returns:
        str: Path to config directory
    """
    return get_resource_path('config')


def get_data_path(filename):
    """Get path to data file in the appropriate directory.
    
    Args:
        filename (str): Name of the data file
        
    Returns:
        str: Full path to the data file
    """
    if is_frozen():
        # For executable, use the same directory as the exe
        return os.path.join(get_app_dir(), filename)
    else:
        # For development, use the project root
        return os.path.join(get_resource_path('.'), filename)
