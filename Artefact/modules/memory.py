"""
Memory Dump Analysis Module
===========================

Analyzes memory dumps for strings, IOCs, processes, and binary artifacts.
Features:
- Memory dump parsing (raw, crash dumps, VMware, VirtualBox)
- String extraction and analysis
- Process listing and analysis
- Memory mapping
- IOC detection
- Binary/file carving
- Pattern matching
"""

import re
import os
import json
import logging
import tempfile
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any, BinaryIO, Generator

import yara
import psutil
from rich.console import Console
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn
from rich.table import Table

from Artefact.error_handler import handle_error, ValidationError, with_error_handling
from Artefact.core import get_logger

# Configure logging
console = Console()
logger = get_logger(__name__)

# Try to import Volatility3 for memory analysis
try:
    import volatility3
    from volatility3.framework import contexts, interfaces, plugins, constants, automagic
    from volatility3.cli.text_renderer import JsonRenderer
    from volatility3.framework.layers.linear import LinearlyMappedLayer
    VOLATILITY_AVAILABLE = True
    logger.info("Volatility3 available - enhanced memory analysis enabled")
except ImportError:
    VOLATILITY_AVAILABLE = False
    logger.info("Volatility3 not available - install with 'pip install volatility3' for enhanced memory analysis")

# Memory dump formats
MEMORY_FORMATS = {
    '.raw': {'description': 'Raw memory dump', 'handler': 'raw'},
    '.dmp': {'description': 'Windows crash dump', 'handler': 'crash'},
    '.vmem': {'description': 'VMware memory dump', 'handler': 'vmware'},
    '.vbox': {'description': 'VirtualBox memory dump', 'handler': 'vbox'},
    '.lime': {'description': 'LiME memory dump', 'handler': 'lime'},
    '.aff4': {'description': 'AFF4 memory image', 'handler': 'aff4'}
}

@dataclass
class ProcessInfo:
    """Container for process information from memory dump."""
    pid: int
    ppid: Optional[int] = None
    name: str = ""
    path: str = ""
    cmdline: List[str] = field(default_factory=list)
    start_time: Optional[datetime] = None
    memory_maps: List[Dict[str, Any]] = field(default_factory=list)
    threads: List[Dict[str, Any]] = field(default_factory=list)
    handles: List[Dict[str, Any]] = field(default_factory=list)
    dlls: List[str] = field(default_factory=list)

@dataclass
class MemoryRegion:
    """Container for memory region information."""
    start: int
    size: int
    protection: str
    state: str
    type: str
    mapped_file: Optional[str] = None
    content: Optional[bytes] = None

@dataclass
class MemoryDump:
    """Container for memory dump information."""
    path: Path
    format: str
    size: int
    architecture: Optional[str] = None
    os_info: Optional[Dict[str, str]] = None
    processes: List[ProcessInfo] = field(default_factory=list)
    regions: List[MemoryRegion] = field(default_factory=list)

def _chunk_reader(file: BinaryIO, chunk_size: int = 1024*1024) -> Generator[bytes, None, None]:
    """Read file in chunks to handle large files."""
    while True:
        chunk = file.read(chunk_size)
        if not chunk:
            break
        yield chunk

