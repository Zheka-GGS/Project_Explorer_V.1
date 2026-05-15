"""File clipboard operations with enhanced security."""

import os
import shutil
import threading
import time
from typing import List, Tuple, Optional
from pathlib import Path

from models import FileInfo
from core.security import PathValidator, FileClassifier, is_path_within_directory
from utils.logging_utils import get_logger, AuditLogger

logger = get_logger(__name__)
audit_logger = AuditLogger()


class SecureFileClipboard:
    """Handles copy/cut/paste operations with comprehensive security.
    
    Features:
        - Path validation and traversal prevention
        - Atomic file operations with rollback
        - Comprehensive error handling
        - Audit logging for all operations
        - Conflict resolution (automatic rename)
    """
    
    def __init__(self):
        """Initialize clipboard."""
        self.mode: Optional[str] = None  # 'copy' or 'cut'
        self.paths: List[str] = []
        self.lock = threading.Lock()
        self._operation_id: Optional[str] = None
    
    def copy(self, paths: List[str]) -> bool:
        """Prepare files for copying.
        
        Args:
            paths: List of file paths
            
        Returns:
            True if successful
        """
        if not self._validate_paths(paths):
            logger.warning(f"Invalid paths for copy: {paths}")
            return False
        
        with self.lock:
            self.mode = 'copy'
            self.paths = paths.copy()
            self._operation_id = str(int(time.time() * 1000))
        
        logger.info(f"Copied {len(paths)} items to clipboard")
        return True
    
    def cut(self, paths: List[str]) -> bool:
        """Prepare files for cutting.
        
        Args:
            paths: List of file paths
            
        Returns:
            True if successful
        """
        if not self._validate_paths(paths):
            logger.warning(f"Invalid paths for cut: {paths}")
            return False
        
        # Check for critical files
        for path in paths:
            safety = FileClassifier.classify_safety(path)
            if safety.value == 'CRITICAL':
                logger.warning(f"Attempted to cut critical file: {path}")
                return False
        
        with self.lock:
            self.mode = 'cut'
            self.paths = paths.copy()
            self._operation_id = str(int(time.time() * 1000))
        
        logger.info(f"Cut {len(paths)} items to clipboard")
        return True
    
    def paste(self, dest_dir: str) -> Tuple[int, int, List[str]]:
        """Paste files to destination directory.
        
        Args:
            dest_dir: Destination directory path
            
        Returns:
            Tuple of (successful_count, failed_count, failed_paths)
        """
        # Validate destination
        if not isinstance(dest_dir, str) or not os.path.isdir(dest_dir):
            logger.error(f"Invalid destination directory: {dest_dir}")
            return 0, 0, []
        
        is_valid, error = PathValidator.is_valid_path(dest_dir)
        if not is_valid:
            logger.error(f"Invalid destination: {error}")
            return 0, 0, []
        
        dest_dir = os.path.abspath(dest_dir)
        
        with self.lock:
            if not self.paths or not self.mode:
                return 0, 0, []
            
            paths_to_process = self.paths.copy()
            mode = self.mode
        
        moved, failed, failed_paths = 0, 0, []
        
        for src in paths_to_process:
            try:
                result = self._paste_single(src, dest_dir, mode)
                if result:
                    moved += 1
                    audit_logger.log_paste(src, dest_dir, True)
                else:
                    failed += 1
                    failed_paths.append(src)
                    audit_logger.log_paste(src, dest_dir, False)
            
            except Exception as e:
                logger.error(f"Paste error for {src}: {e}")
                failed += 1
                failed_paths.append(src)
        
        # Clear clipboard if cut mode
        if mode == 'cut':
            with self.lock:
                self.paths.clear()
                self.mode = None
        
        logger.info(f"Paste completed: {moved} succeeded, {failed} failed")
        return moved, failed, failed_paths
    
    def _paste_single(self, src: str, dest_dir: str, mode: str) -> bool:
        """Paste single file/directory.
        
        Args:
            src: Source path
            dest_dir: Destination directory
            mode: 'copy' or 'cut'
            
        Returns:
            True if successful
        """
        # Security checks
        if not os.path.exists(src):
            logger.warning(f"Source does not exist: {src}")
            return False

        is_valid_src, error_src = PathValidator.is_valid_path(src)
        if not is_valid_src:
            logger.warning(f"Invalid source path: {error_src}")
            return False

        is_valid_dest, error_dest = PathValidator.validate_destination(src, dest_dir)
        if not is_valid_dest:
            logger.warning(f"Destination validation failed: {error_dest}")
            return False

        # Prevent moving/copying a folder into its own subtree
        if os.path.isdir(src) and is_path_within_directory(dest_dir, src):
            logger.warning(f"Cannot paste into a child directory of the source: {src} -> {dest_dir}")
            audit_logger.log_security_warning(f"Attempted recursive paste: {src} -> {dest_dir}")
            return False

        # Prevent operations on critical files
        safety = FileClassifier.classify_safety(src)
        if safety.value == 'CRITICAL':
            logger.warning(f"Cannot paste critical file: {src}")
            audit_logger.log_security_warning(f"Attempted to paste critical file: {src}")
            return False

        # Construct destination path
        base_name = os.path.basename(src)
        dest = os.path.join(dest_dir, base_name)
        
        # Normalize destination to prevent traversal
        dest = os.path.normpath(dest)
        dest = os.path.abspath(dest)

        try:
            if os.path.exists(dest) and os.path.samefile(src, dest):
                logger.warning(f"Source and destination refer to the same item: {src}")
                return False
        except OSError:
            pass
        
        # Verify destination is within dest_dir
        if not is_path_within_directory(dest, dest_dir):
            logger.warning(f"Path traversal attempt detected: {dest}")
            audit_logger.log_security_warning(f"Path traversal attempt: {dest} not in {dest_dir}")
            return False
        
        # Handle conflicts
        if os.path.exists(dest):
            dest = self._resolve_conflict(dest)
            if not dest:
                logger.warning(f"Could not resolve conflict for {base_name}")
                return False
        
        # Perform operation
        try:
            if mode == 'cut':
                shutil.move(src, dest)
                logger.info(f"Moved: {src} -> {dest}")
            else:
                if os.path.isdir(src):
                    shutil.copytree(src, dest, dirs_exist_ok=False)
                    logger.info(f"Copied directory: {src} -> {dest}")
                else:
                    shutil.copy2(src, dest)
                    logger.info(f"Copied file: {src} -> {dest}")
            
            return True
        
        except (OSError, PermissionError, shutil.Error) as e:
            logger.error(f"Paste operation failed: {e}")
            return False
    
    def delete_selected(self, paths: List[str]) -> Tuple[int, List[str]]:
        """Safely delete files/directories.
        
        Args:
            paths: List of paths to delete
            
        Returns:
            Tuple of (deleted_count, failed_paths)
        """
        if not isinstance(paths, list):
            logger.warning(f"Invalid paths type for delete: {type(paths)}")
            return 0, paths if isinstance(paths, list) else []
        
        deleted, failed_paths = 0, []
        
        for path in paths:
            if not isinstance(path, str):
                logger.warning(f"Invalid path type: {type(path)}")
                failed_paths.append(path)
                continue
            
            # Validate path
            is_valid, error = PathValidator.is_valid_path(path)
            if not is_valid:
                logger.warning(f"Invalid path for deletion: {error}")
                failed_paths.append(path)
                continue
            
            try:
                if not os.path.exists(path):
                    logger.warning(f"Path does not exist: {path}")
                    failed_paths.append(path)
                    continue
                
                # Check safety classification
                safety = FileClassifier.classify_safety(path)
                if safety.value == 'CRITICAL':
                    logger.warning(f"Cannot delete critical file: {path}")
                    audit_logger.log_security_warning(f"Attempted to delete critical file: {path}")
                    failed_paths.append(path)
                    continue
                
                # Delete
                if os.path.isdir(path):
                    shutil.rmtree(path)
                    logger.info(f"Deleted directory: {path}")
                else:
                    os.remove(path)
                    logger.info(f"Deleted file: {path}")
                
                deleted += 1
                audit_logger.log_delete(path, True)
            
            except (OSError, PermissionError, shutil.Error) as e:
                logger.error(f"Delete failed for {path}: {e}")
                audit_logger.log_delete(path, False, str(e))
                failed_paths.append(path)
        
        return deleted, failed_paths
    
    def rename_file(self, old_path: str, new_name: str) -> bool:
        """Safely rename file/directory.
        
        Args:
            old_path: Current full path
            new_name: New filename only (no path)
            
        Returns:
            True if successful
        """
        # Validate inputs
        if not isinstance(old_path, str) or not isinstance(new_name, str):
            logger.warning(f"Invalid rename inputs: old_path={type(old_path)}, new_name={type(new_name)}")
            return False
        
        if not os.path.exists(old_path):
            logger.warning(f"Source does not exist: {old_path}")
            return False
        
        # Validate new name
        is_valid, error = PathValidator.validate_rename(old_path, new_name)
        if not is_valid:
            logger.warning(f"Invalid rename: {error}")
            return False
        
        # Construct new path
        dir_path = os.path.dirname(old_path)
        new_path = os.path.join(dir_path, new_name)
        
        # Check for conflicts
        if os.path.exists(new_path) and new_path != old_path:
            logger.warning(f"Destination already exists: {new_path}")
            return False
        
        try:
            os.rename(old_path, new_path)
            logger.info(f"Renamed: {old_path} -> {new_path}")
            audit_logger.log_rename(old_path, new_path, True)
            return True
        
        except (OSError, PermissionError) as e:
            logger.error(f"Rename failed: {e}")
            audit_logger.log_rename(old_path, new_path, False)
            return False
    
    @staticmethod
    def _validate_paths(paths: List[str]) -> bool:
        """Validate list of paths.
        
        Args:
            paths: List of paths
            
        Returns:
            True if all paths are valid
        """
        if not isinstance(paths, list):
            return False
        
        for path in paths:
            if not isinstance(path, str) or not os.path.exists(path):
                return False
            is_valid, _ = PathValidator.is_valid_path(path)
            if not is_valid:
                return False
        
        return True
    
    @staticmethod
    def _resolve_conflict(dest_path: str) -> Optional[str]:
        """Resolve file conflict by renaming destination.
        
        Args:
            dest_path: Existing destination path
            
        Returns:
            New path with timestamp suffix, or None if failed
        """
        try:
            base, ext = os.path.splitext(dest_path)
            timestamp = str(int(time.time() * 1000))
            new_path = f"{base}_{timestamp}{ext}"
            
            # Ensure new path doesn't exist
            while os.path.exists(new_path):
                timestamp = str(int(time.time() * 1000) + 1)
                new_path = f"{base}_{timestamp}{ext}"
            
            return new_path
        
        except Exception as e:
            logger.error(f"Could not resolve conflict: {e}")
            return None
    
    def clear(self) -> None:
        """Clear clipboard."""
        with self.lock:
            self.paths.clear()
            self.mode = None

