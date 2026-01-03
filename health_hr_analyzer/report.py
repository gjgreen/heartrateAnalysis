"""Reporting helpers for CSV and PNG outputs."""

from __future__ import annotations

from pathlib import Path
from typing import Mapping

import matplotlib.pyplot as plt
import pandas as pd


def write_incidents_csv(incidents: pd.DataFrame, output_dir: Path, filename: str = "incidents_over_140.csv") -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / filename
    incidents.to_csv(output_path, index=False)
    return output_path


def plot_incidents(
    incidents: pd.DataFrame,
    output_dir: Path,
    filename: str = "incidents_over_140.png",
    color_map: Mapping[str, str] | None = None,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / filename

    cmap = color_map or {"workout": "tab:green", "unknown": "tab:gray", "non_workout": "tab:orange"}
    fig, ax = plt.subplots(figsize=(10, 5))
    if incidents.empty:
        ax.text(0.5, 0.5, "No incidents detected", ha="center", va="center", transform=ax.transAxes)
    else:
        classes = incidents["classification"].fillna("unknown")
        durations_minutes = incidents["duration_seconds"] / 60.0
        colors = [cmap.get(cls, "tab:blue") for cls in classes]
        ax.scatter(incidents["start_time"], durations_minutes, c=colors, alpha=0.8)
        ax.set_ylabel("Duration (minutes)")
        ax.set_xlabel("Incident start time")
        ax.set_title("Heart rate incidents over threshold")
        # Build legend from unique classifications
        unique_classes = list(dict.fromkeys(classes))
        handles = [
            plt.Line2D([0], [0], marker="o", color="w", label=cls, markerfacecolor=cmap.get(cls, "tab:blue"), markersize=8)
            for cls in unique_classes
        ]
        ax.legend(handles=handles, title="Classification", loc="best")
        fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)
    return output_path


def plot_incident_pie(
    incidents: pd.DataFrame,
    output_dir: Path,
    filename: str = "incidents_over_140_pie.png",
    color_map: Mapping[str, str] | None = None,
) -> Path:
    """Plot a pie chart of incidents by classification with counts and percentages."""
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / filename
    cmap = color_map or {"workout": "tab:green", "unknown": "tab:gray", "non_workout": "tab:orange"}

    fig, ax = plt.subplots(figsize=(6, 6))
    if incidents.empty:
        ax.text(0.5, 0.5, "No incidents detected", ha="center", va="center", transform=ax.transAxes)
    else:
        counts = incidents["classification"].fillna("unknown").value_counts()
        total = counts.sum()
        labels = [f"{cls} ({cnt}, {cnt/total:.1%})" for cls, cnt in counts.items()]
        colors = [cmap.get(cls, "tab:blue") for cls in counts.index]
        ax.pie(counts, labels=labels, colors=colors, autopct=None, startangle=90)
        ax.set_title("Incident classification breakdown")
    fig.tight_layout()
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)
    return output_path


__all__ = ["write_incidents_csv", "plot_incidents", "plot_incident_pie"]
