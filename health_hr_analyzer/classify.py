"""Classification logic for incidents."""

from __future__ import annotations

import pandas as pd

from .workouts import find_best_overlap


def classify_incidents(
    incidents: pd.DataFrame,
    workouts: pd.DataFrame,
    min_overlap_seconds: float = 1.0,
) -> pd.DataFrame:
    """Classify incidents based on explicit workout overlap."""
    result = incidents.copy()
    default_notes = "no explicit workout overlap"
    result["classification"] = "unknown"
    result["workout_confidence"] = "unknown"
    result["workout_type"] = "unknown"
    result["overlap_seconds"] = 0.0
    result["notes"] = default_notes

    if result.empty or workouts.empty:
        return result

    for idx, row in result.iterrows():
        workout, overlap = find_best_overlap(row, workouts)
        if workout is not None and overlap >= min_overlap_seconds:
            workout_type = workout.get("workout_type", "unknown")
            result.at[idx, "classification"] = "workout"
            result.at[idx, "workout_confidence"] = "high"
            result.at[idx, "workout_type"] = workout_type if isinstance(workout_type, str) else "unknown"
            result.at[idx, "overlap_seconds"] = overlap
            result.at[idx, "notes"] = "explicit workout overlap"
    return result


__all__ = ["classify_incidents"]
