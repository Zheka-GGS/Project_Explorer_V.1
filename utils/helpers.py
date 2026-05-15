"""Utility helper functions."""

import os
import psutil
from typing import Tuple, Optional


def format_size(size_bytes: int) -> str:
    """Format byte size to human-readable string.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string (e.g., "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def get_app_memory() -> float:
    """Get current application memory usage.
    
    Returns:
        Memory usage in MB
    """
    try:
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / (1024 * 1024)
    except Exception:
        return 0.0


def get_system_memory_info() -> Tuple[float, float, float]:
    """Get system memory information.
    
    Returns:
        Tuple of (total_gb, used_gb, percent)
    """
    try:
        mem = psutil.virtual_memory()
        return (
            mem.total / (1024 ** 3),
            mem.used / (1024 ** 3),
            mem.percent
        )
    except Exception:
        return 0.0, 0.0, 0.0


def get_disk_usage(path: str) -> Optional[Tuple[float, float, float]]:
    """Get disk usage for a path.
    
    Args:
        path: Path to check
        
    Returns:
        Tuple of (total_gb, used_gb, free_gb) or None if error
    """
    try:
        usage = psutil.disk_usage(path)
        return (
            usage.total / (1024 ** 3),
            usage.used / (1024 ** 3),
            usage.free / (1024 ** 3)
        )
    except Exception:
        return None


def escape_shell_special_chars(s: str) -> str:
    """Escape shell special characters.
    
    Args:
        s: String to escape
        
    Returns:
        Escaped string
    """
    special_chars = {'&', '|', ';', '$', '`', '\\', '"', "'", '<', '>', '(', ')'}
    for char in special_chars:
        s = s.replace(char, '\\' + char)
    return s
