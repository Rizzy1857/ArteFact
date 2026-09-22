import sys

import pytest

from Artefact.modules.disk_forensics import (analyze_registry_hive,
                                              list_volume_shadows,
                                              recover_deleted_files)


def test_registry_requires_existing_hive(tmp_path):
    with pytest.raises(FileNotFoundError):
        analyze_registry_hive(tmp_path / "missing.hive")


@pytest.mark.skipif(sys.platform == "win32", reason="non-Windows behavior")
def test_volume_shadows_are_empty_off_windows():
    assert list_volume_shadows() == []


def test_windows_shadow_output_is_parsed(monkeypatch):
    import Artefact.modules.disk_forensics as module

    output = """Shadow Copy ID: {abc}\nOriginal Volume: (C:)\\\\?\\Volume{vol}\\\nCreation Time: 1/2/2025\nShadow Copy Volume: \\\\?\\GLOBALROOT\\Device\\HarddiskVolumeShadowCopy1\n"""
    monkeypatch.setattr(module.sys, "platform", "win32")
    monkeypatch.setattr(module.subprocess, "run", lambda *args, **kwargs:
                        type("Result", (), {"returncode": 0, "stdout": output, "stderr": ""})())
    snapshots = list_volume_shadows("C:")
    assert snapshots[0]["id"] == "{abc}"
    assert "HarddiskVolumeShadowCopy1" in snapshots[0]["device"]


def test_deleted_recovery_reports_new_files(tmp_path, monkeypatch):
    import Artefact.modules.disk_forensics as module

    output = tmp_path / "recovered"

    def extract(image, partition, destination, filter_pattern, recover_deleted):
        assert recover_deleted is True
        destination.mkdir(parents=True)
        (destination / "deleted.txt").write_text("recovered")

    monkeypatch.setattr(module.diskimage, "extract_partition", extract)
    recovered = recover_deleted_files(tmp_path / "image.raw", 0, output)
    assert recovered == [output / "deleted.txt"]
