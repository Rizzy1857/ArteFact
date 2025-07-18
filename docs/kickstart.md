# KickStart Guide (ArteFact v0.4.0a)

This guide lets you go from zero to a working ArteFact CLI in minutes. Just copy-paste the commands below!

---

## 1. Clone the Repo

```powershell
git clone https://github.com/Rizzy1857/ArteFact.git
cd ArteFact
```

## 2. Set Up Python & Virtual Environment

```powershell
python -m venv venv
.\venv\Scripts\activate
```

## 3. Install Core Dependencies

```powershell
pip install -r requirements.txt
```

## 4. (Optional) Install Extra Features

```powershell
pip install -r requirements-opt.txt
```

## 5. Verify Installation

```powershell
artefact --version
artefact --list-tools
```

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
