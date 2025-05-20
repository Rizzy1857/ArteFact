<h1 align="center">🧠 ARTEFACT</h1>
<p align="center"><i>The Modular Digital Forensics Toolkit</i></p>
<p align="center"><b>Version 0.2.0 - "Carve & Reveal"</b></p>
<p align="center">
  <img src="https://img.shields.io/badge/build-passing-brightgreen?style=flat-square" alt="Build Status"/>
  <img src="https://img.shields.io/badge/python-3.7+-blue?style=flat-square" alt="Python Version"/>
  <img src="https://img.shields.io/badge/license-MIT-yellow?style=flat-square" alt="License"/>
</p>

---

# ARTEFACT
>
> v0.2.0 "Carve & Reveal" — Carving, Metadata, and More.

**Artefact** is a modular command-line toolkit designed for digital forensics and other utilities. It features a visually appealing interface powered by the `rich` library and supports tools like file and directory hashing, file carving, and metadata extraction.

---

## Features

- **File Carving:** Recover JPG, PNG, and PDF files from disk images using signature-based carving (efficient chunked reading).
- **Metadata Extraction:** Extract metadata from images (JPG, PNG) and PDFs using Python libraries, or use exiftool for deep extraction.
- **File Hashing:** Compute cryptographic hashes (MD5, SHA1, SHA256) for files.
- **Directory Hashing:** Compute hashes for all files in a directory, with optional JSON output.
- **Tool Discovery:** Dynamically list available tools in a rich table format.
- **Dark-Mode Aesthetics:** Styled output using the `rich` library.
- **Extensible Architecture:** Easily add new tools to the framework.

---

## Roadmap

See [Roadmap.md](./Roadmap.md) for upcoming features and planned releases.

---

## Installation

### Prerequisites

- Python 3.7 or higher
- `pip` (Python package manager)

### Steps

1. Clone the repository:

   ```powershell
   git clone https://github.com/Rizzy1857/ArteFact.git
   cd ArteFact
   ```

2. Install the dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

3. (Optional) Install the package globally:

   ```powershell
   pip install .
   ```

---

## Usage

### Display the Banner

```powershell
artefact --version
```

### List Available Tools

```powershell
artefact --list-tools
```

### Hash a File

```powershell
artefact hash <file_path> --algorithm <md5|sha1|sha256>
```

Example:

```powershell
artefact hash example.txt --algorithm sha256
```

### Hash a Directory

```powershell
artefact hash <directory_path> --algorithm <md5|sha1|sha256> [--json]
```

Example:

```powershell
artefact hash ./docs --algorithm md5 --json
```

### Carve Files from Disk Image

```powershell
artefact carve -i <image_file> -o <output_dir> [--types jpg png pdf]
```

Example:

```powershell
artefact carve -i disk.img -o output --types jpg pdf
```

### Extract Metadata

```powershell
artefact meta -f <file> [--deep]
```

Example:

```powershell
artefact meta -f sample.jpg
artefact meta -f document.pdf --deep
```

---

## Examples

### File Carving

```powershell
artefact carve -i disk.img -o output --types jpg
```

### Metadata Extraction

```powershell
artefact meta -f sample.jpg
artefact meta -f sample.pdf --deep
```

### File Hashing

```powershell
artefact hash file.txt --algorithm sha256
```

### Directory Hashing (Table Format)

```powershell
artefact hash ./my_folder --algorithm sha1
```

### Directory Hashing (JSON Format)

```powershell
artefact hash ./my_folder --algorithm sha256 --json
```

---

## Development

### Running Locally

1. Activate a virtual environment:

   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

2. Install dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

3. Run the CLI:

   ```powershell
   python -m artefact.cli --help
   ```

### Running Tests

Run the test suite using `pytest`:

```powershell
pytest
```

---

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Submit a pull request with a clear description of your changes.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- [Rich Library](https://github.com/Textualize/rich) for the beautiful terminal output.
- Python community for their amazing tools and libraries.

> **🔒 Note:** For more details on how we handle security, please refer to this [SECURITY.md](SECURITY.md) file.
