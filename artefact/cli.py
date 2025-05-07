#!/usr/bin/env python3
#!/usr/bin/env python3
import argparse
import logging
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from artefact import __version__
from artefact.modules import discover_tools

# Single Console Instance
console = Console(style="bold cyan", force_terminal=True)

# Logging Setup
logging.basicConfig(level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s")

# ---- Banner ----
BANNER = f"""
[bold magenta]
 █████╗ ██████╗ ████████╗███████╗███████╗ █████╗  ██████╗████████╗
██╔══██╗██╔══██╗╚══██╔══╝██╔════╝██╔════╝██╔══██╗██╔════╝╚══██╔══╝
███████║██████╔╝   ██║   █████╗  █████╗  ███████║██║        ██║     
██╔══██║██╔═══╝    ██║   ██╔══╝  ██╔══╝  ██╔══██║██║        ██║     
██║  ██║██║        ██║   ███████╗██║     ██║  ██║╚██████╗   ██║     
╚═╝  ╚═╝╚═╝        ╚═╝   ╚══════╝╚═╝     ╚═╝  ╚═════╝   ╚═╝     
[/bold magenta]
[dim]v{__version__} "Cold Open" | A skeleton in a three-piece suit.[/dim]
"""

# ---- Core Functions ----
def print_banner():
    """Display the ARTEFACT banner"""
    console.print(BANNER)

def list_tools():
    """Display available tools in a rich table"""
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

def hash_command(args):
    """Handle the hash subcommand"""
    from artefact.modules.hasher import hash_file, hash_directory
    target = Path(args.target)
    
    if not target.exists():
        console.print(f"[red]Error:[/] Path '{args.target}' does not exist. Please check the input.")
        return
    
    if args.algorithm.lower() not in ('md5', 'sha1', 'sha256'):
        console.print("[red]Error:[/] Algorithm must be one of: md5, sha1, sha256")
        return
    
    try:
        if target.is_file():
            result = hash_file(target, args.algorithm.lower())
            console.print(f"[green]{args.algorithm.upper()}:[/] {result}")
        elif target.is_dir():
            if args.json:
                result = hash_directory(target, args.algorithm.lower(), "json")
                console.print_json(result)
            else:
                hash_directory(target, args.algorithm.lower())
    except Exception as e:
        logging.error("Error in hash_command", exc_info=True)
        console.print(f"[red]Error:[/] {str(e)}")

# ---- CLI Setup ----
def parse_arguments():
    """Parse CLI arguments"""
    parser = argparse.ArgumentParser(
        prog="artefact",
        description="A minimalist toolkit with dark-mode aesthetics.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="\n [bold] Examples [/]:\n  artefact hash file.txt --algorithm md5\n  artefact hash ./docs --json"
    )
    
    # Global flags
    parser.add_argument('--version', action='store_true', help='Show version')
    parser.add_argument('--list-tools', action='store_true', help='List available tools')
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', title='commands')
    
    # Hash subcommand
    hash_parser = subparsers.add_parser(
        'hash',
        help='Hash files/directories',
        description="Calculate file hashes (MD5, SHA1, SHA256)"
    )
    hash_parser.add_argument('target', help='File or directory to hash')
    hash_parser.add_argument('--algorithm', default='sha256', help='Hash algorithm (md5, sha1, sha256)')
    hash_parser.add_argument('--json', action='store_true', help='Output directory hashes as JSON')
    
    return parser.parse_args()

def main():
    """Main CLI entry point"""
    args = parse_arguments()
    if args.version:
        console.print(f"[bold]ARTEFACT {__version__}[/] — Codename: [italic]Cold Open[/]")
    elif args.list_tools:
        print_banner()
        list_tools()
    elif args.command == 'hash':
        hash_command(args)
    else:
        print_banner()
        console.print("[yellow]No command provided. Use --help for usage information.[/]")