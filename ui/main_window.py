"""Main application window and UI components."""

import os
import re
import queue
import threading
import time
from typing import List, Optional, Callable, Tuple
from datetime import datetime

import customtkinter as ctk
from tkinter import ttk, filedialog, messagebox, simpledialog

from models import FileInfo, SafetyClassification, ProcessInfo
from core import SecureFileClipboard, PathValidator, FileClassifier, ThreadedFileScannerQueue
from config import ConfigManager, THEMES
from utils import get_logger

logger = get_logger(__name__)


class SearchDebounce:
    """Debounce handler for search operations."""
    
    def __init__(self, callback: Callable, delay_ms: int = 300):
        """Initialize debounce.
        
        Args:
            callback: Function to call after delay
            delay_ms: Delay in milliseconds
        """
        self.callback = callback
        self.delay_ms = delay_ms
        self.timer: Optional[threading.Timer] = None
    
    def trigger(self) -> None:
        """Trigger debounced operation."""
        if self.timer:
            self.timer.cancel()
        
        self.timer = threading.Timer(self.delay_ms / 1000, self.callback)
        self.timer.daemon = True
        self.timer.start()
    
    def cancel(self) -> None:
        """Cancel pending operation."""
        if self.timer:
            self.timer.cancel()
            self.timer = None


