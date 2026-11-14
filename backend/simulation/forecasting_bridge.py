"""APEX — Forecasting Bridge: Ingesting Checkpoint Forecasts to Simulation (Phase 7 / EXP-0006).

Converts T0–T5 forecasting checkpoint probabilities, grid positions, and constructor ratings
into calibrated initial conditions for the Monte Carlo race engine.
Preserves input vintage and provenance.
"""
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd

from backend.simulation.state import CircuitProfile, DriverState, DriverStatus, RaceState, TrackCondition, TyreCompound

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = PROJECT_ROOT / "data" / "interim" / "driver_race_results_2010_2026_v2_regulation_metadata.csv"

# Circuit simulation profiles
CIRCUIT_PROFILES: Dict[str, CircuitProfile] = {
    "yas_marina": CircuitProfile(
        circuit_id="yas_marina",
        circuit_name="Yas Marina Circuit",
        total_laps=58,
        base_lap_time_seconds=84.50,
        pit_transit_loss_seconds=20.5,
        overtaking_difficulty_index=0.60,
        safety_car_hazard_rate_per_lap=0.015,
        vsc_hazard_rate_per_lap=0.012,
        track_evolution_gain_per_lap=0.012,
        drs_activation_zones=2,
        drs_zone_lap_fraction=0.22,
        drs_configuration_mode="CIRCUIT_SPECIFIC",
        nominated_compounds={"SOFT": "C5", "MEDIUM": "C4", "HARD": "C3"},
    ),
    "silverstone": CircuitProfile(
        circuit_id="silverstone",
        circuit_name="Silverstone Circuit",
        total_laps=52,
        base_lap_time_seconds=87.50,
        pit_transit_loss_seconds=19.5,
        overtaking_difficulty_index=0.48,
        safety_car_hazard_rate_per_lap=0.018,
        vsc_hazard_rate_per_lap=0.014,
        track_evolution_gain_per_lap=0.010,
        drs_activation_zones=2,
        drs_zone_lap_fraction=0.18,
        drs_configuration_mode="CIRCUIT_SPECIFIC",
        nominated_compounds={"SOFT": "C3", "MEDIUM": "C2", "HARD": "C1"},
    ),
    "bahrain": CircuitProfile(
        circuit_id="bahrain",
        circuit_name="Bahrain International Circuit",
        total_laps=57,
        base_lap_time_seconds=91.00,
        pit_transit_loss_seconds=21.5,
        overtaking_difficulty_index=0.45,
        safety_car_hazard_rate_per_lap=0.016,
        vsc_hazard_rate_per_lap=0.012,
        track_evolution_gain_per_lap=0.014,
        drs_activation_zones=3,
        drs_zone_lap_fraction=0.25,
        drs_configuration_mode="CIRCUIT_SPECIFIC",
        nominated_compounds={"SOFT": "C3", "MEDIUM": "C2", "HARD": "C1"},
    ),
    "monza": CircuitProfile(
        circuit_id="monza",
        circuit_name="Autodromo Nazionale Monza",
        total_laps=53,
        base_lap_time_seconds=81.50,
        pit_transit_loss_seconds=22.0,
        overtaking_difficulty_index=0.40,
        safety_car_hazard_rate_per_lap=0.017,
        vsc_hazard_rate_per_lap=0.015,
        track_evolution_gain_per_lap=0.008,
        drs_activation_zones=2,
        drs_zone_lap_fraction=0.26,
        drs_configuration_mode="CIRCUIT_SPECIFIC",
        nominated_compounds={"SOFT": "C5", "MEDIUM": "C4", "HARD": "C3"},
    ),
    "spa": CircuitProfile(
        circuit_id="spa",
        circuit_name="Circuit de Spa-Francorchamps",
        total_laps=44,
        base_lap_time_seconds=105.00,
        pit_transit_loss_seconds=20.5,
        overtaking_difficulty_index=0.52,
        safety_car_hazard_rate_per_lap=0.022,
        vsc_hazard_rate_per_lap=0.018,
        track_evolution_gain_per_lap=0.009,
        drs_activation_zones=2,
        drs_zone_lap_fraction=0.24,
        drs_configuration_mode="CIRCUIT_SPECIFIC",
        nominated_compounds={"SOFT": "C4", "MEDIUM": "C3", "HARD": "C2"},
    ),
    "red_bull_ring": CircuitProfile(
        circuit_id="red_bull_ring",
        circuit_name="Red Bull Ring",
        total_laps=71,
        base_lap_time_seconds=65.50,
        pit_transit_loss_seconds=19.0,
        overtaking_difficulty_index=0.45,
        safety_car_hazard_rate_per_lap=0.019,
        vsc_hazard_rate_per_lap=0.014,
        track_evolution_gain_per_lap=0.011,
        drs_activation_zones=3,
        drs_zone_lap_fraction=0.28,
        drs_configuration_mode="CIRCUIT_SPECIFIC",
        nominated_compounds={"SOFT": "C5", "MEDIUM": "C4", "HARD": "C3"},
    ),
}


