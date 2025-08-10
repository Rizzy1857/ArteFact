"""
Disk Image Mounting and Extraction Module for ArteFact
- List partitions/volumes in raw/E01 images
- Extract files from partitions
- (Future) Mount images as virtual drives (where supported)
"""
import sys
from pathlib import Path
from rich.console import Console
import subprocess
import shutil
try:
    import pytsk3
except ImportError:
    pytsk3 = None

console = Console()

def convert_e01_to_raw(e01_path, out_path):
    """Convert an E01 image to raw using ewfexport if available."""
    if shutil.which('ewfexport') is None:
        console.print("[red]ewfexport not found. Please install libewf-tools or ewfexport to convert E01 images.")
        return False
    try:
        subprocess.run(['ewfexport', '-t', 'raw', '-o', out_path, e01_path], check=True)
        console.print(f"[green]Converted:[/] {e01_path} -> {out_path}")
        return True
    except Exception as e:
        console.print(f"[red]E01 conversion failed:[/] {e}")
        return False

def open_image(image_path):
    image_path = Path(image_path)
    if image_path.suffix.lower() == '.e01':
        raw_path = image_path.with_suffix('.img')
        if not raw_path.exists():
            console.print(f"[yellow]E01 detected. Converting to raw image: {raw_path}")
            if not convert_e01_to_raw(str(image_path), str(raw_path)):
                return None
        return pytsk3.Img_Info(str(raw_path))
    else:
        return pytsk3.Img_Info(str(image_path))

def list_partitions(image_path):
    if pytsk3 is None:
        console.print("[red]pytsk3 not installed. Install with 'pip install pytsk3'.")
        return
    img = open_image(image_path)
    if img is None:
        return
    vol = pytsk3.Volume_Info(img)
    for part in vol:
        console.print(f"[cyan]Partition {part.addr}[/]: Start: {part.start}, Length: {part.len}, Desc: {part.desc}")

def extract_partition(image_path, partition_addr, output_dir):
    if pytsk3 is None:
        console.print("[red]pytsk3 not installed. Install with 'pip install pytsk3'.")
        return
    img = open_image(image_path)
    if img is None:
        return
    vol = pytsk3.Volume_Info(img)
    for part in vol:
        if str(part.addr) == str(partition_addr):
            fs = pytsk3.FS_Info(img, offset=part.start * 512)
            for dir_entry in fs.open_dir(path="/"):
                if dir_entry.info.name.name in [b".", b".."]:
                    continue
                name = dir_entry.info.name.name.decode()
                if dir_entry.info.meta and dir_entry.info.meta.type == pytsk3.TSK_FS_META_TYPE_REG:
                    out_path = Path(output_dir) / name
                    with open(out_path, "wb") as out:
                        f = fs.open(name)
                        out.write(f.read_random(0, f.info.meta.size))
                    console.print(f"[green]Extracted:[/] {out_path}")
            break

def hash_image(image_path):
    import hashlib
    image_path = Path(image_path)
    h = hashlib.sha256()
    with image_path.open('rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Disk Image Partition Listing and Extraction Tool")
    parser.add_argument('-i', '--input', required=True, help='Input disk image file (.img, .dd, .E01)')
    parser.add_argument('--list', action='store_true', help='List partitions/volumes in the image')
    parser.add_argument('--extract', metavar='PART_ADDR', help='Extract all files from the given partition address')
    parser.add_argument('-o', '--output', help='Output directory for extracted files')
    parser.add_argument('--hash', action='store_true', help='Print SHA256 hash of the image file')
    args = parser.parse_args()
    if args.hash:
        hashval = hash_image(args.input)
        console.print(f"[bold green]SHA256:[/] {hashval}")
    elif args.list:
        list_partitions(args.input)
    elif args.extract:
        if not args.output:
            console.print("[red]Output directory required for extraction.")
            return
        extract_partition(args.input, args.extract, args.output)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
