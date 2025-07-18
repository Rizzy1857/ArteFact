# Installation Guide (ArteFact v0.4.0a)

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