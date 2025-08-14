# Comprehensive Usage Guide (ArteFact v0.4.0a)

This guide provides detailed instructions for using ArteFact's features and modules. For quick start instructions, see the [README](../README.md).

## Command Line Interface

ArteFact provides both a traditional CLI and an interactive menu mode.

### Basic Usage

```bash
artefact <command> [options]
artefact --interactive  # Launch interactive menu
```

### Global Options

| Option | Description |
|--------|-------------|
| `--version` | Show version |
| `--list-tools` | List available tools |
| `--interactive` | Launch interactive menu |
| `--verbose` | Detailed output |
| `--quiet` | Minimal output |
| `--json` | JSON output format |
| `--no-color` | Disable colored output |
| `--config FILE` | Use custom config |

## Core Modules

### Memory Analysis

Analyze memory dumps for forensic artifacts:

```bash
artefact memory [options] -i <dump_file>
```

Options:
- `-i, --input`: Memory dump file
- `--strings`: Extract strings
- `--iocs`: Extract IOCs (IPs, emails, URLs)
- `--pslist`: List processes
- `--netstat`: Network connections
- `--carve`: Carve files
- `--yara`: Run YARA rules
- `--volatility`: Use Volatility plugins

Example:
```bash
# Extract strings and IOCs
artefact memory -i memory.dmp --strings --iocs

# Carve files and analyze processes
artefact memory -i memory.dmp --carve --pslist --output carved/
```

### File Carving

Recover files from disk images or raw data:

```bash
artefact carve [options] -i <image_file>
```

Options:
- `-i, --input`: Input file/image
- `-o, --output`: Output directory
- `--types`: File types to carve
- `--ml`: Use ML detection
- `--resume`: Resume previous job
- `--verify`: Validate carved files

Supported file types:
- Documents: PDF, DOC, DOCX
- Images: JPG, PNG, GIF
- Executables: PE, ELF
- Archives: ZIP, RAR
- Custom signatures

Example:
```bash
# Carve specific file types
artefact carve -i disk.img -o carved/ --types pdf,jpg,png

# Use ML-based detection
artefact carve -i disk.img -o carved/ --ml --verify
```

### Metadata Extraction

Extract and analyze file metadata:

```bash
artefact meta [options] -f <file>
```

Options:
- `-f, --file`: Target file
- `--deep`: Use ExifTool
- `--recursive`: Process directories
- `--strip`: Remove metadata
- `--output`: Output format

Example:
```bash
# Deep metadata extraction
artefact meta -f image.jpg --deep --json

# Process directory
artefact meta -f ./evidence/ --recursive --output report.md
```

### Timeline Generation

Create forensic timelines:

```bash
artefact timeline [options] <path>
```

Options:
- `--format`: Output format
- `--filters`: Event filters
- `--timezone`: Set timezone
- `--correlation`: Enable event correlation
- `--visualize`: Create visual timeline

Example:
```bash
# Generate timeline
artefact timeline ./evidence/ --format markdown

# Advanced correlation
artefact timeline ./logs/ --correlation --visualize
```

### Hashing

Generate and verify file hashes:

```bash
artefact hash [options] <file>
```

Options:
- `--algorithm`: Hash algorithm
- `--recursive`: Process directories
- `--verify`: Check against known hashes
- `--export`: Export hash list

Example:
```bash
# Hash directory
artefact hash ./evidence/ --recursive --algorithm sha256

# Verify against known hashes
artefact hash file.exe --verify hashes.txt
```

### Live System Analysis

Collect live system artifacts:

```bash
artefact liveops [options]
```

Options:
- `--collect`: Artifacts to collect
- `--monitor`: Real-time monitoring
- `--output`: Output directory
- `--compress`: Compress output

Example:
```bash
# Collect system artifacts
artefact liveops --collect processes,network,registry

# Monitor system
artefact liveops --monitor --duration 1h
```

## Advanced Features

### Automation

Create automated analysis workflows:

```bash
artefact auto [options] --config workflow.yml
```

Example workflow:
```yaml
name: Evidence Processing
steps:
  - carve:
      input: disk.img
      types: [pdf, jpg, exe]
  - hash:
      algorithm: sha256
      verify: known_hashes.txt
  - timeline:
      format: json
      correlation: true
```

### Reporting

Generate comprehensive reports:

```bash
artefact report [options] --case <case_id>
```

Options:
- `--template`: Report template
- `--format`: Output format
- `--evidence`: Include evidence
- `--findings`: Include findings

Example:
```bash
# Generate case report
artefact report --case ABC123 --format pdf --evidence

# Custom template
artefact report --case ABC123 --template custom.jinja
```

### Plugin Development

Create custom analysis modules:

```python
from artefact import Plugin, register_plugin

@register_plugin
class CustomAnalyzer(Plugin):
    """Custom analysis plugin."""
    
    def analyze(self, data):
        # Analysis logic here
        return results
```

## Configuration

### Config File

```yaml
# ~/.artefact/config.yml
output:
  format: json
  colors: true
  verbose: false

logging:
  level: info
  file: artefact.log

resources:
  max_memory: 8G
  threads: auto
```

### Environment Variables

- `ARTEFACT_CONFIG`: Config file path
- `ARTEFACT_VERBOSE`: Enable verbose output
- `ARTEFACT_NO_COLOR`: Disable colors
- `ARTEFACT_LOG_LEVEL`: Set log level

## Performance Tips

1. Use appropriate chunk sizes for large files
2. Enable parallel processing when possible
3. Monitor resource usage
4. Use memory-mapped files for large datasets
5. Profile and optimize custom plugins

## Error Handling

Common error patterns and solutions:

```bash
# Permission denied
sudo artefact <command>  # Linux/macOS
# Run as Administrator  # Windows

# Memory error
export ARTEFACT_MAX_MEMORY=16G  # Increase limit
```

## Best Practices

1. Always verify file hashes
2. Use write blockers for evidence
3. Document your analysis steps
4. Back up important findings
5. Follow forensic procedures

## Further Reading

- [Forensic Techniques](docs/techniques.md)
- [Tool Development](docs/development.md)
- [Case Studies](docs/cases.md)
- [Contributing](CONTRIBUTING.md)e Guide (ArteFact v0.4.0a)

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
