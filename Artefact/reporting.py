"""Forensic case reports in Markdown, HTML, JSON and dependency-free PDF."""

import html
import json
import textwrap
import re
from datetime import datetime
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List

from Artefact.case import Case


def correlate_iocs(findings: Iterable[Dict[str, Any]]) -> Dict[str, List[str]]:
    """Collect and deduplicate IOC values embedded in findings."""
    correlated: Dict[str, set] = {}
    for finding in findings:
        details = finding.get("details", {})
        if not isinstance(details, dict):
            continue
        iocs = details.get("iocs", details)
        if not isinstance(iocs, dict):
            continue
        for kind, values in iocs.items():
            if isinstance(values, (list, tuple, set)):
                correlated.setdefault(kind, set()).update(str(value) for value in values)
    return {kind: sorted(values) for kind, values in correlated.items()}


class ReportBuilder:
    def __init__(self, case: Case):
        self.case = case

    def data(self) -> Dict[str, Any]:
        value = asdict(self.case)
        value["ioc_correlation"] = correlate_iocs(self.case.findings)
        value["summary"] = {
            "evidence_count": len(self.case.evidence),
            "finding_count": len(self.case.findings),
            "custody_event_count": len(self.case.chain_of_custody),
        }
        return value

    def markdown(self) -> str:
        data = self.data()
        lines = [f"# Forensic Report: {self.case.title}", "",
                 f"- Case ID: `{self.case.id}`", f"- Created: {self.case.created_at}",
                 f"- Evidence items: {len(self.case.evidence)}", f"- Findings: {len(self.case.findings)}",
                 "", "## Evidence", ""]
        if self.case.evidence:
            lines.extend(["| ID | Path | Size | SHA-256 |", "|---|---|---:|---|"])
            for item in self.case.evidence:
                lines.append(f"| {item.id} | {item.path.replace('|', chr(92) + '|')} | {item.size} | `{item.sha256}` |")
        else:
            lines.append("No evidence recorded.")
        lines.extend(["", "## Findings", ""])
        for finding in self.case.findings:
            lines.extend([f"### {finding['title']}", "",
                          f"Severity: **{finding['severity']}**", "", "```json",
                          json.dumps(finding["details"], indent=2, default=str), "```", ""])
        lines.extend(["## IOC Correlation", "", "```json",
                      json.dumps(data["ioc_correlation"], indent=2), "```", "",
                      "## Chain of Custody", ""])
        for event in self.case.chain_of_custody:
            lines.append(f"- {event['timestamp']} — {event['actor']}: {event['action']} ({event['evidence_id']})")
        return "\n".join(lines).rstrip() + "\n"

    def html(self) -> str:
        markdown = self.markdown()
        body = "<br>".join(html.escape(line) for line in markdown.splitlines())
        visualization = self.timeline_svg()
        return ("<!doctype html><html><head><meta charset='utf-8'><title>" +
                html.escape(self.case.title) + "</title><style>body{background:#111827;color:#e5e7eb;"
                "font:15px system-ui;max-width:1000px;margin:40px auto;line-height:1.5}"
                "code{color:#93c5fd}a{color:#60a5fa}</style></head><body>" + visualization + body + "</body></html>")

    def json(self) -> str:
        return json.dumps(self.data(), indent=2, default=str)

    def render_template(self, template: str) -> str:
        """Render safe dotted placeholders such as ``{{ case.title }}``."""
        context = {"case": self.data(), "summary": self.data()["summary"]}

        def replace(match: Any) -> str:
            value: Any = context
            for component in match.group(1).strip().split("."):
                if not isinstance(value, dict) or component not in value:
                    return ""
                value = value[component]
            return str(value)

        return re.sub(r"\{\{\s*([A-Za-z_][A-Za-z0-9_.]*)\s*\}\}", replace, template)

    def timeline_svg(self) -> str:
        """Create an inline SVG visualization from timeline-bearing findings."""
        events = []
        for finding in self.case.findings:
            details = finding.get("details", {})
            if isinstance(details, dict) and isinstance(details.get("timeline"), list):
                events.extend(details["timeline"])
        parsed = []
        for event in events:
            try:
                parsed.append((datetime.fromisoformat(str(event["timestamp"]).replace("Z", "+00:00")), event))
            except (KeyError, TypeError, ValueError):
                continue
        if not parsed:
            return ""
        parsed.sort(key=lambda item: item[0])
        width, height = 900, 100 + min(len(parsed), 20) * 24
        start, end = parsed[0][0].timestamp(), parsed[-1][0].timestamp()
        span = max(1.0, end - start)
        pieces = [f"<svg role='img' aria-label='Timeline' width='100%' viewBox='0 0 {width} {height}'>",
                  "<line x1='60' y1='45' x2='840' y2='45' stroke='#60a5fa' stroke-width='3'/>"]
        for index, (timestamp, event) in enumerate(parsed[:20]):
            x = 60 + int((timestamp.timestamp() - start) / span * 780)
            y = 75 + index * 24
            label = html.escape(str(event.get("event_type", event.get("protocol", "event"))))
            pieces.append(f"<circle cx='{x}' cy='45' r='5' fill='#f59e0b'/><text x='60' y='{y}' fill='#e5e7eb'>{html.escape(timestamp.isoformat())} — {label}</text>")
        pieces.append("</svg>")
        return "".join(pieces)

    def write(self, output: Path, format: str = "markdown", template: Path = None) -> Path:
        output = Path(output)
        output.parent.mkdir(parents=True, exist_ok=True)
        format = format.lower()
        if template:
            output.write_text(self.render_template(Path(template).read_text(encoding="utf-8")), encoding="utf-8")
        elif format in {"markdown", "md"}:
            output.write_text(self.markdown(), encoding="utf-8")
        elif format == "html":
            output.write_text(self.html(), encoding="utf-8")
        elif format == "json":
            output.write_text(self.json(), encoding="utf-8")
        elif format == "pdf":
            output.write_bytes(_simple_pdf(self.markdown()))
        else:
            raise ValueError(f"Unsupported report format: {format}")
        return output


def _simple_pdf(text: str) -> bytes:
    """Create a basic, standards-compliant text PDF without optional packages."""
    lines = []
    for raw in text.splitlines():
        lines.extend(textwrap.wrap(raw, 95, replace_whitespace=False) or [""])
    pages = [lines[index:index + 48] for index in range(0, len(lines), 48)] or [[]]
    objects: List[bytes] = []
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    page_ids = [4 + index * 2 for index in range(len(pages))]
    objects.append(f"<< /Type /Pages /Count {len(pages)} /Kids [{' '.join(f'{item} 0 R' for item in page_ids)}] >>".encode())
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>")
    for page, page_id in zip(pages, page_ids):
        content_id = page_id + 1
        objects.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 3 0 R >> >> /Contents {content_id} 0 R >>".encode())
        commands = ["BT /F1 9 Tf 40 750 Td 12 TL"]
        for line in page:
            safe = line.encode("ascii", "replace").decode().replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            commands.append(f"({safe}) Tj T*")
        commands.append("ET")
        stream = "\n".join(commands).encode()
        objects.append(b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream")
    result = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for number, obj in enumerate(objects, 1):
        offsets.append(len(result))
        result.extend(f"{number} 0 obj\n".encode() + obj + b"\nendobj\n")
    xref = len(result)
    result.extend(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode())
    for offset in offsets[1:]:
        result.extend(f"{offset:010d} 00000 n \n".encode())
    result.extend(f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
    return bytes(result)


__all__ = ["ReportBuilder", "correlate_iocs"]
