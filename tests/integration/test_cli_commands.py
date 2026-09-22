import json

from Artefact.cli import main


def test_cli_core_case_report_and_plugins(tmp_path, capsys):
    evidence = tmp_path / "evidence.txt"
    evidence.write_text("evidence")
    assert main(["--version"]) == 0
    assert "1.0.0" in capsys.readouterr().out
    assert main(["--list-tools"]) == 0
    assert main(["hash", str(evidence), "--algorithm", "sha256", "--cache", str(tmp_path / "cache.json")]) == 0
    assert "sha256:" in capsys.readouterr().out
    assert main(["meta", "-f", str(evidence), "--json"]) == 0
    metadata = json.loads(capsys.readouterr().out)
    assert metadata["format"] == "txt"
    assert main(["timeline", str(evidence), "--format", "json"]) == 0
    assert "file_modified" in capsys.readouterr().out

    case_file = tmp_path / "case.json"
    assert main(["case", str(case_file), "--create", "CLI Case", "--id", "CLI-1"]) == 0
    assert main(["case", str(case_file), "--add-evidence", str(evidence)]) == 0
    report = tmp_path / "report.md"
    assert main(["report", str(case_file), "-o", str(report)]) == 0
    assert "CLI Case" in report.read_text(encoding="utf-8")
    assert main(["plugins", "--root", str(tmp_path / "plugins"), "--verify"]) == 0
    assert main(["health"]) == 0


def test_cli_carve_memory_and_error_paths(tmp_path, capsys):
    image = tmp_path / "image.img"
    image.write_bytes(b"x\xff\xd8\xffhello\xff\xd9y")
    output = tmp_path / "carved"
    assert main(["carve", "-i", str(image), "-o", str(output), "--types", "jpg"]) == 0
    assert list(output.glob("*.jpg"))

    memory = tmp_path / "memory.raw"
    memory.write_bytes(b"contact admin@example.com at 192.0.2.4\x00")
    assert main(["memory", "-i", str(memory), "--strings", "--iocs", "--min-length", "4"]) == 0
    assert "admin@example.com" in capsys.readouterr().out
    assert main(["hash", str(tmp_path / "missing")]) == 1
    assert "error" in capsys.readouterr().err


def test_cli_liveops_and_gui_dispatch(tmp_path, monkeypatch, capsys):
    import Artefact.gui
    import Artefact.modules.liveops

    monkeypatch.setattr(Artefact.modules.liveops, "collect", lambda items: {items[0]: [{"pid": 1}]})
    assert main(["liveops", "--collect", "processes"]) == 0
    assert '"pid": 1' in capsys.readouterr().out
    monkeypatch.setattr(Artefact.gui, "launch_gui", lambda case_file: 7)
    assert main(["gui"]) == 7
