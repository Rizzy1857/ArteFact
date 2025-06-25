# 📘 Usage Guide

This guide walks you through ArteFact’s key modules and CLI usage.
For a quick overview, see the [README](../README.md).

---

## File Carving

Recover files from raw storage dumps (e.g., disk images, memory dumps). Supports JPG, PNG, PDF by default.

```powershell
artefact carve -i <image_file> -o <output_dir> [--types jpg pdf png]
```

- `-i`: Input disk/image file
- `-o`: Output directory for carved files
- `--types`: (optional) File types to look for (default: all supported)

---

## Disk Image Mounting & Extraction

List partitions in a disk image (RAW, DD, E01):

```powershell
artefact mount -i disk.img --list
```

Extract files from a partition:

```powershell
artefact mount -i disk.img --extract 2 -o output_dir
```

- `-i`: Input disk image file
- `--list`: List partitions
- `--extract`: Partition address to extract
- `-o`: Output directory for extraction

---

## Memory Analysis

Parse raw memory dumps for printable strings, IOCs (IPs, URLs, emails), and carve binaries (PE, ELF, Mach-O).

```powershell
artefact mem -i <memory_dump.raw> [--strings] [--iocs] [--binaries] [--output <dir>] [--min-length N] [--encoding ascii|utf16]
```

- `-i`: Input memory dump file
- `--strings`: Extract printable strings
- `--iocs`: Extract IOCs from strings
- `--binaries`: Carve out binaries
- `--output`: Output directory for binaries
- `--min-length`: Minimum string length (default: 4)
- `--encoding`: String encoding (ascii or utf16)

---

## Live Forensics / Volatile Data Capture

Capture live system artefacts (cross-platform where possible):

List running processes:

```powershell
artefact liveops --processes
```

List open ports and network connections:

```powershell
artefact liveops --connections
```

Dump clipboard contents:

```powershell
artefact liveops --clipboard
```

List running services (Windows only):

```powershell
artefact liveops --services
```

---

## Metadata Extraction

Extract metadata from images (JPG, PNG), PDFs, and other files. Supports deep extraction with exiftool if installed.

```powershell
artefact meta -f <file> [--deep]
```

- `-f`: File to extract metadata from
- `--deep`: Use exiftool for deeper extraction

---

## Hash Checker

Generate and compare file hashes for files or directories. Supports MD5, SHA1, SHA256.

```powershell
artefact hash <file_or_dir> --algorithm <md5|sha1|sha256> [--json]
```

- `--algorithm`: Hash algorithm (default: sha256)
- `--json`: Output directory hashes as JSON

---

## Timeline Generation

Create a forensics timeline from file and metadata timestamps. Output in Markdown or JSON.

```powershell
artefact timeline <file_or_glob_pattern> [--format json|markdown]
```

- `--format`: Output format (default: markdown)

---

## Interactive Menu

Launch the interactive menu for all main features:

```powershell
python -m artefact.cli
```

---

## Tips & Troubleshooting

- For E01 image support, install `pyewf` (see requirements-opt.txt).
- For deep metadata extraction, install exiftool.
- For memory and liveops features, install `psutil` and (on Windows) `wmi`.
- Use `--help` with any command for detailed options.

---

For installation, see the [Installation Guide](./installation.md).
For test coverage, see the [Test Coverage](./coverage.md).
