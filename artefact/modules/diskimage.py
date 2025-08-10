"""
Disk Image Mounting and Extraction Module for ArteFact
- List partitions/volumes in raw/E01/AFF/VHD images
- Extract files from partitions
- Mount images as virtual drives (where supported)
- Calculate disk image hashes and validate integrity
- Support for various filesystem types
"""

import sys
import os
import logging
import tempfile
import hashlib
import textwrap
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Generator, Union, Any, Tuple
from dataclasses import dataclass, asdict
from rich.console import Console
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn
from rich.table import Table
import json
import subprocess
import shutil

from Artefact.error_handler import handle_error, ValidationError, with_error_handling
from Artefact.core import format_bytes, get_logger

# Configure module logger
console = Console()
logger = get_logger(__name__)

from Artefact.error_handler import handle_error, ValidationError, with_error_handling

# Required third-party libraries
try:
    import pytsk3
    import pyewf
    import pyvhdi
    from tabulate import tabulate
except ImportError as e:
    missing_lib = str(e).split("'")[1]
    print(f"Warning: {missing_lib} not installed. Some features may be limited.")
    print(f"Install with: pip install {missing_lib}")

console = Console()
logger = logging.getLogger(__name__)

# Supported image formats and their handlers
IMAGE_FORMATS = {
    '.raw': {'description': 'Raw disk image', 'handler': 'raw'},
    '.dd': {'description': 'Raw disk image', 'handler': 'raw'},
    '.img': {'description': 'Raw disk image', 'handler': 'raw'},
    '.001': {'description': 'Split raw image', 'handler': 'split'},
    '.e01': {'description': 'EnCase image', 'handler': 'ewf'},
    '.ex01': {'description': 'EnCase image', 'handler': 'ewf'},
    '.aff': {'description': 'Advanced Forensics Format', 'handler': 'aff'},
    '.vhd': {'description': 'Virtual Hard Disk', 'handler': 'vhd'},
    '.vmdk': {'description': 'VMware Disk', 'handler': 'vmdk'}
}

@dataclass
class ImageInfo:
    """Container for disk image information."""
    path: Path
    format: str
    size: int
    hash_md5: Optional[str] = None
    hash_sha1: Optional[str] = None
    sector_size: int = 512
    partitions: List[Dict[str, Any]] = None

@with_error_handling("convert_image")
def convert_image(
    input_path: Union[str, Path],
    output_path: Union[str, Path],
    format_hint: Optional[str] = None
) -> bool:
    """
    Convert disk image to raw format using appropriate tools.
    
    Args:
        input_path: Path to input image
        output_path: Path for output raw image
        format_hint: Optional hint for input format
        
    Returns:
        bool: True if conversion successful
        
    Raises:
        ValidationError: If format unsupported or tools missing
    """
    input_path = Path(input_path)
    output_path = Path(output_path)
    
    # Determine format
    if format_hint:
        format = format_hint.lower()
    else:
        format = input_path.suffix.lower()
        
    # EnCase E01
    if format in ['.e01', '.ex01']:
        if 'pyewf' not in sys.modules:
            raise ValidationError("pyewf required for E01 conversion. Install with: pip install pyewf")
            
        try:
            filenames = pyewf.glob(str(input_path))
            ewf_handle = pyewf.handle()
            ewf_handle.open(filenames)
            
            total_size = ewf_handle.get_media_size()
            with output_path.open('wb') as raw_file:
                with Progress(
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                    TimeElapsedColumn()
                ) as progress:
                    task = progress.add_task("Converting E01 image", total=total_size)
                    
                    offset = 0
                    chunk_size = 8 * 1024 * 1024  # 8MB chunks
                    while offset < total_size:
                        available = min(chunk_size, total_size - offset)
                        chunk = ewf_handle.read(available)
                        if not chunk:
                            break
                        raw_file.write(chunk)
                        offset += len(chunk)
                        progress.update(task, advance=len(chunk))
                        
            ewf_handle.close()
            return True
            
        except Exception as e:
            raise RuntimeError(f"E01 conversion failed: {str(e)}")
            
    # VHD format
    elif format == '.vhd':
        if 'pyvhdi' not in sys.modules:
            raise ValidationError("pyvhdi required for VHD conversion. Install with: pip install pyvhdi")
            
        try:
            vhd_handle = pyvhdi.handle()
            vhd_handle.open(str(input_path))
            
            total_size = vhd_handle.get_media_size()
            with output_path.open('wb') as raw_file:
                with Progress() as progress:
                    task = progress.add_task("Converting VHD image", total=total_size)
                    
                    offset = 0
                    chunk_size = 8 * 1024 * 1024  # 8MB chunks
                    while offset < total_size:
                        available = min(chunk_size, total_size - offset)
                        chunk = vhd_handle.read(available)
                        if not chunk:
                            break
                        raw_file.write(chunk)
                        offset += len(chunk)
                        progress.update(task, advance=len(chunk))
                        
            vhd_handle.close()
            return True
            
        except Exception as e:
            raise RuntimeError(f"VHD conversion failed: {str(e)}")
            
    else:
        raise ValidationError(f"Unsupported image format: {format}")
        
    return False

