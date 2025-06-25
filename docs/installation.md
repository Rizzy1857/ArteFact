# Installation Guide

Welcome to **ArteFact** — your modular cyber forensics toolkit. Follow the steps below to get ArteFact up and running on your system.

---

## Prerequisites

- **Python 3.8+**
- **Git** (for cloning the repo)
- **pip** (Python package manager)

Optional tools for deeper features:
- `tshark` for network traffic dissection (Wireshark CLI)
- `exiftool` for advanced metadata extraction
- `volatility` for deep memory dump analysis

---

## Quick Install

```powershell
git clone https://github.com/YOUR_USERNAME/ArteFact.git
cd ArteFact
python -m venv venv
venv\Scripts\activate  # On Windows
pip install -r requirements.txt
```

---

## Verification

```powershell
python -m artefact.cli --help
```

If you see a help or usage info message, you are good to go!

---

## Optional: Install Additional Utilities

- `pip install volatility3` (for memory analysis)
- `pip install scapy tqdm python-magic pillow` (for advanced features)
- `choco install wireshark` (Windows, for tshark)
- `brew install exiftool` (Mac)

---

See the [README](../README.md) for a quick project overview.
See the [Usage Guide](./usage.md) for detailed CLI examples.
See the [Test Coverage](./coverage.md) for testing instructions.