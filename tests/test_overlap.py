from datetime import datetime, timedelta

import pandas as pd

from health_hr_analyzer.classify import classify_incidents


def test_workout_overlap_classification():
    base = datetime(2024, 1, 1, 0, 0, 0)
    incidents_df = pd.DataFrame(
        {
            "incident_id": [1, 2],
            "start_time": [base, base + timedelta(seconds=1000)],
            "end_time": [base + timedelta(seconds=300), base + timedelta(seconds=1100)],
            "duration_seconds": [300.0, 100.0],
            "max_bpm": [170, 150],
            "avg_bpm": [160, 145],
            "sample_count": [5, 3],
        }
    )
    workouts = pd.DataFrame(
        {
            "start_time": [base + timedelta(seconds=50), base + timedelta(seconds=20)],
            "end_time": [base + timedelta(seconds=260), base + timedelta(seconds=40)],
            "workout_type": ["running", "yoga"],
        }
    )
    classified = classify_incidents(incidents_df, workouts, min_overlap_seconds=1)
    first = classified.iloc[0]
    assert first["classification"] == "workout"
    assert first["workout_type"] == "running"
    assert int(first["overlap_seconds"]) == 210
    second = classified.iloc[1]
    assert second["classification"] == "unknown"
    assert second["overlap_seconds"] == 0
