"""Sequential multi-checkpoint prediction endpoints (Phase 6)."""
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.features.practice import build_practice_snapshot
from backend.forecasting.engine import CheckpointForecastingEngine, get_forecasting_engine
from backend.forecasting.evaluator import SequentialForecastEvaluator, get_forecast_evaluator
from backend.forecasting.models import (
    CheckpointForecast,
    SequentialEvaluationReport,
)
from backend.models.event import Event
from backend.models.race_result import RaceResult

router = APIRouter(prefix="/predictions", tags=["predictions"])

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def _load_abu_dhabi_event_context() -> Tuple[List[dict], Dict[int, int], Dict[int, int], Optional[int], Dict[int, int]]:
    """Helper to load drivers, qualifying grid, penalty drops, true winner, and finish positions for Abu Dhabi 2024."""
    drivers_path = PROJECT_ROOT / "data" / "raw" / "openf1" / "drivers" / "9662.json"
    if not drivers_path.exists():
        return [], {}, {}, None, {}

    with open(drivers_path, "r", encoding="utf-8") as f:
        drivers_raw = json.load(f)

    drivers = [
        {
            "driver_number": d["driver_number"],
            "code": d.get("name_acronym", str(d["driver_number"])),
            "name": d.get("broadcast_name", d.get("full_name", f"Driver {d['driver_number']}")),
            "team": d.get("team_name", "Unknown"),
        }
        for d in drivers_raw
    ]

    # Provisional on-track qualifying classification (T4)
    provisional_grid = {
        4: 1, 81: 2, 55: 3, 27: 4, 1: 5, 10: 6, 63: 7, 14: 8, 77: 9, 11: 10,
        22: 11, 23: 12, 18: 13, 20: 14, 43: 15, 30: 16, 24: 17, 44: 18, 16: 19, 61: 20
    }
    # Official penalties confirmed before race start (T5):
    # Hulkenberg (27) served 3-place penalty (P4 -> P7), promoting Verstappen, Gasly, Russell
    # Colapinto (43) served 5-place power unit penalty (P15 -> P20)
    penalties = {27: 3, 43: 5}
    actual_winner = 4  # Norris
    actual_finishing_positions = {
        4: 1, 55: 2, 16: 3, 44: 4, 63: 5, 1: 6, 10: 7, 27: 8, 14: 9, 81: 10,
        23: 11, 22: 12, 24: 13, 18: 14, 61: 15, 20: 16, 30: 17, 77: 18, 43: 19, 11: 20
    }
    return drivers, provisional_grid, penalties, actual_winner, actual_finishing_positions


def _load_practice_data_for_abu_dhabi() -> Dict[str, tuple]:
    """Load cached FP1, FP2, FP3 laps & stints for Abu Dhabi 2024."""
    try:
        fp1_laps = json.load(open(PROJECT_ROOT / "data" / "raw" / "openf1" / "practice" / "fp1_9461_laps.json"))
        fp1_stints = json.load(open(PROJECT_ROOT / "data" / "raw" / "openf1" / "practice" / "fp1_9461_stints.json"))
        fp2_laps = json.load(open(PROJECT_ROOT / "data" / "raw" / "openf1" / "practice" / "fp2_9656_laps.json"))
        fp2_stints = json.load(open(PROJECT_ROOT / "data" / "raw" / "openf1" / "practice" / "fp2_9656_stints.json"))
        fp3_laps = json.load(open(PROJECT_ROOT / "data" / "raw" / "openf1" / "practice" / "fp3_9657_laps.json"))
        fp3_stints = json.load(open(PROJECT_ROOT / "data" / "raw" / "openf1" / "practice" / "fp3_9657_stints.json"))

        return {
            "FP1": (fp1_laps, fp1_stints, "2024-12-06T10:30:00+00:00"),
            "FP2": (fp2_laps, fp2_stints, "2024-12-06T14:00:00+00:00"),
            "FP3": (fp3_laps, fp3_stints, "2024-12-07T11:30:00+00:00"),
        }
    except Exception:
        return {}


