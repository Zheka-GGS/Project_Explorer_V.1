"""Security utilities for path validation and file operations."""

import os
import re
from pathlib import Path
from typing import Tuple, Optional, Set, List
from models import SafetyClassification
from utils.logging_utils import get_logger

logger = get_logger(__name__)


# Security patterns - moved from globals
SAFE_EXTENSIONS = {
    '.tmp', '.bak', '.temp', '.cache', '.crdownload', '.part', '.downloading', '.~tmp'
}

SAFE_DIRECTORIES = {
    'pycache', '.cache', '.pytest_cache', '.mypy_cache', 'node_modules', 'Cache'
}

SAFE_PATH_SEGMENTS = {
    'temp', 'tmp', 'cache', 'downloads', '$Recycle.Bin', '.cache'
}

CRITICAL_DIRECTORIES = {
    'Windows', 'System32', 'SysWOW64', 'Program Files', 'Program Files (x86)',
    'ProgramData', 'Recovery', 'Boot', 'WinSxS', 'etc', 'bin', 'lib', 'sbin', 'var'
}

CRITICAL_PATH_PREFIXES = {
    'C:\\Windows', 'C:\\System32', 'C:\\Program Files', 'C:\\ProgramData',
    '/usr/bin', '/usr/lib', '/etc', '/System', '/Library', '/bin', '/sbin', '/var'
}

CRITICAL_EXTENSIONS = {'.dll', '.sys', '.exe', '.vbs', '.bat', '.ps1', '.com'}

DANGEROUS_FILENAME_CHARS = {'/', '\\', ':', '*', '?', '"', '<', '>', '|'}

MAX_PATH_LENGTH = 260  # Windows MAX_PATH
MAX_FILENAME_LENGTH = 255