@with_error_handling("open_image")
def open_image(image_path: Union[str, Path]) -> ImageInfo:
    """
    Open a disk image and return information about it.
    
    Args:
        image_path: Path to the disk image
        
    Returns:
        ImageInfo: Container with image details
        
    Raises:
        ValidationError: If image format unsupported
        FileNotFoundError: If image not found
    """
    image_path = Path(image_path)
    if not image_path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")
        
    # Get image format
    image_format = image_path.suffix.lower()
    if image_format not in IMAGE_FORMATS:
        raise ValidationError(f"Unsupported image format: {image_format}")
        
    # Convert non-raw formats if needed
    if IMAGE_FORMATS[image_format]['handler'] != 'raw':
        raw_path = image_path.with_suffix('.raw')
        if not raw_path.exists():
            console.print(f"[yellow]Converting {image_format} to raw format...")
            if not convert_image(image_path, raw_path):
                raise RuntimeError(f"Failed to convert {image_format} to raw format")
        image_path = raw_path
        
    # Open with TSK
    try:
        img = pytsk3.Img_Info(str(image_path))
        
        # Get basic image info
        image_info = ImageInfo(
            path=image_path,
            format=image_format,
            size=img.get_size(),
            sector_size=img.info.sector_size,
            partitions=[]
        )
        
        # Calculate hashes if requested (time-consuming)
        if os.environ.get('ARTEFACT_CALC_IMAGE_HASH', '').lower() == 'true':
            with Progress() as progress:
                task = progress.add_task("Calculating image hashes", total=image_info.size)
                
                md5 = hashlib.md5()
                sha1 = hashlib.sha1()
                
                with image_path.open('rb') as f:
                    for chunk in iter(lambda: f.read(8192), b''):
                        md5.update(chunk)
                        sha1.update(chunk)
                        progress.update(task, advance=len(chunk))
                        
                image_info.hash_md5 = md5.hexdigest()
                image_info.hash_sha1 = sha1.hexdigest()
                
        return image_info
        
    except Exception as e:
        raise RuntimeError(f"Failed to open image: {str(e)}")

@dataclass
class PartitionInfo:
    """Container for partition information."""
    addr: int
    start_sector: int
    length: int
    description: str
    fs_type: Optional[str] = None
    volume_label: Optional[str] = None
    total_space: Optional[int] = None
    used_space: Optional[int] = None
    
