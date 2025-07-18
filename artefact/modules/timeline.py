"""
timeline.py: Timeline event data structure and timestamp extraction logic for ArteFact v0.3.0
"""
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
from datetime import datetime
import os
from Artefact.error_handler import handle_error

@dataclass
class TimelineEvent:
    timestamp: datetime
    event_type: str  # e.g., 'created', 'modified', 'metadata', etc.
    source: str      # file path or metadata source
    details: Optional[Dict[str, Any]] = None

def extract_file_timestamps(file_path: str) -> List[TimelineEvent]:
    """
    Extracts filesystem timestamps (created, modified, accessed) for a file.
    Returns a list of TimelineEvent objects.
    """
    events = []
    try:
        stat = os.stat(file_path)
        events.append(TimelineEvent(
            timestamp=datetime.fromtimestamp(stat.st_ctime),
            event_type="created",
            source=file_path
        ))
        events.append(TimelineEvent(
            timestamp=datetime.fromtimestamp(stat.st_mtime),
            event_type="modified",
            source=file_path
        ))
        events.append(TimelineEvent(
            timestamp=datetime.fromtimestamp(stat.st_atime),
            event_type="accessed",
            source=file_path
        ))
    except Exception as e:
        handle_error(e, context="extract_file_timestamps")
    return events

def timeline_to_json(events: List[TimelineEvent]) -> str:
    import json
    return json.dumps([asdict(e) for e in sorted(events, key=lambda x: x.timestamp)], default=str, indent=2)

def timeline_to_markdown(events: List[TimelineEvent]) -> str:
    # Fallback to old Markdown table for test compatibility
    lines = ["| Timestamp | Event Type | Source | Details |", "|-----------|------------|--------|---------|"]
    for e in sorted(events, key=lambda x: x.timestamp):
        details = str(e.details) if e.details else ""
        lines.append(f"| {e.timestamp} | {e.event_type} | {e.source} | {details} |")
    return "\n".join(lines)

# Future: Add metadata extraction hooks for images, PDFs, etc.
