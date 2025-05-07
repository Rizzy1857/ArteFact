import hashlib
import json
from pathlib import Path
from rich.console import Console
from rich.table import Table

console = Console()

SUPPORTED_ALGORITHMS = {
    "md5": hashlib.md5,
    "sha1": hashlib.sha1,
    "sha256": hashlib.sha256
}

def hash_file(file_path: Path, algorithm: str = "sha256") -> str:
    if algorithm not in SUPPORTED_ALGORITHMS:
        raise ValueError(f"Unsupported algorithm: {algorithm}. Supported algorithms are: {', '.join(SUPPORTED_ALGORITHMS.keys())}")
    
    hasher = SUPPORTED_ALGORITHMS[algorithm]()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except FileNotFoundError:
        console.print(f"[red]Error:[/] File '{file_path}' not found.")
        raise
    except PermissionError:
        console.print(f"[red]Error:[/] Permission denied for file '{file_path}'.")
        raise

def hash_directory(dir_path: Path, algorithm: str = "sha256", output_format: str = "table") -> dict:
    if not dir_path.is_dir():
        raise ValueError(f"Invalid directory path: {dir_path}")
    
    results = {}
    for file in dir_path.rglob("*"):
        if file.is_file():
            results[str(file)] = hash_file(file, algorithm)
    
    if not results:
        console.print("[yellow]Warning:[/] No files found in the directory.")
        return {}

    if output_format == "json":
        json_output = json.dumps(results, indent=2)
        console.print_json(json_output)
        return results
    elif output_format == "table":
        table = Table(title=f"Hashes ({algorithm.upper()})", show_lines=True)
        table.add_column("File", style="cyan", overflow="fold")
        table.add_column("Hash", style="green")
        for file, hash_val in results.items():
            table.add_row(file, hash_val)
        console.print(table)
        return results
    else:
        raise ValueError(f"Unsupported output format: {output_format}. Use 'table' or 'json'.")