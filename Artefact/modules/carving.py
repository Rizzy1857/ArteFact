"""
File Carving Module
==================

Recovers deleted or hidden files from disk images and raw data
by searching for file signatures (magic bytes) and using ML-based detection.

Features:
- Multiple file type support
- ML-based file detection
- Parallel processing
- Resume capability
- Progress tracking
"""

import logging
import os
import json
import pickle
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set, Generator, Any

import numpy as np
from rich.console import Console
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn
from rich.table import Table

from Artefact.error_handler import handle_error, ValidationError, with_error_handling
from Artefact.core import get_logger

# Configure logging
console = Console()
logger = get_logger(__name__)

# Configure ML support
ML_AVAILABLE = False
try:
    import numpy as np
    from sklearn.ensemble import RandomForestClassifier
    ML_AVAILABLE = True
except ImportError:
    logger.info("ML support not available. Install scikit-learn for enhanced detection.")
    # Fallback to basic numpy for feature extraction
    try:
        import numpy as np
    except ImportError:
        logger.warning("numpy not available - ML features disabled")
        np = None

# Type aliases for clarity
FilePath = Path
Offset = int
FileData = bytes
FileType = str

def _save_carved_file(
    data: bytes,
    file_type: str,
    output_dir: Path,
    file_counter: int,
    offset: int
) -> Optional[Path]:
    """
    Save carved file data to disk.
    
    Args:
        data: Raw file data
        file_type: Type of file being saved
        output_dir: Directory to save file in
        file_counter: Counter for unique naming
        offset: Original file offset
        
    Returns:
        Path to saved file or None if save failed
    """
    try:
        # Generate unique filename
        ext = FILE_SIGNATURES[file_type]['ext']
        filename = f"carved_{file_counter:04d}_{offset}_{file_type}{ext}"
        out_path = output_dir / filename
        
        # Save file
        out_path.write_bytes(data)
        logger.debug(f"Saved carved file: {out_path} ({len(data)} bytes)")
        
        return out_path
    except Exception as e:
        logger.warning(f"Failed to save carved file: {e}")
        return None

def _validate_carved_file(data: FileData, file_type: FileType) -> bool:
    """
    Validate carved file content.
    
    Args:
        data: Raw file data
        file_type: Type of file
        
    Returns:
        True if file content appears valid
    """
    try:
        if file_type in ['jpg', 'jpeg']:
            return (data.startswith(b'\xff\xd8\xff') and 
                   data.endswith(b'\xff\xd9'))
            
        elif file_type == 'png':
            return (data.startswith(b'\x89PNG\r\n\x1a\n') and 
                   data.endswith(b'IEND\xaeB`\x82'))
            
        elif file_type == 'pdf':
            return (data.startswith(b'%PDF-') and 
                   b'%%EOF' in data[-1024:])
            
        # Add more format-specific validation as needed
        return True
        
    except Exception as e:
        logger.debug(f"Validation failed for {file_type}: {e}")
        return False

def _predict_file_end(data: FileData, model: Any) -> int:
    """
    Use ML model to predict file end position.
    
    Args:
        data: Raw file data
        model: Trained ML model
        
    Returns:
        Predicted end position
    """
    try:
        features = _extract_features(data)
        end_pos = model.predict([features])[0]
        return min(len(data), int(end_pos))
    except Exception as e:
        logger.debug(f"ML prediction failed: {e}")
        return len(data)

def _extract_features(data: FileData) -> List[float]:
    """
    Extract features from byte data for ML prediction.
    
    Args:
        data: Raw file data
        
    Returns:
        List of numerical features or fallback features if numpy is not available
    """
    # Return fallback features if numpy not available
    if not np:
        return [len(data), 0, 0, 0, 0, 0, 0, 0]
        
    if len(data) == 0:
        return [0] * 10
        
    try:
        features = []
        
        # Basic statistical features
        byte_array = np.frombuffer(data, dtype=np.uint8)
        features.extend([
            len(data),
            float(np.mean(byte_array)),
            float(np.std(byte_array)),
            float(np.median(byte_array)),
            float(np.max(byte_array)),
            float(np.min(byte_array))
        ])
        
        # Entropy calculation
        hist = np.bincount(byte_array, minlength=256)
        prob = hist / len(byte_array)
        entropy = -float(np.sum(prob * np.log2(prob + 1e-10)))
        features.append(entropy)
        
        # Compression ratio estimate
        import zlib
        compressed = len(zlib.compress(data))
        features.append(compressed / len(data))
        
        return features
    except Exception as e:
        logger.debug(f"Feature extraction failed: {e}")
        return [len(data), 0, 0, 0, 0, 0, 0, 0]  # Fallback features

