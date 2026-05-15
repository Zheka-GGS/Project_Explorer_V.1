"""Data models and type definitions."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional
from datetime import datetime


class SafetyClassification(Enum):
    """File/process safety classification."""
    SAFE = "SAFE"
    CRITICAL = "CRITICAL"
    SYSTEM_REMOVABLE = "SYSTEM-REMOVABLE"
    UNKNOWN = "UNKNOWN"


class ProcessSafety(Enum):
    """Process safety classification."""
    CRITICAL_SYSTEM = "Critical System"
    HIGH_RESOURCE = "High Resource"
    SAFE = "Safe to End"
    UNKNOWN = "Unknown"


@dataclass
class FileInfo:
    """Information about a file/directory.
    
    Attributes:
        path: Full path to the file
        filename: File name only
        extension: File extension (e.g., '.txt')
        is_dir: Whether it's a directory
        size: File size in bytes
        safety_classification: Safety level
        color: Display color (hex)
        modified_time: Last modified timestamp
        file_type_name: Human-readable type (e.g., 'PDF Document')
        parent_path: Parent directory path
    """
    path: str
    filename: str
    extension: str
    is_dir: bool
    size: int
    safety_classification: SafetyClassification
    color: str
    modified_time: float = 0.0
    file_type_name: str = ""
    parent_path: str = ""

    def __lt__(self, other: 'FileInfo') -> bool:
        """Sort directories first, then by name (case-insensitive)."""
        if self.is_dir != other.is_dir:
            return self.is_dir
        return self.filename.lower() < other.filename.lower()

    def __hash__(self) -> int:
        """Allow use in sets."""
        return hash(self.path)

    def __eq__(self, other: object) -> bool:
        """Check equality by path."""
        if not isinstance(other, FileInfo):
            return NotImplemented
        return self.path == other.path


@dataclass
class ProcessInfo:
    """Information about a running process.
    
    Attributes:
        pid: Process ID
        name: Process name
        cpu_percent: CPU usage percentage
        memory_mb: Memory usage in MB
        status: Process status
        username: Owner username
        safety: Safety classification
    """
    pid: int
    name: str
    cpu_percent: float
    memory_mb: float
    status: str
    username: str
    safety: ProcessSafety


@dataclass
class ScanStats:
    """Statistics from directory scan.
    
    Attributes:
        safe_count: Number of safe files
        critical_count: Number of critical files
        system_removable_count: Number of removable system files
        unknown_count: Number of files with unknown safety
        total_scanned: Total files scanned
    """
    safe_count: int = 0
    critical_count: int = 0
    system_removable_count: int = 0
    unknown_count: int = 0
    total_scanned: int = 0

    @property
    def total(self) -> int:
        """Total files across all categories."""
        return self.safe_count + self.critical_count + self.system_removable_count + self.unknown_count


@dataclass
class ClipboardOperation:
    """Tracks clipboard operations (copy/cut).
    
    Attributes:
        mode: 'copy' or 'cut'
        paths: List of file paths
        timestamp: When operation occurred
    """
    mode: str  # 'copy' or 'cut'
    paths: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
