"""Schema detection and normalization helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd
from pandas.api.types import is_datetime64tz_dtype


@dataclass
class SampleSchema:
    timestamp: str
    bpm: str
    type_column: Optional[str] = None
    allowed_types: Optional[list[str]] = None


@dataclass
class WorkoutSchema:
    start: str
    end: str
    workout_type: Optional[str] = None


def _is_datetime_column(series: pd.Series) -> bool:
    """Heuristic: does this series look like datetimes."""
    sample = series.dropna().head(25)
    if sample.empty:
        return False
    parsed = pd.to_datetime(sample, errors="coerce", utc=False)
    return parsed.notna().mean() >= 0.2


def _is_bpm_column(series: pd.Series) -> bool:
    """Heuristic: numeric values in plausible heart-rate range."""
    numeric = pd.to_numeric(series, errors="coerce")
    sample = numeric.dropna()
    if sample.empty:
        return False
    median = float(sample.median())
    max_val = float(sample.max())
    min_val = float(sample.min())
    plausible_range = 20 <= min_val <= 260 and 40 <= max_val <= 260
    return plausible_range or (60 <= median <= 180)


def _find_heart_rate_types(series: pd.Series) -> list[str]:
    """Return unique values that look like heart rate type identifiers."""
    values = series.dropna().astype(str).str.lower().unique()
    hr_values = [
        v
        for v in values
        if (("heart" in v and "rate" in v) or v.endswith("heartrate") or v == "hkquantitytypeidentifierheartrate")
        and "variability" not in v
    ]
    return list(hr_values)


def _find_workout_types(series: pd.Series) -> list[str]:
    """Return unique values that look like workout type identifiers."""
    values = series.dropna().astype(str).str.lower().unique()
    workout_values = [
        v
        for v in values
        if "workout" in v
        or v.startswith("hkworkout")
        or v.startswith("hkactivitytype")
        or v.startswith("workout")
        or v == "workout"
    ]
    return list(workout_values)


def detect_sample_schema(df: pd.DataFrame) -> Optional[SampleSchema]:
    """Attempt to find timestamp and bpm columns."""
    lower_map = {c.lower(): c for c in df.columns}

    # Detect a type column that contains heart-rate identifiers.
    type_col: Optional[str] = None
    allowed_types: Optional[list[str]] = None
    for col in df.columns:
        if "type" in col.lower():
            hr_types = _find_heart_rate_types(df[col])
            if hr_types:
                type_col = col
                allowed_types = hr_types
                break

    ts_priority = [
        "startdate",
        "timestamp",
        "date",
        "start_time",
        "creationdate",
        "time",
    ]
    ts_col: Optional[str] = None
    for key in ts_priority:
        if key in lower_map:
            candidate = lower_map[key]
            if _is_datetime_column(df[candidate]) or ts_col is None:
                ts_col = candidate
                break
    if ts_col is None:
        for col in df.columns:
            if any(token in col.lower() for token in ["date", "time", "timestamp"]):
                if _is_datetime_column(df[col]):
                    ts_col = col
                    break

    bpm_col: Optional[str] = None
    bpm_keywords = ["bpm", "heart", "pulse", "hr"]
    # If we have a type column with heart-rate identifiers, allow looser BPM selection.
    if type_col and allowed_types:
        for col in df.columns:
            lowered = col.lower()
            if any(k in lowered for k in bpm_keywords):
                bpm_col = col
                break
        if bpm_col is None and "value" in lower_map:
            bpm_col = lower_map["value"]
        if bpm_col is not None:
            numeric = pd.to_numeric(df[bpm_col], errors="coerce").dropna()
            if numeric.empty and "value" in lower_map and lower_map["value"] != bpm_col:
                bpm_col = lower_map["value"]
    else:
        for col in df.columns:
            lowered = col.lower()
            if any(k in lowered for k in bpm_keywords):
                if _is_bpm_column(df[col]):
                    bpm_col = col
                    break
        if bpm_col is None and "value" in lower_map and _is_bpm_column(df[lower_map["value"]]):
            bpm_col = lower_map["value"]
        if bpm_col is None:
            for col in df.columns:
                if _is_bpm_column(df[col]):
                    bpm_col = col
                    break

    if ts_col and bpm_col:
        return SampleSchema(timestamp=ts_col, bpm=bpm_col, type_column=type_col, allowed_types=allowed_types)
    return None


def detect_workout_schema(df: pd.DataFrame) -> Optional[WorkoutSchema]:
    """Find start/end/type columns for workouts.

    To reduce false positives (e.g., heart-rate samples that also have start/end),
    require a plausible workout type/activity column.
    """
    start_col = None
    end_col = None
    type_col: Optional[str] = None

    # Prefer explicit workoutActivityType column if present.
    if "workoutActivityType" in df.columns:
        type_col = "workoutActivityType"
    else:
        for col in df.columns:
            lowered = col.lower()
            if type_col is None and (("workout" in lowered) or ("activity" in lowered and "type" in lowered) or lowered == "type"):
                workout_values = _find_workout_types(df[col])
                if workout_values:
                    type_col = col
                    break

    for col in df.columns:
        lowered = col.lower()
        if start_col is None and ("start" in lowered or "begin" in lowered):
            if _is_datetime_column(df[col]):
                start_col = col
        if end_col is None and ("end" in lowered or "stop" in lowered or "finish" in lowered):
            if _is_datetime_column(df[col]):
                end_col = col
    if start_col and end_col and type_col:
        return WorkoutSchema(start=start_col, end=end_col, workout_type=type_col)
    return None


def normalize_samples(chunk: pd.DataFrame, schema: SampleSchema) -> pd.DataFrame:
    """Return a normalized samples DataFrame with timestamp+bpm."""
    if schema.timestamp not in chunk.columns or schema.bpm not in chunk.columns:
        return pd.DataFrame(columns=["timestamp", "bpm"])
    cols = [schema.timestamp, schema.bpm]
    if schema.type_column and schema.type_column in chunk.columns:
        cols.append(schema.type_column)
    df = chunk[cols].copy()
    rename_map = {schema.timestamp: "timestamp", schema.bpm: "bpm"}
    if schema.type_column:
        rename_map[schema.type_column] = "type"
    df.rename(columns=rename_map, inplace=True)
    if "type" in df.columns and schema.allowed_types:
        df["type"] = df["type"].astype(str).str.lower()
        df = df[df["type"].isin([t.lower() for t in schema.allowed_types])]
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    if is_datetime64tz_dtype(df["timestamp"]):
        df["timestamp"] = df["timestamp"].dt.tz_convert(None)
    df["bpm"] = pd.to_numeric(df["bpm"], errors="coerce")
    df = df.dropna(subset=["timestamp", "bpm"])
    df = df[(df["bpm"] > 0) & (df["bpm"] < 300)]
    return df


def normalize_workouts(chunk: pd.DataFrame, schema: WorkoutSchema) -> pd.DataFrame:
    """Return normalized workouts with start_time/end_time/workout_type."""
    needed = [schema.start, schema.end]
    for col in needed:
        if col not in chunk.columns:
            return pd.DataFrame(columns=["start_time", "end_time", "workout_type"])
    cols = needed + ([schema.workout_type] if schema.workout_type and schema.workout_type in chunk.columns else [])
    df = chunk[cols].copy()
    rename_map = {schema.start: "start_time", schema.end: "end_time"}
    if schema.workout_type and schema.workout_type in df.columns:
        rename_map[schema.workout_type] = "workout_type"
    df.rename(columns=rename_map, inplace=True)
    df["start_time"] = pd.to_datetime(df["start_time"], errors="coerce")
    df["end_time"] = pd.to_datetime(df["end_time"], errors="coerce")
    if is_datetime64tz_dtype(df["start_time"]):
        df["start_time"] = df["start_time"].dt.tz_convert(None)
    if is_datetime64tz_dtype(df["end_time"]):
        df["end_time"] = df["end_time"].dt.tz_convert(None)
    df = df.dropna(subset=["start_time", "end_time"])
    df = df[df["end_time"] >= df["start_time"]]
    if "workout_type" not in df.columns:
        df["workout_type"] = "unknown"
    else:
        df = df[df["workout_type"].notna() & (df["workout_type"].astype(str).str.len() > 0)]
    return df


__all__ = [
    "SampleSchema",
    "WorkoutSchema",
    "detect_sample_schema",
    "detect_workout_schema",
    "normalize_samples",
    "normalize_workouts",
]
