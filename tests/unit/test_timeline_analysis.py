from datetime import datetime, timedelta

import pytest

from Artefact.modules.timeline import (TimelineEvent, correlate_events,
    detect_anomalies, filter_timeline, find_event_patterns, timeline_statistics,
    timeline_to_csv)


def _events():
    start = datetime(2025, 1, 1, 0, 0)
    return [TimelineEvent(start + timedelta(minutes=index), "create" if index % 2 == 0 else "modify",
                          "alpha" if index < 4 else "beta", {"index": index})
            for index in range(8)]


def test_timeline_correlation_patterns_filters_and_statistics():
    events = _events()
    groups = correlate_events(events, timedelta(minutes=2))
    assert len(groups) == 1 and len(groups[0]) == 8
    patterns = find_event_patterns(events)
    assert any(pattern["frequency"] > 1 for pattern in patterns)
    filtered = filter_timeline(events, event_types=["create"], sources=["alpha"], time_window="1d")
    assert len(filtered) == 2
    stats = timeline_statistics(events)
    assert stats["total_events"] == 8
    assert stats["event_types"] == {"create": 4, "modify": 4}
    assert "events_per_hour" in stats["event_density"]
    csv = timeline_to_csv(events)
    assert csv.count("\n") == len(events)


def test_anomaly_windows_accept_day_ranges_and_reject_zero():
    events = _events()
    assert isinstance(detect_anomalies(events, timedelta(days=1)), list)
    with pytest.raises(ValueError, match="positive"):
        detect_anomalies(events, timedelta(0))


def test_timeline_event_parses_supported_string_timestamp():
    event = TimelineEvent("2025:01:02 03:04:05", "created", "x")
    assert event.timestamp.year == 2025
