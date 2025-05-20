import argparse
import logging
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from artefact import __version__
from artefact.modules import discover_tools
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


def list_tools() -> None:
    """Display available tools in a rich table."""
    tools = discover_tools()
    if not tools:
        console.print("[yellow]No tools available.[/]")
        return
    table = Table(title="[bold]Available Tools[/]", show_header=True, header_style="bold magenta")
    table.add_column("Tool", style="cyan", no_wrap=True)
    table.add_column("Description", style="green")
    for name, func in tools.items():
        docstring = func.__doc__ or "No description available"
        table.add_row(name, docstring.split('\n')[0])
    console.print(Panel.fit(table, border_style="dim"))


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


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="artefact",
        description="A minimalist toolkit with dark-mode aesthetics.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="\n [bold] Examples [/]:\n  artefact hash file.txt --algorithm md5\n  artefact hash ./docs --json"
    )
    parser.add_argument('--version', action='store_true', help='Show version')
    parser.add_argument('--list-tools', action='store_true', help='List available tools')
    subparsers = parser.add_subparsers(dest='command', title='commands')
    hash_parser = subparsers.add_parser(
        'hash',
        help='Hash files/directories',
        description="Calculate file hashes (MD5, SHA1, SHA256)"
    )
    hash_parser.add_argument('target', help='File or directory to hash')
    hash_parser.add_argument('--algorithm', default='sha256', help='Hash algorithm (md5, sha1, sha256)')
    hash_parser.add_argument('--json', action='store_true', help='Output directory hashes as JSON')
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
    args = parser.parse_args()
    if args.version:
        console.print(f"[bold]ARTEFACT {__version__}[/] — Codename: [italic]Cold Open[/]")
    elif args.list_tools:
        print_banner()
        list_tools()
    elif hasattr(args, 'func'):
        args.func(args)
    else:
        print_banner()
        parser.print_help()


if __name__ == "__main__":
    main()