@with_error_handling("analyze_partitions")
def analyze_partitions(image_path: Union[str, Path]) -> List[PartitionInfo]:
    """
    Analyze partitions in a disk image.
    
    Args:
        image_path: Path to disk image
        
    Returns:
        List[PartitionInfo]: List of partition information
        
    Raises:
        ValidationError: If pytsk3 not available
    """
    if pytsk3 is None:
        raise ValidationError("pytsk3 required for partition analysis. Install with: pip install pytsk3")
        
    image_info = open_image(image_path)
    img = pytsk3.Img_Info(str(image_info.path))
    
    try:
        vol = pytsk3.Volume_Info(img)
    except Exception:
        # No volume system found, try treating as single partition
        return [PartitionInfo(
            addr=0,
            start_sector=0,
            length=image_info.size // image_info.sector_size,
            description="Raw partition",
            fs_type=_detect_fs_type(img, 0)
        )]
    
    partitions = []
    
    for part in vol:
        # Skip empty or metadata partitions
        if part.len <= 0 or part.desc.lower() in ['unallocated', 'meta']:
            continue
            
        # Get filesystem info if possible
        fs_info = None
        try:
            fs_info = pytsk3.FS_Info(img, offset=part.start * image_info.sector_size)
        except Exception:
            pass
            
        partition = PartitionInfo(
            addr=part.addr,
            start_sector=part.start,
            length=part.len,
            description=part.desc,
            fs_type=_detect_fs_type(img, part.start * image_info.sector_size)
        )
        
        # Get additional filesystem info if available
        if fs_info:
            try:
                partition.total_space = fs_info.info.block_size * fs_info.info.block_count
                partition.used_space = fs_info.info.block_size * (fs_info.info.block_count - fs_info.info.free_block_count)
                
                # Try to get volume label
                try:
                    root = fs_info.open_dir(path="/")
                    for entry in root:
                        if entry.info.name.name == b"." and hasattr(entry.info.fs_info, 'label'):
                            partition.volume_label = entry.info.fs_info.label
                            break
                except Exception:
                    pass
            except Exception:
                pass
                
        partitions.append(partition)
    
    return partitions

def _detect_fs_type(img: pytsk3.Img_Info, offset: int) -> Optional[str]:
    """Detect filesystem type at given offset."""
    try:
        fs = pytsk3.FS_Info(img, offset=offset)
        return fs.info.ftype.decode('utf-8')
    except Exception:
        return None

@with_error_handling("list_partitions")
def list_partitions(image_path: Union[str, Path], output_format: str = "table") -> None:
    """
    List partitions in a disk image with details.
    
    Args:
        image_path: Path to disk image
        output_format: Output format (table/json)
    """
    partitions = analyze_partitions(image_path)
    
    if not partitions:
        console.print("[yellow]No partitions found in image[/]")
        return
        
    if output_format.lower() == 'json':
        import json
        console.print_json(json.dumps([vars(p) for p in partitions], indent=2))
    else:
        table = []
        headers = ['#', 'Start', 'Length', 'Size', 'Type', 'Label', 'Description']
        
        for part in partitions:
            size = _format_size(part.length * 512)  # Assuming 512-byte sectors
            row = [
                part.addr,
                f"{part.start_sector:,}",
                f"{part.length:,}",
                size,
                part.fs_type or 'Unknown',
                part.volume_label or '-',
                part.description
            ]
            table.append(row)
            
        console.print(tabulate(table, headers=headers, tablefmt="grid"))

