# Detailed Installation Guide (ArteFact v0.4.0a)

This guide provides comprehensive installation instructions for ArteFact, including all optional components and platform-specific configurations.

## System Requirements

### Minimum Requirements
- Python 3.7 or higher
- 4GB RAM
- 1GB disk space
- Administrator/root access (for some features)

### Recommended Requirements
- Python 3.9 or higher
- 8GB RAM
- 5GB disk space
- SSD storage
- Multi-core processor

## Platform-Specific Setup

### Windows Setup

1. Install Python:
   - Download from [python.org](https://python.org)
   - Enable "Add Python to PATH"
   - Install with pip and venv options

2. Install Visual C++ Redistributable:
   ```powershell
   winget install Microsoft.VCRedist.2015+.x64
   ```

3. Install Chocolatey and tools:
   ```powershell
   Set-ExecutionPolicy Bypass -Scope Process -Force
   iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))
   choco install exiftool volatility3 git
   ```

### Linux Setup (Debian/Ubuntu)

1. Install Python and tools:
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip python3-venv
   sudo apt install git exiftool volatility3
   ```

2. Install system dependencies:
   ```bash
   sudo apt install libewf-dev sleuthkit
   ```

### macOS Setup

1. Install Homebrew:
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. Install dependencies:
   ```bash
   brew install python3 git exiftool volatility3
   brew install libewf sleuthkit
   ```

## ArteFact Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Rizzy1857/ArteFact.git
   cd ArteFact
   ```

2. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   # .\venv\Scripts\activate  # Windows
   ```

3. Install dependencies:
   ```bash
   pip install -U pip setuptools wheel
   pip install -r requirements.txt
   pip install -r requirements-opt.txt  # Optional features
   pip install -r requirements-dev.txt  # Development tools
   ```

## Optional Components

### ExifTool Integration
- Required for deep metadata extraction
- Install via package manager or from [ExifTool website](https://exiftool.org)
- Verify with: `exiftool -ver`

### Volatility3 Setup
- Required for advanced memory analysis
- Install via pip or package manager
- Configure symbol tables:
  ```bash
  vol3 -h
  vol3 symbol-cache
  ```

### YARA Rules
- Download community rules:
  ```bash
  git clone https://github.com/Yara-Rules/rules.git ./rules
  ```
- Set YARA_RULES_PATH environment variable:
  ```bash
  export YARA_RULES_PATH="./rules"  # Linux/macOS
  # set YARA_RULES_PATH=.\rules  # Windows
  ```

## Verification

1. Check installation:
   ```bash
   artefact --version
   artefact --list-tools
   ```

2. Run tests:
   ```bash
   pytest
   ```

3. Verify features:
   ```bash
   artefact verify-setup
   ```

## Troubleshooting

### Common Issues

1. **DLL Load Failed**
   - Solution: Install/repair Visual C++ Redistributable
   - Check PATH environment variable

2. **Permission Errors**
   - Solution: Run with admin/root privileges
   - Check file permissions

3. **Import Errors**
   - Solution: Verify virtual environment activation
   - Reinstall dependencies

4. **Memory Errors**
   - Solution: Increase Python heap size
   - Use 64-bit Python

### Getting Help

- Check [FAQ](FAQ.md)
- Search [Issues](https://github.com/Rizzy1857/ArteFact/issues)
- Join [Discord](https://discord.gg/artefact)
- Email support: support@artefact.dev

## Upgrading

To upgrade ArteFact:

```bash
git pull origin main
pip install -U -r requirements.txt
pip install -U -r requirements-opt.txt  # if using optional features
```

## Uninstallation

To remove ArteFact:

1. Deactivate virtual environment:
   ```bash
   deactivate
   ```

2. Remove files:
   ```bash
   rm -rf ArteFact  # Linux/macOS
   # rmdir /s /q ArteFact  # Windows
   ```

3. (Optional) Remove tools:
   ```bash
   choco uninstall exiftool volatility3  # Windows
   # apt remove exiftool volatility3  # Debian/Ubuntu
   # brew uninstall exiftool volatility3  # macOS
   ``` (ArteFact v0.4.0a)

Welcome to **ArteFact** — your modular cyber forensics toolkit. Follow the steps below to get ArteFact up and running on your system.

---

## Prerequisites

- **Python 3.8+**
- **Git** (for cloning the repo)
- **pip** (Python package manager)

Optional tools for deeper features:

- `tshark` for network traffic dissection (Wireshark CLI)
- `exiftool` for advanced metadata extraction
- `volatility3` for deep memory dump analysis
- `pytsk3` for disk image mounting

---

## Clone the Repository

```powershell
git clone https://github.com/YOUR_USERNAME/ArteFact.git
cd ArteFact
```

## Set the Virtual Environment (Recommended)

```powershell
python -m venv venv
.\venv\Scripts\activate
```

## Install the dependencies

```powershell
pip install -r requirements.txt
```

## Optional: Install extra features

```powershell
pip install -r requirements-opt.txt
```

## Verification

```powershell
artefact --version
artefact --list-tools
```

If you see the banner and tool list, you are good to go!

---

## Troubleshooting

- *Module not found?* → Check if your virtual environment is activated.
- *Permission issues?* → Try running as administrator, or fix file permissions.
- *Optional tools not found?* → Install them from requirements-opt.txt or your system package manager.