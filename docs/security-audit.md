# ArteFact 1.0 security audit

Audit scope: CLI parsing, evidence paths, archive extraction, plugin loading, report rendering, subprocess use, resource bounds, and optional dependency behavior.

## Controls verified

- Marketplace indexes and downloads require HTTPS.
- Marketplace archives are size limited, hash pinned, and rejected on path traversal.
- Plugin entrypoints are hash verified, API-version checked, and dependency checked before execution.
- HTML reports escape case and finding content; templates perform substitution without code execution.
- PCAP parsing validates headers, link types, record lengths, object lengths, and extraction limits.
- Evidence records use streaming SHA-256 and can be reverified for missing or modified files.
- Disk inventory is read-only; mounts default to read-only; recovery writes to a separate destination.
- External commands use argument arrays without shell interpolation.
- Core startup does not require optional native forensic packages.
- Security regression tests cover archive traversal, report injection, and unsafe filenames.

## Accepted limitations

- Verified plugins are not sandboxed and have the current user’s privileges.
- Native parsers and external tools have their own security boundaries and must be updated independently.
- Live collection visibility depends on operating-system permissions.
- Evidence encryption and multi-user authorization are deployment responsibilities, not local CLI features.

## Release gates

The v1.0 release requires the complete unit/integration/system/security/performance suite, bytecode compilation, packaging installation, CLI smoke tests, and dependency audit. CI repeats tests on Windows and Linux across Python 3.9 and 3.13.
