"""Incident detection logic."""

from __future__ import annotations

from typing import List

import pandas as pd


INCIDENT_COLUMNS = [
    "incident_id",
    "start_time",
    "end_time",
    "duration_seconds",
    "max_bpm",
    "avg_bpm",
    "sample_count",
]


def _summarize_incident(rows: List[pd.Series]) -> dict:
    start_time = rows[0]["timestamp"]
    end_time = rows[-1]["timestamp"]
    duration_seconds = max(0.0, (end_time - start_time).total_seconds())
    bpm_values = [float(r["bpm"]) for r in rows]
    return {
        "start_time": start_time,
        "end_time": end_time,
        "duration_seconds": duration_seconds,
        "max_bpm": max(bpm_values),
        "avg_bpm": sum(bpm_values) / len(bpm_values),
        "sample_count": len(rows),
    }


def detect_incidents(
    samples: pd.DataFrame,
    threshold_bpm: float = 140.0,
    gap_seconds: int = 120,
    min_duration_seconds: float = 0.0,
) -> pd.DataFrame:
    """Group samples above threshold into incidents."""
    if samples.empty:
        return pd.DataFrame(columns=INCIDENT_COLUMNS)
    filtered = samples[samples["bpm"] > threshold_bpm].copy()
    if filtered.empty:
        return pd.DataFrame(columns=INCIDENT_COLUMNS)
    filtered.sort_values("timestamp", inplace=True)
    filtered.reset_index(drop=True, inplace=True)

    incidents = []
    current_rows: List[pd.Series] = [filtered.iloc[0]]
    for idx in range(1, len(filtered)):
        current = filtered.iloc[idx]
        previous = current_rows[-1]
        delta = (current["timestamp"] - previous["timestamp"]).total_seconds()
        if delta <= gap_seconds:
            current_rows.append(current)
        else:
            summary = _summarize_incident(current_rows)
            if summary["duration_seconds"] >= min_duration_seconds:
                incidents.append(summary)
            current_rows = [current]
    # finalize last
    summary = _summarize_incident(current_rows)
    if summary["duration_seconds"] >= min_duration_seconds:
        incidents.append(summary)

    for idx, inc in enumerate(incidents, start=1):
        inc["incident_id"] = idx

    return pd.DataFrame(incidents, columns=INCIDENT_COLUMNS)


__all__ = ["detect_incidents", "INCIDENT_COLUMNS"]
