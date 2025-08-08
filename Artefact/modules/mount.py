"""
Disk Image Mounting Module
==========================

Mounts and extracts data from forensic disk images.
"""

from pathlib import Path
from rich.console import Console

from Artefact.error_handler import with_error_handling

console = Console()

try:
    import pytsk3
    PYTSK3_AVAILABLE = True
except ImportError:
    PYTSK3_AVAILABLE = False

@with_error_handling("list_partitions")
def list_partitions(image_path: str):
    """List partitions in a disk image."""
    if not PYTSK3_AVAILABLE:
        console.print("[red]pytsk3 not available. Install with 'pip install pytsk3'[/]")
        return
    
    try:
        img = pytsk3.Img_Info(str(image_path))
        vol = pytsk3.Volume_Info(img)
        
        console.print(f"[green]Partitions in {image_path}:[/]")
        for part in vol:
            desc = part.desc.decode() if part.desc else "Unknown"
            console.print(f"[cyan]Partition {part.addr}[/]: Start: {part.start}, Length: {part.len}, Desc: {desc}")
    except Exception as e:
        console.print(f"[red]Error listing partitions: {e}[/]")

@with_error_handling("extract_partition")
def extract_partition(image_path: str, partition_addr: str, output_dir: str):
    """Extract files from a partition."""
    if not PYTSK3_AVAILABLE:
        console.print("[red]pytsk3 not available. Install with 'pip install pytsk3'[/]")
        return
    
    try:
        img = pytsk3.Img_Info(str(image_path))
        vol = pytsk3.Volume_Info(img)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        for part in vol:
            if str(part.addr) == str(partition_addr):
                try:
                    fs = pytsk3.FS_Info(img, offset=part.start * 512)
                    console.print(f"[green]Extracting partition {partition_addr}...[/]")
                    
                    # Simple file extraction (limited implementation)
                    file_count = 0
                    for root_entry in fs.open_dir('/'):
                        if root_entry.info.name.name in [b'.', b'..']:
                            continue
                        try:
                            file_obj = fs.open(root_entry.info.name.name)
                            if file_obj and file_obj.info.meta:
                                filename = root_entry.info.name.name.decode('utf-8', errors='ignore')
                                out_file = output_path / filename
                                with open(out_file, 'wb') as f:
                                    f.write(file_obj.read_random(0, file_obj.info.meta.size))
                                file_count += 1
                                console.print(f"Extracted: {filename}")
                        except Exception:
                            continue
                    
                    console.print(f"[green]Extracted {file_count} files to {output_dir}[/]")
                    return
                except Exception as e:
                    console.print(f"[red]Error reading filesystem: {e}[/]")
                    return
        
        console.print(f"[yellow]Partition {partition_addr} not found[/]")
    except Exception as e:
        console.print(f"[red]Error extracting partition: {e}[/]")
