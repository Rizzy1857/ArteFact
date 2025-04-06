# Installation Guide

Welcome to **ArteFact** — your modular cyber forensics toolkit. Follow the steps below to get ArteFact up and running on your system.

---

## Prerequisites

Make sure you have the following installed:

- **Python 3.8+**
- **Git** (for cloning the repo)
- **pip** (Python package manager)

Optional tools for deeper features:

- `tshark` for network traffic dissection (Wireshark CLI)
- `exiftool` for advanced metadata extraction
- `volatility` for deep memory dump analysis

---

## Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/ArteFact.git
cd ArteFact
```
## Set the Virtual Environment (Recommended)

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```
## Install the dependencies

```bash
pip install -r requirements.txt
```
(if i failed to create a good `requirements.txt`)

```bash
pip install scapy tqdm python-magic pillow
```
## VERIFICATION (Important)!!

```bash
python src/carving/file_carver.py --help
```
If you see a help or usage info message, you are good to go!

## Optional:
Install additional utilities for extended module features:

`sudo apt install tshark`

`brew install exiftool (Mac)`

`pip install volatility3`

## Troubleshooting

*Module not found? → Check if your virtual environment is activated.*

*Permission issues? → Try running with `sudo`, or fix file permissions.*