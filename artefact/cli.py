import argparse
import logging
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from artefact import __version__
from artefact import __codename__
from artefact.modules.hasher import hash_file, hash_directory

console = Console(style="bold cyan", force_terminal=True)
logger = logging.getLogger(__name__)

# ---- Banner ----
BANNER = f"""
[bold magenta]
 █████╗ ██████╗ ████████╗███████╗███████╗ █████╗  ██████╗████████╗
██╔══██╗██╔══██╗╚══██╔══╝██╔════╝██╔════╝██╔══██╗██╔════╝╚══██╔══╝
███████║██████╔╝   ██║   █████╗  █████╗  ███████║██║        ██║
██╔══██║██╔═══╝    ██║   ██╔══╝  ██╔══╝  ██╔══██║██║        ██║
██║  ██║██║        ██║   ███████╗██║     ██║  ██║╚██████╗   ██║
╚═╝  ╚═╝╚═╝        ╚═╝   ╚══════╝╚═╝     ╚═╝  ╚═╝ ╚═════╝   ╚═╝
[/bold magenta]
[dim]v{__version__}[/dim]
"""


def print_banner() -> None:
    """Display the ARTEFACT banner."""
    console.print(BANNER)


def hash_command(args: argparse.Namespace) -> None:
    """Handle the hash subcommand."""
    target = Path(args.target)
    if not target.exists():
        console.print(f"[red]Error:[/] Path '{args.target}' does not exist.")
        return
    if args.algorithm.lower() not in ("md5", "sha1", "sha256"):
        console.print("[red]Error:[/] Algorithm must be md5, sha1, or sha256.")
        return
    try:
        if target.is_file():
            result = hash_file(target, args.algorithm.lower())
            console.print(f"[green]{args.algorithm.upper()}:[/] {result}")
        elif target.is_dir():
            hash_directory(target, args.algorithm.lower(), "json" if args.json else "table")
    except Exception as e:
        logger.error(f"Hash command error: {e}")
        console.print(f"[red]Error:[/] {e}")


def carving_command(args: argparse.Namespace) -> None:
    from artefact.modules.carving import carve_files
    carve_files(Path(args.input), Path(args.output), args.types)


def metadata_command(args: argparse.Namespace) -> None:
    from artefact.modules.metadata import extract_metadata
    extract_metadata(Path(args.file), args.deep)


def timeline_command(args: argparse.Namespace) -> None:
    """Handle the timeline subcommand."""
    from artefact.modules.timeline import extract_file_timestamps, timeline_to_json, timeline_to_markdown
    from artefact.modules.timeline import TimelineEvent
    import glob
    from pathlib import Path
    try:
        from dateutil.parser import parse as dtparse
    except ImportError:
        dtparse = None
    events = []
    # Support both file, directory, and glob patterns
    paths = list(glob.glob(args.path, recursive=True))
    if not paths:
        if Path(args.path).exists():
            paths = [args.path]
        else:
            console.print(f"[red]No files matched:[/] {args.path}")
            return
    for file_path in paths:
        if not Path(file_path).is_file():
            continue
        events.extend(extract_file_timestamps(file_path))
        from artefact.modules.metadata import extract_metadata
        meta = extract_metadata(Path(file_path))
        for ts in meta.get('timestamps', []):
            try:
                dt = ts['value']
                if dtparse:
                    timestamp = dtparse(dt, fuzzy=True)
                else:
                    # Try best-effort ISO parse
                    from datetime import datetime
                    try:
                        timestamp = datetime.fromisoformat(dt)
                    except Exception:
                        continue
            except Exception:
                continue
            events.append(TimelineEvent(
                timestamp=timestamp,
                event_type=ts.get('label', 'metadata'),
                source=file_path,
                details={"source": "metadata"}
            ))
    if not events:
        console.print("[yellow]No timeline events found for the given path(s).[/]")
        return
    if args.format == 'json':
        output = timeline_to_json(events)
    else:
        output = timeline_to_markdown(events)
    print(output)

def memory_command(args: argparse.Namespace) -> None:
    from artefact.modules.memory import extract_strings, extract_iocs, carve_binaries
    from pathlib import Path
    file_path = Path(args.input)
    if args.strings or args.iocs:
        strings = extract_strings(file_path, min_length=args.min_length, encoding=args.encoding)
        if args.strings:
            for s in strings:
                print(s)
        if args.iocs:
            iocs = extract_iocs(strings)
            print(iocs)
    if args.binaries:
        if not args.output:
            print("[red]Output directory required for binary carving.")
            return
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)
        carve_binaries(file_path, output_dir)


