import hashlib
import json
import logging
from pathlib import Path
from typing import Dict
from artefact.error_handler import handle_error

SUPPORTED_ALGORITHMS = {
    "md5": hashlib.md5,
    "sha1": hashlib.sha1,
    "sha256": hashlib.sha256,
}


def hash_file(file_path: Path, algorithm: str = "sha256") -> str:
    """Return the hash of a file using the specified algorithm."""
    if algorithm not in SUPPORTED_ALGORITHMS:
        handle_error(ValueError(f"Unsupported algorithm: {algorithm}"), context="hash_file")
        raise ValueError(f"Unsupported algorithm: {algorithm}")
    hasher = SUPPORTED_ALGORITHMS[algorithm]()
    try:
        with file_path.open("rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except (FileNotFoundError, PermissionError) as e:
        handle_error(e, context="hash_file")
        raise


def hash_directory(
    dir_path: Path, algorithm: str = "sha256", output_format: str = "table"
) -> Dict[str, str]:
    """Return hashes for all files in a directory."""
    if not dir_path.is_dir():
        handle_error(ValueError(f"Invalid directory path: {dir_path}"), context="hash_directory")
        raise ValueError(f"Invalid directory path: {dir_path}")
    results = {
        str(file): hash_file(file, algorithm)
        for file in dir_path.rglob("*")
        if file.is_file()
    }
    if not results:
        # Optionally, could use handle_error for warnings
        return {}
    if output_format == "json":
        from rich.console import Console

        console = Console()
        console.print_json(json.dumps(results, indent=2))
    elif output_format == "table":
        from rich.console import Console
        from rich.table import Table

        console = Console()
        table = Table(title=f"Hashes ({algorithm.upper()})", show_lines=True)
        table.add_column("File", style="cyan", overflow="fold")
        table.add_column("Hash", style="green")
        for file, hash_val in results.items():
            table.add_row(file, hash_val)
        console.print(table)
    else:
        handle_error(ValueError(f"Unsupported output format: {output_format}"), context="hash_directory")
        raise ValueError(f"Unsupported output format: {output_format}")
    return results