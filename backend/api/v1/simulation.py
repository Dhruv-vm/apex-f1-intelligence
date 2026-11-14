"""APEX — REST API v1 Simulation Endpoints (Phase 7.1 / EXP-0006-R2).

Exposes Monte Carlo race simulation and counterfactual strategy dynamics endpoints,
featuring background task execution for large iteration runs, run progress polling,
and explicit parameter classifications.
"""
from concurrent.futures import ThreadPoolExecutor
import copy
from typing import Any, Dict, List, Optional
import uuid
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, status
from pydantic import BaseModel, Field

from backend.simulation.counterfactual import CounterfactualComparisonReport, CounterfactualEngine
from backend.simulation.forecasting_bridge import CIRCUIT_PROFILES, ForecastingBridge
from backend.simulation.monte_carlo import MonteCarloSimulator, SimulationRunResult
from backend.simulation.state import TrackCondition, TyreCompound
from backend.simulation.strategy import (
    OneStopStrategy,
    OvercutStrategy,
    SafetyCarReactiveStrategy,
    TwoStopStrategy,
    UndercutStrategy,
)

router = APIRouter(prefix="/simulation", tags=["simulation"])

# In-memory storage for executed simulation runs and background jobs
_SIMULATION_RUNS: Dict[str, SimulationRunResult] = {}
_COUNTERFACTUAL_RUNS: Dict[str, CounterfactualComparisonReport] = {}
_SIMULATION_JOBS: Dict[str, Dict[str, Any]] = {}

_executor = ThreadPoolExecutor(max_workers=4)

bridge = ForecastingBridge()
simulator = MonteCarloSimulator()
cf_engine = CounterfactualEngine()


class CreateSimulationRunRequest(BaseModel):
    season: int = Field(default=2024, ge=2010, le=2026)
    round_num: int = Field(default=24, ge=1, le=25)
    n_iterations: int = Field(default=100, ge=10, le=10000)
    master_seed: int = Field(default=42)
    track_condition: TrackCondition = Field(default=TrackCondition.DRY)
    async_mode: bool = Field(default=False)


class CounterfactualRequest(BaseModel):
    season: int = Field(default=2024, ge=2010, le=2026)
    round_num: int = Field(default=24, ge=1, le=25)
    target_driver_id: str = Field(default="norris")
    n_iterations: int = Field(default=100, ge=10, le=10000)
    master_seed: int = Field(default=42)
    track_condition: TrackCondition = Field(default=TrackCondition.DRY)
    async_mode: bool = Field(default=False)


class JobStatusResponse(BaseModel):
    job_id: str
    job_type: str  # "SIMULATION_RUN" or "COUNTERFACTUAL"
    status: str    # "PENDING", "RUNNING", "COMPLETED", "FAILED"
    progress_pct: float
    result: Optional[Any] = None
    error: Optional[str] = None


@router.get("/circuits")
def list_simulation_circuits() -> List[Dict[str, Any]]:
    """List all available circuit profiles with calibrated simulation parameters."""
    return [
        {
            "circuit_id": p.circuit_id,
            "circuit_name": p.circuit_name,
            "total_laps": p.total_laps,
            "base_lap_time_seconds": p.base_lap_time_seconds,
            "pit_transit_loss_seconds": p.pit_transit_loss_seconds,
            "overtaking_difficulty_index": p.overtaking_difficulty_index,
            "safety_car_hazard_rate": p.safety_car_hazard_rate_per_lap,
        }
        for p in CIRCUIT_PROFILES.values()
    ]