def list_tools():
    table = Table(title="Available Tools in ArteFact v0.2.0", show_lines=True)
    table.add_column("Tool", style="cyan", no_wrap=True)
    table.add_column("Description", style="green")
    table.add_row("hash", "Hash files and directories (MD5, SHA1, SHA256)")
    table.add_row("carve", "Recover files from disk images (JPG, PNG, PDF)")
    table.add_row("meta", "Extract metadata from images and PDFs")
    table.add_row("timeline", "Generate a forensics timeline from file timestamps")
    table.add_row("mem", "Analyze memory dumps (extract strings, IOCs, binaries)")
    table.add_row("mount", "Mount and extract from disk images")
    table.add_row("liveops", "Capture live system forensics (processes, ports, clipboard, services)")
    console.print(table)


def interactive_menu():
    while True:
        console.print("\n[bold cyan]ARTEFACT Interactive Menu[/]")
        console.print("[1] File Carving")
        console.print("[2] Metadata Extraction")
        console.print("[3] Hashing")
        console.print("[4] Timeline Generation")
        console.print("[5] Memory Analysis")
        console.print("[6] Disk Image Mounting")
        console.print("[7] Live Forensics")
        console.print("[0] Exit")
        choice = input("Select an option: ").strip()
        if choice == "1":
            img = input("Enter path to disk/image file: ").strip()
            out = input("Enter output directory: ").strip()
            types = input("File types to carve (comma separated, blank for all): ").strip()
            types_list = [t.strip() for t in types.split(",") if t.strip()] if types else None
            from artefact.modules.carving import carve_files
            carve_files(Path(img), Path(out), types_list)
        elif choice == "2":
            f = input("Enter file path: ").strip()
            deep = input("Use deep extraction (exiftool)? [y/N]: ").strip().lower() == "y"
            from artefact.modules.metadata import extract_metadata
            meta = extract_metadata(Path(f), deep)
            console.print(meta)
        elif choice == "3":
            target = input("Enter file or directory to hash: ").strip()
            algo = input("Hash algorithm (md5/sha1/sha256): ").strip().lower() or "sha256"
            from artefact.modules.hasher import hash_file, hash_directory
            p = Path(target)
            if p.is_file():
                result = hash_file(p, algo)
                console.print(f"[green]{algo.upper()}:[/] {result}")
            elif p.is_dir():
                hash_directory(p, algo, "table")
            else:
                console.print(f"[red]Invalid path:[/] {target}")
        elif choice == "4":
            path = input("Enter file, directory, or glob pattern: ").strip()
            fmt = input("Format (json/markdown) [markdown]: ").strip().lower() or "markdown"
            from artefact.modules.timeline import extract_file_timestamps, timeline_to_json, timeline_to_markdown, TimelineEvent
            import glob
            try:
                from dateutil.parser import parse as dtparse
            except ImportError:
                dtparse = None
            events = []
            paths = list(glob.glob(path, recursive=True))
            if not paths:
                from pathlib import Path
                if Path(path).exists():
                    paths = [path]
                else:
                    console.print(f"[red]No files matched:[/] {path}")
                    continue
            for file_path in paths:
                from pathlib import Path
                if not Path(file_path).is_file():
                    continue
                events.extend(extract_file_timestamps(file_path))
                from artefact.modules.metadata import extract_metadata
                meta = extract_metadata(Path(file_path))
                for ts in meta.get('timestamps', []):
                    try:
                        dt = ts['value']
                        if dtparse:
                            timestamp = dtparse(dt, fuzzy=True)
                        else:
                            from datetime import datetime
                            try:
                                timestamp = datetime.fromisoformat(dt)
                            except Exception:
                                continue
                    except Exception:
                        continue
                    events.append(TimelineEvent(
                        timestamp=timestamp,
                        event_type=ts.get('label', 'metadata'),
                        source=file_path,
                        details={"source": "metadata"}
                    ))
            if not events:
                console.print("[yellow]No timeline events found for the given path(s).[/]")
                continue
            if fmt == 'json':
                output = timeline_to_json(events)
            else:
                output = timeline_to_markdown(events)
            print(output)
        elif choice == "5":
            mem_file = input("Enter path to memory dump file: ").strip()
            output_dir = input("Enter output directory for carved binaries: ").strip()
            extract_strings = input("Extract printable strings? [y/N]: ").strip().lower() == "y"
            extract_iocs = input("Extract IOCs (IPs, URLs, emails) from strings? [y/N]: ").strip().lower() == "y"
            carve_binaries = input("Carve out binaries (PE, ELF, Mach-O)? [y/N]: ").strip().lower() == "y"
            min_length = input("Minimum string length (default 4): ").strip() or 4
            encoding = input("String encoding (ascii, utf16, default ascii): ").strip() or "ascii"
            from artefact.modules.memory import extract_strings, extract_iocs, carve_binaries
            from pathlib import Path
            file_path = Path(mem_file)
            if extract_strings or extract_iocs:
                strings = extract_strings(file_path, min_length=int(min_length), encoding=encoding)
                if extract_strings:
                    for s in strings:
                        print(s)
                if extract_iocs:
                    iocs = extract_iocs(strings)
                    print(iocs)
            if carve_binaries:
                if not output_dir:
                    console.print("[red]Output directory required for binary carving.")
                    continue
                output_dir_path = Path(output_dir)
                output_dir_path.mkdir(parents=True, exist_ok=True)
                carve_binaries(file_path, output_dir_path)
        elif choice == "6":
            img = input("Enter path to disk/image file: ").strip()
            action = input("Action - [l]ist partitions, [e]xtract partition, or [q]uit? ").strip().lower()
            if action == "l":
                from artefact.modules.mount import list_partitions
                list_partitions(img)
            elif action == "e":
                part = input("Enter partition address to extract (e.g. /dev/sda1): ").strip()
                out = input("Enter output directory: ").strip()
                from artefact.modules.mount import extract_partition
                extract_partition(img, part, out)
            elif action == "q":
                continue
            else:
                console.print("[red]Invalid option. Please try again.")
        elif choice == "7":
            proc = input("List running processes? [y/N]: ").strip().lower() == "y"
            conn = input("List open ports/connections? [y/N]: ").strip().lower() == "y"
            clip = input("Dump clipboard contents? [y/N]: ").strip().lower() == "y"
            serv = input("List running services (Windows only)? [y/N]: ").strip().lower() == "y"
            from artefact.modules.liveops import list_processes, list_connections, get_clipboard, list_services
            if proc:
                list_processes()
            if conn:
                list_connections()
            if clip:
                get_clipboard()
            if serv:
                list_services()
            if not (proc or conn or clip or serv):
                print("[yellow]Specify at least one option: --processes, --connections, --clipboard, --services")
        elif choice == "0":
            console.print("[bold green]Goodbye!")
            break
        else:
            console.print("[red]Invalid option. Please try again.")


