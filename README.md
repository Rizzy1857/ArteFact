# ArteFact 1.0

ArteFact is a modular, case-oriented digital-forensics toolkit for Python 3.9+. It provides streaming file analysis, memory and disk workflows, native PCAP inspection, evidence tracking, verified plugins, reports, and an optional Qt desktop interface.

## Install

```powershell
python -m pip install -e .
artefact health
```

Install only the optional capabilities you need:

```powershell
python -m pip install -e ".[analysis,disk,memory,ml,gui]"
```

## Core workflows

```powershell
artefact hash evidence.bin --algorithm sha256 --cache .hash-cache.json
artefact carve -i disk.img -o recovered --types jpg pdf png
artefact meta -f photograph.jpg --deep
artefact timeline evidence --format json
artefact memory -i memory.raw --strings --iocs
artefact network -i traffic.pcap --extract-http objects --threat-feed feed.json
artefact disk --inventory -i disk.img --partition 0
artefact case case.json --create "Incident 42" --id CASE-42
artefact case case.json --add-evidence evidence.bin --actor analyst
artefact report case.json -o report.pdf --format pdf
artefact plugins --root plugins --verify
artefact gui --case case.json
```

Run `artefact --list-tools` or `artefact <command> --help` for the complete interface.

## Security model

- Evidence acquisition paths are read-only by default.
- Evidence records include SHA-256 and chain-of-custody events.
- Marketplace plugins require HTTPS, archive hashes, safe ZIP paths, API compatibility, entrypoint hashes, and declared dependencies.
- External forensic integrations are optional and reported by `artefact health`.
- Plugins execute as Python code in the current process after verification; install only from publishers you trust.

## Quality gates

```powershell
python -m pytest --run-system --performance
python benchmarks/benchmark_core.py
python -m compileall -q Artefact tests
```

See [installation](docs/installation.md), [usage](docs/usage.md), [API](docs/api.md), [plugin development](docs/plugins.md), [troubleshooting](docs/troubleshooting.md), and the [security audit](docs/security-audit.md).
The recorded release evidence is in the [v1.0 release checklist](docs/release-checklist.md).

Licensed under the [MIT License](LICENSE).
