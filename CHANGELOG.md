# ARTEFACT Changelog

## [v0.2.0] - 20-05-25

> *"Carve & Reveal"*

### 🚀 Added in v0.2.0

- **File Carving Module:**
  - Recover JPG, PNG, and PDF files from disk images using signature-based carving.
  - Efficient chunked reading for large images.
- **Metadata Extraction Module:**
  - Extract metadata from images (JPG, PNG) and PDFs using Python libraries.
  - Deep extraction via exiftool (if installed).
  - Graceful handling of missing dependencies.
- **Expanded CLI:**
  - New subcommands: `carve` and `meta` for file carving and metadata extraction.
  - Improved help and error messages.
- **Testing:**
  - Added pytest-based tests for carving and metadata modules.
  - Improved test coverage for all core modules.

### 🔧 Changed in v0.2.0

- **Performance:**
  - Carving now processes disk images in chunks for better memory efficiency.
- **Dependency Management:**
  - requirements.txt now lists all required and optional dependencies.
  - Optional dependencies handled gracefully in code.
- **Error Handling:**
  - Improved error messages and user feedback for all modules.
- **Documentation:**
  - Updated usage and installation docs for new features.

---

## [v0.1.1] - 08-05-25

> *"Polished and ready for action."*

### 🚀 Added (New Features)

- **Improved `hasher` module**:
  - Enhanced error handling for file and directory hashing.
  - Added support for efficient directory traversal using `rglob`.
  - Improved output formatting for JSON and Rich table formats.
- **Type Annotations**:
  - Added type hints to core functions for better readability and IDE support.
- **Logging**:
  - Integrated Python’s `logging` module for better debugging and error tracking.
- **Unit Testing**:
  - Added `pytest` support with initial test cases for `hash_command` and `hasher` module.
- **Development Instructions**:
  - Updated `README.md` with steps for running the project locally and testing.

### 🔧 Changed

- **Refactored `cli.py`**:
  - Consolidated redundant `Console` instances into a single instance.
  - Separated argument parsing from command execution for better readability.
  - Improved error messages for invalid inputs.
- **Optimized `pyproject.toml`**:
  - Added `argparse` to dependencies.
  - Updated metadata for better PyPI compatibility.
- **Improved Documentation**:
  - Updated `README.md` with detailed examples, contributing guidelines, and acknowledgments.

---

## [v0.1.0] - Cold Open - 06-05-25

> *"A skeleton in three-piece suit."*

### 🚀 Added

- **Core CLI framework**:
  - `artefact` command with `--version` and `--list-tools` flags.
  - Dark-mode terminal UI powered by `rich`.
- **First weapon**: `hasher` module:
  - Supports MD5/SHA1/SHA256 hashing.
  - File and directory processing.
  - JSON and Rich table output formats.
- **Modular architecture**:
  - Autodiscovery system for future tools.
  - Versioned module structure.
- **Project foundations**:
  - `setup.py` for pip installation.
  - MIT License.
  - Documentation scaffold.

---

### 🧪 Technical Specs

- Python 3.7+ compatible.
- Zero hardcoded tool dependencies.
- Extensible module system.
