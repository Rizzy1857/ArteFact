# ArteFact Threat Model

## Overview

ArteFact is a digital forensics toolkit that processes potentially untrusted files and disk images. The following threat model and practices are designed to minimize risk to users and their systems.

## Threats Considered

- **Malicious Input Files:** Disk images, documents, or binaries may be crafted to exploit parsing logic or underlying libraries.
- **Dependency Vulnerabilities:** Third-party packages may have security flaws.
- **Command Injection:** Especially when calling external tools (e.g., exiftool).
- **Privilege Escalation:** ArteFact should not require elevated privileges for normal operation.
- **Data Leakage:** Sensitive data processed by ArteFact should not be leaked or logged inappropriately.

## Mitigations

- All file parsing is done with robust libraries and error handling.
- All dependencies are pinned and audited (see CI pipeline).
- External tool calls are sanitized and never use untrusted shell input.
- ArteFact does not require admin/root for normal use.
- Logging avoids sensitive data by default.

## Security Practices

- All dependencies are regularly audited with pip-audit.
- CI runs lint, tests, and security checks on every commit.
- Security issues can be reported via SECURITY.md.
- Users are encouraged to run ArteFact in isolated environments when handling untrusted data.
