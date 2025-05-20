import hashlib
import json
import logging
from pathlib import Path
from typing import Dict

from rich.console import Console
from rich.table import Table

console = Console()
logger = logging.getLogger(__name__)

SUPPORTED_ALGORITHMS = {
    "md5": hashlib.md5,
    "sha1": hashlib.sha1,
    "sha256": hashlib.sha256,
}


def hash_file(file_path: Path, algorithm: str = "sha256") -> str:
    """Return the hash of a file using the specified algorithm."""
    if algorithm not in SUPPORTED_ALGORITHMS:
        raise ValueError(f"Unsupported algorithm: {algorithm}")
    hasher = SUPPORTED_ALGORITHMS[algorithm]()
    try:
        with file_path.open("rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except (FileNotFoundError, PermissionError) as e:
        console.print(f"[red]Error:[/] {e}")
        logger.error(f"File error: {e}")
        raise


def hash_directory(
    dir_path: Path, algorithm: str = "sha256", output_format: str = "table"
) -> Dict[str, str]:
    """Return hashes for all files in a directory."""
    if not dir_path.is_dir():
        raise ValueError(f"Invalid directory path: {dir_path}")
    results = {
        str(file): hash_file(file, algorithm)
        for file in dir_path.rglob("*")
        if file.is_file()
    }
    if not results:
        console.print("[yellow]Warning:[/] No files found in the directory.")
        return {}
    if output_format == "json":
        console.print_json(json.dumps(results, indent=2))
    elif output_format == "table":
        table = Table(title=f"Hashes ({algorithm.upper()})", show_lines=True)
        table.add_column("File", style="cyan", overflow="fold")
        table.add_column("Hash", style="green")
        for file, hash_val in results.items():
            table.add_row(file, hash_val)
        console.print(table)
    else:
        raise ValueError(f"Unsupported output format: {output_format}")
    return results