@router.get("/parameters")
def get_parameter_modality_classifications() -> Dict[str, Any]:
    """
    Returns explicit epistemological classifications for all simulator parameters
    (Observed, Empirically Estimated, Assumed, User-Configured, Synthetic).
    """
    return {
        "observed": [
            {"parameter": "starting_grid", "description": "Starting grid position from official qualifying/grid classifications", "source": "Jolpica / FIA Official Documents"},
            {"parameter": "circuit_geometry", "description": "Circuit length, lap count, and turn configurations", "source": "FIA Circuit Homologation"},
            {"parameter": "historical_dnf_frequency", "description": "Historical race retirement frequencies per circuit (2010-2024)", "source": "APEX Historical Classification Dataset"},
        ],
        "empirically_estimated": [
            {"parameter": "pit_stationary_service", "description": "Stationary wheel-change distribution N(2.45s, 0.35s)", "source": "DHL Fastest Pit Stop Historical Distribution"},
            {"parameter": "circuit_pit_transit_loss", "description": "Pit entry-to-exit transit duration minus straightaway racing time", "source": "OpenF1 Timing Loop Calibration"},
            {"parameter": "sc_transit_discount", "description": "~50% transit time discount under Full SC (~10.0s saved)", "source": "SC Speed Delta Lap Comparison"},
            {"parameter": "vsc_transit_discount", "description": "~35% transit time discount under VSC (~7.0s saved)", "source": "VSC Speed Delta Lap Comparison"},
            {"parameter": "constructor_reliability_multipliers", "description": "Component failure hazard multipliers derived from historical DNF records", "source": "2010-2024 Constructor Failure Logs"},
        ],
        "assumed": [
            {"parameter": "initial_fuel_mass_kg", "value": 105.0, "status": "Latent unmeasured parameter in timing feeds"},
            {"parameter": "fuel_burn_rate_kg_per_lap", "value": 1.75, "status": "Latent parameter (approx 100-105kg / 55-60 laps)"},
            {"parameter": "fuel_lap_time_sensitivity_sec_per_kg", "value": 0.033, "status": "Standard motorsport rule-of-thumb (~0.33s per 10kg)"},
            {"parameter": "track_evolution_gain_per_lap", "value": 0.012, "status": "Surface grip evolution model"},
            {"parameter": "dirty_air_cornering_penalty_sec", "value": 0.25, "status": "Aerodynamic wake turbulence penalty"},
        ],
        "user_configured": [
            "n_iterations",
            "master_seed",
            "track_condition",
            "target_driver_id",
            "candidate_strategies",
        ],
        "synthetic": [
            "simulated_lap_times",
            "simulated_positions",
            "simulated_pit_stops",
            "win_podium_probabilities",
        ],
    }


def _run_simulation_job(job_id: str, req: CreateSimulationRunRequest, race_state: Any) -> None:
    try:
        _SIMULATION_JOBS[job_id]["status"] = "RUNNING"

        def on_progress(current: int, total: int):
            pct = round((current / total) * 100.0, 1)
            _SIMULATION_JOBS[job_id]["progress_pct"] = pct

        res = simulator.run_simulations(
            base_race_state=race_state,
            n_iterations=req.n_iterations,
            master_seed=req.master_seed,
            run_id=job_id,
            progress_callback=on_progress,
        )
        _SIMULATION_RUNS[job_id] = res
        _SIMULATION_JOBS[job_id]["status"] = "COMPLETED"
        _SIMULATION_JOBS[job_id]["progress_pct"] = 100.0
        _SIMULATION_JOBS[job_id]["result"] = res.model_dump()
    except Exception as e:
        _SIMULATION_JOBS[job_id]["status"] = "FAILED"
        _SIMULATION_JOBS[job_id]["error"] = str(e)


def _run_counterfactual_job(job_id: str, req: CounterfactualRequest, race_state: Any, strategies: Dict[str, Any]) -> None:
    try:
        _SIMULATION_JOBS[job_id]["status"] = "RUNNING"
        cf_report = cf_engine.compare_strategies(
            base_race_state=race_state,
            target_driver_id=req.target_driver_id,
            strategies_to_test=strategies,
            n_simulations=req.n_iterations,
            master_seed=req.master_seed,
            compute_out_of_sample_validation=(req.n_iterations >= 200),
        )
        _COUNTERFACTUAL_RUNS[job_id] = cf_report
        _SIMULATION_JOBS[job_id]["status"] = "COMPLETED"
        _SIMULATION_JOBS[job_id]["progress_pct"] = 100.0
        _SIMULATION_JOBS[job_id]["result"] = cf_report.dict()
    except Exception as e:
        _SIMULATION_JOBS[job_id]["status"] = "FAILED"
        _SIMULATION_JOBS[job_id]["error"] = str(e)


@router.post("/runs")
def create_simulation_run(
    req: CreateSimulationRunRequest,
    background_tasks: BackgroundTasks,
) -> Any:
    """
    Executes a Monte Carlo race simulation run.
    Supports asynchronous execution for long-running batches without blocking the event loop.
    """
    try:
        race_state = bridge.build_initial_race_state(
            season=req.season,
            round_num=req.round_num,
            track_condition=req.track_condition,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Could not initialize race simulation: {str(e)}",
        )

    run_id = f"sim_{req.season}_{req.round_num}_{uuid.uuid4().hex[:8]}"

    if req.async_mode or req.n_iterations > 500:
        _SIMULATION_JOBS[run_id] = {
            "job_id": run_id,
            "job_type": "SIMULATION_RUN",
            "status": "PENDING",
            "progress_pct": 0.0,
            "result": None,
            "error": None,
        }
        _executor.submit(_run_simulation_job, run_id, req, race_state)
        return {
            "job_id": run_id,
            "status": "PENDING",
            "message": f"Simulation job '{run_id}' submitted in background ({req.n_iterations} iterations).",
        }

    # Synchronous execution for small iterations
    result = simulator.run_simulations(
        base_race_state=race_state,
        n_iterations=req.n_iterations,
        master_seed=req.master_seed,
        run_id=run_id,
    )
    _SIMULATION_RUNS[run_id] = result
    return result


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
def get_simulation_job_status(job_id: str) -> JobStatusResponse:
    """Poll the status and progress of an asynchronous simulation job."""
    if job_id not in _SIMULATION_JOBS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' not found.",
        )
    job = _SIMULATION_JOBS[job_id]
    return JobStatusResponse(**job)


