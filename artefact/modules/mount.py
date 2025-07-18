"""
Disk Image Mounting and Volume Extraction for ArteFact
- Supports listing partitions and extracting files from raw (.img, .dd) and E01 images
- Integrates with SleuthKit (pytsk3) and ewf-tools if available
"""
import os
from pathlib import Path
from rich.console import Console
from Artefact.error_handler import handle_error

console = Console()

try:
    import pytsk3
except ImportError:
    pytsk3 = None

# Optional: EWF support (E01 images)
try:
    import pyewf
except ImportError:
    pyewf = None

def list_partitions(image_path):
    """List partitions in a disk image using pytsk3."""
    if pytsk3 is None:
        console.print("[red]pytsk3 not installed. Install with 'pip install pytsk3'.")
        return
    try:
        img = pytsk3.Img_Info(str(image_path))
        vol = pytsk3.Volume_Info(img)
        for part in vol:
            console.print(f"[cyan]Partition {part.addr}[/]: Start: {part.start}, Length: {part.len}, Desc: {part.desc.decode()}")
    except Exception as e:
        handle_error(e, context="list_partitions")

def extract_partition(image_path, partition_addr, output_dir):
    """Extract files from a partition in a disk image."""
    if pytsk3 is None:
        console.print("[red]pytsk3 not installed. Install with 'pip install pytsk3'.")
        return
    try:
        img = pytsk3.Img_Info(str(image_path))
        vol = pytsk3.Volume_Info(img)
        for part in vol:
            if str(part.addr) == str(partition_addr):
                fs = pytsk3.FS_Info(img, offset=part.start * 512)
                output_dir = Path(output_dir)
                output_dir.mkdir(parents=True, exist_ok=True)
                for dirpath, dirs, files in fs.walk('/'):  # root directory
                    for f in files:
                        try:
                            file_obj = fs.open(f.info.name.name)
                            out_path = output_dir / f.info.name.name.decode()
                            with open(out_path, 'wb') as out:
                                out.write(file_obj.read_random(0, file_obj.info.meta.size))
                        except Exception as e:
                            handle_error(e, context="extract_partition file copy")
                console.print(f"[green]Extracted files from partition {partition_addr} to {output_dir}")
                return
        console.print(f"[yellow]Partition {partition_addr} not found.")
    except Exception as e:
        handle_error(e, context="extract_partition")

# CLI entrypoint
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Disk Image Mounting and Extraction Tool")
    parser.add_argument('-i', '--input', required=True, help='Input disk image file (.img, .dd, .E01)')
    parser.add_argument('--list', action='store_true', help='List partitions')
    parser.add_argument('--extract', type=str, help='Partition address to extract')
    parser.add_argument('-o', '--output', help='Output directory for extraction')
    args = parser.parse_args()
    if args.list:
        list_partitions(args.input)
    elif args.extract and args.output:
        extract_partition(args.input, args.extract, args.output)
    else:
        parser.print_help()
