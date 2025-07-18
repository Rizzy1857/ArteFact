"""
Live Forensics / Volatile Data Capture for ArteFact
- Captures process list, open ports, clipboard, running services
- Cross-platform (Windows, Linux, Mac where possible)
"""
import sys
import platform
from rich.console import Console
from Artefact.error_handler import handle_error

console = Console()

try:
    import psutil
except ImportError:
    psutil = None

# --- Process List ---
def list_processes():
    if psutil is None:
        console.print("[red]psutil not installed. Install with 'pip install psutil'.")
        return
    try:
        for proc in psutil.process_iter(['pid', 'name', 'username', 'cmdline']):
            info = proc.info
            console.print(f"[cyan]PID {info['pid']}[/] {info['name']} ({info.get('username', '')}) {' '.join(info.get('cmdline', []))}")
    except Exception as e:
        handle_error(e, context="list_processes")

# --- Open Ports / Connections ---
def list_connections():
    if psutil is None:
        console.print("[red]psutil not installed. Install with 'pip install psutil'.")
        return
    try:
        for conn in psutil.net_connections():
            laddr = f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else ""
            raddr = f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else ""
            console.print(f"[green]{conn.type.name}[/] {laddr} -> {raddr} [{conn.status}]")
    except Exception as e:
        handle_error(e, context="list_connections")

# --- Clipboard (platform-specific) ---
def get_clipboard():
    try:
        if platform.system() == "Windows":
            import ctypes
            CF_UNICODETEXT = 13
            ctypes.windll.user32.OpenClipboard(0)
            handle = ctypes.windll.user32.GetClipboardData(CF_UNICODETEXT)
            data = ctypes.wstring_at(handle)
            ctypes.windll.user32.CloseClipboard()
            console.print(f"[magenta]Clipboard:[/] {data}")
        elif platform.system() == "Darwin":
            import subprocess
            data = subprocess.check_output(['pbpaste']).decode()
            console.print(f"[magenta]Clipboard:[/] {data}")
        else:
            import subprocess
            data = subprocess.check_output(['xclip', '-selection', 'clipboard', '-o']).decode()
            console.print(f"[magenta]Clipboard:[/] {data}")
    except Exception as e:
        handle_error(e, context="get_clipboard")

# --- Running Services (Windows) ---
def list_services():
    if platform.system() != "Windows":
        console.print("[yellow]Service listing only supported on Windows.")
        return
    try:
        import wmi
        c = wmi.WMI()
        for service in c.Win32_Service():
            console.print(f"[blue]{service.Name}[/] ({service.State}) - {service.Description}")
    except ImportError:
        console.print("[red]wmi not installed. Install with 'pip install wmi'.")
    except Exception as e:
        handle_error(e, context="list_services")

# --- CLI Entrypoint ---
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Live Forensics / Volatile Data Capture Tool")
    parser.add_argument('--processes', action='store_true', help='List running processes')
    parser.add_argument('--connections', action='store_true', help='List open ports and network connections')
    parser.add_argument('--clipboard', action='store_true', help='Dump clipboard contents')
    parser.add_argument('--services', action='store_true', help='List running services (Windows only)')
    args = parser.parse_args()
    if args.processes:
        list_processes()
    if args.connections:
        list_connections()
    if args.clipboard:
        get_clipboard()
    if args.services:
        list_services()
    if not (args.processes or args.connections or args.clipboard or args.services):
        parser.print_help()
