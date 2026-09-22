# Command reference

Global discovery commands:

```powershell
artefact --version
artefact --list-tools
artefact health
artefact help network
```

Every command has task-focused `--help` output with defaults and copyable examples. Common aliases include `metadata` for `meta` and `pcap` for `network`.

## Analysis

```powershell
artefact hash PATH [--algorithm md5|sha1|sha256|sha512] [--cache FILE]
artefact carve -i IMAGE -o DIRECTORY [--types jpg png pdf]
artefact meta -f FILE [--deep] [--json]
artefact timeline PATH [--format json|markdown|csv] [--no-recursive]
artefact memory -i DUMP [--strings] [--iocs] [--carve -o DIRECTORY]
artefact network -i CAPTURE [-o REPORT.json] [--extract-http DIR] [--threat-feed FEED.json]
```

Threat feeds are JSON objects keyed by IOC type, for example `{"ipv4":["192.0.2.1"],"domain":["example.test"]}`.

## Disk forensics

```powershell
artefact mount -i IMAGE --list
artefact mount -i IMAGE --extract 0 -o extracted
artefact disk --inventory -i IMAGE --partition 0
artefact disk --recover-deleted -i IMAGE --partition 0 -o recovered
artefact disk --registry -i NTUSER.DAT
artefact disk --shadows
```

Disk inspection is read-only. Deleted-file recovery writes only to the requested output directory. Registry parsing and filesystem inventory require their optional feature group.

## Cases and reports

```powershell
artefact case CASE.json --create TITLE [--id ID]
artefact case CASE.json --add-evidence FILE [--description TEXT] [--actor NAME]
artefact report CASE.json -o REPORT --format markdown|html|json|pdf [--template FILE]
```

Templates use safe dotted placeholders such as `{{ case.title }}` and `{{ summary.evidence_count }}`. They do not execute code.

## Plugins and desktop UI

```powershell
artefact plugins --root plugins --verify
artefact plugins --root plugins --install NAME --index https://example.test/index.json
artefact gui [--case CASE.json]
```

The GUI requires PySide6. Plugin installation rejects non-HTTPS indexes/downloads, hash mismatches, unsafe ZIP paths, incompatible API versions, entrypoint tampering, and missing dependencies.
