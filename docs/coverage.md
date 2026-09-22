# Test and coverage gates

The release suite contains unit, integration, system, security, and opt-in performance tests.

```powershell
python -m pytest --run-system --performance
python -m pytest --cov=Artefact --cov-report=term --cov-report=html
python benchmarks/benchmark_core.py
```

System tests exercise CLI subprocesses and complete workflows. Security tests exercise plugin archive traversal, untrusted report content, and filename handling. Performance tests enforce minimum streaming throughput and bounded memory-string extraction time.

CI runs the full suite on Windows and Linux with the oldest and newest supported Python versions.
The release gate requires at least 50% aggregate line coverage; security-sensitive new modules are individually tested above that baseline.
