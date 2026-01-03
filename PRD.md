# PRD — Apple Health Heart Rate Incident Analysis (Local-Only)

## 1. Overview

We need a local-only Python tool that analyzes an exported Apple Health dataset in CSV form (~500MB) and identifies heart-rate “incidents” where the user’s heart rate exceeds **140 bpm** within the **last 9 months**.

The tool must:
- Parse large CSV(s) efficiently using Pandas (chunking supported).
- Detect >140 bpm episodes and group them into incidents.
- Classify incidents as occurring during workouts or normal activity.
- Output a clean CSV summary and a static graph.

**Privacy requirement:** all processing must occur locally. No network access, telemetry, or uploads.

---

## 2. Goals

### Primary goals
- Identify all heart-rate incidents with HR > 140 bpm.
- Group samples into meaningful incident episodes.
- Classify incidents as workout vs non-workout.
- Produce a digestible CSV and a readable plot.

### Secondary goals
- Handle unknown CSV schemas robustly.
- Support very large exports (~500MB).
- Provide transparent confidence scoring for workout classification.

---

## 3. Non-Goals
- No medical diagnosis.
- No UI beyond CLI.
- No cloud or remote processing.

---

## 4. Inputs

- Apple Health CSV export (single file or directory).
- Heart-rate samples.
- Workout records (if present).
- Optional activity signals (steps, energy).

Schema is not guaranteed and must be inferred.

---

## 5. Outputs

### 5.1 CSV
`incidents_over_140.csv` with one row per incident.

Required fields:
- incident_id
- start_time
- end_time
- duration_seconds
- max_bpm
- avg_bpm
- sample_count
- classification
- workout_confidence
- workout_type
- overlap_seconds
- notes

### 5.2 Plot
`incidents_over_140.png` visualizing incidents over time, color-coded by classification.

---

## 6. Core Logic

### Time window
Default: last 9 months relative to run time.
Overrides via CLI supported.

### Incident detection
- Threshold: bpm > 140 (configurable).
- Samples within 120 seconds belong to the same incident.

### Workout classification
- Explicit workout overlap → high confidence.
- Inferred activity → medium/low confidence.
- Otherwise → unknown.

---

## 7. Functional Requirements

- Local-only processing.
- Chunked CSV ingestion.
- Deterministic output.
- Graceful handling of missing data.

---

## 8. Non-Functional Requirements

- Privacy-safe logging.
- Robust to schema variation.
- Maintainable modular code.

---

## 9. Acceptance Criteria

- Generates CSV and PNG.
- No network access.
- Works on large datasets.
