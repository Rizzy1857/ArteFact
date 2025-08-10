"""
Core utilities and configuration for Artefact.
Provides central configuration, logging setup, and common utilities.
"""

import logging
import os
import json
import time
import shutil
import threading
from pathlib import Path
from typing import Optional, Dict, Any, Union
from datetime import datetime

# Version and metadata
__version__ = "0.4.0"
__codename__ = "Cold Open"

# Configuration version for compatibility
CONFIG_VERSION = "1.0.0"

# Default configuration
DEFAULT_CONFIG = {
    'version': CONFIG_VERSION,
    'logging': {
        'level': 'INFO',
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        'file': None,  # Set to path for file logging
        'max_size': 10 * 1024 * 1024,  # 10MB
        'backup_count': 5,
        'compress': True
    },
    'output': {
        'color': True,
        'verbose': False,
        'quiet': False
    },
    'paths': {
        'temp_dir': None,  # Use system temp if None
        'output_dir': './output',
        'config_dir': None,  # Use user config dir if None
        'backup_dir': './backups'
    },
    'resources': {
        'max_memory': '80%',
        'max_cpu': '90%',
        'monitor_interval': 60  # seconds
    },
    'security': {
        'hash_verify': True,
        'read_only': True,
        'audit_log': True
    }
}


