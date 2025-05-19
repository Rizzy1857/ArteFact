import argparse
from pathlib import Path
from rich.console import Console
import subprocess
import json

console = Console()

try:
    from PIL import Image
    from PIL.ExifTags import TAGS
except ImportError:
    Image = None
    TAGS = None

def extract_metadata(file_path: Path, deep=False):
    """Extract metadata from images, PDFs, and other files. Uses exiftool if deep is True."""
    if not file_path.exists():
        console.print(f"[red]Error:[/] File {file_path} does not exist.")
        return
    if deep:
        # Use exiftool for deep extraction
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
        return
    # Basic extraction for images
    if Image is not None and TAGS is not None and file_path.suffix.lower() in ['.jpg', '.jpeg', '.png']:
        try:
            with Image.open(file_path) as img:
                info = img.getexif()
                if info:
                    meta = {TAGS.get(k, k): v for k, v in info.items()}
                else:
                    meta = {}
                console.print_json(json.dumps(meta, indent=2))
        except Exception as e:
            console.print(f"[red]Image metadata extraction error:[/] {e}")
        return
    # Basic extraction for PDFs
    if file_path.suffix.lower() == '.pdf':
        try:
            try:
                from PyPDF2 import PdfReader
            except ImportError:
                PdfReader = None
            if PdfReader is None:
                console.print("[yellow]PyPDF2 not installed. Run 'pip install PyPDF2' for PDF metadata.")
            else:
                reader = PdfReader(str(file_path))
                meta = reader.metadata or {}
                console.print_json(json.dumps(meta, indent=2))
        except Exception as e:
            console.print(f"[red]PDF metadata extraction error:[/] {e}")
        return
    console.print("[yellow]No metadata extractor available for this file type. Try --deep for exiftool.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Metadata Extraction Tool")
    parser.add_argument("-f", "--file", required=True, help="File to extract metadata from")
    parser.add_argument("--deep", action="store_true", help="Use exiftool for deeper extraction")
    args = parser.parse_args()
    extract_metadata(Path(args.file), args.deep)
