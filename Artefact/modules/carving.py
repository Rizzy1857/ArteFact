"""
File Carving Module
==================

Recovers deleted or hidden files from disk images and raw data
by searching for file signatures (magic bytes).
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from rich.console import Console
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn

from Artefact.error_handler import handle_error, ValidationError, with_error_handling

console = Console()
logger = logging.getLogger(__name__)

# File signatures for common types (magic bytes)
FILE_SIGNATURES = {
    'jpg': {
        'header': b'\xff\xd8\xff',
        'footer': b'\xff\xd9',
        'ext': '.jpg',
        'description': 'JPEG Image'
    },
    'jpeg': {
        'header': b'\xff\xd8\xff',
        'footer': b'\xff\xd9',
        'ext': '.jpeg',
        'description': 'JPEG Image'
    },
    'png': {
        'header': b'\x89PNG\r\n\x1a\n',
        'footer': b'IEND\xaeB`\x82',
        'ext': '.png',
        'description': 'PNG Image'
    },
    'pdf': {
        'header': b'%PDF-',
        'footer': b'%%EOF',
        'ext': '.pdf',
        'description': 'PDF Document'
    },
    'zip': {
        'header': b'PK\x03\x04',
        'footer': b'PK\x05\x06',
        'ext': '.zip',
        'description': 'ZIP Archive'
    },
    'gif': {
        'header': b'GIF8',
        'footer': b'\x00;',
        'ext': '.gif',
        'description': 'GIF Image'
    },
    'bmp': {
        'header': b'BM',
        'footer': None,  # BMP doesn't have a specific footer
        'ext': '.bmp',
        'description': 'Windows Bitmap'
    },
    'exe': {
        'header': b'MZ',
        'footer': None,
        'ext': '.exe',
        'description': 'Windows Executable'
    },
    'doc': {
        'header': b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1',
        'footer': None,
        'ext': '.doc',
        'description': 'Microsoft Word Document'
    }
}


@with_error_handling("carve_files")
def carve_files(
    image_path: Path, 
    output_dir: Path, 
    types: Optional[List[str]] = None,
    chunk_size: int = 1024 * 1024,  # 1MB chunks
    max_file_size: int = 50 * 1024 * 1024  # 50MB max per carved file
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
            buffer = b''
            bytes_processed = 0
            file_counter = 1
            
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                
                buffer += chunk
                bytes_processed += len(chunk)
                progress.update(task, completed=bytes_processed)
                
                # Process each file type
                for file_type in types_to_carve:
                    carved = _carve_file_type(
                        buffer, 
                        file_type, 
                        output_dir, 
                        file_counter,
                        max_file_size
                    )
                    carved_files.extend(carved)
                    file_counter += len(carved)
                
                # Keep only the last part of buffer to catch files spanning chunks
                if len(buffer) > chunk_size * 2:
                    buffer = buffer[-chunk_size:]
    
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
