# Installation

ArteFact 1.0 supports CPython 3.9–3.13 on Windows, Linux, and macOS.

## Core installation

```powershell
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -e .
artefact health
```

On Linux or macOS, activate with `source .venv/bin/activate`.

## Optional feature groups

```powershell
python -m pip install -e ".[analysis]" # images, PDFs, Office, PE, ELF
python -m pip install -e ".[disk]"     # TSK and Registry hives
python -m pip install -e ".[memory]"   # psutil, Volatility, YARA
python -m pip install -e ".[ml]"       # ML-assisted carving
python -m pip install -e ".[gui]"      # PySide6 desktop UI
python -m pip install -e ".[test]"     # release tests
```

ExifTool enables deep metadata extraction. OSFMount enables Windows disk mounting. E01 handling requires `pyewf`; AFF conversion requires a compatible external converter. These tools are not silently installed.

## Verify

```powershell
artefact --version
artefact --list-tools
artefact health
python -m pytest
```

`health` distinguishes required dependencies from optional capabilities and prints an actionable fix for anything unavailable.