@with_error_handling("extract_strings")
def extract_strings(
    file_path: Path,
    min_length: int = 4,
    encodings: List[str] = ['ascii', 'utf-16le', 'utf-16be', 'utf-8'],
    context_bytes: int = 0
) -> Dict[str, List[Tuple[str, int]]]:
    """
    Extract printable strings from a memory dump.
    
    Args:
        file_path: Path to memory dump
        min_length: Minimum string length
        encodings: List of encodings to try
        context_bytes: Number of bytes of context to include before/after string
        
    Returns:
        Dictionary mapping encoding to list of (string, offset) tuples
    """
    if not isinstance(file_path, Path):
        file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if not file_path.is_file():
        raise ValidationError(f"Path is not a file: {file_path}")
    
    patterns = {
        'ascii': re.compile(rb'[\x20-\x7E]{%d,}' % min_length),
        'utf-8': re.compile(rb'(?:[\x20-\x7E]|[\xC2-\xDF][\x80-\xBF]|\xE0[\xA0-\xBF][\x80-\xBF]|[\xE1-\xEC\xEE\xEF][\x80-\xBF]{2}|\xED[\x80-\x9F][\x80-\xBF]){%d,}' % min_length),
        'utf-16le': re.compile(b'(?:[\x20-\x7E]\x00){%d,}' % min_length),
        'utf-16be': re.compile(b'(?:\x00[\x20-\x7E]){%d,}' % min_length)
    }
    
    results = {enc: [] for enc in encodings}
    total_size = file_path.stat().st_size
    
    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TextColumn("• {task.completed}/{task.total} bytes"),
        TimeElapsedColumn()
    ) as progress:
        task = progress.add_task("Extracting strings", total=total_size)
        
        with file_path.open('rb') as f:
            offset = 0
            for chunk in _chunk_reader(f):
                # Search for strings in chunk
                for encoding in encodings:
                    matches = patterns[encoding].finditer(chunk)
                    for match in matches:
                        string_bytes = match.group()
                        try:
                            # Add context if requested
                            if context_bytes > 0:
                                start = max(0, match.start() - context_bytes)
                                end = min(len(chunk), match.end() + context_bytes)
                                context = chunk[start:end]
                            
                            # Decode string
                            if encoding == 'ascii':
                                string = string_bytes.decode('ascii', errors='replace')
                            else:
                                string = string_bytes.decode(encoding, errors='replace')
                            
                            # Store string and file offset
                            results[encoding].append((string, offset + match.start()))
                            
                        except UnicodeDecodeError:
                            continue
                
                offset += len(chunk)
                progress.update(task, advance=len(chunk))
    
    # Sort results by offset
    for encoding in results:
        results[encoding].sort(key=lambda x: x[1])
    
    return results

@with_error_handling("extract_iocs")
def extract_iocs(
    strings: List[str],
    custom_patterns: Optional[Dict[str, str]] = None,
    dedup: bool = True,
    validate: bool = True
) -> Dict[str, List[str]]:
    """
    Extract IOCs from strings with validation.
    
    Args:
        strings: List of strings to search
        custom_patterns: Dictionary of custom regex patterns
        dedup: Remove duplicates
        validate: Validate matches (e.g., valid IP addresses)
        
    Returns:
        Dictionary of IOC types and their matches
    """
    # Default IOC patterns
    patterns = {
        'ipv4': r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b',
        'ipv6': r'(?:^|(?<=\s))(?:(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}|(?:[0-9a-fA-F]{1,4}:)*:[0-9a-fA-F]{1,4}|(?:[0-9a-fA-F]{1,4}:){6}:[0-9a-fA-F]{0,4}|(?:[0-9a-fA-F]{1,4}:){5}(?::[0-9a-fA-F]{1,4}){1,2}|(?:[0-9a-fA-F]{1,4}:){4}(?::[0-9a-fA-F]{1,4}){1,3}|(?:[0-9a-fA-F]{1,4}:){3}(?::[0-9a-fA-F]{1,4}){1,4}|(?:[0-9a-fA-F]{1,4}:){2}(?::[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:(?::[0-9a-fA-F]{1,4}){1,6}|:(?:(?::[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(?::[0-9a-fA-F]{0,4}){0,4}(?:%[0-9a-zA-Z]+)?|::(?:ffff(?::0{1,4})?:)?(?:[0-9]{1,3}\.){3}[0-9]{1,3}|(?:[0-9a-fA-F]{1,4}:){1,4}:(?:[0-9]{1,3}\.){3}[0-9]{1,3})(?:$|(?=\s))',
        'domain': r'\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}\b',
        'url': r'(?:https?://|ftp://|file://|hxxps?://|fxp://)\S+',
        'email': r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b',
        'md5': r'\b[a-fA-F0-9]{32}\b',
        'sha1': r'\b[a-fA-F0-9]{40}\b',
        'sha256': r'\b[a-fA-F0-9]{64}\b',
        'bitcoin': r'\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b',
        'credit_card': r'\b(?:\d{4}[- ]){3}\d{4}|\d{16}\b'
    }
    
    # Add custom patterns
    if custom_patterns:
        patterns.update(custom_patterns)
    
    # Compile patterns
    compiled_patterns = {
        name: re.compile(pattern, re.IGNORECASE)
        for name, pattern in patterns.items()
    }
    
    # Extract matches
    results = {name: [] for name in patterns}
    
    for s in strings:
        for ioc_type, pattern in compiled_patterns.items():
            matches = pattern.findall(s)
            if matches:
                results[ioc_type].extend(matches)
    
    # Validate matches if requested
    if validate:
        results = _validate_iocs(results)
    
    # Remove duplicates if requested
    if dedup:
        results = {k: list(set(v)) for k, v in results.items()}
    
    return results

