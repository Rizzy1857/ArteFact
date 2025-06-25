<h1 align="center">🧠 ARTEFACT</h1>
<p align="center"><i>The Modular Digital Forensics Toolkit</i></p>
<p align="center"><b>Version 0.4.0b - "Anti Amnesia"</b></p>
<p align="center">
  <img src="https://img.shields.io/badge/build-passing-brightgreen?style=flat-square" alt="Build Status"/>
  <img src="https://img.shields.io/badge/python-3.7+-blue?style=flat-square" alt="Python Version"/>
  <img src="https://img.shields.io/badge/license-MIT-yellow?style=flat-square" alt="License"/>
</p>

---

# ARTEFACT

**Artefact** is a modular command-line toolkit for digital forensics, featuring a visually appealing interface powered by the `rich` library. It supports file carving, metadata extraction, hashing, timeline generation, memory dump analysis, disk image mounting, and live forensics.

---

## Documentation

- [Usage Guide](./docs/usage.md)
- [Installation Guide](./docs/installation.md)
- [Test Coverage](./docs/coverage.md)
- [Roadmap](./docs/Roadmap.md)

---

## Features (Quick Overview)

- File Carving (JPG, PNG, PDF)
- Metadata Extraction (images, PDFs, exiftool)
- File & Directory Hashing (MD5, SHA1, SHA256)
- Timeline Generation (filesystem & metadata timestamps)
- Memory Dump Analysis (strings, IOCs, binary carving)
- Disk Image Mounting & Extraction
- Live Forensics / Volatile Data Capture
- Interactive Menu & CLI

---

See the [Usage Guide](./docs/usage.md) for all CLI examples and details.

---

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md).

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- [Rich Library](https://github.com/Textualize/rich) for the beautiful terminal output.
- Python community for their amazing tools and libraries.

> **🔒 Note:** For more details on how we handle security, please refer to this [SECURITY.md](./docs/SECURITY.md) file.
> **🛡️ Threat Model:** See our [Threat Model](./docs/threat_model.md) for how ArteFact handles untrusted data and security risks.
> **🤝 Code of Conduct:** Please read our [Code of Conduct](./docs/CODE_OF_CONDUCT.md) before contributing.