class ArtefactConfig:
    """Central configuration manager for Artefact."""
    
    def __init__(self, config_dict: Optional[Dict[str, Any]] = None):
        """Initialize configuration with optional custom settings."""
        self._config = DEFAULT_CONFIG.copy()
        self._load_env_vars()
        if config_dict:
            self._update_config(config_dict)
        self._setup_logging()
        self._setup_monitoring()
        
    def _load_env_vars(self):
        """Load configuration from environment variables."""
        prefix = "ARTEFACT_"
        for key in os.environ:
            if key.startswith(prefix):
                config_key = key[len(prefix):].lower()
                value = os.environ[key]
                
                # Convert to appropriate type
                if value.lower() in ('true', 'false'):
                    value = value.lower() == 'true'
                elif value.isdigit():
                    value = int(value)
                elif value.replace('.', '').isdigit():
                    value = float(value)
                    
                self.set(config_key, value)
    
    def _update_config(self, config_dict: Dict[str, Any]) -> None:
        """Recursively update configuration with new values."""
        def update_nested(original, updates):
            for key, value in updates.items():
                if key in original and isinstance(original[key], dict) and isinstance(value, dict):
                    update_nested(original[key], value)
                else:
                    original[key] = value
        
        update_nested(self._config, config_dict)
    
    def _setup_logging(self) -> None:
        """Setup logging based on configuration with rotation."""
        from logging.handlers import RotatingFileHandler
        
        log_config = self._config['logging']
        level = getattr(logging, log_config['level'].upper(), logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(log_config['format'])
        
        # Setup root logger
        logger = logging.getLogger('Artefact')
        logger.setLevel(level)
        
        # Remove existing handlers
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Console handler
        if not self._config['output']['quiet']:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        # File handler with rotation if specified
        if log_config['file']:
            file_handler = RotatingFileHandler(
                log_config['file'],
                maxBytes=log_config['max_size'],
                backupCount=log_config['backup_count']
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            
    def _setup_monitoring(self):
        """Setup resource monitoring."""
        import psutil
        import threading
        
        def monitor_resources():
            while True:
                try:
                    # Get resource usage
                    cpu = psutil.cpu_percent(interval=1)
                    mem = psutil.virtual_memory().percent
                    
                    # Check thresholds
                    cpu_limit = float(self._config['resources']['max_cpu'].rstrip('%'))
                    mem_limit = float(self._config['resources']['max_memory'].rstrip('%'))
                    
                    if cpu > cpu_limit or mem > mem_limit:
                        logger = logging.getLogger('Artefact')
                        logger.warning(
                            f"Resource usage high - CPU: {cpu}%, Memory: {mem}%"
                        )
                        
                    time.sleep(self._config['resources']['monitor_interval'])
                except Exception as e:
                    logging.error(f"Monitoring error: {e}")
                    
        # Start monitoring in background
        thread = threading.Thread(target=monitor_resources, daemon=True)
        thread.start()
        
    def save_config(self, path: Optional[Path] = None) -> None:
        """Save current configuration to JSON file."""
        if path is None:
            path = Path(self._config['paths']['config_dir']) / 'config.json'
            
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create backup if file exists
        if path.exists() and self._config['security']['backup_config']:
            backup_dir = Path(self._config['paths']['backup_dir'])
            backup_dir.mkdir(parents=True, exist_ok=True)
            backup_path = backup_dir / f"config_{int(time.time())}.json"
            shutil.copy2(path, backup_path)
            
        with path.open('w') as f:
            json.dump(self._config, f, indent=4)
            
    def load_config(self, path: Path) -> None:
        """Load configuration from JSON file with version check."""
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")
            
        with path.open('r') as f:
            config = json.load(f)
            
        # Version compatibility check
        if 'version' not in config:
            raise ValueError("Config file missing version information")
            
        config_version = config['version']
        if config_version != CONFIG_VERSION:
            logger = logging.getLogger('Artefact')
            logger.warning(
                f"Config version mismatch: file={config_version}, current={CONFIG_VERSION}"
            )
            
        self._update_config(config)
        self._setup_logging()  # Reload logging with new config
    
    def get(self, key_path: str, default=None) -> Any:
        """Get configuration value using dot notation (e.g., 'logging.level')."""
        keys = key_path.split('.')
        value = self._config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value: Any) -> None:
        """Set configuration value using dot notation."""
        keys = key_path.split('.')
        config = self._config
        
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        config[keys[-1]] = value
        
        # Reconfigure logging if logging settings changed
        if keys[0] == 'logging':
            self._setup_logging()
    
    def get_temp_dir(self) -> Path:
        """Get temporary directory for operations."""
        temp_dir = self.get('paths.temp_dir')
        if temp_dir:
            return Path(temp_dir)
        return Path.cwd() / 'temp'
    
    def get_output_dir(self) -> Path:
        """Get default output directory."""
        return Path(self.get('paths.output_dir', './output'))
    
    def ensure_output_dir(self, subdir: Optional[str] = None) -> Path:
        """Ensure output directory exists and return path."""
        output_dir = self.get_output_dir()
        if subdir:
            output_dir = output_dir / subdir
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir


# Global configuration instance
_config = ArtefactConfig()


def get_config() -> ArtefactConfig:
    """Get the global configuration instance."""
    return _config


def setup_config(config_dict: Dict[str, Any]) -> None:
    """Setup global configuration with custom settings."""
    global _config
    _config = ArtefactConfig(config_dict)


def get_logger(name: str = 'Artefact') -> logging.Logger:
    """Get a logger instance for the given name."""
    return logging.getLogger(name)


def validate_file_path(file_path: Path, must_exist: bool = True) -> bool:
    """Validate that a file path is valid and optionally exists."""
    if not isinstance(file_path, Path):
        file_path = Path(file_path)
    
    if must_exist and not file_path.exists():
        return False
    
    if must_exist and not file_path.is_file():
        return False
    
    return True


def validate_directory_path(dir_path: Path, must_exist: bool = True, create_if_missing: bool = False) -> bool:
    """Validate that a directory path is valid and optionally exists."""
    if not isinstance(dir_path, Path):
        dir_path = Path(dir_path)
    
    if must_exist and not dir_path.exists():
        if create_if_missing:
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                return True
            except Exception:
                return False
        return False
    
    if must_exist and not dir_path.is_dir():
        return False
    
    return True


def format_bytes(bytes_count: int) -> str:
    """Format byte count into human-readable string."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_count < 1024.0:
            return f"{bytes_count:.2f} {unit}"
        bytes_count /= 1024.0
    return f"{bytes_count:.2f} PB"


def safe_filename(filename: str) -> str:
    """Create a safe filename by removing/replacing invalid characters."""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename.strip()


class ProgressTracker:
    """Simple progress tracking utility."""
    
    def __init__(self, total: int, description: str = "Processing"):
        """Initialize progress tracker."""
        self.total = total
        self.current = 0
        self.description = description
        self.logger = get_logger()
    
    def update(self, increment: int = 1) -> None:
        """Update progress by increment."""
        self.current = min(self.current + increment, self.total)
        if self.current % max(1, self.total // 10) == 0 or self.current == self.total:
            percentage = (self.current / self.total) * 100
            self.logger.info(f"{self.description}: {percentage:.1f}% ({self.current}/{self.total})")
    
    def finish(self) -> None:
        """Mark progress as complete."""
        self.current = self.total
        self.logger.info(f"{self.description}: Complete ({self.total}/{self.total})")
