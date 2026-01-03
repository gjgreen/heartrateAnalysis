"""CSV ingestion and schema detection."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from .normalize import (
    SampleSchema,
    WorkoutSchema,
    detect_sample_schema,
    detect_workout_schema,
    normalize_samples,
    normalize_workouts,
)

logger = logging.getLogger(__name__)


SchemaReport = Dict[str, Any]


def _iter_csv_paths(path: Path) -> List[Path]:
    if path.is_dir():
        return sorted(p for p in path.glob("**/*.csv") if p.is_file())
    if path.is_file():
        return [path]
    raise FileNotFoundError(f"Input path not found: {path}")


def _filter_window(df: pd.DataFrame, start: Optional[pd.Timestamp], end: Optional[pd.Timestamp], time_col: str) -> pd.DataFrame:
    if start is not None:
        df = df[df[time_col] >= start]
    if end is not None:
        df = df[df[time_col] <= end]
    return df


def _sniff_schema(path: Path) -> Tuple[Optional[SampleSchema], Optional[WorkoutSchema]]:
    try:
        preview = pd.read_csv(path, nrows=500, low_memory=False)
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Could not read preview from %s: %s", path, exc)
        return None, None
    sample_schema = detect_sample_schema(preview)
    workout_schema = detect_workout_schema(preview)
    return sample_schema, workout_schema


def _process_file(
    path: Path,
    start: Optional[pd.Timestamp],
    end: Optional[pd.Timestamp],
    chunk_size: int,
) -> Tuple[List[pd.DataFrame], List[pd.DataFrame], SchemaReport]:
    sample_schema, workout_schema = _sniff_schema(path)
    schema_report: SchemaReport = {
        "path": str(path),
        "sample_schema": sample_schema.__dict__ if sample_schema else None,
        "workout_schema": workout_schema.__dict__ if workout_schema else None,
    }
    sample_frames: List[pd.DataFrame] = []
    workout_frames: List[pd.DataFrame] = []
    if sample_schema is None and workout_schema is None:
        return sample_frames, workout_frames, schema_report

    for chunk in pd.read_csv(path, chunksize=chunk_size, low_memory=False):
        if sample_schema:
            normalized = normalize_samples(chunk, sample_schema)
            if not normalized.empty:
                normalized = _filter_window(normalized, start, end, "timestamp")
                if not normalized.empty:
                    sample_frames.append(normalized)
        if workout_schema:
            normalized_w = normalize_workouts(chunk, workout_schema)
            if not normalized_w.empty:
                normalized_w = _filter_window(normalized_w, start, end, "start_time")
                if not normalized_w.empty:
                    workout_frames.append(normalized_w)
    return sample_frames, workout_frames, schema_report


def load_data(
    input_path: Path,
    workout_input: Optional[Path],
    start: Optional[pd.Timestamp],
    end: Optional[pd.Timestamp],
    chunk_size: int = 50000,
) -> Tuple[pd.DataFrame, pd.DataFrame, List[SchemaReport]]:
    """Load samples and workouts from CSVs."""
    sample_frames: List[pd.DataFrame] = []
    workout_frames: List[pd.DataFrame] = []
    reports: List[SchemaReport] = []

    for path in _iter_csv_paths(input_path):
        s_frames, w_frames, report = _process_file(path, start, end, chunk_size)
        reports.append(report)
        sample_frames.extend(s_frames)
        workout_frames.extend(w_frames)

    if workout_input and workout_input != input_path:
        for path in _iter_csv_paths(workout_input):
            _, w_frames, report = _process_file(path, start, end, chunk_size)
            reports.append(report)
            workout_frames.extend(w_frames)

    samples = (
        pd.concat(sample_frames, ignore_index=True).sort_values("timestamp").reset_index(drop=True)
        if sample_frames
        else pd.DataFrame(columns=["timestamp", "bpm"])
    )
    workouts = (
        pd.concat(workout_frames, ignore_index=True).sort_values("start_time").reset_index(drop=True)
        if workout_frames
        else pd.DataFrame(columns=["start_time", "end_time", "workout_type"])
    )
    logger.info("Loaded %d heart rate samples and %d workouts", len(samples), len(workouts))
    return samples, workouts, reports


__all__ = ["load_data"]
