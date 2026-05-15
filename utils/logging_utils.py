"""Logging configuration and utilities."""

import logging
import os
from typing import Optional
from pathlib import Path
from datetime import datetime


def setup_logging(
    log_dir: Optional[str] = None,
    log_level: int = logging.INFO,
    enable_file: bool = True,
    enable_console: bool = True
) -> logging.Logger:
    """Set up application logging.
    
    Args:
        log_dir: Directory for log files. Defaults to user home/.explorer_pro/logs
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        enable_file: Whether to log to file
        enable_console: Whether to log to console
        
    Returns:
        Configured logger instance
        
    Example:
        logger = setup_logging(log_level=logging.DEBUG)
        logger.info("Application started")
    """
    if log_dir is None:
        log_dir = os.path.join(os.path.expanduser("~"), ".explorer_pro", "logs")
    
    os.makedirs(log_dir, exist_ok=True)
    
    logger = logging.getLogger("ProjectExplorerPro")
    logger.setLevel(log_level)
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # File handler
    if enable_file:
        log_file = os.path.join(log_dir, f"app_{datetime.now().strftime('%Y%m%d')}.log")
        try:
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except (IOError, OSError) as e:
            logger.warning(f"Could not create log file {log_file}: {e}")
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get or create a named logger.
    
    Args:
        name: Logger name (typically __name__ of module)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class AuditLogger:
    """Dedicated logger for security-related operations."""
    
    def __init__(self, log_dir: Optional[str] = None):
        """Initialize audit logger.
        
        Args:
            log_dir: Directory for audit logs
        """
        if log_dir is None:
            log_dir = os.path.join(os.path.expanduser("~"), ".explorer_pro", "audit")
        
        os.makedirs(log_dir, exist_ok=True)
        self.log_dir = log_dir
        self.logger = logging.getLogger("ProjectExplorerPro.Audit")
        self.logger.setLevel(logging.INFO)
        self.logger.handlers.clear()
        
        # Audit file handler (separate from main logs)
        audit_file = os.path.join(log_dir, f"audit_{datetime.now().strftime('%Y%m%d')}.log")
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        try:
            file_handler = logging.FileHandler(audit_file, encoding='utf-8')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        except (IOError, OSError) as e:
            logging.error(f"Could not create audit log: {e}")
    
    def log_delete(self, file_path: str, success: bool, reason: str = "") -> None:
        """Log file deletion."""
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(f"DELETE {status}: {file_path} | Reason: {reason}")
    
    def log_rename(self, old_path: str, new_path: str, success: bool) -> None:
        """Log file rename."""
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(f"RENAME {status}: {old_path} -> {new_path}")
    
    def log_paste(self, source: str, destination: str, success: bool) -> None:
        """Log copy/cut/paste operation."""
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(f"PASTE {status}: {source} -> {destination}")
    
    def log_execute(self, file_path: str, success: bool, reason: str = "") -> None:
        """Log file execution."""
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(f"EXECUTE {status}: {file_path} | Reason: {reason}")
    
    def log_access_denied(self, file_path: str, operation: str) -> None:
        """Log denied access."""
        self.logger.warning(f"ACCESS_DENIED: {operation} on {file_path}")
    
    def log_security_warning(self, message: str) -> None:
        """Log security-related warning."""
        self.logger.warning(f"SECURITY_WARNING: {message}")
