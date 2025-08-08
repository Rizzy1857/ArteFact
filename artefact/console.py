"""
Console utilities and interactive features for Artefact.
Provides enhanced console interaction and user experience features.
"""

import sys
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


def interactive_mode():
    """
    Interactive mode for Artefact CLI.
    Provides a guided experience for users to select operations.
    """
    console.print("[bold cyan]Welcome to Artefact Interactive Mode![/]")
    console.print("This mode will guide you through common forensic tasks.\n")
    
    while True:
        console.print("[bold]Available operations:[/]")
        console.print("1. Hash files/directories")
        console.print("2. Extract metadata")
        console.print("3. Create timeline")
        console.print("4. Carve files from images")
        console.print("5. Analyze memory dumps")
        console.print("6. Live system analysis")
        console.print("7. Mount disk images")
        console.print("8. Exit")
        
        choice = Prompt.ask("\nSelect an operation", choices=["1", "2", "3", "4", "5", "6", "7", "8"])
        
        if choice == "8":
            console.print("[green]Goodbye![/]")
            sys.exit(0)
        elif choice == "1":
            _interactive_hash()
        elif choice == "2":
            _interactive_metadata()
        elif choice == "3":
            _interactive_timeline()
        elif choice == "4":
            _interactive_carve()
        elif choice == "5":
            _interactive_memory()
        elif choice == "6":
            _interactive_liveops()
        elif choice == "7":
            _interactive_mount()
        
        if not Confirm.ask("\nWould you like to perform another operation?"):
            break


def _interactive_hash():
    """Interactive hash operation."""
    target = Prompt.ask("Enter file or directory path to hash")
    algorithm = Prompt.ask("Choose hash algorithm", choices=["md5", "sha1", "sha256"], default="sha256")
    
    from Artefact.cli import hash_command
    import argparse
    
    args = argparse.Namespace()
    args.target = target
    args.algorithm = algorithm
    args.json = Confirm.ask("Output as JSON?", default=False)
    
    hash_command(args)


def _interactive_metadata():
    """Interactive metadata extraction."""
    file_path = Prompt.ask("Enter file path for metadata extraction")
    deep = Confirm.ask("Use deep extraction (requires exiftool)?", default=False)
    
    from Artefact.cli import metadata_command
    import argparse
    
    args = argparse.Namespace()
    args.file = file_path
    args.deep = deep
    
    metadata_command(args)


def _interactive_timeline():
    """Interactive timeline creation."""
    path = Prompt.ask("Enter file or glob pattern for timeline")
    format_choice = Prompt.ask("Choose output format", choices=["json", "markdown"], default="markdown")
    
    from Artefact.cli import timeline_command
    import argparse
    
    args = argparse.Namespace()
    args.path = path
    args.format = format_choice
    
    timeline_command(args)


def _interactive_carve():
    """Interactive file carving."""
    input_file = Prompt.ask("Enter input disk/image file path")
    output_dir = Prompt.ask("Enter output directory")
    types_str = Prompt.ask("Enter file types to carve (comma-separated, leave empty for all)", default="")
    
    types = [t.strip() for t in types_str.split(",")] if types_str else None
    
    from Artefact.cli import carving_command
    import argparse
    
    args = argparse.Namespace()
    args.input = input_file
    args.output = output_dir
    args.types = types
    
    carving_command(args)


def _interactive_memory():
    """Interactive memory analysis."""
    input_file = Prompt.ask("Enter memory dump file path")
    
    console.print("\n[bold]Memory analysis options:[/]")
    strings = Confirm.ask("Extract strings?", default=True)
    iocs = Confirm.ask("Extract IOCs (IPs, URLs, emails)?", default=True) if strings else False
    binaries = Confirm.ask("Carve binaries?", default=False)
    
    output_dir = None
    if binaries:
        output_dir = Prompt.ask("Enter output directory for carved binaries")
    
    from Artefact.cli import memory_command
    import argparse
    
    args = argparse.Namespace()
    args.input = input_file
    args.strings = strings
    args.iocs = iocs
    args.binaries = binaries
    args.output = output_dir
    args.min_length = 4
    args.encoding = "ascii"
    args.types = None
    
    memory_command(args)


def _interactive_liveops():
    """Interactive live operations."""
    console.print("\n[bold]Live system analysis options:[/]")
    processes = Confirm.ask("List running processes?", default=True)
    connections = Confirm.ask("List network connections?", default=True)
    clipboard = Confirm.ask("Get clipboard contents?", default=False)
    services = Confirm.ask("List running services? (Windows only)", default=False)
    
    from Artefact.cli import liveops_command
    import argparse
    
    args = argparse.Namespace()
    args.processes = processes
    args.connections = connections
    args.clipboard = clipboard
    args.services = services
    
    liveops_command(args)


def _interactive_mount():
    """Interactive disk image mounting."""
    input_file = Prompt.ask("Enter disk image file path")
    
    list_partitions = Confirm.ask("List partitions?", default=True)
    
    from Artefact.cli import mount_command
    import argparse
    
    if list_partitions:
        args = argparse.Namespace()
        args.input = input_file
        args.list = True
        args.extract = None
        args.output = None
        
        mount_command(args)
        
        if Confirm.ask("\nWould you like to extract a partition?"):
            partition = Prompt.ask("Enter partition address to extract")
            output_dir = Prompt.ask("Enter output directory")
            
            args.list = False
            args.extract = partition
            args.output = output_dir
            
            mount_command(args)


def show_progress_bar(description: str, total: int = 100):
    """
    Show a progress bar for long-running operations.
    
    Args:
        description: Description of the operation
        total: Total steps (default 100)
    
    Returns:
        Progress context manager
    """
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    )


if __name__ == "__main__":
    interactive_mode()
