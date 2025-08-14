<p align="center"><!-- Version and Codename -->
  <img src="https://img.shields.io/badge/version-v0.4.0a-red?style=for-the-badge&label=Artefact" /></p>
  <p align="center"><i>The Modular Digital Forensics Toolkit</i></p>
<p align="center">
  <img src="https://img.shields.io/badge/build-passing-brightgreen?style=flat-square" alt="Build Status"/>
  <img src="https://img.shields.io/badge/python-3.7+-blue?style=flat-square" alt="Python Version"/>
  <img src="https://img.shields.io/badge/license-MIT-yellow?style=flat-square" alt="License"/>
  <img src="https://img.shields.io/badge/tests-100%25-brightgreen?style=flat-square" alt="Test Coverage"/>
  <img src="https://img.shields.io/badge/docs-comprehensive-blue?style=flat-square" alt="Documentation"/>
</p>

---

# ARTEFACT

A professional-grade digital forensics toolkit designed for efficiency, modularity, and comprehensive analysis capabilities. Built with modern Python practices and extensive testing.

## Quick Start

📚 **Documentation Hub**
- [Quick Start Guide](docs/kickstart.md) - Get started in minutes
- [Installation Guide](docs/installation.md) - Detailed setup instructions
- [Usage Guide](docs/usage.md) - Command reference and examples
- [Development Roadmap](docs/Roadmap.md) - Future plans and features
- [Security Policy](docs/SECURITY.md) - Security considerations
- [Threat Model](docs/threat_model.md) - Security architecture
- [Test Coverage](docs/coverage.md) - Quality metrics
- [Code of Conduct](docs/CODE_OF_CONDUCT.md) - Community guidelines

## Core Features

🔍 **Analysis Capabilities**
- Advanced memory dump analysis (strings, IOCs, processes)
- File/directory hashing (MD5, SHA1, SHA256)
- File carving with ML support (PE, ELF, JPG, PNG, PDF)
- Deep metadata extraction with exiftool integration
- Comprehensive timeline generation
- Live system analysis capabilities
- Disk image mounting
- LiveOps (live system collection)

## Example CLI Usage

```powershell
artefact hash test/text.txt --algorithm md5
artefact carve -i disk.img -o output --types jpg
artefact meta -f sample.jpg --deep
artefact timeline "C:\Users\HRISHI\Documents\*" --format markdown
artefact mount -i disk.img --list
artefact memory -i memdump.raw --strings
artefact liveops --collect processes network
```

## License

MIT License. See [LICENSE](LICENSE).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md)

---

For full details, see the docs above.