class ScannerTab:
    """Directory scanner tab."""
    
    def __init__(
        self,
        parent: ctk.CTkTabview,
        config: ConfigManager,
        clipboard: SecureFileClipboard,
        on_file_selected: Callable
    ):
        """Initialize scanner tab.
        
        Args:
            parent: Parent tabview
            config: Configuration manager
            clipboard: File clipboard
            on_file_selected: Callback when file selected
        """
        self.config = config
        self.clipboard = clipboard
        self.on_file_selected = on_file_selected
        
        self.tab = parent.add("📁 Directory Scanner")
        self.frame = ctk.CTkFrame(self.tab)
        self.frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.all_files: List[FileInfo] = []
        self.scanner: Optional[ThreadedFileScannerQueue] = None
        self.search_debounce = SearchDebounce(self._on_search_debounced)
        
        self._build_ui()
    
    def _build_ui(self) -> None:
        # Control bar
        ctrl = ctk.CTkFrame(self.frame)
        ctrl.pack(fill=ctk.X, padx=10, pady=5)
        
        ctk.CTkButton(ctrl, text="📁 Up", command=self._go_up).pack(side=ctk.LEFT, padx=2)
        
        self.path_var = ctk.StringVar(value=str(os.path.expanduser("~")))
        self.path_entry = ctk.CTkEntry(ctrl, textvariable=self.path_var, width=60)
        self.path_entry.pack(side=ctk.LEFT, padx=5, fill=ctk.X, expand=True)
        self.path_entry.bind('<Return>', lambda e: self._start_scan())
        
        ctk.CTkButton(ctrl, text="Browse", command=self._browse_folder).pack(side=ctk.LEFT, padx=2)
        self.scan_button = ctk.CTkButton(ctrl, text="🔍 Scan", command=self._start_scan)
        self.scan_button.pack(side=ctk.LEFT, padx=2)
        self.cancel_button = ctk.CTkButton(ctrl, text="⏹ Cancel", command=self._cancel_scan, state=ctk.DISABLED)
        self.cancel_button.pack(side=ctk.LEFT, padx=2)
        
        # Quick buttons
        quick = ctk.CTkFrame(self.frame)
        quick.pack(fill=ctk.X, padx=10, pady=5)
        
        self.skip_system_var = ctk.BooleanVar(value=self.config.get("skip_system_dirs", False))
        ctk.CTkCheckBox(quick, text="Skip System", variable=self.skip_system_var).pack(side=ctk.LEFT, padx=5)
        
        ctk.CTkLabel(quick, text="Mode:").pack(side=ctk.LEFT, padx=(15, 5))
        self.mode_var = ctk.StringVar(value=self.config.get("scan_mode", "quick"))
        ctk.CTkComboBox(quick, variable=self.mode_var, values=["quick", "full"], width=6, state="readonly").pack(side=ctk.LEFT, padx=5)
        
        # Tree
        tree_frame = ctk.CTkFrame(self.frame)
        tree_frame.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)
        
        vsb = ctk.CTkScrollbar(tree_frame, orientation=ctk.VERTICAL)
        hsb = ctk.CTkScrollbar(tree_frame, orientation=ctk.HORIZONTAL)
        vsb.pack(side=ctk.RIGHT, fill=ctk.Y)
        hsb.pack(side=ctk.BOTTOM, fill=ctk.X)
        
        self.tree = ttk.Treeview(
            tree_frame,
            columns=('Size', 'Type', 'Modified', 'Safety'),
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set
        )
        self.tree.pack(fill="both", expand=True)
        
        vsb.configure(command=self.tree.yview)
        hsb.configure(command=self.tree.xview)
        
        self.tree.heading('#0', text='Filename')
        for col, width, anchor in [('Size', 90, "e"), ('Type', 110, "w"), ('Modified', 140, "w"), ('Safety', 110, "center")]:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width, anchor=anchor)
        
        self.tree.bind('<Double-1>', lambda e: self._on_double_click())
        self.tree.bind('<Button-3>', lambda e: self._on_right_click(e))
        
        # Search
        search_frame = ctk.CTkFrame(self.frame)
        search_frame.pack(fill=ctk.X, padx=10, pady=5)
        
        ctk.CTkLabel(search_frame, text="🔍 Search:").pack(side=ctk.LEFT, padx=(0, 5))
        self.search_var = ctk.StringVar()
        search_entry = ctk.CTkEntry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=ctk.LEFT, padx=5)
        search_entry.bind('<KeyRelease>', lambda e: self.search_debounce.trigger())
        
        # Stats
        status_frame = ctk.CTkFrame(self.frame)
        status_frame.pack(fill=ctk.X, padx=10, pady=5)
        
        self.stats_label = ctk.CTkLabel(status_frame, text="Ready", font=ctk.CTkFont(weight="bold"))
        self.stats_label.pack(side=ctk.LEFT)
    
    def _start_scan(self) -> None:

        path = self.path_var.get().strip()
        
        is_valid, error = PathValidator.is_valid_path(path)
        if not is_valid or not os.path.isdir(path):
            messagebox.showerror("Error", f"Invalid path: {error or path}")
            return
        
        path = os.path.abspath(path)
        logger.info(f"Starting scan: {path}")
        self.all_files.clear()
        self.tree.delete(*self.tree.get_children())
        
        self.scan_button.configure(state="disabled")
        self.cancel_button.configure(state="normal")
        self.stats_label.configure(text="Scanning...")
        
        # Start scanner
        scanner_queue = queue.Queue()
        self.scanner = ThreadedFileScannerQueue(scanner_queue)
        self.scanner.start_scan(
            path,
            skip_system=self.skip_system_var.get(),
            skip_hidden=(self.mode_var.get() == "quick")
        )
        
        # Process results in background
        self._process_scan_results(scanner_queue)
    
    def _process_scan_results(self, scanner_queue) -> None:
        """Process scan results from queue."""
        try:
            msg_type, data = scanner_queue.get(block=False)

            if msg_type == 'started':
                self.stats_label.configure(text="Scanning started...")
                logger.debug(f"Scan started for {data.get('path')}")

            elif msg_type == 'batch':
                for fi in data:
                    self.all_files.append(fi)
                    self._add_file_to_tree(fi)
                self.stats_label.configure(text=f"Scanning... {len(self.all_files)} items loaded")

            elif msg_type == 'completed':
                self.scan_button.configure(state="normal")
                self.cancel_button.configure(state="disabled")
                self.stats_label.configure(text=f"📊 Total: {data['total']} files")
                logger.info(f"Scan completed: {data['total']} files")

            elif msg_type == 'error':
                messagebox.showerror("Error", data)
                self.scan_button.configure(state="normal")
                self.cancel_button.configure(state="disabled")

            elif msg_type == 'progress':
                self.stats_label.configure(text=f"{data.get('message')} ({data.get('count')})")

        except queue.Empty:
            pass
        except Exception as e:
            logger.error(f"Error processing scan results: {e}")

        scan_active = self.scanner and (self.scanner._scan_thread.is_alive() or not scanner_queue.empty())
        if scan_active:
            self.frame.after(100, lambda: self._process_scan_results(scanner_queue))
        else:
            self.scan_button.configure(state="normal")
            self.cancel_button.configure(state="disabled")
    
    def _add_file_to_tree(self, fi: FileInfo) -> None:
        """Add file to tree.
        
        Args:
            fi: File info object
        """
        badge_map = {
            SafetyClassification.SAFE: '🟢',
            SafetyClassification.CRITICAL: '🔴',
            SafetyClassification.SYSTEM_REMOVABLE: '🟡',
            SafetyClassification.UNKNOWN: '⚪'
        }
        
        badge = badge_map.get(fi.safety_classification, '⚪')
        safety_text = f"{badge} {fi.safety_classification.value}"
        
        size_str = self._format_size(fi.size) if not fi.is_dir else '-'
        mod_time = datetime.fromtimestamp(fi.modified_time).strftime('%Y-%m-%d %H:%M') if fi.modified_time else '-'
        
        icon = '📁' if fi.is_dir else '📄'
        display_name = f"{icon} {fi.filename}"
        
        self.tree.insert('', 'end', iid=fi.path, text=display_name,
                        values=(size_str, fi.file_type_name, mod_time, safety_text))
    
    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Format byte size.
        
        Args:
            size_bytes: Size in bytes
            
        Returns:
            Formatted size string
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"
    
    def _on_double_click(self) -> None:
        """Handle double-click on file."""
        sel = self.tree.selection()
        if not sel:
            return
        
        file_path = sel[0]
        if os.path.isdir(file_path):
            self.path_var.set(file_path)
            self._start_scan()
        else:
            try:
                if os.name == 'nt':
                    os.startfile(file_path)
                else:
                    os.system(f"xdg-open '{file_path}'")
            except Exception as e:
                logger.error(f"Cannot open file: {e}")
    
    def _on_right_click(self, event) -> None:
        """Handle right-click context menu."""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            # Context menu would be built here
    
    def _go_up(self) -> None:
        """Navigate to parent directory."""
        current = self.path_var.get()
        parent = os.path.dirname(current)
        if parent and os.path.isdir(parent):
            self.path_var.set(parent)
            self._start_scan()
    
    def _browse_folder(self) -> None:
        """Browse for folder."""
        folder = filedialog.askdirectory()
        if folder:
            self.path_var.set(folder)
            self._start_scan()
    
    def _cancel_scan(self) -> None:
        """Cancel scan."""
        if self.scanner:
            self.scanner.stop()
        self.scan_button.configure(state="normal")
        self.cancel_button.configure(state="disabled")
    
    def _on_search_debounced(self) -> None:
        """Handle debounced search."""
        query = self.search_var.get().strip()
        
        # Clear tree
        self.tree.delete(*self.tree.get_children())
        
        if not query:
            # Show all
            for fi in self.all_files:
                self._add_file_to_tree(fi)
            return
        
        # Filter
        try:
            pattern = re.compile(re.escape(query), re.IGNORECASE)
            matches = [f for f in self.all_files if pattern.search(f.filename)]
            
            for fi in matches[:1000]:  # Limit to 1000
                self._add_file_to_tree(fi)
            
            self.stats_label.configure(text=f"🔍 Found {len(matches)} matches")
        
        except Exception as e:
            logger.error(f"Search error: {e}")


