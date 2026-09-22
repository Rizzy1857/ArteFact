"""Runtime dependency and capability diagnostics."""

import importlib.util
import shutil
import sys
from dataclasses import asdict, dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class HealthCheck:
    name: str
    available: bool
    required: bool
    purpose: str
    fix: Optional[str] = None


PYTHON_MODULES = {
    "rich": (True, "terminal interface", "pip install rich"),
    "dateutil": (True, "timestamp parsing", "pip install python-dateutil"),
    "psutil": (False, "resource monitoring and live analysis", "pip install psutil"),
    "PIL": (False, "image metadata", "pip install Pillow"),
    "pypdf": (False, "PDF metadata", "pip install pypdf"),
    "pytsk3": (False, "filesystem image analysis", "pip install pytsk3"),
    "yara": (False, "YARA memory scanning", "pip install yara-python"),
    "volatility3": (False, "advanced memory analysis", "pip install volatility3"),
    "PySide6": (False, "Qt desktop interface", "pip install PySide6"),
}

EXECUTABLES = {
    "exiftool": (False, "deep metadata extraction"),
    "tshark": (False, "advanced network dissection"),
}


def dependency_health() -> Dict[str, object]:
    checks: List[HealthCheck] = []
    for name, (required, purpose, fix) in PYTHON_MODULES.items():
        available = importlib.util.find_spec(name) is not None
        checks.append(HealthCheck(name, available, required, purpose, None if available else fix))
    for name, (required, purpose) in EXECUTABLES.items():
        available = shutil.which(name) is not None
        checks.append(HealthCheck(name, available, required, purpose,
                                  None if available else f"Install {name} and add it to PATH"))
    required_ok = all(item.available for item in checks if item.required)
    return {
        "healthy": required_ok,
        "python": sys.version.split()[0],
        "checks": [asdict(item) for item in checks],
        "available_capabilities": [item.purpose for item in checks if item.available],
    }


__all__ = ["HealthCheck", "dependency_health"]
