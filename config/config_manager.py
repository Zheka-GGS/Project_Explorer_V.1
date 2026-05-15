"""Configuration management."""

import os
import json
from typing import Any, Dict, List, Optional

from utils.logging_utils import get_logger

logger = get_logger(__name__)


class ConfigManager:
    """Manages application configuration and user preferences.
    
    Features:
        - Persistent JSON-based configuration
        - Default values
        - Recent paths tracking
        - Type-safe get/set methods
    """
    
    # Configuration file path
    CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".explorer_pro_config.json")
    
    # Default configuration
    DEFAULTS: Dict[str, Any] = {
        "theme": "Modern Dark",
        "scan_mode": "quick",
        "skip_system_dirs": False,
        "task_refresh_interval": 2,
        "recent_paths": [],
        "search_case_sensitive": False,
        "search_regex": False,
        "search_include_hidden": True,
        "tree_depth_limit": 5,
        "font_size": 10,
        "window_geometry": "1450x850",
        "auto_refresh": True,
    }
    
    def __init__(self):
        """Initialize configuration manager."""
        self.config: Dict[str, Any] = self.DEFAULTS.copy()
        self.load()
    
    def load(self) -> None:
        """Load configuration from file."""
        if not os.path.exists(self.CONFIG_PATH):
            logger.info(f"Config file not found, using defaults: {self.CONFIG_PATH}")
            return
        
        try:
            with open(self.CONFIG_PATH, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                
                # Type check
                if not isinstance(loaded, dict):
                    logger.warning(f"Invalid config format, using defaults")
                    return
                
                # Update with loaded values (preserving defaults for missing keys)
                for key, value in loaded.items():
                    if key in self.DEFAULTS:
                        self.config[key] = value
                
                logger.info(f"Configuration loaded from {self.CONFIG_PATH}")
        
        except json.JSONDecodeError as e:
            logger.error(f"Config JSON decode error: {e}")
        except (IOError, OSError) as e:
            logger.error(f"Config file read error: {e}")
    
    def save(self) -> None:
        """Save configuration to file."""
        try:
            # Ensure directory exists
            config_dir = os.path.dirname(self.CONFIG_PATH)
            os.makedirs(config_dir, exist_ok=True)
            
            with open(self.CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"Configuration saved to {self.CONFIG_PATH}")
        
        except (IOError, OSError) as e:
            logger.error(f"Failed to save config: {e}")
    
    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """Get configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        val = self.config.get(key)
        
        if val is not None:
            return val
        
        if default is not None:
            return default
        
        return self.DEFAULTS.get(key)
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value and save.
        
        Args:
            key: Configuration key
            value: Value to set
        """
        if not isinstance(key, str):
            logger.warning(f"Invalid config key type: {type(key)}")
            return
        
        self.config[key] = value
        self.save()
        logger.debug(f"Config set: {key} = {value}")
    
    def add_recent_path(self, path: str) -> None:
        """Add path to recent paths list.
        
        Args:
            path: Path to add
        """
        if not isinstance(path, str) or not path:
            return
        
        paths: List[str] = self.get("recent_paths", [])
        
        # Remove if already in list
        if path in paths:
            paths.remove(path)
        
        # Add to beginning
        paths.insert(0, path)
        
        # Keep only 10 most recent
        paths = paths[:10]
        
        self.config["recent_paths"] = paths
        self.save()
        logger.debug(f"Added recent path: {path}")
    
    def get_recent_paths(self) -> List[str]:
        """Get list of recent paths.
        
        Returns:
            List of recent paths
        """
        paths = self.get("recent_paths", [])
        if not isinstance(paths, list):
            return []
        
        # Filter out non-existent paths
        return [p for p in paths if isinstance(p, str) and os.path.exists(p)]
    
    def reset_to_defaults(self) -> None:
        """Reset all settings to defaults."""
        self.config = self.DEFAULTS.copy()
        self.save()
        logger.info("Configuration reset to defaults")