def _validate_iocs(iocs: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """Validate extracted IOCs."""
    validated = {}
    
    for ioc_type, values in iocs.items():
        valid_values = []
        
        for value in values:
            try:
                if ioc_type == 'ipv4':
                    # Validate IPv4 address
                    octets = [int(x) for x in value.split('.')]
                    if len(octets) == 4 and all(0 <= x <= 255 for x in octets):
                        valid_values.append(value)
                
                elif ioc_type == 'domain':
                    # Basic domain validation
                    if 1 < len(value) <= 253 and all(part and len(part) <= 63 
                                                   for part in value.split('.')):
                        valid_values.append(value)
                
                elif ioc_type in ['md5', 'sha1', 'sha256']:
                    # Hash validation (check hex and length)
                    if all(c in '0123456789abcdefABCDEF' for c in value):
                        valid_values.append(value.lower())
                
                elif ioc_type == 'url':
                    # Basic URL validation
                    if '.' in value and ' ' not in value:
                        valid_values.append(value)
                
                elif ioc_type == 'email':
                    # Basic email validation
                    if '@' in value and '.' in value.split('@')[1]:
                        valid_values.append(value.lower())
                
                else:
                    # For other types, keep all values
                    valid_values.append(value)
                    
            except Exception:
                continue
        
        validated[ioc_type] = valid_values
    
    return validated

@with_error_handling("analyze_memory_dump")
def analyze_memory_dump(file_path: Path) -> MemoryDump:
    """
    Analyze a memory dump using available tools.
    
    Args:
        file_path: Path to memory dump file
        
    Returns:
        MemoryDump object with analysis results
    """
    if not isinstance(file_path, Path):
        file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"Memory dump not found: {file_path}")
    
    # Determine format
    format = file_path.suffix.lower()
    if format not in MEMORY_FORMATS:
        raise ValidationError(f"Unsupported memory dump format: {format}")
    
    # Create memory dump object
    dump = MemoryDump(
        path=file_path,
        format=format,
        size=file_path.stat().st_size
    )
    
    # Use Volatility if available
    if VOLATILITY_AVAILABLE:
        try:
            # Initialize Volatility context
            context = contexts.Context()
            
            # Create a file layer
            base_config_path = "plugins"
            single_location = "file:" + str(file_path.absolute())
            context.config["automagic.LayerStacker.single_location"] = single_location
            
            # Add automagic and requirements
            automagics = automagic.available(context)
            automagic.choose_automagic(automagics, base_config_path)
            
            # Run basic plugins
            os_info = _run_volatility_plugin(context, "windows.info.Info", base_config_path)
            if os_info:
                dump.os_info = {
                    "version": os_info.get("major", "") + "." + os_info.get("minor", ""),
                    "build": os_info.get("build", ""),
                    "architecture": os_info.get("architecture", ""),
                    "memory_size": os_info.get("memory_size", 0)
                }
            
            # Get process list
            processes = _run_volatility_plugin(context, "windows.pslist.PsList", base_config_path)
            if processes:
                for proc in processes:
                    dump.processes.append(ProcessInfo(
                        pid=proc.get("PID"),
                        ppid=proc.get("PPID"),
                        name=proc.get("ImageFileName", ""),
                        start_time=datetime.fromtimestamp(proc.get("CreateTime", 0))
                    ))
                
        except Exception as e:
            logger.warning(f"Volatility analysis failed: {e}")
    
    return dump

