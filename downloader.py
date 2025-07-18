import subprocess
import sys
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.console import Console

console = Console()

# Core and optional dependencies
core = [
    "rich>=13.0.0",
    "argparse"
]
optional = [
    "pytsk3", "Pillow", "PyPDF2", "volatility3", "pyewf", "psutil", "wmi"
]

def pip_install(pkg):
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])
        return True
    except subprocess.CalledProcessError:
        return False

def main():
    all_pkgs = core + optional
    console.print("[bold cyan]ArteFact Downloader (Beta)[/]")
    with Progress(
        SpinnerColumn(),
        BarColumn(),
        TextColumn("{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task("Installing dependencies...", total=len(all_pkgs))
        for pkg in all_pkgs:
            progress.update(task, description=f"Installing [yellow]{pkg}[/]...")
            ok = pip_install(pkg)
            if ok:
                progress.console.print(f"[green]Installed:[/] {pkg}")
            else:
                progress.console.print(f"[red]Failed:[/] {pkg}")
            progress.advance(task)
    console.print("[bold green]All done! You can now use ArteFact CLI.[/]")

if __name__ == "__main__":
    main()