def _format_size(size_bytes: int) -> str:
    """Format byte size to human readable string."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"

@dataclass
class FileEntry:
    """Container for file information from image."""
    name: str
    path: str
    size: int
    created: Optional[int] = None
    modified: Optional[int] = None
    accessed: Optional[int] = None
    is_directory: bool = False
    is_deleted: bool = False

@with_error_handling("extract_partition")
def extract_partition(
    image_path: Union[str, Path],
    partition_addr: int,
    output_dir: Union[str, Path],
    filter_pattern: Optional[str] = None,
    recover_deleted: bool = False
) -> List[Path]:
    """
    Extract files from a partition in the disk image.
    
    Args:
        image_path: Path to disk image
        partition_addr: Partition address to extract
        output_dir: Directory to save extracted files
        filter_pattern: Optional glob pattern to filter files
        recover_deleted: Whether to attempt recovering deleted files
        
    Returns:
        List[Path]: Paths of extracted files
        
    Raises:
        ValidationError: If partition not found or invalid
    """
    if pytsk3 is None:
        raise ValidationError("pytsk3 required for file extraction. Install with: pip install pytsk3")
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    image_info = open_image(image_path)
    img = pytsk3.Img_Info(str(image_info.path))
    
    # Find requested partition
    try:
        vol = pytsk3.Volume_Info(img)
        target_part = None
        
        for part in vol:
            if part.addr == partition_addr:
                target_part = part
                break
                
        if not target_part:
            raise ValidationError(f"Partition {partition_addr} not found")
            
    except Exception as e:
        if partition_addr == 0:  # Handle single partition images
            target_part = type('Partition', (), {
                'start': 0,
                'len': image_info.size // image_info.sector_size
            })
        else:
            raise ValidationError(f"Failed to read partition table: {str(e)}")
    
    # Open filesystem
    try:
        fs = pytsk3.FS_Info(img, offset=target_part.start * image_info.sector_size)
    except Exception as e:
        raise ValidationError(f"Failed to open filesystem: {str(e)}")
    
    extracted_files = []
    
    def extract_dir(fs_obj, cur_path: str = ""):
        try:
            for entry in fs_obj:
                if entry.info.name.name in [b".", b".."]:
                    continue
                    
                try:
                    name = entry.info.name.name.decode('utf-8')
                except UnicodeDecodeError:
                    name = entry.info.name.name.decode('utf-8', errors='replace')
                    
                # Apply filter if specified
                if filter_pattern and not Path(name).match(filter_pattern):
                    continue
                    
                try:
                    file_path = (Path(cur_path) / name).as_posix()
                    is_deleted = bool(entry.info.meta.flags & pytsk3.TSK_FS_META_FLAG_UNALLOC)
                    
                    if not recover_deleted and is_deleted:
                        continue
                        
                    if entry.info.meta.type == pytsk3.TSK_FS_META_TYPE_REG:
                        out_path = output_dir / file_path
                        out_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        try:
                            f = fs.open(file_path)
                            with out_path.open('wb') as out:
                                offset = 0
                                size = f.info.meta.size
                                
                                with Progress() as progress:
                                    task = progress.add_task(
                                        f"Extracting: {file_path}",
                                        total=size
                                    )
                                    
                                    while offset < size:
                                        buffer = f.read_random(
                                            offset,
                                            min(1024*1024, size - offset)
                                        )
                                        if not buffer:
                                            break
                                        out.write(buffer)
                                        offset += len(buffer)
                                        progress.update(task, advance=len(buffer))
                                        
                            extracted_files.append(out_path)
                            status = "[red](Deleted) " if is_deleted else ""
                            console.print(f"[green]Extracted:[/] {status}{file_path}")
                            
                        except Exception as e:
                            logger.warning(f"Failed to extract {file_path}: {str(e)}")
                            
                    elif entry.info.meta.type == pytsk3.TSK_FS_META_TYPE_DIR:
                        extract_dir(entry.as_directory(), file_path)
                        
                except Exception as e:
                    logger.warning(f"Failed to process {name}: {str(e)}")
                    
        except Exception as e:
            logger.warning(f"Failed to list directory {cur_path}: {str(e)}")
    
    # Start recursive extraction from root
    extract_dir(fs.open_dir(path="/"))
    
    return extracted_files

@with_error_handling("mount_image")
def mount_image(
    image_path: Union[str, Path],
    mount_point: Union[str, Path],
    partition: Optional[int] = None,
    read_only: bool = True
) -> bool:
    """
    Mount a disk image using appropriate tools.
    
    Args:
        image_path: Path to disk image
        mount_point: Directory to mount image
        partition: Optional partition number to mount
        read_only: Mount read-only (recommended)
        
    Returns:
        bool: True if mounted successfully
        
    Note: Requires admin/root privileges and appropriate tools
    """
    image_path = Path(image_path)
    mount_point = Path(mount_point)
    
    if not mount_point.exists():
        mount_point.mkdir(parents=True)
    
    # Check platform-specific requirements
    if sys.platform == 'win32':
        if not shutil.which('OSFMount'):
            raise ValidationError(
                "OSFMount required for mounting on Windows. "
                "Download from: https://www.osforensics.com/tools/mount-disk-images.html"
            )
    else:  # Linux/macOS
        if not shutil.which('mount'):
            raise ValidationError("mount command not found")
            
    try:
        if sys.platform == 'win32':
            cmd = [
                'OSFMount',
                '-a', str(image_path),  # Add image
                '-m', str(mount_point),  # Mount point
                '-t', 'disk'            # Type: disk image
            ]
            
            if read_only:
                cmd.append('-r')  # Read-only
                
            if partition is not None:
                cmd.extend(['-p', str(partition)])
                
        else:  # Linux/macOS
            opts = ['loop']
            if read_only:
                opts.append('ro')
                
            if partition is not None:
                opts.append(f'offset={partition * 512}')  # Assuming 512-byte sectors
                
            cmd = [
                'sudo',
                'mount',
                '-o', ','.join(opts),
                str(image_path),
                str(mount_point)
            ]
            
        subprocess.run(cmd, check=True)
        console.print(f"[green]Mounted:[/] {image_path} at {mount_point}")
        return True
        
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Mount failed: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Mount failed: {str(e)}")

@with_error_handling("unmount_image")
def unmount_image(mount_point: Union[str, Path]) -> bool:
    """
    Unmount a previously mounted disk image.
    
    Args:
        mount_point: Directory where image is mounted
        
    Returns:
        bool: True if unmounted successfully
    """
    mount_point = Path(mount_point)
    
    try:
        if sys.platform == 'win32':
            if not shutil.which('OSFMount'):
                raise ValidationError("OSFMount required for unmounting")
                
            cmd = ['OSFMount', '-d', str(mount_point)]
        else:
            cmd = ['sudo', 'umount', str(mount_point)]
            
        subprocess.run(cmd, check=True)
        console.print(f"[green]Unmounted:[/] {mount_point}")
        return True
        
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Unmount failed: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Unmount failed: {str(e)}")

def main():
    """CLI interface for standalone usage."""
    import argparse
    parser = argparse.ArgumentParser(
        description="Disk Image Analysis and Extraction Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
            Examples:
              # List partitions in disk image
              %(prog)s -i disk.img --list
              
              # Extract files from partition 1
              %(prog)s -i disk.img --extract 1 -o ./extracted
              
              # Mount image (requires admin/root)
              %(prog)s -i disk.img --mount /mnt/image
              
              # List supported formats
              %(prog)s --formats
        """)
    )
    
    parser.add_argument('-i', '--input',
                        help='Input disk image file')
    parser.add_argument('-o', '--output',
                        help='Output directory for extracted files')
    parser.add_argument('--list', action='store_true',
                        help='List partitions/volumes in the image')
    parser.add_argument('--extract', type=int, metavar='PART_NUM',
                        help='Extract files from partition number')
    parser.add_argument('--mount', metavar='MOUNT_POINT',
                        help='Mount the disk image (requires admin/root)')
    parser.add_argument('--unmount', metavar='MOUNT_POINT',
                        help='Unmount a mounted disk image')
    parser.add_argument('--recover-deleted', action='store_true',
                        help='Attempt to recover deleted files during extraction')
    parser.add_argument('--filter', metavar='PATTERN',
                        help='Filter files during extraction (e.g., "*.jpg")')
    parser.add_argument('--formats', action='store_true',
                        help='List supported disk image formats')
    
    args = parser.parse_args()
    
    try:
        if args.formats:
            console.print("\n[bold]Supported disk image formats:[/]")
            for ext, info in IMAGE_FORMATS.items():
                console.print(f"  {ext:8} {info['description']}")
            return
            
        if args.mount:
            mount_image(args.input, args.mount)
            return
            
        if args.unmount:
            unmount_image(args.unmount)
            return
            
        if not args.input:
            parser.print_help()
            return
            
        if args.list:
            list_partitions(args.input)
            
        elif args.extract is not None:
            if not args.output:
                console.print("[red]Error:[/] Output directory required for extraction")
                return
                
            extract_partition(
                args.input,
                args.extract,
                args.output,
                filter_pattern=args.filter,
                recover_deleted=args.recover_deleted
            )
            
    except Exception as e:
        console.print(f"[red]Error:[/] {str(e)}")
        if os.environ.get('ARTEFACT_DEBUG'):
            import traceback
            console.print("[red]Stack trace:[/]")
            console.print(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()
