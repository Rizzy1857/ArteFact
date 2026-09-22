"""Backward-compatible disk image API.

The implementation lives in :mod:`Artefact.modules.diskimage`; this module
keeps the public ``Artefact.modules.mount`` import used by the CLI and older
clients.
"""

from .diskimage import (
    analyze_partitions,
    extract_partition,
    list_partitions,
    mount_image,
    open_image,
    unmount_image,
)

__all__ = [
    "analyze_partitions",
    "extract_partition",
    "list_partitions",
    "mount_image",
    "open_image",
    "unmount_image",
]
