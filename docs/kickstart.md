# Quick start

```powershell
python -m pip install -e .
artefact health
artefact hash README.md
```

Create a case, attach evidence, and generate a report:

```powershell
artefact case investigation.json --create "Example investigation" --id DEMO-001
artefact case investigation.json --add-evidence README.md --description "Known sample"
artefact report investigation.json -o investigation.html --format html
```

Analyze a capture and extract complete HTTP response bodies:

```powershell
artefact network -i capture.pcap -o network.json --extract-http recovered-http
```

Use `artefact <command> --help` for command-specific options. Optional capabilities fail with a direct installation hint instead of preventing the core package from starting.
