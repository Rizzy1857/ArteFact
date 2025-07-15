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

A modular command-line toolkit for digital forensics. Fast, extensible, and cross-platform.

## Quick Start

- Install: See [INSTALLATION GUIDE](docs/installation.md)
- Usage: See [DOCUMENTATION GUIDE](docs/usage.md)
- Features: See [ROADMAP](docs/Roadmap.md)
- Security: See [SECURITY](docs/SECURITY.md)
- Threat Model: See [THREAT MODEL](docs/threat_model.md)
- Coverage: See [COVERAGE](docs/coverage.md)
- Code of Conduct: See [CODE OF CONDUCT](docs/CODE_OF_CONDUCT.md)

## Main Features

- File/directory hashing (MD5, SHA1, SHA256)
- File carving (JPG, PNG, PDF)
- Metadata extraction (images, PDFs, deep via exiftool)
- Timeline generation
- Memory analysis
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
