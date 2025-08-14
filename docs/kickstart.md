# KickStart Guide (ArteFact v0.4.0a)

This guide provides step-by-step instructions to get started with ArteFact. Follow these steps for a complete setup with all features.

## Prerequisites

- Python 3.7 or higher
- Git
- Windows, Linux, or macOS
- (Optional) ExifTool for deep metadata extraction
- (Optional) Volatility3 for advanced memory analysis

## Installation Steps

### 1. Clone the Repository

```powershell
git clone https://github.com/Rizzy1857/ArteFact.git
cd ArteFact
```

### 2. Set Up Python Environment

Create and activate a virtual environment:

```powershell
python -m venv venv
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/macOS
```

### 3. Install Dependencies

Install core dependencies:

```powershell
pip install -r requirements.txt
```

Optional features (recommended):

```powershell
pip install -r requirements-opt.txt
```

Development tools (for contributors):

```powershell
pip install -r requirements-dev.txt
```

### 4. External Tool Setup

#### Windows (via Chocolatey)

```powershell
choco install exiftool volatility3
```

#### Linux (Debian/Ubuntu)

```bash
sudo apt install exiftool volatility3
```

### 5. Verify Installation

Check core functionality:

```powershell
artefact --version
artefact --list-tools
```

Run the test suite:

```powershell
pytest
```

## Next Steps

- Read the [Usage Guide](usage.md) for detailed command reference
- Check [Example Usage](#example-usage) below for common scenarios
- Join our community on [Discord](https://discord.gg/artefact)

## Example Usage

### File Analysis

```powershell
# Hash a file or directory
artefact hash file.txt --algorithm sha256
artefact hash ./evidence/ --recursive --json

# Extract metadata
artefact meta image.jpg --deep
artefact meta document.pdf --output report.json
```

### Memory Analysis

```powershell
# Analyze a memory dump
artefact memory -i dump.raw --strings --iocs
artefact memory -i dump.raw --carve --output carved_files/

# Process listing and network connections
artefact memory -i dump.raw --pslist --netstat
```

### Timeline Generation

```powershell
# Create a timeline from directory
artefact timeline ./evidence/ --format markdown
artefact timeline ./logs/ --output timeline.json
```

### Live System Analysis

```powershell
# Collect system artifacts
artefact liveops --collect processes,network,registry
artefact liveops --monitor --duration 1h
```

## Troubleshooting

Common issues and solutions:

1. **ImportError: DLL load failed**: Install Visual C++ Redistributable
2. **Permission denied**: Run with appropriate privileges
3. **Memory errors**: Adjust Python heap size or use 64-bit Python

For more help:
- Check our [FAQ](../docs/FAQ.md)
- Report issues on [GitHub](https://github.com/Rizzy1857/ArteFact/issues)
- Join our [Discord](https://discord.gg/artefact) community

## 6. Try the CLI (Copy-Paste Examples)

```powershell
# Hash a file
artefact hash test/text.txt --algorithm md5

# Carve files from a disk image
artefact carve -i disk.img -o output --types jpg

# Extract metadata
artefact meta -f sample.jpg --deep

# Generate a timeline
artefact timeline "C:\Users\HRISHI\Documents\*" --format markdown

# Mount a disk image (if supported)
artefact mount -i disk.img --list

# Analyze a memory dump (if volatility3 installed)
artefact memory -i memdump.raw --strings

# Collect live system info
artefact liveops --collect processes network
```

---

## 7. Run Tests (Optional)

```powershell
pytest
```

---

For more, see [docs/usage.md](usage.md) and [README.md](../README.md).
