#!/usr/bin/env python3
"""Project Explorer Pro V1.4.1 - Advanced File Manager & Task Monitor.

Migration: Classic tkinter → CustomTkinter 5.2+
Modern dark theme, DPI-aware, high-res support.

Version: 1.4.1
License: MIT
"""

import os
import sys
import threading
import queue
import platform
import time
import logging as logging_module
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable, Tuple

import customtkinter as ctk
from tkinter import filedialog, messagebox
from tkinter import ttk

import psutil

from config import ConfigManager, THEMES, get_theme
from models import FileInfo, ProcessInfo, SafetyClassification, ScanStats
from core import (
    OptimizedFileScanner,
    ThreadedFileScannerQueue,
    PathValidator,
    FileClassifier,
    SecureFileClipboard,
    ProcessMonitor,
)
from utils import setup_logging, get_logger, AuditLogger

logger = get_logger(__name__)
audit_logger = AuditLogger()


# ==============================================================================
# UI SCALING & THEME MANAGEMENT
# ==============================================================================

class ScalingManager:
    """Manage DPI scaling and responsive layout for CTk."""

    def __init__(self, root: ctk.CTk):
        self.root = root
        self.dpi_scale = self._get_dpi_scale()
        self.base_font_size = 13
        logger.debug(f"DPI Scale: {self.dpi_scale}x")

    def _get_dpi_scale(self) -> float:
        try:
            if platform.system() == "Windows":
                import ctypes
                try:
                    user32 = ctypes.windll.user32
                    dpi = user32.GetDpiForSystem()
                    return dpi / 96.0
                except Exception:
                    pass
            self.root.update_idletasks()
            screen_width_mm = self.root.winfo_screenmmwidth()
            screen_width_px = self.root.winfo_screenwidth()
            if screen_width_mm > 0:
                dpi = (screen_width_px * 25.4) / screen_width_mm
                return dpi / 96.0
        except Exception:
            pass
        return 1.0

    def scale_size(self, size: int) -> int:
        return max(1, int(size * self.dpi_scale))

    def scale_font_size(self, size: int) -> int:
        return max(8, int(size * self.dpi_scale))

    def get_ctk_font(self, family: str = "Segoe UI", size: int = 13, weight: str = "normal") -> ctk.CTkFont:
        scaled_size = self.scale_font_size(size)
        return ctk.CTkFont(family=family, size=scaled_size, weight=weight)


class ThemeManager:
    """Manage application themes for CTk."""

    def __init__(self, config: ConfigManager, scaling: ScalingManager):
        self.config = config
        self.scaling = scaling
        self.current_theme_name = config.get("theme", "Modern Dark")
        self.current_theme = get_theme(self.current_theme_name)
        self.font_size = config.get("font_size", 13)
        self.update_callbacks: List[Callable] = []

        self._apply_ctk_appearance_mode()
        logger.info(f"Theme: {self.current_theme_name}")

    def _apply_ctk_appearance_mode(self) -> None:
        light_themes = {"Soft Warm", "White"}
        if self.current_theme_name in light_themes:
            ctk.set_appearance_mode("light")
        else:
            ctk.set_appearance_mode("dark")

    def register_callback(self, callback: Callable) -> None:
        self.update_callbacks.append(callback)

    def set_theme(self, theme_name: str, font_size: Optional[int] = None) -> bool:
        if theme_name not in THEMES:
            logger.warning(f"Theme not found: {theme_name}")
            return False

        self.current_theme_name = theme_name
        self.current_theme = get_theme(theme_name)
        self.config.set("theme", theme_name)

        if font_size is not None:
            self.font_size = font_size
            self.config.set("font_size", font_size)

        self._apply_ctk_appearance_mode()

        for callback in self.update_callbacks:
            try:
                callback(self.current_theme, self.font_size)
            except Exception as e:
                logger.error(f"Theme callback error: {e}")

        logger.info(f"Theme changed to: {theme_name}")
        return True

    def get_ttk_style(self) -> ttk.Style:
        style = ttk.Style()
        style.theme_use('clam')

        font_name = "Segoe UI"
        font_size = self.scaling.scale_font_size(self.font_size)
        theme = self.current_theme

        style.configure('TNotebook', background=theme["bg_primary"], borderwidth=0)
        style.configure(
            'TNotebook.Tab',
            padding=(20, 10),
            background=theme["bg_secondary"],
            foreground=theme["fg_primary"],
            font=(font_name, font_size)
        )
        style.map('TNotebook.Tab', background=[('selected', theme["bg_tertiary"])])

        style.configure('TFrame', background=theme["bg_primary"])
        style.configure('TLabel', background=theme["bg_primary"],
                       foreground=theme["fg_primary"],
                       font=(font_name, font_size))
        style.configure('Header.TLabel', background=theme["bg_primary"],
                       foreground=theme["accent"],
                       font=(font_name, font_size + 1, 'bold'))

        style.configure('Treeview', background=theme["bg_secondary"],
                       foreground=theme["fg_primary"],
                       fieldbackground=theme["bg_secondary"],
                       font=(font_name, font_size))
        style.map('Treeview', background=[('selected', theme["accent"])],
                 foreground=[('selected', '#FFFFFF')])
        style.configure('Treeview.Heading', background=theme["bg_tertiary"],
                       foreground=theme["accent"],
                       font=(font_name, font_size, 'bold'))

        return style


