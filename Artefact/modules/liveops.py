"""Read-only live system collection helpers."""

from typing import Any, Dict, List


def _psutil():
    try:
        import psutil
    except ImportError as exc:
        raise RuntimeError("Live system collection requires psutil") from exc
    return psutil


def list_processes() -> List[Dict[str, Any]]:
    """Return a snapshot of running processes."""
    psutil = _psutil()
    rows = []
    for process in psutil.process_iter(["pid", "ppid", "name", "username", "cmdline"]):
        try:
            rows.append(dict(process.info))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return rows


def list_connections() -> List[Dict[str, Any]]:
    """Return a snapshot of system network connections."""
    psutil = _psutil()
    rows = []
    for connection in psutil.net_connections(kind="inet"):
        rows.append({
            "fd": connection.fd,
            "family": str(connection.family),
            "type": str(connection.type),
            "local_address": list(connection.laddr) if connection.laddr else None,
            "remote_address": list(connection.raddr) if connection.raddr else None,
            "status": connection.status,
            "pid": connection.pid,
        })
    return rows


def collect(items: List[str]) -> Dict[str, Any]:
    """Collect the requested read-only live artifacts."""
    collectors = {"processes": list_processes, "network": list_connections}
    unknown = sorted(set(items) - set(collectors))
    if unknown:
        raise ValueError(f"Unsupported live collection type(s): {', '.join(unknown)}")
    return {item: collectors[item]() for item in items}


__all__ = ["collect", "list_connections", "list_processes"]