def _estimate_file_end(data: FileData, file_type: FileType) -> int:
    """
    Estimate file end position using heuristics.
    
    Args:
        data: Raw file data
        file_type: Type of file
        
    Returns:
        Estimated end position
    """
    if file_type in ['jpg', 'jpeg']:
        # Look for JPEG EOI marker
        end = data.find(b'\xff\xd9')
        if end != -1:
            return end + 2
            
    elif file_type == 'png':
        # Look for PNG IEND chunk
        end = data.find(b'IEND\xaeB`\x82')
        if end != -1:
            return end + 8
            
    elif file_type == 'pdf':
        # Look for PDF EOF marker
        end = data.rfind(b'%%EOF')
        if end != -1:
            return end + 5
            
    elif file_type == 'bmp':
        # Try to get size from BMP header
        try:
            if len(data) >= 6:
                size = int.from_bytes(data[2:6], byteorder='little')
                if size > 0:
                    return min(size, len(data))
        except Exception:
            pass
            
    # Default: scan for next known header
    for sig in FILE_SIGNATURES.values():
        header = sig['header']
        pos = data.find(header, 1)  # Start after current header
        if pos != -1:
            return pos
            
    return len(data)

# Optional ML support
try:
    import sklearn
    from sklearn.ensemble import RandomForestClassifier
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

@dataclass
class CarvingState:
    """State tracking for resumable carving."""
    image_path: Path
    output_dir: Path
    processed_bytes: int
    found_files: Set[Path]
    last_position: int
    
    def save(self, path: Path) -> None:
        """Save carving state to file."""
        data = {
            'image_path': str(self.image_path),
            'output_dir': str(self.output_dir),
            'processed_bytes': self.processed_bytes,
            'found_files': [str(p) for p in self.found_files],
            'last_position': self.last_position
        }
        path.write_text(json.dumps(data, indent=2))
    
    @classmethod
    def load(cls, path: Path) -> 'CarvingState':
        """Load carving state from file."""
        data = json.loads(path.read_text())
        return cls(
            image_path=Path(data['image_path']),
            output_dir=Path(data['output_dir']),
            processed_bytes=data['processed_bytes'],
            found_files=set(Path(p) for p in data['found_files']),
            last_position=data['last_position']
        )

console = Console()
logger = logging.getLogger(__name__)

# File format signatures for magic number-based detection
FILE_SIGNATURES: Dict[str, Dict[str, Any]] = {
    'jpg': {
        'header': b'\xff\xd8\xff',
        'footer': b'\xff\xd9',
        'ext': '.jpg',
        'description': 'JPEG Image',
        'max_size': 100 * 1024 * 1024  # 100MB
    },
    'jpeg': {
        'header': b'\xff\xd8\xff',
        'footer': b'\xff\xd9',
        'ext': '.jpeg',
        'description': 'JPEG Image',
        'max_size': 100 * 1024 * 1024  # 100MB
    },
    'png': {
        'header': b'\x89PNG\r\n\x1a\n',
        'footer': b'IEND\xaeB`\x82',
        'ext': '.png',
        'description': 'PNG Image',
        'max_size': 50 * 1024 * 1024  # 50MB
    },
    'pdf': {
        'header': b'%PDF-',
        'footer': b'%%EOF',
        'ext': '.pdf',
        'description': 'PDF Document',
        'max_size': 100 * 1024 * 1024  # 100MB
    },
    'zip': {
        'header': b'PK\x03\x04',
        'footer': b'PK\x05\x06',
        'ext': '.zip',
        'description': 'ZIP Archive',
        'max_size': 1024 * 1024 * 1024  # 1GB
    },
    'gif': {
        'header': b'GIF8',
        'footer': b'\x00;',
        'ext': '.gif',
        'description': 'GIF Image',
        'max_size': 50 * 1024 * 1024  # 50MB
    },
    'bmp': {
        'header': b'BM',
        'footer': None,  
        'ext': '.bmp',
        'description': 'Windows Bitmap',
        'max_size': 100 * 1024 * 1024  # 100MB
    },
    'exe': {
        'header': b'MZ',
        'footer': None,
        'ext': '.exe',
        'description': 'Windows Executable',
        'max_size': 1024 * 1024 * 1024  # 1GB
    },
    'doc': {
        'header': b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1',
        'footer': None,
        'ext': '.doc',
        'description': 'Microsoft Word Document',
        'max_size': 100 * 1024 * 1024  # 100MB
    }
}


