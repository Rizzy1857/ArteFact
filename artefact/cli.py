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


def list_tools():
    table = Table(title="Available Tools in ArteFact v0.2.0", show_lines=True)
    table.add_column("Tool", style="cyan", no_wrap=True)
    table.add_column("Description", style="green")
    table.add_row("hash", "Hash files and directories (MD5, SHA1, SHA256)")
    table.add_row("carve", "Recover files from disk images (JPG, PNG, PDF)")
    table.add_row("meta", "Extract metadata from images and PDFs")
    table.add_row("timeline", "Generate a forensics timeline from file timestamps")
    console.print(table)


def main() -> None:
    """Main CLI entry point."""
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
    args = parser.parse_args()

    # Show banner and help if no subcommand is given
    if not hasattr(args, "func") and not args.version and not args.list_tools:
        print_banner()
        parser.print_help()
        return

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
    else:
        print_banner()
        console.print("[red]Error:[/] No command provided or unknown command. See usage below.")
        parser.print_help()
        return


if __name__ == "__main__":
    main()