"""
Output and UI utilities for ArteFact. Handles all console/print/rich output.
"""
from rich.console import Console
from rich.table import Table
import json
import subprocess

console = Console(style="bold cyan", force_terminal=True)

# --- Output for Hashing ---
def print_hash_result(result, algorithm):
    console.print(f"[green]{algorithm.upper()}:[/] {result}")

def print_hash_table(results, algorithm):
    table = Table(title=f"Hashes ({algorithm.upper()})", show_lines=True)
    table.add_column("File", style="cyan", overflow="fold")
    table.add_column("Hash", style="green")
    for file, hash_val in results.items():
        table.add_row(file, hash_val)
    console.print(table)

def print_hash_json(results):
    console.print_json(json.dumps(results, indent=2))

# --- Output for Carving ---
def print_carved_files(carved):
    if not carved:
        console.print("[yellow]No files carved. Try different types or check the image file.")
        return
    for fname in carved:
        console.print(f"[green]Carved:[/] {fname}")
    console.print(f"[bold green]Total files carved:[/] {len(carved)}")

def write_carved_files(carved, output_dir):
    from pathlib import Path
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    for fname, data in carved.items():
        with (output_dir / fname).open('wb') as f:
            f.write(data)

# --- Output for Metadata ---
def print_metadata(meta):
    if meta is None:
        console.print("[yellow]No metadata extractor available for this file type. Try --deep for exiftool.")
    else:
        console.print_json(json.dumps(meta, indent=2))

def print_metadata_deep(file_path):
    try:
        result = subprocess.run([
            'exiftool', str(file_path)
        ], capture_output=True, text=True, check=True)
        console.print(f"[bold green]ExifTool Output:[/]")
        console.print(result.stdout)
    except FileNotFoundError:
        console.print("[red]ExifTool not found. Please install exiftool for deep extraction.")
    except subprocess.CalledProcessError as e:
        console.print(f"[red]ExifTool error:[/] {e}")