@with_error_handling("carve_files")
def carve_files(
    image_path: Path, 
    output_dir: Path, 
    types: Optional[List[str]] = None,
    chunk_size: int = 1024 * 1024,  # 1MB chunks
    max_file_size: int = 50 * 1024 * 1024,  # 50MB max per carved file
    parallel: bool = True,
    max_workers: Optional[int] = None,
    recover_fragmented: bool = False,
    use_ml: bool = False,
    resume_file: Optional[Path] = None
) -> List[Path]:
    """
    Recover files from a disk image by searching for file signatures.
    
    Args:
        image_path: Path to disk image file
        output_dir: Directory to save carved files
        types: List of file types to carve (None = all supported types)
        chunk_size: Size of chunks to read at once
        max_file_size: Maximum size for carved files
        
    Returns:
        List of paths to carved files
        
    Raises:
        ValidationError: If inputs are invalid
        FileNotFoundError: If image file doesn't exist
    """
    if not isinstance(image_path, Path):
        image_path = Path(image_path)
    
    if not isinstance(output_dir, Path):
        output_dir = Path(output_dir)
    
    # Validate inputs
    if not image_path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")
    
    if not image_path.is_file():
        raise ValidationError(f"Path is not a file: {image_path}")
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load ML model if requested
    ml_model = None
    if use_ml and ML_AVAILABLE:
        model_path = Path(__file__).parent / 'models' / 'file_type_classifier.pkl'
        if model_path.exists():
            with model_path.open('rb') as f:
                ml_model = pickle.load(f)
        else:
            logger.warning("ML model not found, falling back to signature-based detection")
    
    # Resume from previous state if requested
    state = None
    if resume_file and resume_file.exists():
        try:
            state = CarvingState.load(resume_file)
            if (state.image_path != image_path or 
                state.output_dir != output_dir):
                logger.warning("Resume state mismatch, starting fresh")
                state = None
        except Exception as e:
            logger.warning(f"Failed to load resume state: {e}")
    
    # Initialize new state if needed
    if not state:
        state = CarvingState(
            image_path=image_path,
            output_dir=output_dir,
            processed_bytes=0,
            found_files=set(),
            last_position=0
        )
    
    # Determine which types to carve
    if types is None:
        types_to_carve = list(FILE_SIGNATURES.keys())
    else:
        types_to_carve = []
        for file_type in types:
            if file_type.lower() in FILE_SIGNATURES:
                types_to_carve.append(file_type.lower())
            else:
                logger.warning(f"Unknown file type: {file_type}")
    
    if not types_to_carve:
        raise ValidationError("No valid file types specified for carving")
    
    console.print(f"[green]Carving file types:[/] {', '.join(types_to_carve)}")
    console.print(f"[green]Output directory:[/] {output_dir}")
    
    def carve_chunk(chunk_data: bytes, offset: int) -> List[Tuple[bytes, str, int]]:
        """Process a single chunk of data."""
        results = []
        for file_type in types_to_carve:
            sig = FILE_SIGNATURES[file_type]
            header = sig['header']
            footer = sig.get('footer')
            
            # Find all header positions in chunk
            pos = 0
            while True:
                pos = chunk_data.find(header, pos)
                if pos == -1:
                    break
                    
                # Extract potential file
                start = pos
                if footer:
                    end = chunk_data.find(footer, start + len(header))
                    if end == -1:
                        pos += 1
                        continue
                    end += len(footer)
                else:
                    # Use ML or heuristics to determine end
                    if ml_model and use_ml:
                        end = _predict_file_end(chunk_data[start:], ml_model)
                    else:
                        end = _estimate_file_end(chunk_data[start:], file_type)
                
                if end > start:
                    file_data = chunk_data[start:end]
                    if len(file_data) <= max_file_size:
                        results.append((file_data, file_type, offset + start))
                pos += 1
        return results
    
    carved_files = []
    image_size = image_path.stat().st_size
    
    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TextColumn("• {task.completed}/{task.total} bytes"),
        TimeElapsedColumn(),
        console=console,
        transient=False
    ) as progress:
        task = progress.add_task("Carving files...", total=image_size)
        
        with image_path.open('rb') as f:
            if state.last_position > 0:
                f.seek(state.last_position)
            
            file_counter = len(state.found_files) + 1
            overlap_size = max_file_size  # Size of overlap between chunks
            
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                
                current_pos = f.tell()
                
                # Process chunk
                if parallel and chunk_size > 1024*1024:  # Only parallelize large chunks
                    # Split chunk into sub-chunks for parallel processing
                    sub_chunks = []
                    sub_size = chunk_size // (max_workers or os.cpu_count() or 4)
                    
                    for i in range(0, len(chunk), sub_size):
                        sub_chunk = chunk[i:i + sub_size + overlap_size]
                        if sub_chunk:
                            sub_chunks.append((sub_chunk, current_pos + i))
                    
                    # Process sub-chunks in parallel
                    with ProcessPoolExecutor(max_workers=max_workers) as executor:
                        futures = [
                            executor.submit(carve_chunk, sub_chunk, offset)
                            for sub_chunk, offset in sub_chunks
                        ]
                        
                        for future in as_completed(futures):
                            try:
                                for file_data, file_type, offset in future.result():
                                    if _validate_carved_file(file_data, file_type):
                                        out_path = _save_carved_file(
                                            file_data, file_type, output_dir,
                                            file_counter, offset
                                        )
                                        if out_path:
                                            carved_files.append(out_path)
                                            state.found_files.add(out_path)
                                            file_counter += 1
                            except Exception as e:
                                logger.error(f"Parallel carving error: {e}")
                else:
                    # Sequential processing
                    for file_data, file_type, offset in carve_chunk(chunk, current_pos):
                        if _validate_carved_file(file_data, file_type):
                            out_path = _save_carved_file(
                                file_data, file_type, output_dir,
                                file_counter, offset
                            )
                            if out_path:
                                carved_files.append(out_path)
                                state.found_files.add(out_path)
                                file_counter += 1
                
                # Update progress and state
                state.processed_bytes += len(chunk)
                state.last_position = current_pos
                progress.update(task, completed=state.processed_bytes)
                
                # Save state periodically
                if resume_file and state.processed_bytes % (100 * 1024 * 1024) == 0:  # Every 100MB
                    state.save(resume_file)
    
    console.print(f"[bold green]Carving complete![/] Found {len(carved_files)} files")
    
    # Display summary
    if carved_files:
        _display_carving_summary(carved_files)
    
    return carved_files


