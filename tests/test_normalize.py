import pandas as pd

from health_hr_analyzer.normalize import WorkoutSchema, detect_workout_schema, normalize_workouts
from health_hr_analyzer.normalize import SampleSchema, detect_sample_schema, normalize_samples


def test_normalize_workouts_strips_timezone():
    data = pd.DataFrame(
        {
            "startDate": ["2024-01-01T00:00:00+00:00"],
            "endDate": ["2024-01-01T01:00:00+00:00"],
            "workoutActivityType": ["running"],
        }
    )
    schema = WorkoutSchema(start="startDate", end="endDate", workout_type="workoutActivityType")
    normalized = normalize_workouts(data, schema)
    assert normalized["start_time"].dt.tz is None
    assert normalized["end_time"].dt.tz is None


def test_detect_workout_schema_requires_type_column():
    hr_like = pd.DataFrame(
        {
            "startDate": ["2024-01-01T00:00:00"],
            "endDate": ["2024-01-01T00:01:00"],
            "value": [140],
        }
    )
    assert detect_workout_schema(hr_like) is None


def test_detect_sample_schema_filters_to_heart_rate_type():
    data = pd.DataFrame(
        {
            "startDate": ["2024-01-01T00:00:00", "2024-01-01T00:05:00"],
            "value": [80, 90],
            "type": ["HKQuantityTypeIdentifierHeartRate", "HKQuantityTypeIdentifierStepCount"],
        }
    )
    schema = detect_sample_schema(data)
    assert schema is not None
    assert schema.type_column == "type"
    normalized = normalize_samples(data, schema)
    assert len(normalized) == 1
    assert normalized.iloc[0]["bpm"] == 80


def test_detect_sample_schema_sparse_bpm_column():
    data = pd.DataFrame(
        {
            "startDate": ["2024-01-01T00:00:00", "2024-01-01T00:05:00", "2024-01-01T00:10:00"],
            "bpm": [None, None, 150],
            "type": ["OxygenSaturation", "ActiveEnergyBurned", "HeartRate"],
        }
    )
    schema = detect_sample_schema(data)
    assert schema is not None
    normalized = normalize_samples(data, schema)
    assert len(normalized) == 1
    assert normalized.iloc[0]["bpm"] == 150


def test_detect_sample_schema_uses_value_when_bpm_empty():
    data = pd.DataFrame(
        {
            "startDate": ["2024-01-01T00:00:00"],
            "value": [72],
            "bpm": [None],
            "type": ["HeartRate"],
        }
    )
    schema = detect_sample_schema(data)
    assert schema is not None
    assert schema.bpm == "value"


def test_detect_sample_schema_with_mixed_value_ranges_and_types():
    data = pd.DataFrame(
        {
            "startDate": ["2024-01-01T00:00:00", "2024-01-01T00:01:00"],
            "value": [72, 0.94],
            "type": ["HeartRate", "OxygenSaturation"],
        }
    )
    schema = detect_sample_schema(data)
    assert schema is not None
    normalized = normalize_samples(data, schema)
    assert len(normalized) == 1
    assert normalized.iloc[0]["bpm"] == 72


def test_detect_workout_schema_prefers_workout_activity_type_column():
    data = pd.DataFrame(
        {
            "startDate": ["2024-01-01T00:00:00"],
            "endDate": ["2024-01-01T01:00:00"],
            "workoutActivityType": ["HKWorkoutActivityTypeRunning"],
        }
    )
    schema = detect_workout_schema(data)
    assert schema is not None
    assert schema.workout_type == "workoutActivityType"
    normalized = normalize_workouts(data, schema)
    assert len(normalized) == 1
    assert normalized.iloc[0]["workout_type"] == "HKWorkoutActivityTypeRunning"
