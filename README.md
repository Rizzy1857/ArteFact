<h1 align="center">🧠 ARTEFACT</h1>
<p align="center"><i>The Modular Digital Forensics Toolkit</i></p>
<p align="center"><b>Version 1.0.1 - "Polished and Ready for Action"</b></p>
<p align="center">
  <img src="https://img.shields.io/badge/build-passing-brightgreen?style=flat-square" alt="Build Status"/>
  <img src="https://img.shields.io/badge/python-3.7+-blue?style=flat-square" alt="Python Version"/>
  <img src="https://img.shields.io/badge/license-MIT-yellow?style=flat-square" alt="License"/>
</p>

---

# ARTEFACT
>
> v1.0.1 "Polished and Ready for Action" — A skeleton in a three-piece suit.

**Artefact** is a modular command-line toolkit designed for digital forensics and other utilities. It features a visually appealing interface powered by the `rich` library and supports tools like file and directory hashing.

---

## Features

- **File Hashing**: Compute cryptographic hashes (MD5, SHA1, SHA256) for files.
- **Directory Hashing**: Compute hashes for all files in a directory, with optional JSON output.
- **Tool Discovery**: Dynamically list available tools in a rich table format.
- **Dark-Mode Aesthetics**: Styled output using the `rich` library.
- **Extensible Architecture**: Easily add new tools to the framework.

---

## Installation

### Prerequisites

- Python 3.7 or higher
- `pip` (Python package manager)

### Steps

1. Clone the repository:

   ```bash
   git clone https://github.com/Rizzy1857/ArteFact.git
   cd ArteFact
   ```

2. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. (Optional) Install the package globally:

   ```bash
   pip install .
   ```

---

## Usage

### Display the Banner

```bash
artefact --version
```

### List Available Tools

```bash
artefact --list-tools
```

### Hash a File

```bash
artefact hash <file_path> --algorithm <md5|sha1|sha256>
```

Example:

```bash
artefact hash example.txt --algorithm sha256
```

### Hash a Directory

```bash
artefact hash <directory_path> --algorithm <md5|sha1|sha256> [--json]
```

Example:

```bash
artefact hash ./docs --algorithm md5 --json
```

---

## Examples

### File Hashing

```bash
artefact hash file.txt --algorithm sha256
```

Output:

```bash
SHA256: 3a7bd3e2360a3d5d9f6f8c3c3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e
```

### Directory Hashing (Table Format)

```bash
artefact hash ./my_folder --algorithm sha1
```

Output:

```
+----------------------+------------------------------------------+
| File                | Hash                                     |
+----------------------+------------------------------------------+
| ./my_folder/file1   | 2fd4e1c67a2d28fced849ee1bb76e7391b93eb12 |
| ./my_folder/file2   | 3a7bd3e2360a3d5d9f6f8c3c3e3e3e3e3e3e3e3e |
+----------------------+------------------------------------------+
```

### Directory Hashing (JSON Format)

```bash
artefact hash ./my_folder --algorithm sha256 --json
```

Output:

```json
{
  "./my_folder/file1": "2fd4e1c67a2d28fced849ee1bb76e7391b93eb12",
  "./my_folder/file2": "3a7bd3e2360a3d5d9f6f8c3c3e3e3e3e3e3e3e3e"
}
```

---

## Development

### Running Locally

1. Activate a virtual environment:

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Run the CLI:

   ```bash
   python -m artefact.cli --help
   ```

### Running Tests

Run the test suite using `pytest`:

```bash
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
