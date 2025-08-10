"""
Centralized error handling module for ArteFact.
Handles exceptions, logs errors, and provides user-friendly fixes.
"""
import logging
import time
import json
import traceback
from typing import Any, Callable, Optional, Union, List, Dict
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from rich.console import Console
import re
import subprocess

# Configure logging
console = Console()
logger = logging.getLogger("Artefact")

# Error statistics tracking
ERROR_STATS = defaultdict(lambda: {
    'count': 0,
    'first_seen': None,
    'last_seen': None,
    'contexts': set(),
    'messages': set()
})

# Custom error hooks
ERROR_HOOKS: List[Callable[[Exception, Optional[str]], None]] = []
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


class ArtefactError(Exception):
    """Base class for ArteFact errors."""
    def __init__(self, message: str, recovery_steps: Optional[List[str]] = None):
        super().__init__(message)
        self.recovery_steps = recovery_steps or []
        self.timestamp = datetime.now()
        self.traceback = traceback.format_exc()
        
    def get_recovery_guide(self) -> str:
        """Get formatted recovery steps if available."""
        if not self.recovery_steps:
            return "No automatic recovery steps available."
            
        steps = "\n".join(f"{i+1}. {step}" for i, step in enumerate(self.recovery_steps))
        return f"Recovery steps:\n{steps}"


class ValidationError(ArtefactError):
    """Raised when input validation fails."""
    pass


class ConfigurationError(ArtefactError):
    """Raised when configuration is invalid."""
    pass


class ProcessingError(ArtefactError):
    """Raised when processing operations fail."""
    pass


def register_error_hook(hook: Callable[[Exception, Optional[str]], None]) -> None:
    """Register a custom error handling hook."""
    ERROR_HOOKS.append(hook)

def get_error_statistics() -> Dict[str, Dict[str, Any]]:
    """Get current error statistics."""
    stats = {}
    for error_type, data in ERROR_STATS.items():
        stats[error_type] = {
            'count': data['count'],
            'first_seen': data['first_seen'],
            'last_seen': data['last_seen'],
            'contexts': list(data['contexts']),
            'messages': list(data['messages'])
        }
    return stats

def save_error_statistics(path: Path) -> None:
    """Save error statistics to JSON file."""
    stats = get_error_statistics()
    path.write_text(json.dumps(stats, indent=2, default=str))

def handle_error(exc: Exception, context: Optional[str] = None) -> None:
    """
    Central error handler. Logs, prints, and suggests fixes for known errors.
    
    Args:
        exc (Exception): The exception instance.
        context (str, optional): Additional context about where the error occurred.
    """
    # Update error statistics
    error_type = exc.__class__.__name__
    now = datetime.now().isoformat()
    
    ERROR_STATS[error_type]['count'] += 1
    ERROR_STATS[error_type]['last_seen'] = now
    if not ERROR_STATS[error_type]['first_seen']:
        ERROR_STATS[error_type]['first_seen'] = now
    if context:
        ERROR_STATS[error_type]['contexts'].add(context)
    ERROR_STATS[error_type]['messages'].add(str(exc))
    if context:
        logger.error(f"[{context}] {exc}")
    else:
        logger.error(str(exc))

    # Print user-friendly message and suggest fixes
    if isinstance(exc, FileNotFoundError):
        console.print(f"[red]Error:[/] File not found: {exc}")
        console.print("[yellow]Fix:[/] Check if the file path is correct and the file exists.")
        
    elif isinstance(exc, PermissionError):
        console.print(f"[red]Error:[/] Permission denied: {exc}")
        console.print("[yellow]Fix:[/] Check file permissions or try running as administrator.")
        
    elif isinstance(exc, ImportError):
        console.print(f"[red]Error:[/] Import failed: {exc}")
        module_name = str(exc).split("'")[1] if "'" in str(exc) else "unknown"
        console.print(f"[yellow]Fix:[/] Install required package: pip install {module_name}")
        
    elif isinstance(exc, ValueError):
        console.print(f"[red]Error:[/] {exc}")
        console.print("[yellow]Fix:[/] Verify the input values and formats.")
        
    elif isinstance(exc, OSError):
        console.print(f"[red]OS error:[/] {exc}")
        console.print("[yellow]Fix:[/] Check file permissions, disk space, or file integrity.")
        
    elif isinstance(exc, re.error):
        console.print(f"[red]Regex error:[/] {exc}")
        console.print("[yellow]Fix:[/] Check your regular expression syntax.")
        
    elif isinstance(exc, subprocess.SubprocessError):
        error_msg = ""
        if hasattr(exc, 'stderr') and exc.stderr:
            error_msg += f"stderr: {exc.stderr}\n"
        if hasattr(exc, 'stdout') and exc.stdout:
            error_msg += f"stdout: {exc.stdout}"
        console.print(f"[red]Subprocess error:[/] {error_msg or str(exc)}")
        console.print("[yellow]Fix:[/] Check the command, its arguments, and system environment.")
        
    elif isinstance(exc, ValidationError):
        console.print(f"[red]Validation error:[/] {exc}")
        console.print("[yellow]Fix:[/] Check input parameters and ensure they meet requirements.")
        
    elif isinstance(exc, ConfigurationError):
        console.print(f"[red]Configuration error:[/] {exc}")
        console.print("[yellow]Fix:[/] Check configuration file or environment variables.")
        
    elif isinstance(exc, ProcessingError):
        console.print(f"[red]Processing error:[/] {exc}")
        console.print("[yellow]Fix:[/] Check input data format and processing parameters.")
        
    else:
        console.print(f"[red]Unexpected error:[/] {exc}")
        console.print("[yellow]Fix:[/] See logs for more details or contact support.")
    
    # Add stack trace in debug mode
    if logger.getEffectiveLevel() <= logging.DEBUG:
        console.print("[red]Stack trace:[/]")
        console.print(traceback.format_exc())
    
    # Execute custom error hooks
    for hook in ERROR_HOOKS:
        try:
            hook(exc, context)
        except Exception as e:
            logger.error(f"Error hook failed: {e}")


