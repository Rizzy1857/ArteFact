"""Advanced read-only disk, deleted-file, registry, and snapshot analysis."""

import os
import re
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from Artefact.error_handler import ValidationError
from Artefact.modules import diskimage


def filesystem_inventory(image_path: Union[str, Path], partition_addr: int = 0,
                         max_entries: int = 100_000) -> Dict[str, Any]:
    """Inventory allocated and deleted filesystem entries without writing evidence."""
    if diskimage.pytsk3 is None:
        raise ValidationError("Filesystem analysis requires pytsk3")
    image = diskimage.open_image(image_path)
    img = diskimage.pytsk3.Img_Info(str(image.path))
    start_sector = 0
    try:
        volume = diskimage.pytsk3.Volume_Info(img)
        partition = next((part for part in volume if part.addr == partition_addr), None)
        if partition is None:
            raise ValidationError(f"Partition {partition_addr} not found")
        start_sector = partition.start
    except ValidationError:
        raise
    except Exception:
        if partition_addr != 0:
            raise ValidationError(f"Partition table unavailable; only partition 0 is valid")
    fs = diskimage.pytsk3.FS_Info(img, offset=start_sector * image.sector_size)
    entries: List[Dict[str, Any]] = []

    def walk(directory: Any, parent: str = "") -> None:
        if len(entries) >= max_entries:
            return
        for entry in directory:
            name_bytes = entry.info.name.name
            if name_bytes in (b".", b"..") or entry.info.meta is None:
                continue
            name = name_bytes.decode("utf-8", errors="replace")
            path = (Path(parent) / name).as_posix()
            meta = entry.info.meta
            deleted = bool(meta.flags & diskimage.pytsk3.TSK_FS_META_FLAG_UNALLOC)
            is_directory = meta.type == diskimage.pytsk3.TSK_FS_META_TYPE_DIR
            entries.append({"path": path, "size": meta.size or 0,
                            "created": meta.crtime or None, "modified": meta.mtime or None,
                            "accessed": meta.atime or None, "directory": is_directory,
                            "deleted": deleted, "inode": meta.addr})
            if is_directory and not deleted and len(entries) < max_entries:
                try:
                    walk(entry.as_directory(), path)
                except Exception:
                    continue

    walk(fs.open_dir(path="/"))
    return {
        "image": str(image.path), "partition": partition_addr,
        "read_only": True, "truncated": len(entries) >= max_entries,
        "entries": entries,
        "summary": {"total": len(entries),
                    "files": sum(not item["directory"] for item in entries),
                    "directories": sum(item["directory"] for item in entries),
                    "deleted": sum(item["deleted"] for item in entries)},
    }


def recover_deleted_files(image_path: Union[str, Path], partition_addr: int,
                          output_dir: Union[str, Path], pattern: Optional[str] = None) -> List[Path]:
    """Recover unallocated directory entries through the existing safe extractor."""
    before = set(Path(output_dir).rglob("*")) if Path(output_dir).exists() else set()
    diskimage.extract_partition(image_path, partition_addr, output_dir,
                                filter_pattern=pattern, recover_deleted=True)
    return sorted(path for path in Path(output_dir).rglob("*") if path.is_file() and path not in before)


def analyze_registry_hive(path: Union[str, Path], max_depth: int = 4,
                          max_values: int = 10_000) -> Dict[str, Any]:
    """Read an offline Windows Registry hive and return a bounded key/value tree."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(path)
    try:
        from Registry import Registry
    except ImportError as exc:
        raise RuntimeError("Registry analysis requires python-registry") from exc
    hive = Registry.Registry(str(path))
    rows: List[Dict[str, Any]] = []

    def walk(key: Any, depth: int) -> None:
        if depth > max_depth or len(rows) >= max_values:
            return
        for value in key.values():
            try:
                data = value.value()
                if isinstance(data, bytes):
                    data = data.hex()
                rows.append({"key": key.path(), "name": value.name(),
                             "type": value.value_type_str(), "value": data})
            except Exception:
                continue
            if len(rows) >= max_values:
                return
        for child in key.subkeys():
            walk(child, depth + 1)

    walk(hive.root(), 0)
    return {"hive": str(path), "read_only": True, "values": rows,
            "truncated": len(rows) >= max_values}


def list_volume_shadows(volume: Optional[str] = None) -> List[Dict[str, str]]:
    """List Windows Volume Shadow Copy snapshots without mounting or modifying them."""
    if sys.platform != "win32":
        return []
    command = ["vssadmin", "list", "shadows"]
    if volume:
        command.append(f"/for={volume}")
    process = subprocess.run(command, capture_output=True, text=True, timeout=30)
    if process.returncode != 0:
        raise RuntimeError(process.stderr.strip() or "vssadmin failed")
    snapshots: List[Dict[str, str]] = []
    current: Dict[str, str] = {}
    for raw in process.stdout.splitlines():
        line = raw.strip()
        match = re.match(r"(?:Shadow Copy ID|Contents of shadow copy set ID):\s*(.+)", line, re.I)
        if match:
            if current:
                snapshots.append(current)
            current = {"id": match.group(1)}
        elif "Shadow Copy Volume:" in line:
            current["device"] = line.split(":", 1)[1].strip()
        elif "Creation Time:" in line:
            current["created"] = line.split(":", 1)[1].strip()
        elif "Original Volume:" in line:
            current["volume"] = line.split(":", 1)[1].strip()
    if current:
        snapshots.append(current)
    return snapshots


__all__ = ["analyze_registry_hive", "filesystem_inventory", "list_volume_shadows",
           "recover_deleted_files"]
