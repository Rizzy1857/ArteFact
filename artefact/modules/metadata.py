import argparse
from pathlib import Path
from rich.console import Console
import subprocess
import json
from datetime import datetime

console = Console()

try:
    from PIL import Image
    from PIL.ExifTags import TAGS
except ImportError:
    Image = None
    TAGS = None

def extract_metadata(file_path: Path, deep=False):
    """Extract metadata from images, PDFs, and other files. Returns a dict with timestamps if found."""
    result = {"timestamps": []}
    if not file_path.exists():
        console.print(f"[red]Error:[/] File {file_path} does not exist.")
        return result
    if deep:
        # Use exiftool for deep extraction
        try:
            proc = subprocess.run([
                'exiftool', str(file_path)
            ], capture_output=True, text=True, check=True)
            for line in proc.stdout.splitlines():
                if any(key in line.lower() for key in ["date", "time"]):
                    try:
                        key, value = line.split(':', 1)
                        dt = value.strip()
                        result["timestamps"].append({"label": key.strip(), "value": dt})
                    except Exception:
                        continue
        except FileNotFoundError:
            console.print("[red]ExifTool not found. Please install exiftool for deep extraction.")
        except subprocess.CalledProcessError as e:
            console.print(f"[red]ExifTool error:[/] {e}")
        return result
    # Basic extraction for images
    if Image is not None and TAGS is not None and file_path.suffix.lower() in ['.jpg', '.jpeg', '.png']:
        try:
            with Image.open(file_path) as img:
                info = img.getexif()
                if info:
                    meta = {TAGS.get(k, k): v for k, v in info.items()}
                    for k, v in meta.items():
                        if isinstance(k, str) and any(x in k.lower() for x in ["date", "time"]):
                            try:
                                dt = str(v)
                                result["timestamps"].append({"label": k, "value": dt})
                            except Exception:
                                continue
                # Optionally print
                # console.print_json(json.dumps(meta, indent=2))
        except Exception as e:
            console.print(f"[red]Image metadata extraction error:[/] {e}")
        return result
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
                for k, v in meta.items():
                    if any(x in k.lower() for x in ["date", "time"]):
                        try:
                            dt = str(v)
                            result["timestamps"].append({"label": k, "value": dt})
                        except Exception:
                            continue
                # Optionally print
                # console.print_json(json.dumps(meta, indent=2))
        except Exception as e:
            console.print(f"[red]PDF metadata extraction error:[/] {e}")
        return result
    # No extractor
    console.print("[yellow]No metadata extractor available for this file type. Try --deep for exiftool.")
    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Metadata Extraction Tool")
    parser.add_argument("-f", "--file", required=True, help="File to extract metadata from")
    parser.add_argument("--deep", action="store_true", help="Use exiftool for deeper extraction")
    args = parser.parse_args()
    extract_metadata(Path(args.file), args.deep)