def cli_error(msg: str, exc: Optional[Exception] = None, context: Optional[str] = None) -> None:
    """
    Unified CLI error handler. Prints, logs, and delegates to handle_error if exception is given.
    
    Args:
        msg: Error message to display
        exc: Optional exception that caused the error
        context: Optional context where the error occurred
    """
    if exc is not None:
        handle_error(exc, context)
    else:
        console.print(f"[red]Error:[/] {msg}")
        logger.error(msg)


def validate_input(value: Any, validation_type: str, **kwargs) -> bool:
    """
    Validate input based on type.
    
    Args:
        value: Value to validate
        validation_type: Type of validation ('file', 'dir', 'hash_algorithm', etc.)
        **kwargs: Additional validation parameters
    
    Returns:
        bool: True if validation succeeds
    
    Raises:
        ValidationError: If validation fails
    """
    try:
        if validation_type == 'file':
            from pathlib import Path
            path = Path(value)
            if not path.exists():
                raise ValidationError(f"File does not exist: {value}")
            if not path.is_file():
                raise ValidationError(f"Path is not a file: {value}")
                
        elif validation_type == 'directory':
            from pathlib import Path
            path = Path(value)
            if not path.exists():
                if kwargs.get('create_if_missing', False):
                    path.mkdir(parents=True, exist_ok=True)
                else:
                    raise ValidationError(f"Directory does not exist: {value}")
            elif not path.is_dir():
                raise ValidationError(f"Path is not a directory: {value}")
                
        elif validation_type == 'hash_algorithm':
            valid_algorithms = ['md5', 'sha1', 'sha256', 'sha512']
            if value.lower() not in valid_algorithms:
                raise ValidationError(f"Invalid hash algorithm: {value}. Valid options: {', '.join(valid_algorithms)}")
                
        elif validation_type == 'output_format':
            valid_formats = ['json', 'csv', 'table', 'markdown']
            if value.lower() not in valid_formats:
                raise ValidationError(f"Invalid output format: {value}. Valid options: {', '.join(valid_formats)}")
                
        elif validation_type == 'file_types':
            if isinstance(value, str):
                value = [value]
            valid_types = [
                # Images
                'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'webp',
                # Documents
                'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'rtf',
                # Executables and Libraries
                'exe', 'dll', 'sys', 'so', 'dylib',
                # Archives
                'zip', 'rar', '7z', 'tar', 'gz',
                # Memory and disk images
                'mem', 'raw', 'vmem', 'dmp', 'img', 'iso',
                # Other forensic artifacts
                'evt', 'evtx', 'reg', 'log'
            ]
            invalid_types = [t for t in value if t.lower() not in valid_types]
            if invalid_types:
                raise ValidationError(f"Invalid file types: {', '.join(invalid_types)}. Valid options: {', '.join(valid_types)}")
                
        return True
        
    except Exception as e:
        if isinstance(e, ValidationError):
            raise
        else:
            raise ValidationError(f"Validation failed for {validation_type}: {str(e)}")


def safe_execute(func: Callable[..., Any], *args: Any, context: Optional[str] = None, **kwargs: Any) -> Optional[Any]:
    """
    Safely execute a function with error handling.
    
    Args:
        func: Function to execute
        *args: Function arguments
        context: Context description for error reporting
        **kwargs: Function keyword arguments
        
    Returns:
        Optional[Any]: Function result or None if error occurred
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        handle_error(e, context=context or func.__name__)
        return None


def with_error_handling(context: Optional[str] = None) -> Callable:
    """
    Decorator for automatic error handling.
    
    Args:
        context: Context description for error reporting
    
    Returns:
        Callable: Decorated function with error handling
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                handle_error(e, context=context or func.__name__)
                raise
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper
    return decorator
