"""Command line interface for the Apple Health heart rate analyzer."""

from __future__ import annotations

import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
from dateutil.relativedelta import relativedelta

from . import incidents, report
from .classify import classify_incidents
from .ingest import load_data

logger = logging.getLogger(__name__)


def _parse_date(value: Optional[str]) -> Optional[pd.Timestamp]:
    if not value:
        return None
    ts = pd.to_datetime(value, errors="coerce")
    if ts is pd.NaT:
        return None
    if ts.tzinfo is not None:
        ts = ts.tz_convert(None)
    return ts


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Local-only Apple Health heart rate incident analyzer.")
    parser.add_argument("-i", "--input", required=True, help="Path to Apple Health CSV file or directory.")
    parser.add_argument("--workouts-input", help="Optional path to workouts CSV or directory.")
    parser.add_argument("-o", "--output-dir", default="output", help="Directory for generated outputs.")
    parser.add_argument("--threshold", type=float, default=140.0, help="BPM threshold for incidents.")
    parser.add_argument("--gap-seconds", type=int, default=120, help="Gap (seconds) to join samples into one incident.")
    parser.add_argument(
        "--min-duration-seconds",
        type=float,
        default=0.0,
        help="Drop incidents shorter than this duration.",
    )
    parser.add_argument(
        "--overlap-min-seconds",
        type=float,
        default=1.0,
        help="Minimum overlap with workouts to classify as workout.",
    )
    parser.add_argument("--start-date", help="Optional ISO date to start analysis window.")
    parser.add_argument("--end-date", help="Optional ISO date to end analysis window (default: now).")
    parser.add_argument("--chunk-size", type=int, default=50000, help="CSV chunk size for pandas.")
    parser.add_argument("--csv-name", default="incidents_over_140.csv", help="Output CSV filename.")
    parser.add_argument("--png-name", default="incidents_over_140.png", help="Output plot filename.")
    parser.add_argument("--pie-name", default="incidents_over_140_pie.png", help="Output pie chart filename.")
    parser.add_argument("--schema-report", action="store_true", help="Print detected schema mappings and exit.")
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (summary only; no raw data).",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO), format="%(levelname)s %(message)s")
    input_path = Path(args.input)
    workout_input = Path(args.workouts_input) if args.workouts_input else None

    end_date = _parse_date(args.end_date) or pd.Timestamp(datetime.now())
    start_date = _parse_date(args.start_date) or (end_date - relativedelta(months=9))
    if start_date > end_date:
        parser.error("start-date must be before or equal to end-date")

    logger.info(
        "Analyzing input=%s workouts=%s window=%s to %s threshold=%.1f gap=%ss",
        input_path,
        workout_input or "auto",
        start_date,
        end_date,
        args.threshold,
        args.gap_seconds,
    )

    samples, workouts_df, schema_reports = load_data(
        input_path=input_path,
        workout_input=workout_input,
        start=start_date,
        end=end_date,
        chunk_size=args.chunk_size,
    )

    if args.schema_report:
        for report_entry in schema_reports:
            logger.info("Schema for %s: samples=%s workouts=%s", report_entry["path"], report_entry["sample_schema"], report_entry["workout_schema"])
        if not samples.empty:
            logger.info("Detected %d samples in analysis window.", len(samples))
        if not workouts_df.empty:
            logger.info("Detected %d workouts in analysis window.", len(workouts_df))
        return

    incidents_df = incidents.detect_incidents(
        samples=samples,
        threshold_bpm=args.threshold,
        gap_seconds=args.gap_seconds,
        min_duration_seconds=args.min_duration_seconds,
    )
    logger.info("Found %d incidents above threshold", len(incidents_df))

    classified = classify_incidents(
        incidents=incidents_df,
        workouts=workouts_df,
        min_overlap_seconds=args.overlap_min_seconds,
    )

    output_dir = Path(args.output_dir)
    csv_path = report.write_incidents_csv(classified, output_dir=output_dir, filename=args.csv_name)
    png_path = report.plot_incidents(classified, output_dir=output_dir, filename=args.png_name)
    pie_path = report.plot_incident_pie(classified, output_dir=output_dir, filename=args.pie_name)
    logger.info("Wrote incident summary to %s", csv_path)
    logger.info("Wrote incident plot to %s", png_path)
    logger.info("Wrote incident classification pie to %s", pie_path)


if __name__ == "__main__":  # pragma: no cover
    main()
