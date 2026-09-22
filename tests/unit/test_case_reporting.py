from Artefact.case import Case
from Artefact.reporting import ReportBuilder


def test_case_evidence_and_reports(tmp_path):
    evidence = tmp_path / "evidence.bin"
    evidence.write_bytes(b"evidence")
    case = Case.create("Example", "CASE-001")
    item = case.add_evidence(evidence, "disk image", "investigator")
    assert len(item.sha256) == 64
    case.add_finding("Network IOC", {"iocs": {"ipv4": ["192.0.2.1"]}}, "high")
    case_file = case.save(tmp_path / "case.json")
    loaded = Case.load(case_file)
    assert loaded.evidence[0].sha256 == item.sha256
    assert loaded.verify_evidence()[0]["valid"]
    evidence.write_bytes(b"tampered")
    assert not loaded.verify_evidence()[0]["valid"]
    builder = ReportBuilder(loaded)
    assert builder.data()["ioc_correlation"]["ipv4"] == ["192.0.2.1"]
    for format, suffix in (("markdown", ".md"), ("html", ".html"),
                           ("json", ".json"), ("pdf", ".pdf")):
        output = builder.write(tmp_path / ("report" + suffix), format)
        assert output.stat().st_size > 20
    assert (tmp_path / "report.pdf").read_bytes().startswith(b"%PDF-1.4")
    template = tmp_path / "template.txt"
    template.write_text("{{ case.title }} / {{ summary.evidence_count }}", encoding="utf-8")
    custom = builder.write(tmp_path / "custom.txt", template=template)
    assert custom.read_text(encoding="utf-8") == "Example / 1"


def test_timeline_visualization(tmp_path):
    case = Case.create("Timeline")
    case.add_finding("Events", {"timeline": [
        {"timestamp": "2025-01-01T00:00:00+00:00", "event_type": "created"},
        {"timestamp": "2025-01-01T00:01:00+00:00", "event_type": "modified"},
    ]})
    svg = ReportBuilder(case).timeline_svg()
    assert svg.startswith("<svg")
    assert "created" in svg and "modified" in svg