@with_error_handling("carve_files")
def carve_files(
    dump_path: Path,
    output_dir: Path,
    file_types: Optional[List[str]] = None,
    min_size: int = 1024,
    max_size: int = 100 * 1024 * 1024  # 100MB
) -> List[Path]:
    """
    Carve files from memory dump.
    
    Args:
        dump_path: Path to memory dump
        output_dir: Directory to save carved files
        file_types: List of file types to carve (None = all supported)
        min_size: Minimum file size in bytes
        max_size: Maximum file size in bytes
        
    Returns:
        List of paths to carved files
    """
    # File signatures
    signatures = {
        'pe': {
            'header': b'MZ',
            'footer': None,
            'ext': '.exe',
            'validate': _validate_pe
        },
        'elf': {
            'header': b'\x7fELF',
            'footer': None,
            'ext': '.elf',
            'validate': _validate_elf
        },
        'pdf': {
            'header': b'%PDF-',
            'footer': b'%%EOF',
            'ext': '.pdf',
            'validate': _validate_pdf
        },
        'zip': {
            'header': b'PK\x03\x04',
            'footer': b'PK\x05\x06',
            'ext': '.zip',
            'validate': _validate_zip
        },
        'jpg': {
            'header': b'\xff\xd8\xff',
            'footer': b'\xff\xd9',
            'ext': '.jpg',
            'validate': _validate_jpeg
        },
        'png': {
            'header': b'\x89PNG\r\n\x1a\n',
            'footer': b'IEND\xaeB`\x82',
            'ext': '.png',
            'validate': _validate_png
        }
    }
    
    if file_types:
        signatures = {k: v for k, v in signatures.items() if k in file_types}
    
    if not signatures:
        raise ValidationError("No valid file types specified for carving")
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    carved_files = []
    dump_size = dump_path.stat().st_size
    
    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn()
    ) as progress:
        task_id = progress.add_task("Carving files", total=dump_size)
        
        with dump_path.open('rb') as f:
            for chunk in _chunk_reader(f):
                progress.advance(task_id, len(chunk))
                for file_type, sig in signatures.items():
                    header = sig['header']
                    footer = sig['footer']
                    validate_func = sig['validate']
                    
                    # Find file headers
                    pos = 0
                    while True:
                        pos = chunk.find(header, pos)
                        if pos == -1:
                            break
                            
                        # Extract file data
                        if footer:
                            end = chunk.find(footer, pos + len(header))
                            if end == -1:
                                pos += 1
                                continue
                            end += len(footer)
                        else:
                            # Try to determine end heuristically
                            end = _find_file_end(chunk[pos:], file_type)
                            if end == -1:
                                pos += 1
                                continue
                            end += pos
                        
                        # Check size limits
                        file_data = chunk[pos:end]
                        if min_size <= len(file_data) <= max_size:
                            # Validate file content
                            if validate_func(file_data):
                                # Save file
                                out_path = output_dir / f"carved_{len(carved_files)}{sig['ext']}"
                                out_path.write_bytes(file_data)
                                carved_files.append(out_path)
                                logger.info(f"Carved {file_type} file: {out_path} ({len(file_data)} bytes)")
                        
                        pos = end
    
    return carved_files

def _validate_pe(data: bytes) -> bool:
    """Validate PE file format."""
    try:
        if not data.startswith(b'MZ'):
            return False
            
        # Check for DOS stub and PE header
        if len(data) < 0x40:  # Need at least this much for MZ + e_lfanew
            return False
            
        # Get PE header offset from e_lfanew
        pe_offset = int.from_bytes(data[0x3c:0x40], byteorder='little', signed=False)
        if pe_offset < 0x40 or pe_offset > len(data) - 4:  # Need space for PE\0\0
            return False
            
        # Check PE signature
        return data[pe_offset:pe_offset+4] == b'PE\0\0'
    except Exception as e:
        logger.debug(f"PE validation failed: {str(e)}")
        return False

def _validate_elf(data: bytes) -> bool:
    """Validate ELF file format."""
    return (len(data) > 4 and
            data.startswith(b'\x7fELF') and
            data[4] in [1, 2])  # 32/64-bit

def _validate_pdf(data: bytes) -> bool:
    """Validate PDF file format."""
    return (data.startswith(b'%PDF-') and
            b'%%EOF' in data[-1024:])

