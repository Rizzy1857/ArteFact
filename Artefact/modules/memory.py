"""
Memory Dump Analysis Module
===========================

Analyzes memory dumps for strings, IOCs, and binary artifacts.
"""

import re
from pathlib import Path
from typing import Dict, List
from rich.console import Console

from Artefact.error_handler import with_error_handling

console = Console()

@with_error_handling("extract_strings")
def extract_strings(file_path: Path, min_length: int = 4, encoding: str = 'ascii') -> List[str]:
    """Extract printable strings from a memory dump."""
    results = []
    try:
        with file_path.open('rb') as f:
            data = f.read()
        if encoding == 'ascii':
            pattern = rb'[\x20-\x7E]{%d,}' % min_length
            results = [s.decode('ascii', errors='ignore') for s in re.findall(pattern, data)]
        elif encoding == 'utf16':
            pattern = (b'(?:[\x20-\x7E]\x00){%d,}' % min_length)
            results = [s.decode('utf-16le', errors='ignore') for s in re.findall(pattern, data)]
    except Exception as e:
        console.print(f"[red]Error extracting strings: {e}[/]")
    return results

@with_error_handling("extract_iocs")
def extract_iocs(strings: List[str]) -> Dict[str, List[str]]:
    """Extract IOCs from strings."""
    iocs = {'ipv4': [], 'ipv6': [], 'url': [], 'email': []}
    ipv4_re = re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b')
    ipv6_re = re.compile(r'\b([0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}\b')
    url_re = re.compile(r'https?://[\w\.-]+(?:/[\w\./-]*)?')
    email_re = re.compile(r'[\w\.-]+@[\w\.-]+')
    
    for s in strings:
        iocs['ipv4'].extend(ipv4_re.findall(s))
        iocs['ipv6'].extend(ipv6_re.findall(s))
        iocs['url'].extend(url_re.findall(s))
        iocs['email'].extend(email_re.findall(s))
    
    return iocs

@with_error_handling("carve_binaries")
def carve_binaries(file_path: Path, output_dir: Path, types: List[str] = None) -> int:
    """Carve binaries from memory dump."""
    sigs = {
        'pe': {'header': b'MZ', 'ext': '.exe'},
        'elf': {'header': b'\x7fELF', 'ext': '.elf'},
        'macho': {'header': b'\xcf\xfa\xed\xfe', 'ext': '.macho'},
    }
    if types:
        sigs = {k: v for k, v in sigs.items() if k in types}
    
    found = 0
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        with file_path.open('rb') as f:
            data = f.read()
        
        for name, sig in sigs.items():
            start = 0
            while True:
                idx = data.find(sig['header'], start)
                if idx == -1:
                    break
                end = min(idx + 1024*1024, len(data))  # 1MB max
                carved = data[idx:end]
                output_file = output_dir / f"carved_{found+1}{sig['ext']}"
                output_file.write_bytes(carved)
                console.print(f"[green]Carved:[/] {output_file}")
                found += 1
                start = idx + 1
    except Exception as e:
        console.print(f"[red]Error carving binaries: {e}[/]")
    
    return found
