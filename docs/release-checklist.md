# ArteFact 1.0 release checklist

Audited 2026-09-22 against the completed roadmap and built artifact.

| Milestone | Acceptance evidence | Status |
|---|---|---|
| Core improvements | Streaming/chunked hash, carving and memory paths; parallel carving; hash cache; `health`; benchmark suite | Complete |
| Network analysis | Native PCAP parser, bidirectional sessions, HTTP extraction, IOCs, timeline, statistics, threat-feed matching | Complete |
| Plugin API 2.0 | Versioned manifests, registry, dependencies, HTTPS marketplace, archive/entrypoint hashes, safe extraction, developer guide | Complete |
| Reporting | Markdown/HTML/JSON/PDF, safe templates, evidence chain, summaries, timeline SVG, IOC correlation | Complete |
| Disk forensics | Raw/E01/AFF conversion paths, read-only mount default, inventory, deleted recovery, Registry hives, shadow-copy discovery | Complete |
| Desktop | PySide6 dark UI, asynchronous PCAP analysis, interactive filtered timeline, case/evidence workflow, report preview | Complete |
| Stable release | Stable metadata, cross-platform CI, security audit, documentation, benchmarks, vulnerability audit, wheel verification | Complete |

## Recorded release gates

- Full suite: 56 passed, 1 platform-conditional skip.
- Aggregate line coverage: 53.42%; configured minimum: 50%.
- Bytecode compilation: Python 3.13 and Python 3.10 passed.
- Core benchmark: 10,400,000-byte SHA-256 and string extraction completed within thresholds.
- Dependency audit: no known vulnerabilities in the core requirements.
- Qt smoke test: offscreen application startup and clean shutdown passed.
- Isolated wheel install: version, console entrypoint, import metadata, and hashing passed.
- Wheel: `dist/artefact-1.0.0-py3-none-any.whl`.
- Wheel SHA-256: `1c4f49a5fe10725b859f56919ffd79457a477689ceba130ea092783781012659`.

Optional native integrations still depend on host support, and the security boundaries documented in `security-audit.md` remain applicable. Those constraints are explicit product behavior rather than unfinished release work.