def _carve_file_type(
    buffer: bytes, 
    file_type: str, 
    output_dir: Path, 
    file_counter: int,
    max_file_size: int
) -> List[Path]:
    """Carve files of a specific type from buffer."""
    carved_files = []
    sig = FILE_SIGNATURES[file_type]
    header = sig['header']
    footer = sig.get('footer')
    ext = sig['ext']
    
    start = 0
    while True:
        # Find header
        header_pos = buffer.find(header, start)
        if header_pos == -1:
            break
        
        # If no footer defined, estimate file size or use fixed size
        if footer is None:
            if file_type == 'bmp':
                # BMP has size info in header
                end_pos = _estimate_bmp_size(buffer, header_pos, max_file_size)
            elif file_type == 'exe':
                # For executables, carve a reasonable amount
                end_pos = min(header_pos + max_file_size, len(buffer))
            else:
                # Default: carve until next header or end of buffer
                next_header = buffer.find(header, header_pos + 1)
                if next_header != -1:
                    end_pos = next_header
                else:
                    end_pos = min(header_pos + max_file_size, len(buffer))
        else:
            # Find footer
            footer_pos = buffer.find(footer, header_pos + len(header))
            if footer_pos == -1:
                start = header_pos + 1
                continue
            end_pos = footer_pos + len(footer)
        
        # Extract file data
        if end_pos > header_pos and (end_pos - header_pos) < max_file_size:
            file_data = buffer[header_pos:end_pos]
            
            # Save carved file
            output_file = output_dir / f"carved_{file_counter:04d}_{file_type}{ext}"
            try:
                output_file.write_bytes(file_data)
                carved_files.append(output_file)
                logger.debug(f"Carved {file_type} file: {output_file} ({len(file_data)} bytes)")
            except Exception as e:
                logger.error(f"Failed to save carved file: {e}")
        
        start = header_pos + 1
    
    return carved_files