class PathValidator:
    """Validates file paths for security risks."""
    
    @staticmethod
    def is_valid_path(path: str, allow_relative: bool = False) -> Tuple[bool, str]:
        """Validate if path is safe to use.
        
        Args:
            path: Path to validate
            allow_relative: Whether to allow relative paths
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(path, str) or not path:
            return False, "Path must be a non-empty string"

        if '\0' in path:
            return False, "Path contains invalid null byte"

        if len(path) > MAX_PATH_LENGTH:
            return False, f"Path exceeds maximum length ({MAX_PATH_LENGTH})"

        if not allow_relative and not os.path.isabs(path):
            return False, "Path must be absolute"

        # Normalize to absolute path
        try:
            abs_path = os.path.abspath(path)
        except (ValueError, OSError) as e:
            return False, f"Invalid path: {e}"

        # Check for path traversal attempts
        try:
            if '..' in [segment for segment in path.replace('\\', '/').split('/') if segment]:
                return False, "Path traversal segments are not allowed"

            resolved = os.path.realpath(abs_path)
            if resolved != abs_path:
                logger.debug(f"Resolved path differs from normalized path: {abs_path} -> {resolved}")
        except (ValueError, OSError):
            pass

        return True, ""
    
    @staticmethod
    def validate_destination(src: str, dest: str) -> Tuple[bool, str]:
        """Validate copy/move destination to prevent path traversal.
        
        Args:
            src: Source path
            dest: Destination path
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Validate source exists
        if not os.path.exists(src):
            return False, "Source does not exist"

        dest_dir = dest if os.path.isdir(dest) else os.path.dirname(dest)
        if not dest_dir:
            return False, "Invalid destination"

        dest_dir = os.path.abspath(dest_dir)
        if not os.path.isdir(dest_dir):
            return False, "Destination directory does not exist"

        try:
            abs_dest = os.path.abspath(dest)
            if not is_path_within_directory(abs_dest, dest_dir):
                return False, "Destination escapes the target directory"
        except Exception as e:
            logger.warning(f"Could not validate destination: {e}")
            return False, f"Destination validation failed: {e}"

        return True, ""
    
    @staticmethod
    def validate_rename(old_path: str, new_name: str) -> Tuple[bool, str]:
        """Validate filename for rename operation.
        
        Args:
            old_path: Full path to file
            new_name: New filename only (no path)
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(new_name, str) or not new_name:
            return False, "New name must be non-empty string"
        
        if len(new_name) > MAX_FILENAME_LENGTH:
            return False, f"Filename too long (max {MAX_FILENAME_LENGTH} chars)"
        
        if len(new_name) == 0:
            return False, "Filename cannot be empty"
        
        # Check for dangerous characters
        dangerous = DANGEROUS_FILENAME_CHARS & set(new_name)
        if dangerous:
            return False, f"Invalid characters in filename: {', '.join(dangerous)}"
        
        # Check for null bytes
        if '\0' in new_name:
            return False, "Filename cannot contain null bytes"
        
        # Check for reserved names (Windows)
        reserved_names = {'CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4',
                         'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2',
                         'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'}
        
        if new_name.upper() in reserved_names or new_name.upper().split('.')[0] in reserved_names:
            return False, f"'{new_name}' is a reserved filename (Windows)"
        
        return True, ""


class FileClassifier:
    """Classifies files by safety level."""
    
    @staticmethod
    def classify_safety(path: str) -> SafetyClassification:
        """Classify file/directory safety level.
        
        Args:
            path: Full path to file or directory
            
        Returns:
            SafetyClassification enum value
        """
        try:
            path_lower = os.path.normpath(path).lower()
            filename = os.path.basename(path)
            _, ext = os.path.splitext(filename)
            
            # Check if critical
            if FileClassifier._is_critical(path_lower, filename, ext):
                return SafetyClassification.CRITICAL
            
            # Check if system removable
            if FileClassifier._is_system_removable(path_lower, filename):
                return SafetyClassification.SYSTEM_REMOVABLE
            
            # Check if safe
            if FileClassifier._is_safe(path_lower, filename, ext):
                return SafetyClassification.SAFE
            
            return SafetyClassification.UNKNOWN
            
        except Exception as e:
            logger.warning(f"Error classifying {path}: {e}")
            return SafetyClassification.UNKNOWN
    
    @staticmethod
    def _is_critical(path_lower: str, filename: str, ext: str) -> bool:
        """Check if file is critical system file."""
        # Critical extensions
        if ext.lower() in CRITICAL_EXTENSIONS:
            return True
        
        # Critical directories
        if filename in CRITICAL_DIRECTORIES:
            return True
        
        # Critical path prefixes
        for prefix in CRITICAL_PATH_PREFIXES:
            if path_lower.startswith(prefix.lower()):
                return True
        
        return False
    
    @staticmethod
    def _is_system_removable(path_lower: str, filename: str) -> bool:
        """Check if file is system-removable."""
        removable_names = {
            'Windows.old', 'Prefetch', '$WINDOWS.~BT', 'installer', 'backup'
        }
        
        if filename in removable_names:
            return True
        
        path_parts = path_lower.split(os.sep)
        removable_parts = {'windows.old', 'prefetch', 'installer_cache', 'old_windows'}
        
        return any(part in removable_parts for part in path_parts)
    
    @staticmethod
    def _is_safe(path_lower: str, filename: str, ext: str) -> bool:
        """Check if file is safe."""
        # Safe extensions
        if ext.lower() in SAFE_EXTENSIONS:
            return True
        
        # Safe directory names
        if filename in SAFE_DIRECTORIES:
            return True
        
        # Safe path segments
        path_parts = path_lower.split(os.sep)
        return any(part in SAFE_PATH_SEGMENTS for part in path_parts)
    
    @staticmethod
    def is_locked_file(file_path: str) -> bool:
        """Check if file is currently locked (opened by another process).
        
        Args:
            file_path: Path to check
            
        Returns:
            True if file appears to be locked
        """
        if not os.path.exists(file_path):
            return False
        
        # Try to open file exclusively (on Windows) or for writing
        try:
            if hasattr(os, 'open'):
                # Unix-like
                try:
                    fd = os.open(file_path, os.O_WRONLY | os.O_EXCL)
                    os.close(fd)
                    return False
                except (OSError, IOError):
                    return True
            else:
                # Windows - try opening with exclusive access
                import msvcrt
                try:
                    handle = open(file_path, 'a')
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                    handle.close()
                    return False
                except (IOError, OSError):
                    return True
        except Exception as e:
            logger.warning(f"Could not check lock status of {file_path}: {e}")
        
        return False


def is_symlink(path: str) -> bool:
    """Check if path is a symbolic link.
    
    Args:
        path: Path to check
        
    Returns:
        True if path is a symlink
    """
    try:
        return os.path.islink(path)
    except (OSError, ValueError):
        return False


def safe_realpath(path: str) -> Optional[str]:
    """Safely resolve real path of a file, including symlinks.
    
    Args:
        path: Path to resolve
        
    Returns:
        Real path if successful, None otherwise
    """
    try:
        return os.path.realpath(path)
    except (OSError, ValueError) as e:
        logger.warning(f"Could not resolve real path of {path}: {e}")
        return None


def is_path_within_directory(file_path: str, directory: str) -> bool:
    """Check if file_path is within directory (including subdirectories).
    
    Args:
        file_path: Full path to file
        directory: Base directory path
        
    Returns:
        True if file_path is within or equal to directory
    """
    try:
        real_file = os.path.realpath(file_path)
        real_dir = os.path.realpath(directory)
        
        # Normalize paths
        real_file = os.path.normpath(real_file)
        real_dir = os.path.normpath(real_dir)
        
        # Check if file is within directory
        return real_file.startswith(real_dir + os.sep) or real_file == real_dir
    except (OSError, ValueError):
        return False
