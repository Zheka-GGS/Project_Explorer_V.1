"""Process monitoring and task management."""

import threading
import queue
from typing import List, Optional, Callable
import psutil

from models import ProcessInfo, ProcessSafety
from utils.logging_utils import get_logger

logger = get_logger(__name__)


class ProcessMonitor(threading.Thread):
    """Background thread for monitoring running processes.
    
    Features:
        - Real-time process monitoring
        - Thread-safe queue-based result delivery
        - Pause/resume support
        - Resource usage tracking
    """
    
    def __init__(
        self,
        result_queue: queue.Queue,
        refresh_interval: float = 2.0,
        daemon: bool = True
    ):
        """Initialize process monitor.
        
        Args:
            result_queue: Queue for results
            refresh_interval: Update interval in seconds
            daemon: Whether to run as daemon thread
        """
        super().__init__(daemon=daemon)
        self.result_queue = result_queue
        self.refresh_interval = max(0.5, refresh_interval)  # Min 0.5 seconds
        self._stop_event = threading.Event()
        self._paused_event = threading.Event()
        self._refresh_event = threading.Event()
    
    def stop(self) -> None:
        """Stop monitoring gracefully."""
        self._stop_event.set()

    def trigger_refresh(self) -> None:
        """Request an immediate refresh from the monitor."""
        self._refresh_event.set()
    
    def set_paused(self, paused: bool) -> None:
        """Pause or resume monitoring.
        
        Args:
            paused: True to pause, False to resume
        """
        if paused:
            self._paused_event.set()
        else:
            self._paused_event.clear()
    
    def run(self) -> None:
        """Main monitoring loop."""
        logger.info("Process monitor started")
        
        try:
            while not self._stop_event.is_set():
                # Respect pause requests
                if self._paused_event.is_set():
                    self._stop_event.wait(0.1)
                    continue
                
                try:
                    processes = self._get_processes()
                    self.result_queue.put(('processes', processes))
                except Exception as e:
                    logger.error(f"Error getting processes: {e}")
                    self.result_queue.put(('error', str(e)))
                
                # Wait for next refresh or an explicit refresh request
                elapsed = 0.0
                while elapsed < self.refresh_interval and not self._stop_event.is_set():
                    if self._refresh_event.wait(timeout=0.1):
                        self._refresh_event.clear()
                        break
                    elapsed += 0.1
        
        except Exception as e:
            logger.error(f"Process monitor error: {e}", exc_info=True)
        
        finally:
            logger.info("Process monitor stopped")
    
    @staticmethod
    def _get_processes() -> List[ProcessInfo]:
        """Get list of all running processes.
        
        Returns:
            List of ProcessInfo objects, sorted by memory usage
        """
        processes = []
        
        # Critical process names that should be protected
        critical_names = {
            'explorer.exe', 'svchost.exe', 'csrss.exe', 'wininit.exe',
            'winlogon.exe', 'lsass.exe', 'system', 'Idle', 'kernel_task',
            'systemd', 'launchd', 'init'
        }
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'status', 'username']):
                try:
                    with proc.oneshot():
                        # Get basic info
                        pid = proc.pid
                        name = proc.name() or "Unknown"
                        status = proc.status()
                        
                        # Get username (may fail on some systems)
                        try:
                            username = proc.username() if hasattr(proc, 'username') else 'System'
                        except (AttributeError, psutil.Error):
                            username = 'System'
                        
                        # Get resource usage (with timeout)
                        try:
                            cpu_percent = proc.cpu_percent(interval=0)
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            cpu_percent = 0.0
                        
                        try:
                            mem_info = proc.memory_info()
                            memory_mb = mem_info.rss / (1024 * 1024)
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            memory_mb = 0.0
                        
                        # Classify process safety
                        safety = ProcessMonitor._classify_process(
                            name, username, cpu_percent, memory_mb, pid
                        )
                        
                        processes.append(ProcessInfo(
                            pid=pid,
                            name=name,
                            cpu_percent=cpu_percent,
                            memory_mb=memory_mb,
                            status=status,
                            username=username,
                            safety=safety
                        ))
                
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    # Process terminated or access denied, skip it
                    continue
                except Exception as e:
                    logger.debug(f"Error processing {proc}: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error getting process list: {e}")
        
        # Sort by memory usage (descending)
        processes.sort(key=lambda x: x.memory_mb, reverse=True)
        
        return processes
    
    @staticmethod
    def _classify_process(
        name: str,
        username: str,
        cpu_percent: float,
        memory_mb: float,
        pid: int
    ) -> ProcessSafety:
        """Classify process safety level.
        
        Args:
            name: Process name
            username: Process owner
            cpu_percent: CPU usage percentage
            memory_mb: Memory usage in MB
            pid: Process ID
            
        Returns:
            ProcessSafety classification
        """
        # Critical system processes
        critical_names = {
            'explorer.exe', 'svchost.exe', 'csrss.exe', 'wininit.exe',
            'winlogon.exe', 'lsass.exe', 'system', 'Idle', 'kernel_task',
            'systemd', 'launchd', 'init'
        }
        
        critical_usernames = {'system', 'local system', 'root', '_system'}
        
        # Check for critical system process
        if name.lower() in {n.lower() for n in critical_names}:
            return ProcessSafety.CRITICAL_SYSTEM
        
        if username.lower() in critical_usernames:
            return ProcessSafety.CRITICAL_SYSTEM
        
        # Check for high resource usage
        if cpu_percent > 50.0 or memory_mb > 1500:
            return ProcessSafety.HIGH_RESOURCE
        
        return ProcessSafety.SAFE
    
    @staticmethod
    def terminate_process(pid: int) -> tuple[bool, str]:
        """Terminate a process safely.
        
        Args:
            pid: Process ID to terminate
            
        Returns:
            Tuple of (success, message)
        """
        try:
            proc = psutil.Process(pid)
            
            # Don't terminate critical processes
            if proc.name() in {'explorer.exe', 'csrss.exe', 'system'}:
                return False, "Cannot terminate critical system process"
            
            if proc.username() and 'system' in proc.username().lower():
                return False, "Cannot terminate system process"
            
            # Attempt graceful termination
            proc.terminate()
            
            try:
                proc.wait(timeout=3)
                logger.info(f"Terminated process {pid}: {proc.name()}")
                return True, f"Terminated {proc.name()}"
            
            except psutil.TimeoutExpired:
                # Force kill if terminate doesn't work
                proc.kill()
                logger.warning(f"Force killed process {pid}: {proc.name()}")
                return True, f"Force killed {proc.name()}"
        
        except psutil.NoSuchProcess:
            return False, "Process not found"
        
        except psutil.AccessDenied:
            return False, "Access denied - administrator required"
        
        except Exception as e:
            logger.error(f"Error terminating process {pid}: {e}")
            return False, f"Error: {str(e)}"