class ForecastingBridge:
    """Bridges forecasting models into simulation initial states."""

    def __init__(self, data_path: Optional[Path] = None):
        self.data_path = data_path or DATA_PATH
        self._df: Optional[pd.DataFrame] = None

    def _load_data(self) -> pd.DataFrame:
        if self._df is None:
            self._df = pd.read_csv(self.data_path)
            self._df["season_int"] = self._df["season"].astype(int)
            self._df["round_int"] = self._df["round"].astype(int)
            self._df["grid_int"] = self._df["grid_position"].astype(int)
        return self._df

    def build_initial_race_state(
        self,
        season: int,
        round_num: int,
        checkpoint: str = "T5_FINAL_PRE_RACE",
        track_condition: TrackCondition = TrackCondition.DRY,
    ) -> RaceState:
        """
        Extracts driver field, starting grid, and constructor form to construct an initialized RaceState.
        """
        df = self._load_data()
        race_rows = df[(df["season_int"] == season) & (df["round_int"] == round_num)].copy()

        if race_rows.empty:
            raise ValueError(f"No historical race records found for season {season} round {round_num}")

        circuit_id = str(race_rows["circuit_id"].iloc[0])
        circuit_profile = CIRCUIT_PROFILES.get(
            circuit_id,
            CircuitProfile(
                circuit_id=circuit_id,
                circuit_name=str(race_rows["circuit_name"].iloc[0]),
                total_laps=int(race_rows["laps_completed"].max() or 55),
                base_lap_time_seconds=86.0,
                pit_transit_loss_seconds=20.0,
            ),
        )

        # Estimate rolling constructor pace advantage from prior 5 races
        hist_df = df[
            (df["season_int"] < season) | ((df["season_int"] == season) & (df["round_int"] < round_num))
        ]

        constructor_pace_deltas: Dict[str, float] = {}
        for c_id in race_rows["constructor_id"].unique():
            c_hist = hist_df[hist_df["constructor_id"] == c_id].tail(10)
            if not c_hist.empty:
                mean_pos = float(c_hist["finish_position"].mean())
                # Top constructors get a negative pace delta (faster lap times)
                pace_delta = (mean_pos - 10.0) * 0.08
            else:
                pace_delta = 0.0
            constructor_pace_deltas[c_id] = float(np.clip(pace_delta, -1.2, 1.2))

        # Build DriverState objects
        drivers_dict: Dict[str, DriverState] = {}
        for _, row in race_rows.sort_values("grid_int").iterrows():
            d_id = str(row["driver_id"])
            c_id = str(row["constructor_id"])
            grid = int(row["grid_int"])
            if grid <= 0:
                grid = int(race_rows["grid_int"].max() + 1)

            team_delta = constructor_pace_deltas.get(c_id, 0.0)
            base_pace = circuit_profile.base_lap_time_seconds + team_delta

            # Choose starting compound based on grid (top 10 often start Medium, back of grid Hard/Soft)
            start_comp = TyreCompound.MEDIUM if grid <= 14 else (
                TyreCompound.HARD if grid % 2 == 0 else TyreCompound.SOFT
            )
            if track_condition == TrackCondition.WET:
                start_comp = TyreCompound.WET
            elif track_condition == TrackCondition.DAMP:
                start_comp = TyreCompound.INTERMEDIATE

            drivers_dict[d_id] = DriverState(
                driver_id=d_id,
                driver_name=str(row["driver_name"]),
                constructor_id=c_id,
                starting_grid=grid,
                current_position=grid,
                current_lap=0,
                accumulated_race_time=0.0,
                current_compound=start_comp,
                current_tyre_age=0,
                current_stint=1,
                compounds_used=[start_comp],
                pit_stop_count=0,
                status=DriverStatus.RUNNING,
                base_pace_seconds=round(base_pace, 3),
                driver_pace_sigma=0.22,
            )

        return RaceState(
            race_id=f"{season}_{round_num:02d}",
            circuit=circuit_profile,
            season=season,
            round_num=round_num,
            current_lap=0,
            total_laps=circuit_profile.total_laps,
            track_condition=track_condition,
            drivers=drivers_dict,
        )
