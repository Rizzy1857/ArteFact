import json

from Artefact.core import (ArtefactConfig, ProgressTracker, format_bytes,
                           safe_filename, validate_directory_path,
                           validate_file_path)


def test_config_round_trip_and_nested_updates(tmp_path, monkeypatch):
    monkeypatch.setattr(ArtefactConfig, "_setup_monitoring", lambda self: None)
    config = ArtefactConfig({"output": {"quiet": True}, "paths": {"output_dir": str(tmp_path / "out")}})
    assert config.get("output.quiet") is True
    config.set("logging.level", "DEBUG")
    path = tmp_path / "config.json"
    config.save_config(path)
    assert json.loads(path.read_text())["logging"]["level"] == "DEBUG"
    second = ArtefactConfig({"output": {"quiet": True}})
    second.load_config(path)
    assert second.get("logging.level") == "DEBUG"
    assert second.ensure_output_dir("case").is_dir()


def test_path_and_format_helpers(tmp_path):
    file = tmp_path / "item.txt"
    file.write_text("x")
    assert validate_file_path(file)
    assert not validate_file_path(tmp_path)
    created = tmp_path / "new" / "directory"
    assert validate_directory_path(created, create_if_missing=True)
    assert format_bytes(1024) == "1.00 KB"
    assert safe_filename('a:b?.txt') == "a_b_.txt"


def test_zero_length_progress_is_safe():
    tracker = ProgressTracker(0)
    tracker.update()
    tracker.finish()
    assert tracker.current == 0