def _validate_zip(data: bytes) -> bool:
    """Validate ZIP file format."""
    return (data.startswith(b'PK\x03\x04') and
            b'PK\x05\x06' in data[-22:])

def _validate_jpeg(data: bytes) -> bool:
    """Validate JPEG file format."""
    return (data.startswith(b'\xff\xd8\xff') and
            data.endswith(b'\xff\xd9'))

def _validate_png(data: bytes) -> bool:
    """Validate PNG file format."""
    return (data.startswith(b'\x89PNG\r\n\x1a\n') and
            data.endswith(b'IEND\xaeB`\x82'))

def _find_file_end(data: bytes, file_type: str) -> int:
    """Find end of file heuristically."""
    if file_type == 'pe':
        try:
            # Try to find the end through PE headers
            pe_offset = int.from_bytes(data[0x3c:0x40], byteorder='little')
            if pe_offset < len(data):
                # Read number of sections
                num_sections = int.from_bytes(data[pe_offset+6:pe_offset+8], byteorder='little')
                if num_sections > 0 and num_sections < 100:  # Sanity check
                    # Last section should contain the end
                    section_table = pe_offset + 0xF8  # Size of PE headers
                    last_section = section_table + (num_sections - 1) * 40
                    if last_section + 40 <= len(data):
                        raw_size = int.from_bytes(data[last_section+16:last_section+20], byteorder='little')
                        raw_offset = int.from_bytes(data[last_section+20:last_section+24], byteorder='little')
                        return raw_offset + raw_size
        except Exception:
            pass
    
    # Default: return reasonable size or look for next file header
    return min(1024*1024, len(data))  # 1MB max

def display_memory_analysis(dump: MemoryDump):
    """Display memory analysis results in formatted tables."""
    # Basic info
    info_table = Table(title="Memory Dump Information", show_lines=True)
    info_table.add_column("Property", style="cyan")
    info_table.add_column("Value", style="white")
    
    info_table.add_row("File", str(dump.path))
    info_table.add_row("Format", MEMORY_FORMATS[dump.format]['description'])
    info_table.add_row("Size", _format_size(dump.size))
    if dump.architecture:
        info_table.add_row("Architecture", dump.architecture)
    if dump.os_info:
        for key, value in dump.os_info.items():
            info_table.add_row(key, str(value))
    
    console.print(info_table)
    
    # Process list
    if dump.processes:
        proc_table = Table(title="Process List", show_lines=True)
        proc_table.add_column("PID", style="cyan", justify="right")
        proc_table.add_column("PPID", style="blue", justify="right")
        proc_table.add_column("Name", style="green")
        proc_table.add_column("Start Time", style="yellow")
        proc_table.add_column("Path", style="white")
        
        for proc in sorted(dump.processes, key=lambda x: x.pid):
            proc_table.add_row(
                str(proc.pid),
                str(proc.ppid or ''),
                proc.name,
                proc.start_time.strftime('%Y-%m-%d %H:%M:%S') if proc.start_time else '',
                proc.path
            )
        
        console.print(proc_table)

