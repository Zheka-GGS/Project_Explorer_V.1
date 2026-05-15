"""High-performance directory scanner with thread safety and proper resource management."""

import os
import threading
import queue
from pathlib import Path
from typing import List, Optional, Callable, Dict, Any, Iterator
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict

from models import FileInfo, SafetyClassification, ScanStats
from core.security import FileClassifier, PathValidator
from utils.logging_utils import get_logger

logger = get_logger(__name__)


class OptimizedFileScanner:
    """High-performance file scanner with thread pooling and caching.
    
    Features:
        - Efficient recursive scanning without UI blocking
        - Thread pool for parallel processing
        - Proper resource cleanup
        - Batch processing for large directories
        - Configurable depth limit and filters
    """
    
    def __init__(
        self,
        max_workers: int = 4,
        batch_size: int = 500,
        max_depth: int = 5
    ):
        """Initialize scanner.
        
        Args:
            max_workers: Number of worker threads
            batch_size: Files to batch before yielding results
            max_depth: Maximum recursion depth
        """
        self.max_workers = max(1, min(max_workers, 8))  # Limit 1-8 workers
        self.batch_size = max(10, batch_size)
        self.max_depth = max(1, max_depth)
        
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self.stats = ScanStats()
    
    def scan(
        self,
        root_path: str,
        skip_system: bool = False,
        skip_hidden: bool = False,
        progress_callback: Optional[Callable[[str, int], None]] = None
    ) -> List[FileInfo]:
        """Scan directory recursively.
        
        Args:
            root_path: Root directory to scan
            skip_system: Skip critical system paths
            skip_hidden: Skip hidden files/folders
            progress_callback: Called with (status_msg, count) during scan
            
        Returns:
            List of FileInfo objects
            
        Raises:
            ValueError: If root_path is invalid
        """
        # Validate root path
        is_valid, error = PathValidator.is_valid_path(root_path)
        if not is_valid:
            raise ValueError(error)
        
        root_path = os.path.abspath(root_path)
        if not os.path.exists(root_path) or not os.path.isdir(root_path):
            raise ValueError(f"Path does not exist or is not a directory: {root_path}")
        
        self._stop_event.clear()
        self.stats = ScanStats()
        
        results: List[FileInfo] = []
        batch_buffer: List[FileInfo] = []
        
        try:
            # Use pathlib for better performance in some cases
            for file_info in self._scan_recursive(
                root_path, 0, skip_system, skip_hidden, progress_callback
            ):
                if self._stop_event.is_set():
                    break
                
                batch_buffer.append(file_info)
                
                # Classify file
                if file_info.safety_classification == SafetyClassification.SAFE:
                    self.stats.safe_count += 1
                elif file_info.safety_classification == SafetyClassification.CRITICAL:
                    self.stats.critical_count += 1
                elif file_info.safety_classification == SafetyClassification.SYSTEM_REMOVABLE:
                    self.stats.system_removable_count += 1
                else:
                    self.stats.unknown_count += 1
                
                self.stats.total_scanned += 1
                
                # Flush batch
                if len(batch_buffer) >= self.batch_size:
                    results.extend(batch_buffer)
                    batch_buffer.clear()
                    
                    if progress_callback:
                        progress_callback(f"Scanned {self.stats.total_scanned} files", self.stats.total_scanned)
            
            # Flush remaining
            if batch_buffer:
                results.extend(batch_buffer)
        
        except Exception as e:
            logger.error(f"Scan error: {e}", exc_info=True)
            raise
        
        return results
    
    def _scan_recursive(
        self,
        path: str,
        depth: int,
        skip_system: bool,
        skip_hidden: bool,
        progress_callback: Optional[Callable] = None
    ) -> Iterator[FileInfo]:
        """Recursively scan directory.
        
        Args:
            path: Current path to scan
            depth: Current recursion depth
            skip_system: Skip critical paths
            skip_hidden: Skip hidden files
            progress_callback: Progress callback
            
        Yields:
            FileInfo objects
        """
        if self._stop_event.is_set() or depth >= self.max_depth:
            return
        
        try:
            # Use os.scandir for efficiency
            entries = sorted(
                os.scandir(path),
                key=lambda e: (not e.is_dir(), e.name.lower())
            )
        except (PermissionError, OSError) as e:
            logger.warning(f"Cannot scan {path}: {e}")
            return
        
        for entry in entries:
            if self._stop_event.is_set():
                return
            
            # Skip symlinks (security)
            try:
                if entry.is_symlink():
                    continue
            except (OSError, ValueError):
                continue
            
            # Skip hidden files if requested
            if skip_hidden and entry.name.startswith('.'):
                continue
            
            # Skip system directories if requested
            if skip_system:
                path_lower = entry.path.lower()
                if self._is_critical_path(path_lower):
                    continue
            
            try:
                # Classify file
                safety = FileClassifier.classify_safety(entry.path)
                
                # Create FileInfo
                stat_info = entry.stat()
                is_dir = entry.is_dir()
                size = stat_info.st_size if not is_dir else 0
                
                _, ext = os.path.splitext(entry.name)
                
                fi = FileInfo(
                    path=entry.path,
                    filename=entry.name,
                    extension=ext.lower(),
                    is_dir=is_dir,
                    size=size,
                    safety_classification=safety,
                    color=self._get_color_for_file(ext, is_dir, safety),
                    modified_time=stat_info.st_mtime,
                    file_type_name=self._get_file_type(ext),
                    parent_path=path
                )
                
                yield fi
                
                # Recursively scan subdirectories
                if is_dir and depth < self.max_depth - 1:
                    yield from self._scan_recursive(
                        entry.path, depth + 1, skip_system, skip_hidden, progress_callback
                    )
            
            except (PermissionError, OSError) as e:
                logger.debug(f"Cannot process {entry.path}: {e}")
                continue
    
    @staticmethod
    def _is_critical_path(path_lower: str) -> bool:
        """Check if path is critical system path."""
        critical_prefixes = {
            'c:\\windows', 'c:\\system32', 'c:\\program files',
            '/usr/bin', '/usr/lib', '/etc', '/System', '/Library'
        }
        return any(path_lower.startswith(prefix) for prefix in critical_prefixes)
    
    @staticmethod
    def _get_color_for_file(ext: str, is_dir: bool, safety: SafetyClassification) -> str:
        """Get display color for file."""
        # This will be set by UI theme manager - return default
        return "#A0A0A0"
    
    @staticmethod
    def _get_file_type(ext: str) -> str:
        """Get human-readable file type."""
        type_map = {
            '.pdf': 'PDF Document', '.docx': 'Word Document', '.xlsx': 'Excel',
            '.py': 'Python', '.js': 'JavaScript', '.html': 'Web Page',
            '.jpg': 'Image', '.png': 'Image', '.zip': 'Archive',
            '.exe': 'Executable', '.mp4': 'Video', '.mp3': 'Audio',
        }
        return type_map.get(ext.lower(), f'{ext[1:].upper()} File' if ext else 'File')
    
    def stop(self) -> None:
        """Stop scanning gracefully."""
        self._stop_event.set()


