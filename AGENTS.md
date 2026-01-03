# AGENTS.md — Codex Agent Instructions

## Mission
Implement a local-only Python CLI tool per PRD.md.

---

## Hard Rules

- **No network calls.**
- No telemetry or uploads.
- Do not log raw PHI.
- Deterministic behavior required.

---

## Project Structure

health_hr_analyzer/
- cli.py
- ingest.py
- incidents.py
- workouts.py
- classify.py
- report.py

tests/
- test_incidents.py
- test_overlap.py

---

## Implementation Guidance

### CSV Handling
- Support file or directory input.
- Use pandas with chunked reads.
- Filter by time window early.

### Incident Detection
- Group samples using gap rule.
- Compute summary stats per incident.

### Workout Classification
- Prefer explicit workouts.
- Fallback inference with confidence labels.

### Reporting
- Output CSV + PNG.
- Clear legends and labels.

---

## Testing
- Synthetic test data only.
- No real health data in repo.

---

## Definition of Done
- CLI works end-to-end.
- Outputs correct files.
- Tests pass.
