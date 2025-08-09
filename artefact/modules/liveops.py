"""
Live Forensics Module for ArteFact
- Capture process list, open ports, clipboard, running services
- (Future) RAM snapshot support
"""
from rich.console import Console
console = Console()
try:
    import psutil
except ImportError:
    psutil = None
    console.print("[red]psutil not installed. Install with 'pip install psutil'.")

def list_processes():
    if psutil is None:
        console.print("[red]psutil not installed. Install with 'pip install psutil'.")
        return
    for proc in psutil.process_iter(['pid', 'name', 'username']):
        console.print(f"PID: {proc.info['pid']}, Name: {proc.info['name']}, User: {proc.info['username']}")

def list_ports():
    if psutil is None:
        console.print("[red]psutil not installed. Install with 'pip install psutil'.")
        return
    for conn in psutil.net_connections():
        if conn.laddr:
            console.print(f"Proto: {conn.type}, Local: {conn.laddr}, Remote: {conn.raddr}, Status: {conn.status}")

def get_clipboard():
    try:
        import pyperclip
    except ImportError:
        console.print("[red]pyperclip not installed. Install with 'pip install pyperclip'.")
        return
    try:
        data = pyperclip.paste()
        console.print(f"[cyan]Clipboard:[/] {data}")
    except Exception as e:
        console.print(f"[red]Clipboard error:[/] {e}")

def list_services():
    if psutil is None:
        console.print("[red]psutil not installed. Install with 'pip install psutil'.")
        return
    try:
        for svc in psutil.win_service_iter():
            console.print(f"Service: {svc.name()}, Status: {svc.status()}")
    except AttributeError:
        console.print("[yellow]Service listing is only available on Windows.")
