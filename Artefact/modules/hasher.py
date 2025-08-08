"""
File and Directory Hashing Module
=================================

Provides secure hashing functionality for files and directories
using various algorithms (MD5, SHA1, SHA256, SHA512).
"""

import hashlib
import json
import logging
from pathlib import Path
from typing import Dict, Optional, List
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn

from Artefact.error_handler import handle_error, ValidationError, with_error_handling

console = Console()
logger = logging.getLogger(__name__)

SUPPORTED_ALGORITHMS = {
    "md5": hashlib.md5,
    "sha1": hashlib.sha1,
    "sha256": hashlib.sha256,
    "sha512": hashlib.sha512,
}

CHUNK_SIZE = 64 * 1024  # 64KB chunks for efficient memory usage


@with_error_handling("hash_file")
def hash_file(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Calculate hash of a single file using specified algorithm.
    
    Args:
        file_path: Path to the file to hash
        algorithm: Hash algorithm to use (md5, sha1, sha256, sha512)
        
    Returns:
        Hexadecimal hash string
        
    Raises:
        ValidationError: If algorithm is not supported
        FileNotFoundError: If file doesn't exist
        PermissionError: If file cannot be read
    """
    if not isinstance(file_path, Path):
        file_path = Path(file_path)
    
    # Validate inputs
    if algorithm.lower() not in SUPPORTED_ALGORITHMS:
        raise ValidationError(f"Unsupported algorithm: {algorithm}")
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if not file_path.is_file():
        raise ValidationError(f"Path is not a file: {file_path}")
    
    # Initialize hasher
    hasher = SUPPORTED_ALGORITHMS[algorithm.lower()]()
    
    try:
        with file_path.open("rb") as f:
            while True:
                chunk = f.read(CHUNK_SIZE)
                if not chunk:
                    break
                hasher.update(chunk)
        
        result = hasher.hexdigest()
        logger.debug(f"Calculated {algorithm.upper()} hash for {file_path}: {result}")
        return result
        
    except PermissionError:
        raise PermissionError(f"Permission denied reading file: {file_path}")
    except Exception as e:
        raise RuntimeError(f"Failed to hash file {file_path}: {str(e)}")


@with_error_handling("hash_directory")
def hash_directory(
    dir_path: Path, 
    algorithm: str = "sha256", 
    output_format: str = "table",
    recursive: bool = True,
    include_hidden: bool = False
) -> Dict[str, str]:
    """
    Calculate hashes for all files in a directory.
    
    Args:
        dir_path: Path to the directory
        algorithm: Hash algorithm to use
        output_format: Output format (table, json, csv)
        recursive: Whether to process subdirectories
        include_hidden: Whether to include hidden files
        
    Returns:
        Dictionary mapping file paths to hash values
        
    Raises:
        ValidationError: If directory doesn't exist or algorithm invalid
    """
    if not isinstance(dir_path, Path):
        dir_path = Path(dir_path)
    
    # Validate inputs
    if not dir_path.exists():
        raise ValidationError(f"Directory not found: {dir_path}")
    
    if not dir_path.is_dir():
        raise ValidationError(f"Path is not a directory: {dir_path}")
    
    if algorithm.lower() not in SUPPORTED_ALGORITHMS:
        raise ValidationError(f"Unsupported algorithm: {algorithm}")
    
    # Collect files to hash
    files_to_hash = []
    pattern = "**/*" if recursive else "*"
    
    for file_path in dir_path.glob(pattern):
        if file_path.is_file():
            # Skip hidden files if not requested
            if not include_hidden and any(part.startswith('.') for part in file_path.parts):
                continue
            files_to_hash.append(file_path)
    
    if not files_to_hash:
        console.print(f"[yellow]No files found in directory: {dir_path}[/]")
        return {}
    
    results = {}
    
    # Hash files with progress bar
    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
        transient=True
    ) as progress:
        task = progress.add_task(f"Hashing files ({algorithm.upper()})", total=len(files_to_hash))
        
        for file_path in files_to_hash:
            try:
                file_hash = hash_file(file_path, algorithm)
                results[str(file_path.relative_to(dir_path))] = file_hash
                progress.advance(task)
            except Exception as e:
                logger.warning(f"Failed to hash {file_path}: {str(e)}")
                results[str(file_path.relative_to(dir_path))] = f"ERROR: {str(e)}"
                progress.advance(task)
    
    # Display results
    _display_results(results, algorithm, output_format)
    
    return results


def _display_results(results: Dict[str, str], algorithm: str, output_format: str):
    """Display hashing results in the specified format."""
    if not results:
        return
    
    if output_format.lower() == "json":
        console.print_json(json.dumps(results, indent=2))
        
    elif output_format.lower() == "csv":
        console.print("File,Hash")
        for file_path, file_hash in results.items():
            console.print(f'"{file_path}",{file_hash}')
            
    elif output_format.lower() == "table":
        table = Table(title=f"File Hashes ({algorithm.upper()})", show_lines=True)
        table.add_column("File", style="cyan", overflow="fold")
        table.add_column("Hash", style="green", no_wrap=False)
        
        for file_path, file_hash in results.items():
            # Color code error entries
            if file_hash.startswith("ERROR:"):
                table.add_row(file_path, f"[red]{file_hash}[/red]")
            else:
                table.add_row(file_path, file_hash)
        
        console.print(table)
    else:
        raise ValidationError(f"Unsupported output format: {output_format}")


@with_error_handling("batch_hash")
def batch_hash_files(file_list: List[Path], algorithm: str = "sha256") -> Dict[str, str]:
    """
    Hash multiple files in batch.
    
    Args:
        file_list: List of file paths to hash
        algorithm: Hash algorithm to use
        
    Returns:
        Dictionary mapping file paths to hash values
    """
    results = {}
    
    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
        transient=True
    ) as progress:
        task = progress.add_task(f"Hashing {len(file_list)} files", total=len(file_list))
        
        for file_path in file_list:
            try:
                file_hash = hash_file(file_path, algorithm)
                results[str(file_path)] = file_hash
            except Exception as e:
                logger.warning(f"Failed to hash {file_path}: {str(e)}")
                results[str(file_path)] = f"ERROR: {str(e)}"
            
            progress.advance(task)
    
    return results


def verify_hash(file_path: Path, expected_hash: str, algorithm: str = "sha256") -> bool:
    """
    Verify a file's hash against expected value.
    
    Args:
        file_path: Path to file to verify
        expected_hash: Expected hash value
        algorithm: Hash algorithm to use
        
    Returns:
        True if hash matches, False otherwise
    """
    try:
        actual_hash = hash_file(file_path, algorithm)
        return actual_hash.lower() == expected_hash.lower()
    except Exception as e:
        logger.error(f"Hash verification failed for {file_path}: {str(e)}")
        return False


if __name__ == "__main__":
    # CLI interface for standalone usage
    import argparse
    
    parser = argparse.ArgumentParser(description="File and Directory Hashing Tool")
    parser.add_argument("path", help="File or directory path to hash")
    parser.add_argument("-a", "--algorithm", default="sha256", 
                       choices=list(SUPPORTED_ALGORITHMS.keys()),
                       help="Hash algorithm to use")
    parser.add_argument("-f", "--format", default="table",
                       choices=["table", "json", "csv"],
                       help="Output format")
    parser.add_argument("--no-recursive", action="store_true",
                       help="Don't process subdirectories")
    parser.add_argument("--include-hidden", action="store_true",
                       help="Include hidden files")
    
    args = parser.parse_args()
    
    path = Path(args.path)
    
    if path.is_file():
        try:
            result = hash_file(path, args.algorithm)
            console.print(f"[green]{args.algorithm.upper()}:[/] {result}")
        except Exception as e:
            console.print(f"[red]Error:[/] {str(e)}")
    elif path.is_dir():
        hash_directory(
            path,
            algorithm=args.algorithm,
            output_format=args.format,
            recursive=not args.no_recursive,
            include_hidden=args.include_hidden
        )
    else:
        console.print(f"[red]Error:[/] Path not found: {path}")