def _estimate_bmp_size(buffer: bytes, header_pos: int, max_size: int) -> int:
    """Estimate BMP file size from header information."""
    try:
        # BMP file size is stored at offset 2-5 in little-endian format
        if header_pos + 6 <= len(buffer):
            size_bytes = buffer[header_pos + 2:header_pos + 6]
            file_size = int.from_bytes(size_bytes, byteorder='little')
            return min(header_pos + file_size, header_pos + max_size, len(buffer))
    except Exception:
        pass
    
    # Fallback to reasonable default
    return min(header_pos + max_size, len(buffer))


def _display_carving_summary(carved_files: List[Path]):
    """Display summary of carved files."""
    from rich.table import Table
    
    # Group by file type
    type_counts = {}
    total_size = 0
    
    for file_path in carved_files:
        try:
            file_size = file_path.stat().st_size
            total_size += file_size
            
            # Extract file type from filename
            file_type = file_path.stem.split('_')[-1] if '_' in file_path.stem else 'unknown'
            
            if file_type not in type_counts:
                type_counts[file_type] = {'count': 0, 'size': 0}
            
            type_counts[file_type]['count'] += 1
            type_counts[file_type]['size'] += file_size
            
        except Exception as e:
            logger.warning(f"Failed to get info for {file_path}: {e}")
    
    # Create summary table
    table = Table(title="Carving Summary", show_lines=True)
    table.add_column("File Type", style="cyan")
    table.add_column("Count", style="green", justify="right")
    table.add_column("Total Size", style="yellow", justify="right")
    table.add_column("Description", style="white")
    
    for file_type, stats in sorted(type_counts.items()):
        size_str = _format_file_size(stats['size'])
        description = FILE_SIGNATURES.get(file_type, {}).get('description', 'Unknown')
        
        table.add_row(
            file_type.upper(),
            str(stats['count']),
            size_str,
            description
        )
    
    # Add total row
    table.add_row(
        "[bold]TOTAL[/bold]",
        f"[bold]{len(carved_files)}[/bold]",
        f"[bold]{_format_file_size(total_size)}[/bold]",
        "[bold]All carved files[/bold]"
    )
    
    console.print(table)


def _format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def get_supported_types() -> Dict[str, Dict[str, str]]:
    """Get information about supported file types for carving."""
    return FILE_SIGNATURES.copy()


if __name__ == "__main__":
    # CLI interface for standalone usage
    import argparse
    
    parser = argparse.ArgumentParser(description="File Carving Tool")
    parser.add_argument("-i", "--input", required=True, help="Input disk/image file")
    parser.add_argument("-o", "--output", required=True, help="Output directory")
    parser.add_argument("--types", nargs="*", help="File types to carve (default: all)")
    parser.add_argument("--chunk-size", type=int, default=1024*1024, 
                       help="Chunk size in bytes (default: 1MB)")
    parser.add_argument("--max-file-size", type=int, default=50*1024*1024,
                       help="Maximum file size in bytes (default: 50MB)")
    parser.add_argument("--list-types", action="store_true",
                       help="List supported file types")
    
    args = parser.parse_args()
    
    if args.list_types:
        console.print("[bold]Supported file types for carving:[/]")
        for file_type, info in FILE_SIGNATURES.items():
            console.print(f"  {file_type.upper()}: {info['description']}")
        exit(0)
    
    try:
        carved = carve_files(
            Path(args.input),
            Path(args.output),
            types=args.types,
            chunk_size=args.chunk_size,
            max_file_size=args.max_file_size
        )
        
        console.print(f"\n[green]Success![/] Carved {len(carved)} files to {args.output}")
        
    except Exception as e:
        console.print(f"[red]Error:[/] {str(e)}")
        exit(1)
