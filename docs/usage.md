# Usage Guide (ArteFact v0.4.0a)

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

Analyze memory dumps for strings, processes, and indicators:

```powershell
artefact memory -i memdump.raw --strings --pslist
```

- `-i`: Memory dump file
- `--strings`: Extract printable strings
- `--pslist`: Attempt process list reconstruction

---

## Metadata Extraction

Extract metadata from images, PDFs, and more:

```powershell
artefact meta -f sample.jpg
artefact meta -f document.pdf --deep
```

- `-f`: File to extract metadata from
- `--deep`: Use exiftool for deeper extraction (if installed)

---

## Hash Checker

Generate and compare file hashes:

```powershell
artefact hash <file> --algorithm sha256
artefact hash <directory> --algorithm md5 --json
```

- `--algorithm`: Hash algorithm (`md5`, `sha1`, `sha256`)
- `--json`: Output directory hashes as JSON

---

## Timeline Generator

Create a timeline of file events from timestamps:

```powershell
artefact timeline "C:\Users\HRISHI\Documents\*" --format markdown
```

- `--format`: Output format (`json`, `markdown`)

---

## LiveOps (Live System Collection)

Collect live system artifacts (processes, network, etc.):

```powershell
artefact liveops --collect processes network
```

- `--collect`: Specify which live artifacts to collect

---

## More Help

Each module supports --help:

```powershell
artefact carve --help
artefact memory --help
```
