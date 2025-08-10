"""
Unit tests for the metadata module
"""
import pytest
from Artefact.modules.metadata import extract_metadata

def test_extract_metadata_basic(sample_files):
    """Test basic metadata extraction."""
    result = extract_metadata(sample_files['text'])
    assert isinstance(result, dict)
    assert 'timestamps' in result
    assert len(result['timestamps']) > 0

def test_extract_metadata_nonexistent():
    """Test metadata extraction from nonexistent file."""
    result = extract_metadata("nonexistent_file.txt")
    assert isinstance(result, dict)
    assert len(result['timestamps']) == 0
    assert 'error' in result

def test_extract_metadata_empty(sample_files):
    """Test metadata extraction from empty file."""
    result = extract_metadata(sample_files['empty'])
    assert isinstance(result, dict)
    assert 'timestamps' in result

def test_extract_metadata_binary(sample_files):
    """Test metadata extraction from binary file."""
    result = extract_metadata(sample_files['binary'])
    assert isinstance(result, dict)
    assert 'timestamps' in result
