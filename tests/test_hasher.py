import pytest
from pathlib import Path
from artefact.modules import hasher

def test_hash_file(tmp_path):
    # Create a temporary file
    file = tmp_path / "test.txt"
    file.write_text("hello world")
    # Test SHA256
    result = hasher.hash_file(file, "sha256")
    assert result == "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
    # Test MD5
    result = hasher.hash_file(file, "md5")
    assert result == "5eb63bbbe01eeed093cb22bb8f5acdc3"
    # Test SHA1
    result = hasher.hash_file(file, "sha1")
    assert result == "2aae6c35c94fcfb415dbe95f408b9ce91ee846ed"

def test_hash_directory(tmp_path):
    (tmp_path / "a.txt").write_text("a")
    (tmp_path / "b.txt").write_text("b")
    results = hasher.hash_directory(tmp_path, "md5", output_format="json")
    assert results[str(tmp_path / "a.txt")] == "0cc175b9c0f1b6a831c399e269772661"
    assert results[str(tmp_path / "b.txt")] == "92eb5ffee6ae2fec3ad71c777531578f"
