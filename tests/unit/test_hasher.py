"""
Unit tests for the hasher module
"""
import pytest
from pathlib import Path
from Artefact.modules.hasher import hash_file, hash_directory, SUPPORTED_ALGORITHMS

def test_hash_file_basic(sample_files):
    """Test basic file hashing functionality."""
    result = hash_file(sample_files['text'], 'sha256')
    assert isinstance(result, str)
    assert len(result) == 64  # SHA256 is 64 chars in hex

def test_hash_file_algorithms(sample_files):
    """Test all supported hash algorithms."""
    for algorithm in SUPPORTED_ALGORITHMS:
        result = hash_file(sample_files['text'], algorithm)
        assert isinstance(result, str)
        assert len(result) > 0

def test_hash_file_nonexistent():
    """Test hashing nonexistent file."""
    with pytest.raises(FileNotFoundError):
        hash_file(Path("nonexistent_file.txt"), "sha256")

def test_hash_directory_basic(temp_dir):
    """Test basic directory hashing."""
    results = hash_directory(temp_dir, "sha256")
    assert isinstance(results, dict)
    assert len(results) > 0

def test_hash_directory_recursive(temp_dir):
    """Test recursive directory hashing."""
    # Create nested directory
    subdir = temp_dir / "subdir"
    subdir.mkdir()
    (subdir / "test.txt").write_text("Test content")
    
    results = hash_directory(temp_dir, "sha256", recursive=True)
    assert any("subdir" in path for path in results.keys())
