#!/usr/bin/env python3
import argparse
from pathlib import Path
from rich.console import Console
console = Console(force_terminal=True)  
from rich.table import Table
from rich.panel import Panel
from artefact import __version__
from artefact.modules import discover_tools

console = Console(style="bold cyan")

# ---- Banner ----
BANNER = """
[bold magenta]
 █████╗ ██████╗ ████████╗███████╗███████╗ █████╗  ██████╗████████╗
██╔══██╗██╔══██╗╚══██╔══╝██╔════╝██╔════╝██╔══██╗██╔════╝╚══██╔══╝
███████║██████╔╝   ██║   █████╗  █████╗  ███████║██║        ██║     
██╔══██║██╔═══╝    ██║   ██╔══╝  ██╔══╝  ██╔══██║██║        ██║     
██║  ██║██║        ██║   ███████╗██║     ██║  ██║╚██████╗   ██║     
╚═╝  ╚═╝╚═╝        ╚═╝   ╚══════╝╚═╝     ╚═╝  ╚═╝ ╚═════╝   ╚═╝     
[/bold magenta]
[dim]v{} "Cold Open" | A skeleton in a three-piece suit.[/dim]
""".format(__version__)

# ---- Core Functions ----
def print_banner():
    """Display the ARTEFACT banner"""
    console.print(BANNER)

def list_tools():
    """Display available tools in a rich table"""
    tools = discover_tools()
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
        console.print(f"[red]Error:[/] Path '{args.target}' does not exist")
        return
    
    if args.algorithm.lower() not in ('md5', 'sha1', 'sha256'):
        console.print("[red]Error:[/] Algorithm must be md5, sha1, or sha256")
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
        console.print(f"[red]Error:[/] {str(e)}")

# ---- CLI Setup ----
def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        prog="artefact",
        description="A minimalist toolkit with dark-mode aesthetics.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="\nExamples:\n  artefact hash file.txt --algorithm md5\n  artefact hash ./docs --json"
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
    hash_parser.add_argument(
        '--algorithm', 
        default='sha256',
        help='Hash algorithm (md5, sha1, sha256)'
    )
    hash_parser.add_argument(
        '--json', 
        action='store_true',
        help='Output directory hashes as JSON'
    )
    
    args = parser.parse_args()
    
    if args.version:
        console.print(f"[bold]ARTEFACT {__version__}[/] — Codename: [italic]Cold Open[/]")
    elif args.list_tools:
        print_banner()
        list_tools()
    elif args.command == 'hash':
        hash_command(args)
    else:
        print_banner()
        parser.print_help()

if __name__ == "__main__":
    main()