class TaskManagerTab:
    """Task manager tab."""
    
    def __init__(
        self,
        parent: ctk.CTkTabview,
        on_refresh: Optional[Callable[[], None]] = None,
        on_terminate: Optional[Callable[[int], Tuple[bool, str]]] = None,
        on_auto_refresh_toggle: Optional[Callable[[bool], None]] = None,
    ):
        """Initialize task manager tab.
        
        Args:
            parent: Parent tabview
            on_refresh: Callback to request a refresh
            on_terminate: Callback to terminate a selected process
            on_auto_refresh_toggle: Callback when auto-refresh state changes
        """
        self.on_refresh = on_refresh
        self.on_terminate = on_terminate
        self.on_auto_refresh_toggle = on_auto_refresh_toggle

        self.tab = parent.add("⚙️ Task Manager")
        self.frame = ctk.CTkFrame(self.tab)
        self.frame.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)
        
        # Control bar
        ctrl = ctk.CTkFrame(self.frame)
        ctrl.pack(fill=ctk.X, padx=10, pady=10)
        
        self.auto_refresh_var = ctk.BooleanVar(value=True)
        self.auto_refresh_var.trace_add("write", self._handle_auto_refresh_toggle)
        ctk.CTkCheckBox(ctrl, text="Auto-refresh", variable=self.auto_refresh_var).pack(side=ctk.LEFT)
        ctk.CTkButton(ctrl, text="Refresh Now", command=self._refresh).pack(side=ctk.LEFT, padx=10)
        
        # Tree
        tree_frame = ctk.CTkFrame(self.frame)
        tree_frame.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)
        
        vsb = ctk.CTkScrollbar(tree_frame, orientation=ctk.VERTICAL)
        vsb.pack(side=ctk.RIGHT, fill=ctk.Y)
        
        self.tree = ttk.Treeview(
            tree_frame,
            columns=('PID', 'CPU%', 'Memory MB', 'Status', 'User'),
            yscrollcommand=vsb.set
        )
        self.tree.pack(fill="both", expand=True)
        vsb.configure(command=self.tree.yview)
        
        self.tree.heading('#0', text='Process Name')
        for col, width in [('PID', 70), ('CPU%', 70), ('Memory MB', 100), ('Status', 100), ('User', 140)]:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width)
        
        # End Task button
        ctk.CTkButton(self.frame, text="End Task", command=self._end_task).pack(pady=5)
    
    def update_processes(self, processes: List[ProcessInfo]) -> None:
        """Update process list.
        
        Args:
            processes: List of process info
        """
        self.tree.delete(*self.tree.get_children())
        
        for proc in processes:
            self.tree.insert('', 'end', text=proc.name[:40],
                           values=(proc.pid, f"{proc.cpu_percent:.1f}",
                                  f"{proc.memory_mb:.1f}", proc.status, proc.username[:20]))
    
    def _handle_auto_refresh_toggle(self, *_args) -> None:
        enabled = self.auto_refresh_var.get()
        logger.info(f"Auto-refresh {'enabled' if enabled else 'disabled'}")
        if self.on_auto_refresh_toggle:
            self.on_auto_refresh_toggle(enabled)
    
    def _refresh(self) -> None:
        """Refresh process list."""
        if self.on_refresh:
            self.on_refresh()
        else:
            logger.info("Refreshing process list")
    
    def _end_task(self) -> None:
        """End selected task."""
        sel = self.tree.selection()
        if not sel:
            return
        
        pid = int(self.tree.item(sel[0])['values'][0])
        if messagebox.askyesno("Confirm", f"Terminate process {pid}?"):
            if self.on_terminate:
                success, message = self.on_terminate(pid)
                if success:
                    messagebox.showinfo("Terminated", message)
                else:
                    messagebox.showerror("Error", message)
            else:
                logger.info(f"Terminating process {pid}")
