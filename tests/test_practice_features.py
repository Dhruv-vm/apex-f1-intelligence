"""Unit tests for FP1/FP2/FP3 practice intelligence and sequential snapshots."""
import json
from pathlib import Path
import pytest

from backend.features.practice import (
    TemporalLeakageError,
    build_practice_snapshot,
    compute_linear_slope,
    extract_session_practice_features,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def sample_fp1_data():
    laps_path = PROJECT_ROOT / "data" / "raw" / "openf1" / "practice" / "fp1_9461_laps.json"
    stints_path = PROJECT_ROOT / "data" / "raw" / "openf1" / "practice" / "fp1_9461_stints.json"
    with open(laps_path, "r", encoding="utf-8") as f:
        laps = json.load(f)
    with open(stints_path, "r", encoding="utf-8") as f:
        stints = json.load(f)
    return laps, stints


def test_linear_slope_computation():
    # Constant pace = 0 degradation
    assert compute_linear_slope([1.0, 2.0, 3.0], [90.0, 90.0, 90.0]) == 0.0
    # Positive degradation (+0.1s / lap)
    assert compute_linear_slope([1.0, 2.0, 3.0], [90.0, 90.1, 90.2]) == pytest.approx(0.1, abs=1e-3)


def test_extract_practice_features_norris(sample_fp1_data):
    laps, stints = sample_fp1_data
    features = extract_session_practice_features(laps, stints)

    assert 4 in features  # Norris
    norris = features[4]
    assert norris.single_lap.best_lap_time is not None
    assert norris.single_lap.best_lap_time < 90.0
    assert norris.single_lap.lap_count_total == 25
    assert norris.single_lap.lap_count_clean > 10
    assert norris.single_lap.out_in_laps_count > 0
    assert norris.single_lap.sector_1_best is not None
    assert norris.single_lap.sector_2_best is not None
    assert norris.single_lap.sector_3_best is not None
    assert norris.single_lap.theoretical_best_lap <= norris.single_lap.best_lap_time

    # Stints and race simulation identification
    assert len(norris.stints) > 0
    assert norris.primary_race_sim_stint is not None
    assert norris.primary_race_sim_stint.stint_length_laps >= 7
    assert norris.primary_race_sim_stint.is_race_simulation is True
    assert norris.primary_race_sim_stint.degradation_slope_sec_per_lap is not None


def test_sequential_practice_snapshots_and_anti_leakage(sample_fp1_data):
    fp1_laps, fp1_stints = sample_fp1_data
    fp2_laps_path = PROJECT_ROOT / "data" / "raw" / "openf1" / "practice" / "fp2_9656_laps.json"
    fp2_stints_path = PROJECT_ROOT / "data" / "raw" / "openf1" / "practice" / "fp2_9656_stints.json"
    with open(fp2_laps_path, "r", encoding="utf-8") as f:
        fp2_laps = json.load(f)
    with open(fp2_stints_path, "r", encoding="utf-8") as f:
        fp2_stints = json.load(f)

    sessions_data = {
        "FP1": (fp1_laps, fp1_stints, "2024-12-06T10:30:00+00:00"),
        "FP2": (fp2_laps, fp2_stints, "2024-12-06T14:00:00+00:00"),
    }

    # Valid T1 snapshot
    snap_t1 = build_practice_snapshot(
        season=2024,
        event_id=1,
        event_name="Abu Dhabi Grand Prix",
        checkpoint="T1_POST_FP1",
        cutoff_iso="2024-12-06T11:00:00+00:00",
        sessions_data=sessions_data,
    )
    assert snap_t1.checkpoint == "T1_POST_FP1"
    assert snap_t1.included_sessions == ["FP1"]
    assert "4" in snap_t1.driver_features

    # Valid T2 snapshot
    snap_t2 = build_practice_snapshot(
        season=2024,
        event_id=1,
        event_name="Abu Dhabi Grand Prix",
        checkpoint="T2_POST_FP2",
        cutoff_iso="2024-12-06T14:30:00+00:00",
        sessions_data=sessions_data,
    )
    assert snap_t2.checkpoint == "T2_POST_FP2"
    assert snap_t2.included_sessions == ["FP1", "FP2"]

    # Strict Anti-Leakage Test: Cutoff timestamp occurs BEFORE session ended
    with pytest.raises(TemporalLeakageError) as exc_info:
        build_practice_snapshot(
            season=2024,
            event_id=1,
            event_name="Abu Dhabi Grand Prix",
            checkpoint="T1_POST_FP1",
            cutoff_iso="2024-12-06T09:30:00+00:00",  # Cutoff set before FP1 end!
            sessions_data=sessions_data,
        )
    assert "Temporal leakage detected" in str(exc_info.value)