@router.get("/runs/{run_id}", response_model=SimulationRunResult)
def get_simulation_run(run_id: str) -> SimulationRunResult:
    """Retrieve metadata and candidate distributions for a specific simulation run."""
    if run_id not in _SIMULATION_RUNS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Simulation run '{run_id}' not found.",
        )
    return _SIMULATION_RUNS[run_id]


@router.get("/runs/{run_id}/results")
def get_simulation_results_summary(run_id: str) -> Dict[str, Any]:
    """Retrieve high-level probabilities and confidence intervals for a simulation run."""
    if run_id not in _SIMULATION_RUNS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Simulation run '{run_id}' not found.",
        )
    res = _SIMULATION_RUNS[run_id]
    return {
        "run_id": res.run_id,
        "circuit_name": res.circuit_name,
        "n_iterations": res.n_iterations,
        "most_likely_winner": res.most_likely_winner,
        "winner_win_probability": res.winner_win_probability,
        "candidates": [
            {
                "driver_id": c.driver_id,
                "driver_name": c.driver_name,
                "constructor_id": c.constructor_id,
                "starting_grid": c.starting_grid,
                "expected_finish_position": c.expected_finish_position,
                "win_probability": c.win_probability,
                "win_probability_ci_95": c.win_probability_ci_95,
                "podium_probability": c.podium_probability,
                "podium_probability_ci_95": c.podium_probability_ci_95,
                "top5_probability": c.top5_probability,
                "top5_probability_ci_95": c.top5_probability_ci_95,
            }
            for c in res.candidates
        ],
    }


@router.get("/runs/{run_id}/distribution")
def get_simulation_position_distribution(run_id: str) -> Dict[str, Any]:
    """Retrieve full finishing position probability distributions for all drivers."""
    if run_id not in _SIMULATION_RUNS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Simulation run '{run_id}' not found.",
        )
    res = _SIMULATION_RUNS[run_id]
    return {
        "run_id": res.run_id,
        "distributions": {
            c.driver_id: {
                "name": c.driver_name,
                "expected_position": c.expected_finish_position,
                "position_distribution": c.position_distribution,
            }
            for c in res.candidates
        },
    }


@router.post("/counterfactual")
def run_counterfactual_comparison(
    req: CounterfactualRequest,
    background_tasks: BackgroundTasks,
) -> Any:
    """
    Executes a counterfactual comparison of multiple pit strategies on identical race seeds (CRN).
    Supports asynchronous execution for large iterations.
    """
    try:
        race_state = bridge.build_initial_race_state(
            season=req.season,
            round_num=req.round_num,
            track_condition=req.track_condition,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Could not initialize race for counterfactual comparison: {str(e)}",
        )

    if req.target_driver_id not in race_state.drivers:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Driver '{req.target_driver_id}' not found in entrant list for season {req.season} round {req.round_num}",
        )

    strategies = {
        "Reference_1Stop_M_H": OneStopStrategy(target_pit_lap=22, secondary_compound=TyreCompound.HARD),
        "Aggressive_2Stop_S_H_M": TwoStopStrategy(stop1_lap=15, stop2_lap=38),
        "Tactical_Undercut": UndercutStrategy(base_window_start=18, base_window_end=22),
        "Tactical_Overcut": OvercutStrategy(nominal_pit_lap=22, overcut_extension_laps=4),
        "SafetyCar_Reactive": SafetyCarReactiveStrategy(fallback_pit_lap=26),
    }

    job_id = f"cf_{req.season}_{req.round_num}_{req.target_driver_id}_{uuid.uuid4().hex[:6]}"

    if req.async_mode or req.n_iterations > 500:
        _SIMULATION_JOBS[job_id] = {
            "job_id": job_id,
            "job_type": "COUNTERFACTUAL",
            "status": "PENDING",
            "progress_pct": 0.0,
            "result": None,
            "error": None,
        }
        _executor.submit(_run_counterfactual_job, job_id, req, race_state, strategies)
        return {
            "job_id": job_id,
            "status": "PENDING",
            "message": f"Counterfactual job '{job_id}' submitted in background ({req.n_iterations} iterations).",
        }

    cf_report = cf_engine.compare_strategies(
        base_race_state=race_state,
        target_driver_id=req.target_driver_id,
        strategies_to_test=strategies,
        n_simulations=req.n_iterations,
        master_seed=req.master_seed,
        compute_out_of_sample_validation=False,
    )
    _COUNTERFACTUAL_RUNS[job_id] = cf_report
    return cf_report
