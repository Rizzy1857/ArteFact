"""
Live Operations Module
======================

Collects live system artifacts including processes, network connections,
and other volatile data.
"""

import platform
from rich.console import Console

from Artefact.error_handler import with_error_handling

console = Console()

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

@with_error_handling("list_processes")
def list_processes():
    """List running processes."""
    if not PSUTIL_AVAILABLE:
        console.print("[red]psutil not available. Install with 'pip install psutil'[/]")
        return
    
    try:
        for proc in psutil.process_iter(['pid', 'name', 'username', 'cmdline']):
            info = proc.info
            cmdline = ' '.join(info.get('cmdline', []))[:50]  # Limit length
            console.print(f"[cyan]PID {info['pid']}[/] {info['name']} ({info.get('username', 'N/A')}) {cmdline}")
    except Exception as e:
        console.print(f"[red]Error listing processes: {e}[/]")

@with_error_handling("list_connections")
def list_connections():
    """List network connections."""
    if not PSUTIL_AVAILABLE:
        console.print("[red]psutil not available. Install with 'pip install psutil'[/]")
        return
    
    try:
        for conn in psutil.net_connections():
            laddr = f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "N/A"
            raddr = f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "N/A"
            console.print(f"[green]{conn.type.name}[/] {laddr} -> {raddr} [{conn.status}]")
    except Exception as e:
        console.print(f"[red]Error listing connections: {e}[/]")

@with_error_handling("get_clipboard")
def get_clipboard():
    """Get clipboard contents."""
    try:
        if platform.system() == "Windows":
            import ctypes
            ctypes.windll.user32.OpenClipboard(0)
            handle = ctypes.windll.user32.GetClipboardData(13)  # CF_UNICODETEXT
            if handle:
                data = ctypes.wstring_at(handle)
                ctypes.windll.user32.CloseClipboard()
                console.print(f"[magenta]Clipboard:[/] {data[:100]}...")
            else:
                console.print("[yellow]Clipboard is empty[/]")
        else:
            console.print("[yellow]Clipboard access not implemented for this OS[/]")
    except Exception as e:
        console.print(f"[red]Error accessing clipboard: {e}[/]")

@with_error_handling("list_services")
def list_services():
    """List running services (Windows only)."""
    if platform.system() != "Windows":
        console.print("[yellow]Service listing only supported on Windows[/]")
        return
    
    try:
        import wmi
        c = wmi.WMI()
        for service in c.Win32_Service():
            console.print(f"[blue]{service.Name}[/] ({service.State}) - {service.Description[:50]}")
    except ImportError:
        console.print("[red]WMI module not available. Install with 'pip install wmi'[/]")
    except Exception as e:
        console.print(f"[red]Error listing services: {e}[/]")
