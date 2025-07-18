"""
Centralized error handling module for ArteFact.
Handles exceptions, logs errors, and provides user-friendly fixes.
"""
import logging
from rich.console import Console
import re

console = Console()
logger = logging.getLogger("artefact")

class ArtefactError(Exception):
    """Base class for ArteFact errors."""
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
    elif isinstance(exc, ImportError):
        console.print(f"[red]Error:[/] Import failed: {exc}")
        console.print("[yellow]Fix:[/] Ensure all required packages are installed.")
    elif isinstance(exc, PermissionError):
        console.print(f"[red]Error:[/] Permission denied: {exc}")
        console.print("[yellow]Fix:[/] Check file permissions or try running as administrator.")
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
    else:
        console.print(f"[red]Unexpected error:[/] {exc}")
        console.print("[yellow]Fix:[/] See logs for more details or contact support.")

    # Optionally, re-raise for debugging
    # raise exc

def cli_error(msg: str, exc: Exception = None, context: str = None):
    """
    Unified CLI error handler. Prints, logs, and delegates to handle_error if exception is given.
    """
    if exc is not None:
        handle_error(exc, context)
    else:
        console.print(f"[red]Error:[/] {msg}")
    exit(1)
