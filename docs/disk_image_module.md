# Disk Image Module Documentation

The disk image module provides functionality for analyzing, extracting, and mounting disk images in various formats.

## Features

- Support for multiple disk image formats:
  - Raw disk images (.raw, .dd, .img)
  - EnCase Evidence Files (.e01, .ex01)
  - Virtual Hard Disks (.vhd)
  - Advanced Forensics Format (.aff)
  - VMware Disk Images (.vmdk)

- Partition analysis:
  - List and analyze partitions
  - Detect filesystem types
  - Get partition metadata

- File extraction:
  - Extract files from partitions
  - Support for deleted file recovery
  - Pattern-based file filtering
  - Progress tracking

- Image mounting:
  - Mount images as virtual drives
  - Support for both Windows and Linux
  - Read-only mounting for forensic integrity

## Requirements

### Core Dependencies

- pytsk3: The Sleuth Kit Python bindings
- rich: Terminal formatting and progress bars
- tabulate: Table formatting

### Optional Dependencies

- pyewf: EnCase image support
- pyvhdi: VHD image support
- afflib: AFF image support

### System Requirements

- Windows:
  - OSFMount for image mounting
- Linux:
  - mount/losetup commands
  - root privileges for mounting

## Usage Examples

### List Partitions

```python
from Artefact.modules.diskimage import list_partitions

# List partitions in a disk image
list_partitions("disk.img")
```

### Extract Files

```python
from Artefact.modules.diskimage import extract_partition

# Extract files from partition 1
extract_partition(
    "disk.img",
    partition_addr=1,
    output_dir="./extracted",
    filter_pattern="*.jpg",  # Optional: filter by pattern
    recover_deleted=True     # Optional: attempt deleted file recovery
)
```

### Mount Image

```python
from Artefact.modules.diskimage import mount_image, unmount_image

# Mount disk image
mount_image(
    "disk.img",
    mount_point="/mnt/evidence",
    partition=1,        # Optional: specific partition
    read_only=True     # Recommended for forensics
)

# Unmount when done
unmount_image("/mnt/evidence")
```

## Command Line Interface

The module can be used directly from the command line:

```bash
# List partitions
python -m Artefact.modules.diskimage -i disk.img --list

# Extract files
python -m Artefact.modules.diskimage -i disk.img --extract 1 -o ./extracted

# Mount image
python -m Artefact.modules.diskimage -i disk.img --mount /mnt/evidence
```

## Error Handling

The module uses Artefact's central error handling system. Common errors include:

- FileNotFoundError: Image file not found
- ValidationError: Invalid parameters or unsupported formats
- PermissionError: Insufficient permissions (especially for mounting)
- RuntimeError: General processing errors

Errors are logged and provide user-friendly fixes where possible.

## Best Practices

1. Always work with write-blocked or copied images
2. Use read-only mounting when possible
3. Verify image integrity with hashes
4. Keep detailed logs of all operations
5. Handle large images in chunks to manage memory usage

## Contributing

To add support for new image formats:

1. Add format details to IMAGE_FORMATS
2. Implement format-specific handler
3. Update documentation
4. Add tests for new functionality
