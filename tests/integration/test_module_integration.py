"""
Integration tests for ArteFact modules
"""
import pytest
from pathlib import Path
from Artefact.modules.hasher import hash_file
from Artefact.modules.metadata import extract_metadata
from Artefact.modules.timeline import extract_file_timestamps, timeline_to_json

def test_metadata_timeline_integration(sample_files):
    """Test metadata extraction and timeline generation together."""
    # Extract metadata
    metadata = extract_metadata(sample_files['text'])
    assert 'timestamps' in metadata
    
    # Generate timeline
    timeline = extract_file_timestamps(sample_files['text'])
    assert len(timeline) > 0
    
    # Convert to JSON
    json_output = timeline_to_json(timeline)
    assert isinstance(json_output, str)
    assert len(json_output) > 0

def test_hash_metadata_integration(sample_files):
    """Test file hashing and metadata extraction together."""
    # Hash file
    file_hash = hash_file(sample_files['text'], 'sha256')
    assert isinstance(file_hash, str)
    assert len(file_hash) == 64
    
    # Extract metadata
    metadata = extract_metadata(sample_files['text'])
    assert 'timestamps' in metadata
    
    # Verify file hasn't changed
    new_hash = hash_file(sample_files['text'], 'sha256')
    assert new_hash == file_hash
