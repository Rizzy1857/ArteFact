# Security policy

## Supported versions

| Version | Security support |
|---|---|
| 1.0.x | Supported |
| < 1.0 | Unsupported |

Report vulnerabilities privately to `Rizzy1857@gmail.com` with subject `[SECURITY] ArteFact vulnerability`. Include affected versions, reproduction steps, impact, and any suggested mitigation. Do not attach sensitive evidence.

## Operational guidance

- Work on copies and use a hardware write blocker where appropriate.
- Do not run ArteFact as administrator/root unless a specific mount or collection workflow requires it.
- Verify evidence through its case record before and after analysis.
- Treat every plugin as trusted Python code. Integrity verification proves identity, not safety.
- Use only HTTPS marketplace indexes and independently validate publisher-provided hashes.
- Keep optional parsers current; forensic input formats are attacker-controlled.

See [security-audit.md](security-audit.md) and [threat_model.md](threat_model.md).
