"""
Centralized error handling module for ArteFact.
Handles exceptions, logs errors, and provides user-friendly fixes.
"""
import logging
from rich.console import Console
import re

console = Console()
logger = logging.getLogger("Artefact")


class ArtefactError(Exception):
    """Base class for ArteFact errors."""
    pass


class ValidationError(ArtefactError):
    """Raised when input validation fails."""
    pass


class ConfigurationError(ArtefactError):
    """Raised when configuration is invalid."""
    pass


class ProcessingError(ArtefactError):
    """Raised when processing operations fail."""
    pass


def handle_error(exc, context=None):
    """
    Central error handler. Logs, prints, and suggests fixes for known errors.
    Args:
        exc (Exception): The exception instance.
        context (str, optional): Additional context about where the error occurred.
    """
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
        
    elif hasattr(exc, 'stderr') and exc.stderr:
        console.print(f"[red]Subprocess error:[/] {exc.stderr}")
        console.print("[yellow]Fix:[/] Check the command and its arguments.")
        
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


def cli_error(msg: str, exc: Exception = None, context: str = None):
    """
    Unified CLI error handler. Prints, logs, and delegates to handle_error if exception is given.
    """
    if exc is not None:
        handle_error(exc, context)
    else:
        console.print(f"[red]Error:[/] {msg}")
        logger.error(msg)


def validate_input(value, validation_type: str, **kwargs):
    """
    Validate input based on type.
    
    Args:
        value: Value to validate
        validation_type: Type of validation ('file', 'dir', 'hash_algorithm', etc.)
        **kwargs: Additional validation parameters
    
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
            valid_types = ['jpg', 'jpeg', 'png', 'pdf', 'doc', 'docx', 'exe', 'dll']
            invalid_types = [t for t in value if t.lower() not in valid_types]
            if invalid_types:
                raise ValidationError(f"Invalid file types: {', '.join(invalid_types)}. Valid options: {', '.join(valid_types)}")
                
        return True
        
    except Exception as e:
        if isinstance(e, ValidationError):
            raise
        else:
            raise ValidationError(f"Validation failed for {validation_type}: {str(e)}")


def safe_execute(func, *args, context: str = None, **kwargs):
    """
    Safely execute a function with error handling.
    
    Args:
        func: Function to execute
        *args: Function arguments
        context: Context description for error reporting
        **kwargs: Function keyword arguments
        
    Returns:
        Function result or None if error occurred
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        handle_error(e, context=context or func.__name__)
        return None


def with_error_handling(context: str = None):
    """
    Decorator for automatic error handling.
    
    Args:
        context: Context description for error reporting
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                handle_error(e, context=context or func.__name__)
                raise
        return wrapper
    return decorator
