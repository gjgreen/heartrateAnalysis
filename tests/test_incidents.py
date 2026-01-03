from datetime import datetime, timedelta

import pandas as pd

from health_hr_analyzer.incidents import detect_incidents


def test_detect_incidents_groups_by_gap():
    base = datetime(2024, 1, 1, 0, 0, 0)
    samples = pd.DataFrame(
        {
            "timestamp": [
                base,
                base + timedelta(seconds=60),
                base + timedelta(seconds=400),
                base + timedelta(seconds=460),
            ],
            "bpm": [150, 160, 170, 150],
        }
    )
    incidents = detect_incidents(samples, threshold_bpm=140, gap_seconds=120)
    assert len(incidents) == 2
    first = incidents.iloc[0]
    assert first["sample_count"] == 2
    assert first["max_bpm"] == 160
    second = incidents.iloc[1]
    assert second["sample_count"] == 2
    assert int(second["duration_seconds"]) == 60


def test_detect_incidents_applies_strict_threshold():
    base = datetime(2024, 2, 1, 12, 0, 0)
    samples = pd.DataFrame({"timestamp": [base, base + timedelta(seconds=30)], "bpm": [140, 141]})
    incidents = detect_incidents(samples, threshold_bpm=140, gap_seconds=120)
    assert len(incidents) == 1
    assert incidents.iloc[0]["start_time"] == base + timedelta(seconds=30)
