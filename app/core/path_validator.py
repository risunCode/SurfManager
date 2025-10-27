"""Path validation utilities for SurfManager."""
import os
import re
from pathlib import Path
from typing import Tuple, Optional


class PathValidator:
    """Validates file paths and user inputs for security and correctness."""
    
    # Dangerous path patterns - simplified, less strict
    DANGEROUS_PATTERNS = [
        r'\.\.[\\/]',  # Parent directory traversal
        r'[<>"|?*]',  # Invalid Windows characters (removed colon - valid for drive letters)
    ]
    
    # Maximum path length (Windows limit)
    MAX_PATH_LENGTH = 260
    
    @staticmethod
    def validate_path(path: str, must_exist: bool = False, 
                     allow_creation: bool = True) -> Tuple[bool, str, Optional[Path]]:
        """Validate a file system path.
        
        Args:
            path: Path string to validate
            must_exist: If True, path must already exist
            allow_creation: If True, allow paths that don't exist but could be created
            
        Returns:
            Tuple of (is_valid, error_message, normalized_path)
        """
        if not path or not isinstance(path, str):
            return False, "Path cannot be empty", None
        
        # Remove extra whitespace
        path = path.strip()
        
        # Check length
        if len(path) > PathValidator.MAX_PATH_LENGTH:
            return False, f"Path too long (max {PathValidator.MAX_PATH_LENGTH} characters)", None
        
        # Check for dangerous patterns
        for pattern in PathValidator.DANGEROUS_PATTERNS:
            match = re.search(pattern, path, re.IGNORECASE)
            if match:
                # Show the actual problematic character/pattern, not the regex
                if pattern == r'[<>"|?*]':
                    return False, f"Path contains invalid characters: {match.group()}", None
                elif pattern == r'\.\.[\\/]':
                    return False, "Path contains parent directory traversal (..)", None
                else:
                    return False, f"Path contains invalid pattern: {match.group()}", None
        
        # Try to normalize path
        try:
            normalized = Path(path).resolve()
        except Exception as e:
            return False, f"Invalid path format: {e}", None
        
        # Check if path exists
        if must_exist and not normalized.exists():
            return False, "Path does not exist", None
        
        # Check if path is accessible
        if normalized.exists():
            try:
                # Try to access the path
                if normalized.is_dir():
                    list(normalized.iterdir())
                elif normalized.is_file():
                    normalized.stat()
            except PermissionError:
                return False, "Permission denied to access path", None
            except Exception as e:
                return False, f"Cannot access path: {e}", None
        elif not allow_creation:
            return False, "Path does not exist and creation not allowed", None
        
        return True, "", normalized
    
    @staticmethod
    def validate_backup_path(path: str) -> Tuple[bool, str]:
        """Validate backup destination path.
        
        Args:
            path: Backup path to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        is_valid, error, normalized = PathValidator.validate_path(
            path, must_exist=False, allow_creation=True
        )
        
        if not is_valid:
            return False, error
        
        # Check if parent directory exists or can be created
        parent = normalized.parent
        if not parent.exists():
            try:
                parent.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                return False, f"Cannot create backup directory: {e}"
        
        # Check write permissions
        try:
            test_file = parent / ".write_test"
            test_file.touch()
            test_file.unlink()
        except Exception as e:
            return False, f"No write permission in backup directory: {e}"
        
        return True, ""
    
    @staticmethod
    def sanitize_filename(filename: str, max_length: int = 255) -> str:
        """Sanitize filename by removing invalid characters.
        
        Args:
            filename: Original filename
            max_length: Maximum filename length
            
        Returns:
            Sanitized filename
        """
        # Remove invalid characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        # Remove control characters
        sanitized = ''.join(char for char in sanitized if ord(char) >= 32)
        
        # Trim whitespace
        sanitized = sanitized.strip()
        
        # Ensure not empty
        if not sanitized:
            sanitized = "unnamed"
        
        # Truncate if too long
        if len(sanitized) > max_length:
            name, ext = os.path.splitext(sanitized)
            max_name_len = max_length - len(ext)
            sanitized = name[:max_name_len] + ext
        
        return sanitized
    
    @staticmethod
    def is_safe_to_delete(path: str) -> Tuple[bool, str]:
        """Check if path is safe to delete.
        
        Args:
            path: Path to check
            
        Returns:
            Tuple of (is_safe, warning_message)
        """
        try:
            normalized = Path(path).resolve()
        except Exception as e:
            return False, f"Invalid path: {e}"
        
        # Don't allow deleting system directories
        dangerous_paths = [
            Path.home(),
            Path.home() / "Documents",
            Path.home() / "Desktop",
            Path.home() / "Downloads",
            Path("C:\\Windows"),
            Path("C:\\Program Files"),
            Path("C:\\Program Files (x86)"),
        ]
        
        for dangerous in dangerous_paths:
            try:
                if normalized == dangerous.resolve() or normalized in dangerous.resolve().parents:
                    return False, f"Cannot delete system/important directory: {dangerous}"
            except (OSError, RuntimeError):
                pass  # Path resolution may fail for some directories
        
        return True, ""
