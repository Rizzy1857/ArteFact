import os
import tempfile
from Artefact.modules.timeline import extract_file_timestamps, timeline_to_json, timeline_to_markdown, TimelineEvent
from datetime import datetime

def test_extract_file_timestamps():
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"test")
        tmp.flush()
        events = extract_file_timestamps(tmp.name)
        # Creation time may not be available on all platforms/filesystems
        event_types = [e.event_type for e in events]
        assert "file_modified" in event_types
        assert "file_accessed" in event_types
        # Accept either "file_created" or "file_creation" for cross-platform compatibility
        assert any(et in event_types for et in ["file_created", "file_creation"])
    os.unlink(tmp.name)

def test_timeline_to_json_and_markdown():
    events = [
        TimelineEvent(timestamp=datetime(2024, 1, 1, 12, 0), event_type="created", source="file1"),
        TimelineEvent(timestamp=datetime(2024, 1, 2, 13, 0), event_type="modified", source="file1"),
    ]
    json_out = timeline_to_json(events)
    md_out = timeline_to_markdown(events)
    assert "created" in json_out and "modified" in json_out
    assert "| Timestamp | Event Type | Source | Details |" in md_out
    assert "2024-01-01" in md_out and "2024-01-02" in md_out
