"""
Memory Dump Analysis Module for ArteFact v0.4.0
- Extracts printable strings (ASCII/Unicode)
- Finds IP addresses, URLs, and other IOCs
- Carves out binary executables (PE, ELF, Mach-O)
"""
import re
from pathlib import Path
from rich.console import Console
from artefact.error_handler import handle_error

console = Console()

# --- String Extraction ---
def extract_strings(file_path: Path, min_length=4, encoding='ascii'):
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
        else:
            handle_error(ValueError(f"Unsupported encoding: {encoding}"), context="extract_strings")
    except Exception as e:
        handle_error(e, context="extract_strings")
    return results

# --- IOC Extraction ---
def extract_iocs(strings):
    """Extract IPs, URLs, and emails from a list of strings."""
    iocs = {'ipv4': [], 'ipv6': [], 'url': [], 'email': []}
    ipv4_re = re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b')
    ipv6_re = re.compile(r'\b([0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}\b')
    url_re = re.compile(r'https?://[\w\.-]+(?:/[\w\./-]*)?')
    email_re = re.compile(r'[\w\.-]+@[\w\.-]+')
    for s in strings:
        if ipv4_re.search(s):
            iocs['ipv4'].append(s)
        if ipv6_re.search(s):
            iocs['ipv6'].append(s)
        if url_re.search(s):
            iocs['url'].append(s)
        if email_re.search(s):
            iocs['email'].append(s)
    return iocs

# --- Binary Carving (PE, ELF, Mach-O) ---
def carve_binaries(file_path: Path, output_dir: Path, types=None):
    """Carve out executables from memory dump by searching for known headers."""
    sigs = {
        'pe': {'header': b'MZ', 'ext': '.exe'},
        'elf': {'header': b'\x7fELF', 'ext': '.elf'},
        'macho': {'header': b'\xcf\xfa\xed\xfe', 'ext': '.macho'},
    }
    if types is not None:
        sigs = {k: v for k, v in sigs.items() if k in types}
    found = 0
    try:
        with file_path.open('rb') as f:
            data = f.read()
        for name, sig in sigs.items():
            start = 0
            while True:
                idx = data.find(sig['header'], start)
                if idx == -1:
                    break
                # Heuristic: carve up to next header or 1MB
                end = data.find(sig['header'], idx + 1)
                if end == -1 or end - idx > 1024*1024:
                    end = idx + 1024*1024
                carved = data[idx:end]
                out_file = output_dir / f"carved_{found+1}{sig['ext']}"
                with out_file.open('wb') as out:
                    out.write(carved)
                console.print(f"[green]Carved:[/] {out_file} ({name.upper()})")
                found += 1
                start = end
        if found == 0:
            console.print("[yellow]No binaries carved. Try other types or check the memory image.")
        else:
            console.print(f"[bold green]Total binaries carved:[/] {found}")
    except Exception as e:
        handle_error(e, context="carve_binaries")

# --- CLI Entrypoint ---
def main():
    import argparse
    parser = argparse.ArgumentParser(description="Memory Dump Analysis Tool")
    parser.add_argument('-i', '--input', required=True, help='Input memory dump file')
    parser.add_argument('-s', '--strings', action='store_true', help='Extract printable strings')
    parser.add_argument('--min-length', type=int, default=4, help='Minimum string length')
    parser.add_argument('--encoding', choices=['ascii', 'utf16'], default='ascii', help='String encoding')
    parser.add_argument('--iocs', action='store_true', help='Extract IOCs (IPs, URLs, emails) from strings')
    parser.add_argument('-b', '--binaries', action='store_true', help='Carve out binaries (PE, ELF, Mach-O)')
    parser.add_argument('-o', '--output', help='Output directory for carved binaries')
    args = parser.parse_args()
    file_path = Path(args.input)
    if args.strings or args.iocs:
        strings = extract_strings(file_path, min_length=args.min_length, encoding=args.encoding)
        if args.strings:
            for s in strings:
                console.print(s)
        if args.iocs:
            iocs = extract_iocs(strings)
            console.print(iocs)
    if args.binaries:
        if not args.output:
            console.print("[red]Output directory required for binary carving.")
            return
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)
        carve_binaries(file_path, output_dir)

if __name__ == "__main__":
    main()