def mount_command(args: argparse.Namespace) -> None:
    from artefact.modules.mount import list_partitions, extract_partition
    if args.list:
        list_partitions(args.input)
    elif args.extract and args.output:
        extract_partition(args.input, args.extract, args.output)
    else:
        print("[yellow]Specify --list or --extract <partition_addr> -o <output_dir>")


def main() -> None:
    import sys
    # If no arguments (just 'artefact'), launch interactive menu
    if len(sys.argv) == 1:
        print_banner()
        interactive_menu()
        return
    # Always launch interactive menu if no subcommand or --version/--list-tools is given
    parser = argparse.ArgumentParser(
        prog="artefact",
        description="A minimalist toolkit with dark-mode aesthetics.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="\n Examples:\n  artefact hash file.txt --algorithm md5\n  artefact hash ./docs --json"
    )
    parser.add_argument('--version', action='store_true', help='Show version')
    parser.add_argument('--list-tools', action='store_true', help='List available tools')
    subparsers = parser.add_subparsers(dest='command', title='commands')
    subparsers.required = False  # Allow running with no subcommand
    hash_parser = subparsers.add_parser(
        'hash',
        help='Hash files/directories',
        description="Calculate file hashes (MD5, SHA1, SHA256)"
    )
    hash_parser.add_argument('target', help='File or directory to hash')
    hash_parser.add_argument('--algorithm', default='sha256', help='Hash algorithm (md5, sha1, sha256)')
    hash_parser.add_argument('--json', action='store_true', help='Output directory hashes as JSON')
    hash_parser.set_defaults(func=hash_command)
    # Carving subcommand
    carving_parser = subparsers.add_parser(
        'carve',
        help='Recover files from disk images',
        description="File carving from raw disk/image files"
    )
    carving_parser.add_argument('-i', '--input', required=True, help='Input disk/image file')
    carving_parser.add_argument('-o', '--output', required=True, help='Output directory')
    carving_parser.add_argument('--types', nargs='*', help='File types to look for (e.g. jpg, pdf)')
    carving_parser.set_defaults(func=carving_command)
    # Metadata subcommand
    metadata_parser = subparsers.add_parser(
        'meta',
        help='Extract metadata from files',
        description="Extract metadata from images, documents, and media files"
    )
    metadata_parser.add_argument('-f', '--file', required=True, help='File to extract metadata from')
    metadata_parser.add_argument('--deep', action='store_true', help='Use exiftool for deeper extraction')
    metadata_parser.set_defaults(func=metadata_command)
    # Timeline subcommand
    timeline_parser = subparsers.add_parser(
        'timeline',
        help='Generate a forensics timeline from files',
        description="Create a timeline of file events from timestamps"
    )
    timeline_parser.add_argument('path', help='File or glob pattern to scan for timestamps')
    timeline_parser.add_argument('--format', choices=['json', 'markdown'], default='markdown', help='Export format')
    timeline_parser.set_defaults(func=timeline_command)
    # Add memory analysis subcommand
    memory_parser = subparsers.add_parser(
        'mem',
        help='Analyze memory dumps',
        description="Memory dump analysis: extract strings, IOCs, binaries"
    )
    memory_parser.add_argument('-i', '--input', required=True, help='Input memory dump file')
    memory_parser.add_argument('-s', '--strings', action='store_true', help='Extract printable strings')
    memory_parser.add_argument('--min-length', type=int, default=4, help='Minimum string length')
    memory_parser.add_argument('--encoding', choices=['ascii', 'utf16'], default='ascii', help='String encoding')
    memory_parser.add_argument('--iocs', action='store_true', help='Extract IOCs (IPs, URLs, emails) from strings')
    memory_parser.add_argument('-b', '--binaries', action='store_true', help='Carve out binaries (PE, ELF, Mach-O)')
    memory_parser.add_argument('-o', '--output', help='Output directory for carved binaries')
    memory_parser.set_defaults(func=memory_command)
    # Add disk image mounting subcommand
    mount_parser = subparsers.add_parser(
        'mount',
        help='Mount and extract from disk images',
        description="List partitions and extract files from disk images (.img, .dd, .E01)"
    )
    mount_parser.add_argument('-i', '--input', required=True, help='Input disk image file')
    mount_parser.add_argument('--list', action='store_true', help='List partitions in the image')
    mount_parser.add_argument('--extract', type=str, help='Partition address to extract')
    mount_parser.add_argument('-o', '--output', help='Output directory for extraction')
    mount_parser.set_defaults(func=mount_command)
    # Add liveops subcommand
    liveops_parser = subparsers.add_parser(
        'liveops',
        help='Capture live system forensics (processes, ports, clipboard, services)',
        description="Live forensics: process list, open ports, clipboard, running services"
    )
    liveops_parser.add_argument('--processes', action='store_true', help='List running processes')
    liveops_parser.add_argument('--connections', action='store_true', help='List open ports and network connections')
    liveops_parser.add_argument('--clipboard', action='store_true', help='Dump clipboard contents')
    liveops_parser.add_argument('--services', action='store_true', help='List running services (Windows only)')
    liveops_parser.set_defaults(func=liveops_command)
    args = parser.parse_args()

    # If any subcommand or flag is given, run as normal
    if hasattr(args, "func") or args.version or args.list_tools:
        if args.version:
            print_banner()
            console.print(f"[bold]ARTEFACT {__version__}[/] — Codename: [italic]{__codename__}[/]")
            return
        elif args.list_tools:
            print_banner()
            list_tools()
            return
        elif hasattr(args, 'func'):
            args.func(args)
            return
    # Otherwise, always launch interactive menu
    print_banner()
    interactive_menu()


if __name__ == "__main__":
    main()