@router.get("/events/{event_id}", response_model=List[CheckpointForecast])
def get_event_predictions(
    event_id: int,
    engine: CheckpointForecastingEngine = Depends(get_forecasting_engine),
):
    """Retrieve all chronological checkpoint predictions (T0 through T5) for a Grand Prix event."""
    if not isinstance(engine, CheckpointForecastingEngine):
        engine = get_forecasting_engine()
    drivers, prov_grid, penalties, _, _ = _load_abu_dhabi_event_context()
    if not drivers:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate driver context for event {event_id} not found",
        )

    sess_data = _load_practice_data_for_abu_dhabi()
    snap_t1 = build_practice_snapshot(2024, event_id, "Abu Dhabi GP", "T1_POST_FP1", "2024-12-06T11:00:00+00:00", sess_data) if sess_data else None
    snap_t2 = build_practice_snapshot(2024, event_id, "Abu Dhabi GP", "T2_POST_FP2", "2024-12-06T15:00:00+00:00", sess_data) if sess_data else None
    snap_t3 = build_practice_snapshot(2024, event_id, "Abu Dhabi GP", "T3_POST_FP3", "2024-12-07T12:00:00+00:00", sess_data) if sess_data else None

    fc_t0 = engine.generate_checkpoint_forecast(2024, event_id, "Abu Dhabi Grand Prix", "T0_PRE_WEEKEND", "2024-12-05T12:00:00+00:00", drivers)
    fc_t1 = engine.generate_checkpoint_forecast(2024, event_id, "Abu Dhabi Grand Prix", "T1_POST_FP1", "2024-12-06T11:00:00+00:00", drivers, practice_snapshot=snap_t1)
    fc_t2 = engine.generate_checkpoint_forecast(2024, event_id, "Abu Dhabi Grand Prix", "T2_POST_FP2", "2024-12-06T15:00:00+00:00", drivers, practice_snapshot=snap_t2)
    fc_t3 = engine.generate_checkpoint_forecast(2024, event_id, "Abu Dhabi Grand Prix", "T3_POST_FP3", "2024-12-07T12:00:00+00:00", drivers, practice_snapshot=snap_t3)
    fc_t4 = engine.generate_checkpoint_forecast(2024, event_id, "Abu Dhabi Grand Prix", "T4_POST_QUALIFYING", "2024-12-07T15:30:00+00:00", drivers, qualifying_grid=prov_grid)
    fc_t5 = engine.generate_checkpoint_forecast(
        2024, event_id, "Abu Dhabi Grand Prix", "T5_FINAL_PRE_RACE", "2024-12-08T12:00:00+00:00",
        drivers, qualifying_grid=prov_grid, penalty_drops=penalties,
        weather_forecast={"air_temp": 26.5, "track_temp": 32.0, "rain_prob": 0.0}
    )

    return [fc_t0, fc_t1, fc_t2, fc_t3, fc_t4, fc_t5]


@router.get("/events/{event_id}/checkpoints/{checkpoint}", response_model=CheckpointForecast)
def get_checkpoint_prediction(
    event_id: int,
    checkpoint: str,
    engine: CheckpointForecastingEngine = Depends(get_forecasting_engine),
):
    """Retrieve immutable probabilistic forecast for a single specified weekend checkpoint."""
    if not isinstance(engine, CheckpointForecastingEngine):
        engine = get_forecasting_engine()
    all_fcs = get_event_predictions(event_id=event_id, engine=engine)
    norm_cp = checkpoint.upper().strip()
    match = next((fc for fc in all_fcs if fc.checkpoint == norm_cp), None)
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Checkpoint '{checkpoint}' not found for event {event_id}",
        )
    return match


@router.get("/events/{event_id}/evaluation", response_model=SequentialEvaluationReport)
def evaluate_event_checkpoints(
    event_id: int,
    engine: CheckpointForecastingEngine = Depends(get_forecasting_engine),
    evaluator: SequentialForecastEvaluator = Depends(get_forecast_evaluator),
):
    """Evaluate sequential prediction quality (HYP-0001) across T0-T5 against observed race outcome."""
    if not isinstance(engine, CheckpointForecastingEngine):
        engine = get_forecasting_engine()
    if not isinstance(evaluator, SequentialForecastEvaluator):
        evaluator = get_forecast_evaluator()
    forecasts = get_event_predictions(event_id=event_id, engine=engine)
    _, _, _, actual_winner, finishing_positions = _load_abu_dhabi_event_context()
    if actual_winner is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ground truth winner not available for event {event_id}",
        )

    return evaluator.evaluate_checkpoints(
        checkpoint_forecasts=forecasts,
        actual_winner_driver_number=actual_winner,
        actual_finishing_positions=finishing_positions,
        evaluation_cohort_label="2024 Abu Dhabi Grand Prix (Primary Demonstration)",
    )
