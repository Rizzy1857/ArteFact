import argparse
from pathlib import Path
from rich.console import Console
import os
import re

console = Console()

# File signatures for common types (magic bytes)
FILE_SIGNATURES = {
    'jpg': {
        'header': b'\xff\xd8\xff',
        'footer': b'\xff\xd9',
        'ext': '.jpg'
    },
    'pdf': {
        'header': b'%PDF-',
        'footer': b'%%EOF',
        'ext': '.pdf'
    },
    'png': {
        'header': b'\x89PNG\r\n\x1a\n',
        'footer': b'IEND\xaeB`\x82',
        'ext': '.png'
    },
    # Add more as needed
}

def carve_files(image_path: Path, output_dir: Path, types=None, chunk_size=1024*1024):
    """Recover files from a disk image by searching for file signatures. Reads in chunks for large files."""
    if not image_path.exists():
        console.print(f"[red]Error:[/] Image file {image_path} does not exist.")
        return
    output_dir.mkdir(parents=True, exist_ok=True)
    if types is None:
        types = list(FILE_SIGNATURES.keys())
    else:
        types = [t.lower() for t in types if t.lower() in FILE_SIGNATURES]
    found = 0
    # Read and process in chunks
    with image_path.open('rb') as f:
        buffer = b''
        offset = 0
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            buffer += chunk
            for ftype in types:
                sig = FILE_SIGNATURES[ftype]
                header = sig['header']
                footer = sig['footer']
                ext = sig['ext']
                start = 0
                while True:
                    h_idx = buffer.find(header, start)
                    if h_idx == -1:
                        break
                    f_idx = buffer.find(footer, h_idx + len(header))
                    if f_idx == -1:
                        # Keep only the last part of buffer for next chunk
                        buffer = buffer[h_idx:]
                        break
                    end_idx = f_idx + len(footer)
                    carved = buffer[h_idx:end_idx]
                    out_file = output_dir / f"carved_{found+1}{ext}"
                    with out_file.open('wb') as out:
                        out.write(carved)
                    found += 1
                    console.print(f"[green]Carved:[/] {out_file} ({ftype.upper()})")
                    start = end_idx
                else:
                    # If no header found, clear buffer
                    buffer = b''
    if found == 0:
        console.print("[yellow]No files carved. Try different types or check the image file.")
    else:
        console.print(f"[bold green]Total files carved:[/] {found}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="File Carving Tool")
    parser.add_argument("-i", "--input", required=True, help="Input disk/image file")
    parser.add_argument("-o", "--output", required=True, help="Output directory")
    parser.add_argument("--types", nargs="*", help="File types to look for (e.g. jpg, pdf)")
    args = parser.parse_args()
    carve_files(Path(args.input), Path(args.output), args.types)
