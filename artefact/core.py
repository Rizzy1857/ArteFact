"""
Core business logic for ArteFact. No CLI or output code here.
"""
from pathlib import Path
from typing import Dict, Any, Optional
import hashlib
import json

# --- Hashing ---
def hash_file(file_path: Path, algorithm: str = "sha256") -> str:
    if algorithm not in ("md5", "sha1", "sha256"):
        raise ValueError(f"Unsupported algorithm: {algorithm}")
    hasher = getattr(hashlib, algorithm)()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def hash_directory(dir_path: Path, algorithm: str = "sha256") -> Dict[str, str]:
    if not dir_path.is_dir():
        raise ValueError(f"Invalid directory path: {dir_path}")
    return {
        str(file): hash_file(file, algorithm)
        for file in dir_path.rglob("*")
        if file.is_file()
    }

# --- Carving ---
FILE_SIGNATURES = {
    'jpg': {'header': b'\xff\xd8\xff', 'footer': b'\xff\xd9', 'ext': '.jpg'},
    'pdf': {'header': b'%PDF-', 'footer': b'%%EOF', 'ext': '.pdf'},
    'png': {'header': b'\x89PNG\r\n\x1a\n', 'footer': b'IEND\xaeB`\x82', 'ext': '.png'},
}

def carve_files(image_path: Path, types=None, chunk_size=1024*1024) -> Dict[str, Any]:
    """Return a dict of carved files: {filename: bytes} (no output, no writing)."""
    if not image_path.exists():
        raise FileNotFoundError(f"Image file {image_path} does not exist.")
    if types is None:
        types = list(FILE_SIGNATURES.keys())
    else:
        types = [t.lower() for t in types if t.lower() in FILE_SIGNATURES]
    found = {}
    with image_path.open('rb') as f:
        buffer = b''
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            buffer += chunk
            for ftype in types:
                sig = FILE_SIGNATURES[ftype]
                header, footer, ext = sig['header'], sig['footer'], sig['ext']
                start = 0
                while True:
                    h_idx = buffer.find(header, start)
                    if h_idx == -1:
                        break
                    f_idx = buffer.find(footer, h_idx + len(header))
                    if f_idx == -1:
                        buffer = buffer[h_idx:]
                        break
                    end_idx = f_idx + len(footer)
                    carved = buffer[h_idx:end_idx]
                    fname = f"carved_{len(found)+1}{ext}"
                    found[fname] = carved
                    start = end_idx
                else:
                    buffer = b''
    return found

# --- Metadata ---
def extract_metadata(file_path: Path, deep=False) -> Optional[Dict[str, Any]]:
    """Return metadata as a dict, or None if not supported."""
    if not file_path.exists():
        raise FileNotFoundError(f"File {file_path} does not exist.")
    if deep:
        # Deep extraction should be handled by the output/UI layer (calls exiftool)
        return None
    try:
        from PIL import Image
        from PIL.ExifTags import TAGS
    except ImportError:
        Image = None
        TAGS = None
    if Image and TAGS and file_path.suffix.lower() in ['.jpg', '.jpeg', '.png']:
        try:
            with Image.open(file_path) as img:
                # Only JPEGs have EXIF; PNGs do not, so fallback to .info
                if hasattr(img, 'getexif'):
                    info = img.getexif()
                    if info:
                        return {str(TAGS.get(k, k)): v for k, v in info.items()}
                    return {}
                else:
                    # For PNG and others, return .info dict if present, keys as str
                    return {str(k): v for k, v in img.info.items()} if img.info else {}
        except Exception:
            return None
    if file_path.suffix.lower() == '.pdf':
        try:
            from PyPDF2 import PdfReader
        except ImportError:
            return None
        reader = PdfReader(str(file_path))
        return {str(k): v for k, v in (reader.metadata or {}).items()}
    return None
