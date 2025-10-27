"""Centralized logging system for SurfManager."""
import logging
import sys
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Optional


class SurfManagerLogger:
    """Centralized logger for SurfManager application."""
    
    _instance: Optional['SurfManagerLogger'] = None
    _initialized = False
    
    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize logger (only once)."""
        if SurfManagerLogger._initialized:
            return
        
        # Setup log directory
        self.log_dir = Path.home() / ".surfmanager" / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create logger
        self.logger = logging.getLogger('SurfManager')
        self.logger.setLevel(logging.DEBUG)
        
        # Prevent duplicate handlers
        if self.logger.handlers:
            return
        
        # File handler - rotating log files (max 5MB, keep 5 backups)
        log_file = self.log_dir / "surfmanager.log"
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        # Console handler - only warnings and above
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.WARNING)
        console_formatter = logging.Formatter(
            '%(levelname)s: %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # Error file handler - separate file for errors only
        error_file = self.log_dir / "errors.log"
        error_handler = RotatingFileHandler(
            error_file,
            maxBytes=5 * 1024 * 1024,
            backupCount=3,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        self.logger.addHandler(error_handler)
        
        SurfManagerLogger._initialized = True
        self.logger.info("=" * 80)
        self.logger.info(f"SurfManager Logger initialized - {datetime.now()}")
        self.logger.info("=" * 80)
    
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self.logger.debug(message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message."""
        self.logger.info(message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self.logger.warning(message, **kwargs)
    
    def error(self, message: str, exc_info=False, **kwargs):
        """Log error message."""
        self.logger.error(message, exc_info=exc_info, **kwargs)
    
    def critical(self, message: str, exc_info=True, **kwargs):
        """Log critical message."""
        self.logger.critical(message, exc_info=exc_info, **kwargs)
    
    def exception(self, message: str, **kwargs):
        """Log exception with traceback."""
        self.logger.exception(message, **kwargs)
    
    def get_log_file_path(self) -> Path:
        """Get current log file path."""
        return self.log_dir / "surfmanager.log"
    
    def get_error_log_path(self) -> Path:
        """Get error log file path."""
        return self.log_dir / "errors.log"
    
    def clear_old_logs(self, days: int = 30):
        """Clear log files older than specified days."""
        try:
            import time
            current_time = time.time()
            cutoff_time = current_time - (days * 24 * 60 * 60)
            
            for log_file in self.log_dir.glob("*.log*"):
                if log_file.stat().st_mtime < cutoff_time:
                    log_file.unlink()
                    self.info(f"Deleted old log file: {log_file.name}")
        except Exception as e:
            self.error(f"Failed to clear old logs: {e}")


# Global logger instance
_logger = None

def get_logger() -> SurfManagerLogger:
    """Get global logger instance."""
    global _logger
    if _logger is None:
        _logger = SurfManagerLogger()
    return _logger


# Convenience functions
def log_debug(message: str, **kwargs):
    """Log debug message."""
    get_logger().debug(message, **kwargs)

def log_info(message: str, **kwargs):
    """Log info message."""
    get_logger().info(message, **kwargs)

def log_warning(message: str, **kwargs):
    """Log warning message."""
    get_logger().warning(message, **kwargs)

def log_error(message: str, exc_info=False, **kwargs):
    """Log error message."""
    get_logger().error(message, exc_info=exc_info, **kwargs)

def log_critical(message: str, exc_info=True, **kwargs):
    """Log critical message."""
    get_logger().critical(message, exc_info=exc_info, **kwargs)

def log_exception(message: str, **kwargs):
    """Log exception with traceback."""
    get_logger().exception(message, **kwargs)
