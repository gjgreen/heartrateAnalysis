"""Workout utilities."""

from __future__ import annotations

from typing import Optional, Tuple

import pandas as pd


def compute_overlap_seconds(
    incident_start: pd.Timestamp, incident_end: pd.Timestamp, workout_start: pd.Timestamp, workout_end: pd.Timestamp
) -> float:
    latest_start = max(incident_start, workout_start)
    earliest_end = min(incident_end, workout_end)
    return max(0.0, (earliest_end - latest_start).total_seconds())


def find_best_overlap(
    incident_row: pd.Series, workouts: pd.DataFrame
) -> Tuple[Optional[pd.Series], float]:
    """Return workout with max overlap in seconds."""
    best_overlap = 0.0
    best_workout: Optional[pd.Series] = None
    for _, workout in workouts.iterrows():
        overlap = compute_overlap_seconds(
            incident_row["start_time"],
            incident_row["end_time"],
            workout["start_time"],
            workout["end_time"],
        )
        if overlap > best_overlap:
            best_overlap = overlap
            best_workout = workout
    return best_workout, best_overlap


__all__ = ["compute_overlap_seconds", "find_best_overlap"]