def _format_size(size_bytes: int) -> str:
    """Format size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"

if __name__ == "__main__":
    import argparse
    import textwrap
    
    parser = argparse.ArgumentParser(
        description="Memory Dump Analysis Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
            Examples:
              # Extract strings from memory dump
              %(prog)s -i dump.raw --strings
              
              # Carve files from memory dump
              %(prog)s -i dump.raw --carve -o ./carved
              
              # Extract IOCs
              %(prog)s -i dump.raw --iocs
              
              # Full analysis
              %(prog)s -i dump.raw --analyze
              
              # List supported formats
              %(prog)s --formats
        """)
    )
    
    parser.add_argument("-i", "--input",
                       help="Input memory dump file")
    parser.add_argument("-o", "--output",
                       help="Output directory for carved files")
    parser.add_argument("--strings", action="store_true",
                       help="Extract strings from dump")
    parser.add_argument("--min-length", type=int, default=4,
                       help="Minimum string length")
    parser.add_argument("--encodings", nargs="+",
                       default=['ascii', 'utf-16le', 'utf-8'],
                       help="String encodings to extract")
    parser.add_argument("--carve", action="store_true",
                       help="Carve files from dump")
    parser.add_argument("--file-types", nargs="+",
                       help="File types to carve")
    parser.add_argument("--iocs", action="store_true",
                       help="Extract IOCs")
    parser.add_argument("--analyze", action="store_true",
                       help="Perform full memory analysis")
    parser.add_argument("--formats", action="store_true",
                       help="List supported memory dump formats")
    parser.add_argument("--json", action="store_true",
                       help="Output in JSON format")
    
    args = parser.parse_args()
    
    try:
        if args.formats:
            console.print("\n[bold]Supported memory dump formats:[/]")
            for ext, info in MEMORY_FORMATS.items():
                console.print(f"  {ext:8} {info['description']}")
            exit(0)
        
        if not args.input:
            parser.print_help()
            exit(1)
        
        dump_path = Path(args.input)
        
        if args.analyze:
            # Full analysis
            dump = analyze_memory_dump(dump_path)
            if args.json:
                console.print_json(json.dumps(asdict(dump), default=str))
            else:
                display_memory_analysis(dump)
        
        if args.strings:
            # Extract strings
            strings = extract_strings(
                dump_path,
                min_length=args.min_length,
                encodings=args.encodings
            )
            
            if args.json:
                console.print_json(json.dumps(strings, indent=2))
            else:
                for encoding, matches in strings.items():
                    console.print(f"\n[bold]{encoding} strings:[/]")
                    for string, offset in matches[:100]:  # Limit output
                        console.print(f"[cyan]{offset:#x}:[/] {string}")
                    if len(matches) > 100:
                        console.print(f"[yellow]...and {len(matches)-100} more[/]")
        
        if args.carve:
            if not args.output:
                console.print("[red]Error:[/] Output directory required for carving")
                exit(1)
            
            carved_files = carve_files(
                dump_path,
                Path(args.output),
                file_types=args.file_types
            )
            
            console.print(f"\n[green]Carved {len(carved_files)} files to {args.output}[/]")
        
        if args.iocs:
            # First extract strings
            strings = extract_strings(dump_path)
            # Then extract IOCs from all strings
            all_strings = []
            for matches in strings.values():
                all_strings.extend(match[0] for match in matches)
            
            iocs = extract_iocs(all_strings)
            
            if args.json:
                console.print_json(json.dumps(iocs, indent=2))
            else:
                for ioc_type, values in iocs.items():
                    if values:
                        console.print(f"\n[bold]{ioc_type.upper()}:[/]")
                        for value in sorted(values):
                            console.print(f"  {value}")
        
    except Exception as e:
        console.print(f"[red]Error:[/] {str(e)}")
        if os.environ.get('ARTEFACT_DEBUG'):
            import traceback
            console.print(traceback.format_exc())
        exit(1)

def _run_volatility_plugin(context: Any, plugin_name: str, config_path: str) -> Any:
    """Run a Volatility plugin and return results."""

@with_error_handling("carve_binaries")
def carve_binaries(
    dump_path: Path,
    output_dir: Path,
    types: Optional[List[str]] = None,
    min_size: int = 64,  # Lower minimum size for test binary files
    max_size: int = 100 * 1024 * 1024
) -> List[Path]:
    """
    Carve binary files (PE, ELF, etc.) from a memory dump.
    Args:
        dump_path: Path to memory dump
        output_dir: Directory to save carved binaries
        types: List of binary types to carve (e.g., ["pe", "elf"])
        min_size: Minimum file size (default: 64 bytes to allow test files)
        max_size: Maximum file size
    Returns:
        List of paths to carved binaries
    """
    # Reuse carve_files logic, but restrict to binary types
    binary_types = ["pe", "elf"]
    if types:
        binary_types = [t for t in types if t in binary_types]
    return carve_files(dump_path, output_dir, file_types=binary_types, min_size=min_size, max_size=max_size)
    try:
        # Configure plugin
        plugin = plugins.construct_plugin(context, [config_path, plugin_name])
        
        # Create TreeGrid
        grid = plugin.run()
        
        # Convert TreeGrid to JSON
        renderer = JsonRenderer()
        output = renderer.render(grid)
        
        # Parse and return results
        return json.loads(output)
    except Exception as e:
        logger.warning(f"Volatility plugin {plugin_name} failed: {e}")
        return None