# ==============================================================================
# SPLASH SCREEN
# ==============================================================================

class SplashScreen:
    """Modern splash screen with CTk progress bar."""

    def __init__(self, parent: Optional[ctk.CTk] = None):
        self.splash = ctk.CTkToplevel(parent) if parent else ctk.CTk()
        self.splash.title("PROJECT EXPLORER PRO")
        self.splash.geometry("500x300")
        self.splash.resizable(False, False)

        self.splash.overrideredirect(True)

        self.splash.update_idletasks()
        x = (self.splash.winfo_screenwidth() // 2) - 250
        y = (self.splash.winfo_screenheight() // 2) - 150
        self.splash.geometry(f"+{x}+{y}")

        self.splash.configure(fg_color="#0A0A0F")

        frame = ctk.CTkFrame(self.splash, fg_color="#0A0A0F")
        frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)

        title = ctk.CTkLabel(
            frame, text="\U0001F680 PROJECT EXPLORER PRO",
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
            text_color="#67E8F9"
        )
        title.pack(pady=(40, 10))

        version = ctk.CTkLabel(
            frame, text="v2.0 — CustomTkinter Edition",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#A5F3FC"
        )
        version.pack(pady=5)

        self.status_label = ctk.CTkLabel(
            frame, text="Loading...",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#60A5FA"
        )
        self.status_label.pack(pady=15)

        self.progress_bar = ctk.CTkProgressBar(
            frame,
            width=460,
            height=18,
            fg_color="#16161F",
            progress_color="#22D3EE",
            corner_radius=4
        )
        self.progress_bar.pack(pady=15)
        self.progress_bar.set(0.0)

        self.progress = 0

    def update_progress(self, percent: int, status: str = "") -> None:
        self.progress = max(0, min(100, percent))
        self.progress_bar.set(self.progress / 100.0)
        if status:
            self.status_label.configure(text=status)
        self.splash.update()

    def close(self) -> None:
        try:
            self.splash.destroy()
        except Exception:
            pass


# ==============================================================================
# MAIN APPLICATION
# ==============================================================================

class ProjectExplorerPro:
    """Main application class — CTk-based."""

    def __init__(self, root: ctk.CTk):
        self.root = root
        self.root.title("PROJECT EXPLORER PRO - v2.0")
        self.root.withdraw()

        self.splash = SplashScreen()
        self.splash.update_progress(5, "Loading configuration...")

        self.config = ConfigManager()
        self.splash.update_progress(10, "Initializing scaling...")

        self.scaling = ScalingManager(self.root)
        self.splash.update_progress(15, "Setting up themes...")

        self.theme_manager = ThemeManager(self.config, self.scaling)

        self.splash.update_progress(20, "Initializing security...")
        self.clipboard = SecureFileClipboard()

        self.scanner_queue = queue.Queue()
        self.task_queue = queue.Queue()

        self.all_files: List[FileInfo] = []
        self.scanner_thread: Optional[threading.Thread] = None
        self.task_monitor: Optional[ProcessMonitor] = None

        self.current_path = str(Path.home())
        self.scan_mode = ctk.StringVar(value=self.config.get("scan_mode", "quick"))
        self.skip_system = ctk.BooleanVar(value=self.config.get("skip_system_dirs", False))
        self.auto_refresh = ctk.BooleanVar(value=True)

        self.splash.update_progress(40, "Building UI...")
        self._build_ui()

        self.splash.update_progress(70, "Starting services...")
        self._start_services()

        self.splash.update_progress(90, "Finalizing...")
        self.root.geometry(self.config.get("window_geometry", "1450x850"))
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self.splash.update_progress(100, "Ready!")
        self.root.after(500, self._finalize_startup)

        logger.info("Application initialized successfully")

    def _finalize_startup(self) -> None:
        try:
            self.splash.close()
        except Exception:
            pass
        self.root.deiconify()
        self.status_label.configure(text="\u2705 Ready")
        logger.info("Application ready")

    def _build_ui(self) -> None:
        theme = self.theme_manager.current_theme
        self.root.configure(fg_color=theme["bg_primary"])
        self.theme_manager.get_ttk_style()

        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        main_frame = ctk.CTkFrame(self.root, fg_color=theme["bg_primary"], corner_radius=0)
        main_frame.pack(fill=ctk.BOTH, expand=True)

        header = ctk.CTkFrame(main_frame, fg_color="transparent")
        header.pack(fill=ctk.X, padx=10, pady=(8, 0))

        title_font = self.scaling.get_ctk_font(size=16, weight="bold")
        ctk.CTkLabel(
            header, text="\U0001F680 Project Explorer Pro v2.0",
            font=title_font, text_color=theme["accent"]
        ).pack(side=ctk.LEFT, padx=5)

        ctk.CTkLabel(
            header, text="CTk Edition",
            font=self.scaling.get_ctk_font(size=11),
            text_color=theme["fg_secondary"]
        ).pack(side=ctk.LEFT, padx=(5, 0))

        status_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        status_frame.pack(fill=ctk.X, padx=10, pady=(5, 0))

        self.status_label = ctk.CTkLabel(
            status_frame, text="Ready",
            font=self.scaling.get_ctk_font(size=13, weight="bold"),
            text_color=theme["accent"]
        )
        self.status_label.pack(side=ctk.LEFT, padx=5)

        # Tabs
        self.tabview = ctk.CTkTabview(main_frame, width=1400, height=700)
        self.tabview.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)

        from ui.main_window import ScannerTab, TaskManagerTab
        self.scanner_tab = ScannerTab(self.tabview, self.config, self.clipboard, self._on_file_selected)
        self.task_tab = TaskManagerTab(
            self.tabview,
            on_refresh=self._request_task_refresh,
            on_terminate=self._terminate_task,
            on_auto_refresh_toggle=self._toggle_task_auto_refresh,
        )

        logger.info("UI built successfully")

    def _on_file_selected(self, file_path: str) -> None:
        """Handle file selection."""
        logger.info(f"File selected: {file_path}")

    def _start_services(self) -> None:
        self.task_monitor = ProcessMonitor(self.task_queue, refresh_interval=self.config.get("task_refresh_interval", 2))
        self.task_monitor.start()
        self.root.after(500, self._pump_task_queue)
        logger.info("Task monitor started")

    def _pump_task_queue(self) -> None:
        """Consume task monitor messages and update the UI."""
        try:
            while True:
                msg_type, payload = self.task_queue.get(block=False)
                if msg_type == 'processes':
                    self.task_tab.update_processes(payload)
                elif msg_type == 'error':
                    logger.error(f"Process monitor error: {payload}")
        except queue.Empty:
            pass
        except Exception as e:
            logger.error(f"Error handling task queue: {e}")
        finally:
            self.root.after(1000, self._pump_task_queue)

    def _request_task_refresh(self) -> None:
        """Request an immediate refresh from the task monitor."""
        if self.task_monitor:
            self.task_monitor.trigger_refresh()

    def _terminate_task(self, pid: int) -> Tuple[bool, str]:
        """Terminate a selected process through ProcessMonitor."""
        if not self.task_monitor:
            return False, "Task monitor unavailable"
        return ProcessMonitor.terminate_process(pid)

    def _toggle_task_auto_refresh(self, enabled: bool) -> None:
        """Enable or disable automatic task refresh."""
        if self.task_monitor:
            self.task_monitor.set_paused(not enabled)

    def _on_close(self) -> None:
        try:
            if self.task_monitor:
                self.task_monitor.stop()
                self.task_monitor.join(timeout=2)

            if hasattr(self, 'scanner_tab') and getattr(self.scanner_tab, 'scanner', None):
                try:
                    self.scanner_tab.scanner.stop()
                except Exception:
                    pass

            self.config.set("window_geometry", self.root.geometry())
            logger.info("Application closed gracefully")
        except Exception as e:
            logger.error(f"Error during close: {e}")
        finally:
            self.root.destroy()


def main() -> None:
    """Main entry point."""
    setup_logging(log_level=logging_module.INFO)
    logger.info("=" * 80)
    logger.info("PROJECT EXPLORER PRO V2 (CustomTkinter) - Starting")
    logger.info(f"Python: {sys.version}")
    logger.info(f"Platform: {platform.platform()}")
    logger.info("=" * 80)

    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")

    try:
        if platform.system() == "Windows":
            try:
                import ctypes
                ctypes.windll.shcore.SetProcessDpiAwareness(1)
            except Exception:
                pass

        ctk.set_widget_scaling(1.0)
        ctk.set_window_scaling(1.0)

        root = ctk.CTk()
        app = ProjectExplorerPro(root)
        root.mainloop()

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        messagebox.showerror("Error", f"Fatal error: {e}")
        sys.exit(1)

    logger.info("Application exited")


if __name__ == "__main__":
    main()