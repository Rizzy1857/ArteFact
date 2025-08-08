"""
Timeline Generation Module
==========================

Creates forensic timelines from file timestamps and metadata
for temporal analysis of digital evidence.
"""

import os
import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from rich.console import Console
from rich.table import Table

from Artefact.error_handler import handle_error, with_error_handling

console = Console()

@dataclass
class TimelineEvent:
    """Represents a single event in the timeline."""
    timestamp: datetime
    event_type: str  # e.g., 'created', 'modified', 'metadata', etc.
    source: str      # file path or metadata source
    details: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Ensure timestamp is a datetime object."""
        if isinstance(self.timestamp, str):
            try:
                self.timestamp = datetime.fromisoformat(self.timestamp.replace('Z', '+00:00'))
            except ValueError:
                # Try other common formats
                for fmt in ['%Y-%m-%d %H:%M:%S', '%Y:%m:%d %H:%M:%S']:
                    try:
                        self.timestamp = datetime.strptime(self.timestamp, fmt)
                        break
                    except ValueError:
                        continue


@with_error_handling("extract_file_timestamps")
def extract_file_timestamps(file_path: str) -> List[TimelineEvent]:
    """
    Extract filesystem timestamps (created, modified, accessed) for a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        List of TimelineEvent objects
    """
    events = []
    
    try:
        if not os.path.exists(file_path):
            return events
            
        stat = os.stat(file_path)
        
        # Create timeline events for filesystem timestamps
        events.extend([
            TimelineEvent(
                timestamp=datetime.fromtimestamp(stat.st_ctime),
                event_type="file_created",
                source=file_path,
                details={"source": "filesystem", "size": stat.st_size}
            ),
            TimelineEvent(
                timestamp=datetime.fromtimestamp(stat.st_mtime),
                event_type="file_modified",
                source=file_path,
                details={"source": "filesystem", "size": stat.st_size}
            ),
            TimelineEvent(
                timestamp=datetime.fromtimestamp(stat.st_atime),
                event_type="file_accessed",
                source=file_path,
                details={"source": "filesystem", "size": stat.st_size}
            )
        ])
        
    except Exception as e:
        handle_error(e, context=f"extract_file_timestamps for {file_path}")
    
    return events


@with_error_handling("create_timeline_from_directory")
def create_timeline_from_directory(
    directory: Path, 
    recursive: bool = True,
    include_metadata: bool = True,
    file_extensions: Optional[List[str]] = None
) -> List[TimelineEvent]:
    """
    Create timeline from all files in a directory.
    
    Args:
        directory: Directory to scan
        recursive: Whether to scan subdirectories
        include_metadata: Whether to include metadata timestamps
        file_extensions: List of file extensions to include (None = all)
        
    Returns:
        List of TimelineEvent objects
    """
    events = []
    
    if not directory.exists() or not directory.is_dir():
        console.print(f"[red]Directory not found or invalid: {directory}[/]")
        return events
    
    # Collect files to process
    files_to_process = []
    pattern = "**/*" if recursive else "*"
    
    for file_path in directory.glob(pattern):
        if file_path.is_file():
            # Filter by extension if specified
            if file_extensions:
                if file_path.suffix.lower() not in [ext.lower() for ext in file_extensions]:
                    continue
            files_to_process.append(file_path)
    
    console.print(f"[green]Processing {len(files_to_process)} files for timeline...[/]")
    
    # Process each file
    for file_path in files_to_process:
        try:
            # Add filesystem timestamps
            file_events = extract_file_timestamps(str(file_path))
            events.extend(file_events)
            
            # Add metadata timestamps if requested
            if include_metadata:
                metadata_events = _extract_metadata_timestamps(file_path)
                events.extend(metadata_events)
                
        except Exception as e:
            console.print(f"[yellow]Warning: Failed to process {file_path}: {e}[/]")
    
    # Sort events by timestamp
    events.sort(key=lambda x: x.timestamp)
    
    console.print(f"[green]Generated timeline with {len(events)} events[/]")
    return events


def _extract_metadata_timestamps(file_path: Path) -> List[TimelineEvent]:
    """Extract timestamps from file metadata."""
    events = []
    
    try:
        # Import metadata module to extract timestamps
        from Artefact.modules.metadata import extract_metadata
        
        metadata = extract_metadata(file_path, deep=False)
        
        for timestamp_info in metadata.get("timestamps", []):
            if timestamp_info.get("source") != "filesystem":  # Skip filesystem timestamps
                try:
                    dt_str = timestamp_info.get("value")
                    if dt_str:
                        # Parse ISO format timestamp
                        timestamp = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
                        
                        events.append(TimelineEvent(
                            timestamp=timestamp,
                            event_type=f"metadata_{timestamp_info.get('label', 'unknown').lower().replace(' ', '_')}",
                            source=str(file_path),
                            details={
                                "source": timestamp_info.get("source", "metadata"),
                                "label": timestamp_info.get("label", "Unknown"),
                                "metadata_type": timestamp_info.get("source", "unknown")
                            }
                        ))
                except Exception as e:
                    # Skip invalid timestamps
                    continue
                    
    except Exception as e:
        # Metadata extraction failed, skip
        pass
    
    return events


def timeline_to_json(events: List[TimelineEvent], indent: int = 2) -> str:
    """
    Export timeline events to JSON format.
    
    Args:
        events: List of timeline events
        indent: JSON indentation level
        
    Returns:
        JSON string representation
    """
    # Convert events to serializable format
    serializable_events = []
    for event in sorted(events, key=lambda x: x.timestamp):
        event_dict = asdict(event)
        # Convert datetime to string
        event_dict["timestamp"] = event.timestamp.isoformat()
        serializable_events.append(event_dict)
    
    return json.dumps(serializable_events, indent=indent, default=str)


def timeline_to_markdown(events: List[TimelineEvent]) -> str:
    """
    Export timeline events to Markdown table format.
    
    Args:
        events: List of timeline events
        
    Returns:
        Markdown table string
    """
    lines = [
        "| Timestamp | Event Type | Source | Details |",
        "|-----------|------------|--------|---------|"
    ]
    
    for event in sorted(events, key=lambda x: x.timestamp):
        timestamp_str = event.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        details = str(event.details) if event.details else ""
        
        # Escape pipe characters in content
        source = str(event.source).replace("|", "\\|")
        event_type = event.event_type.replace("|", "\\|")
        details = details.replace("|", "\\|")
        
        lines.append(f"| {timestamp_str} | {event_type} | {source} | {details} |")
    
    return "\n".join(lines)


def timeline_to_csv(events: List[TimelineEvent]) -> str:
    """
    Export timeline events to CSV format.
    
    Args:
        events: List of timeline events
        
    Returns:
        CSV string
    """
    lines = ["Timestamp,Event Type,Source,Details"]
    
    for event in sorted(events, key=lambda x: x.timestamp):
        timestamp_str = event.timestamp.isoformat()
        
        # Escape quotes and commas
        source = f'"{str(event.source).replace('"', '""')}"'
        event_type = f'"{event.event_type.replace('"', '""')}"'
        details = f'"{str(event.details).replace('"', '""')}"' if event.details else '""'
        
        lines.append(f"{timestamp_str},{event_type},{source},{details}")
    
    return "\n".join(lines)


def display_timeline(events: List[TimelineEvent], limit: int = 50):
    """
    Display timeline events in a formatted table.
    
    Args:
        events: List of timeline events
        limit: Maximum number of events to display
    """
    if not events:
        console.print("[yellow]No timeline events to display[/]")
        return
    
    # Sort events by timestamp
    sorted_events = sorted(events, key=lambda x: x.timestamp)
    
    # Create table
    table = Table(title=f"Timeline ({len(sorted_events)} events)", show_lines=True)
    table.add_column("Timestamp", style="cyan", width=20)
    table.add_column("Event Type", style="yellow", width=20)
    table.add_column("Source", style="green", overflow="fold")
    table.add_column("Details", style="white", width=30, overflow="fold")
    
    # Add events to table (limited)
    display_events = sorted_events[:limit]
    
    for event in display_events:
        timestamp_str = event.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        
        # Format details
        details_str = ""
        if event.details:
            key_details = []
            for key, value in event.details.items():
                if key in ['size', 'source', 'label']:
                    key_details.append(f"{key}: {value}")
            details_str = ", ".join(key_details[:2])  # Limit to 2 key details
        
        # Color code event types
        event_type_colored = event.event_type
        if "created" in event.event_type:
            event_type_colored = f"[green]{event.event_type}[/green]"
        elif "modified" in event.event_type:
            event_type_colored = f"[yellow]{event.event_type}[/yellow]"
        elif "accessed" in event.event_type:
            event_type_colored = f"[blue]{event.event_type}[/blue]"
        elif "metadata" in event.event_type:
            event_type_colored = f"[magenta]{event.event_type}[/magenta]"
        
        table.add_row(
            timestamp_str,
            event_type_colored,
            str(event.source),
            details_str
        )
    
    console.print(table)
    
    if len(sorted_events) > limit:
        console.print(f"[yellow]Showing first {limit} of {len(sorted_events)} events[/]")


def filter_timeline(
    events: List[TimelineEvent],
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    event_types: Optional[List[str]] = None,
    sources: Optional[List[str]] = None
) -> List[TimelineEvent]:
    """
    Filter timeline events based on criteria.
    
    Args:
        events: List of timeline events
        start_time: Filter events after this time
        end_time: Filter events before this time
        event_types: List of event types to include
        sources: List of source patterns to include
        
    Returns:
        Filtered list of timeline events
    """
    filtered_events = events.copy()
    
    # Filter by time range
    if start_time:
        filtered_events = [e for e in filtered_events if e.timestamp >= start_time]
    
    if end_time:
        filtered_events = [e for e in filtered_events if e.timestamp <= end_time]
    
    # Filter by event types
    if event_types:
        filtered_events = [e for e in filtered_events if e.event_type in event_types]
    
    # Filter by source patterns
    if sources:
        filtered_by_source = []
        for event in filtered_events:
            for source_pattern in sources:
                if source_pattern.lower() in str(event.source).lower():
                    filtered_by_source.append(event)
                    break
        filtered_events = filtered_by_source
    
    return filtered_events


def timeline_statistics(events: List[TimelineEvent]) -> Dict[str, Any]:
    """
    Generate statistics about timeline events.
    
    Args:
        events: List of timeline events
        
    Returns:
        Dictionary containing statistics
    """
    if not events:
        return {}
    
    sorted_events = sorted(events, key=lambda x: x.timestamp)
    
    # Count by event type
    event_type_counts = {}
    for event in events:
        event_type_counts[event.event_type] = event_type_counts.get(event.event_type, 0) + 1
    
    # Count by source
    source_counts = {}
    for event in events:
        source_counts[str(event.source)] = source_counts.get(str(event.source), 0) + 1
    
    stats = {
        "total_events": len(events),
        "time_range": {
            "start": sorted_events[0].timestamp.isoformat(),
            "end": sorted_events[-1].timestamp.isoformat(),
            "duration_hours": (sorted_events[-1].timestamp - sorted_events[0].timestamp).total_seconds() / 3600
        },
        "event_types": event_type_counts,
        "unique_sources": len(source_counts),
        "top_sources": dict(sorted(source_counts.items(), key=lambda x: x[1], reverse=True)[:10])
    }
    
    return stats


if __name__ == "__main__":
    # CLI interface for standalone usage
    import argparse
    
    parser = argparse.ArgumentParser(description="Timeline Generation Tool")
    parser.add_argument("path", help="File or directory path to create timeline from")
    parser.add_argument("-o", "--output", help="Output file path")
    parser.add_argument("-f", "--format", choices=["json", "markdown", "csv"], 
                       default="markdown", help="Output format")
    parser.add_argument("--recursive", action="store_true", 
                       help="Process directories recursively")
    parser.add_argument("--no-metadata", action="store_true",
                       help="Skip metadata timestamp extraction")
    parser.add_argument("--extensions", nargs="*",
                       help="File extensions to include")
    parser.add_argument("--display", action="store_true",
                       help="Display timeline in terminal")
    parser.add_argument("--stats", action="store_true",
                       help="Show timeline statistics")
    
    args = parser.parse_args()
    
    path = Path(args.path)
    
    try:
        if path.is_file():
            events = extract_file_timestamps(str(path))
        elif path.is_dir():
            events = create_timeline_from_directory(
                path,
                recursive=args.recursive,
                include_metadata=not args.no_metadata,
                file_extensions=args.extensions
            )
        else:
            console.print(f"[red]Error:[/] Path not found: {path}")
            exit(1)
        
        if not events:
            console.print("[yellow]No timeline events found[/]")
            exit(0)
        
        # Generate output
        if args.format == "json":
            output = timeline_to_json(events)
        elif args.format == "csv":
            output = timeline_to_csv(events)
        else:  # markdown
            output = timeline_to_markdown(events)
        
        # Save or display output
        if args.output:
            Path(args.output).write_text(output, encoding='utf-8')
            console.print(f"[green]Timeline saved to {args.output}[/]")
        else:
            console.print(output)
        
        # Display in terminal if requested
        if args.display:
            console.print("\n")
            display_timeline(events)
        
        # Show statistics if requested
        if args.stats:
            stats = timeline_statistics(events)
            console.print("\n[bold]Timeline Statistics:[/bold]")
            console.print_json(json.dumps(stats, indent=2, default=str))
        
    except Exception as e:
        console.print(f"[red]Error:[/] {str(e)}")
        exit(1)