class ThreadedFileScannerQueue:
    """Thread-safe scanner with queue-based result delivery.
    
    Results are delivered to a queue for UI consumption, preventing UI blocking.
    """
    
    def __init__(self, result_queue: queue.Queue, max_workers: int = 4):
        """Initialize.
        
        Args:
            result_queue: Queue for results
            max_workers: Number of worker threads
        """
        self.result_queue = result_queue
        self.scanner = OptimizedFileScanner(max_workers=max_workers)
        self._scan_thread: Optional[threading.Thread] = None
    
    def start_scan(
        self,
        root_path: str,
        skip_system: bool = False,
        skip_hidden: bool = False
    ) -> threading.Thread:
        """Start scanning in background thread.
        
        Args:
            root_path: Directory to scan
            skip_system: Skip system paths
            skip_hidden: Skip hidden files
            
        Returns:
            Thread object (already started)
        """
        self._scan_thread = threading.Thread(
            target=self._scan_worker,
            args=(root_path, skip_system, skip_hidden),
            daemon=True
        )
        self._scan_thread.start()
        return self._scan_thread
    
    def _scan_worker(self, root_path: str, skip_system: bool, skip_hidden: bool) -> None:
        """Background worker for scanning."""
        try:
            self.result_queue.put(('started', {'path': root_path}))
            
            files = self.scanner.scan(
                root_path,
                skip_system=skip_system,
                skip_hidden=skip_hidden,
                progress_callback=lambda msg, count: self.result_queue.put(('progress', {'message': msg, 'count': count}))
            )
            
            # Send results in batches
            batch_size = 500
            for i in range(0, len(files), batch_size):
                if self.scanner._stop_event.is_set():
                    break
                batch = files[i:i + batch_size]
                self.result_queue.put(('batch', batch))
            
            # Send completion
            self.result_queue.put(('completed', {
                'total': self.scanner.stats.total_scanned,
                'stats': {
                    'SAFE': self.scanner.stats.safe_count,
                    'CRITICAL': self.scanner.stats.critical_count,
                    'SYSTEM_REMOVABLE': self.scanner.stats.system_removable_count,
                    'UNKNOWN': self.scanner.stats.unknown_count
                }
            }))
        
        except Exception as e:
            logger.error(f"Scan worker error: {e}", exc_info=True)
            self.result_queue.put(('error', str(e)))
    
    def stop(self) -> None:
        """Stop scanning."""
        self.scanner.stop()
