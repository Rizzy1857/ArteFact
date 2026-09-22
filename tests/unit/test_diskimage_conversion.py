from pathlib import Path

from Artefact.modules import diskimage


def test_aff_conversion_streams_affcat_output(tmp_path, monkeypatch):
    source = tmp_path / "sample.aff"
    source.write_bytes(b"AFF")
    output = tmp_path / "sample.raw"
    monkeypatch.setattr(diskimage.shutil, "which", lambda name: "affcat" if name == "affcat" else None)

    def run(command, stdout, stderr, check):
        assert command == ["affcat", str(source)]
        stdout.write(b"RAW-DATA")
        return type("Result", (), {"returncode": 0, "stderr": b""})()

    monkeypatch.setattr(diskimage.subprocess, "run", run)
    assert diskimage.convert_image(source, output)
    assert output.read_bytes() == b"RAW-DATA"
