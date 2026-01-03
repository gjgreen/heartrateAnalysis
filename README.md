# Apple Health Heart Rate Incident Analyzer

A **local-only** Python tool for analyzing Apple Health CSV exports to identify **heart-rate incidents above 140 bpm**.

## Features
- Local-only processing
- Large CSV support
- Incident grouping
- Workout-aware classification
- CSV + PNG outputs

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
python -m health_hr_analyzer   --input /path/to/export   --output-dir ./output
```

## Outputs

- incidents_over_140.csv
- incidents_over_140.png

## Privacy

All processing is local. No data leaves your machine.

## Disclaimer

Not a medical device. Informational use only.
