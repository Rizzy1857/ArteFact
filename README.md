<p align="center"><!-- Version and Codename -->
  <img src="https://img.shields.io/badge/version-v0.4.0a-red?style=for-the-badge&label=Artefact" /></p>
  <p align="center"><i>The Modular Digital Forensics Toolkit</i></p>
<p align="center">
  <img src="https://img.shields.io/badge/build-passing-brightgreen?style=flat-square" alt="Build Status"/>
  <img src="https://img.shields.io/badge/python-3.7+-blue?style=flat-square" alt="Python Version"/>
  <img src="https://img.shields.io/badge/license-MIT-yellow?style=flat-square" alt="License"/>
</p>

---

# ARTEFACT

A modular command-line toolkit for digital forensics. Fast, extensible, and cross-platform.

## Quick Start

- KickStart Guide: See [here](docs/kickstart.md)
- Install: See [here](docs/installation.md)
- Usage: See [here](docs/usage.md)
- Features: See [here](docs/Roadmap.md)
- Security: See [here](docs/SECURITY.md)
- Threat Model: See [here](docs/threat_model.md)
- Coverage: See [here](docs/coverage.md)
- Code of Conduct: See [here](docs/CODE_OF_CONDUCT.md)

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

MPL 2.0 License. See [LICENSE](LICENSE).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md)

---

For full details, see the docs above.
