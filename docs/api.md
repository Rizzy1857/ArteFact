# Python API

Stable v1 entry points:

```python
from pathlib import Path
from Artefact.case import Case
from Artefact.modules.hasher import hash_file, hash_file_cached
from Artefact.modules.network import analyze_pcap, extract_http_objects, parse_pcap
from Artefact.plugins import PluginMarketplace, PluginRegistry
from Artefact.reporting import ReportBuilder

digest = hash_file(Path("evidence.bin"), "sha256")
network = analyze_pcap(Path("capture.pcap"), Path("feed.json"))

case = Case.create("Incident", "CASE-001")
case.add_evidence(Path("evidence.bin"), actor="analyst")
case.add_finding("Network analysis", network, severity="high")
case.save(Path("case.json"))
ReportBuilder(case).write(Path("report.pdf"), "pdf")
```

Additional modules:

- `Artefact.modules.carving`: signature and optional ML-assisted recovery.
- `Artefact.modules.metadata`: filesystem and format-specific metadata.
- `Artefact.modules.timeline`: event extraction, correlation, filtering, anomalies, and exports.
- `Artefact.modules.memory`: strings, IOCs, binary carving, and optional Volatility analysis.
- `Artefact.modules.diskimage`: conversion, partition inspection, extraction, and read-only mounting.
- `Artefact.modules.disk_forensics`: inventory, deleted recovery, Registry hives, and shadow copies.
- `Artefact.health`: required and optional capability diagnostics.

Functions accept `pathlib.Path` or documented path-like values and raise specific validation, file, permission, or runtime errors. Optional integrations are imported lazily.
