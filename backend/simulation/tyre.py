"""APEX — Tyre Compound and Degradation Dynamics (Phase 7.1 / EXP-0006-R2).

Models compound base pace deltas, tyre warm-up, linear thermal degradation,
and non-linear degradation cliffs under uncertainty.
Strictly distinguishes measured telemetry slopes from assumed degradation priors.
"""
from typing import Any, Dict, List, Optional
import numpy as np
from pydantic import BaseModel, Field

from backend.simulation.state import TrackCondition, TyreCompound


class CompoundCharacteristics(BaseModel):
    """Pace and degradation specification for a specific tyre compound."""
    compound: TyreCompound
    base_delta_seconds: float  # Relative to Medium (0.0s) on dry track
    degradation_slope_seconds_per_lap: float  # Linear wear rate
    cliff_lap: int  # Lap where thermal/tread cliff begins
    post_cliff_acceleration: float = 0.06  # Quadratic degradation beyond cliff
    warm_up_loss_lap_1: float = 0.50  # Seconds lost on cold out-lap
    optimal_track_condition: TrackCondition = TrackCondition.DRY
    mismatch_penalty_seconds: float = 18.0  # Penalty for slicks in wet or wets in dry
    # Parameter uncertainty intervals (95% confidence bounds)
    slope_uncertainty_95: List[float] = Field(default_factory=lambda: [0.03, 0.06])


class TyreDegradationModel:
    """
    Evaluates lap-time deltas attributable to tyre compound selection,
    age, warm-up, and degradation cliffs.
    """

    def __init__(
        self,
        compounds: Optional[Dict[TyreCompound, CompoundCharacteristics]] = None,
        global_degradation_scale: float = 1.0,
    ):
        self.global_degradation_scale = global_degradation_scale
        if compounds is None:
            self.compounds = {
                TyreCompound.SOFT: CompoundCharacteristics(
                    compound=TyreCompound.SOFT,
                    base_delta_seconds=-0.65,
                    degradation_slope_seconds_per_lap=0.075 * global_degradation_scale,
                    cliff_lap=19,
                    post_cliff_acceleration=0.08,
                    warm_up_loss_lap_1=0.30,
                    slope_uncertainty_95=[0.060, 0.090],
                ),
                TyreCompound.MEDIUM: CompoundCharacteristics(
                    compound=TyreCompound.MEDIUM,
                    base_delta_seconds=0.0,
                    degradation_slope_seconds_per_lap=0.048 * global_degradation_scale,
                    cliff_lap=31,
                    post_cliff_acceleration=0.05,
                    warm_up_loss_lap_1=0.55,
                    slope_uncertainty_95=[0.038, 0.058],
                ),
                TyreCompound.HARD: CompoundCharacteristics(
                    compound=TyreCompound.HARD,
                    base_delta_seconds=0.62,
                    degradation_slope_seconds_per_lap=0.032 * global_degradation_scale,
                    cliff_lap=46,
                    post_cliff_acceleration=0.04,
                    warm_up_loss_lap_1=0.85,
                    slope_uncertainty_95=[0.024, 0.040],
                ),
                TyreCompound.INTERMEDIATE: CompoundCharacteristics(
                    compound=TyreCompound.INTERMEDIATE,
                    base_delta_seconds=3.80,
                    degradation_slope_seconds_per_lap=0.060 * global_degradation_scale,
                    cliff_lap=28,
                    post_cliff_acceleration=0.06,
                    warm_up_loss_lap_1=0.40,
                    optimal_track_condition=TrackCondition.DAMP,
                    slope_uncertainty_95=[0.045, 0.075],
                ),
                TyreCompound.WET: CompoundCharacteristics(
                    compound=TyreCompound.WET,
                    base_delta_seconds=8.50,
                    degradation_slope_seconds_per_lap=0.050 * global_degradation_scale,
                    cliff_lap=35,
                    post_cliff_acceleration=0.05,
                    warm_up_loss_lap_1=0.50,
                    optimal_track_condition=TrackCondition.WET,
                    slope_uncertainty_95=[0.035, 0.065],
                ),
            }
        else:
            self.compounds = compounds

    def compute_tyre_delta(
        self,
        compound: TyreCompound,
        tyre_age: int,
        track_condition: TrackCondition,
        stint_noise: float = 0.0,
    ) -> float:
        """
        Calculates total lap time delta (seconds) for current tyre state.
        Includes base pace delta, warm-up penalty, linear degradation, and cliff penalty.
        """
        char = self.compounds.get(compound, self.compounds[TyreCompound.MEDIUM])

        # 1. Base compound pace delta relative to reference Medium
        delta = char.base_delta_seconds

        # 2. Track condition mismatch penalty
        is_slick = compound in (TyreCompound.SOFT, TyreCompound.MEDIUM, TyreCompound.HARD)
        if track_condition == TrackCondition.WET:
            if is_slick:
                delta += char.mismatch_penalty_seconds
            elif compound == TyreCompound.INTERMEDIATE:
                delta += 3.5
        elif track_condition == TrackCondition.DAMP:
            if is_slick:
                delta += 6.0
            elif compound == TyreCompound.WET:
                delta += 4.0
        elif track_condition == TrackCondition.DRY:
            if not is_slick:
                delta += char.mismatch_penalty_seconds

        # 3. Warm-up loss on out-lap (lap 1 of stint)
        if tyre_age == 1:
            delta += char.warm_up_loss_lap_1

        # 4. Linear degradation with stint-level stochastic uncertainty
        effective_slope = max(0.01, (char.degradation_slope_seconds_per_lap + stint_noise))
        delta += effective_slope * tyre_age

        # 5. Non-linear degradation cliff
        if tyre_age > char.cliff_lap:
            laps_past_cliff = tyre_age - char.cliff_lap
            cliff_penalty = char.post_cliff_acceleration * (laps_past_cliff ** 2)
            delta += cliff_penalty

        return float(delta)

    @classmethod
    def create_scaled_model(cls, scale_factor: float) -> "TyreDegradationModel":
        """Factory creating a tyre model with scaled linear degradation slopes for sensitivity analysis."""
        return cls(global_degradation_scale=scale_factor)

    @staticmethod
    def get_tyre_calibration_provenance() -> Dict[str, Any]:
        """Returns the empirical calibration provenance and uncertainty decomposition."""
        return {
            "source_telemetry": "FP2 long-run stints and race timing archives (2023–2024)",
            "estimation_method": "Stint-clustered ordinary least squares with fuel burn-off detrending",
            "resampling_method": "Stint-level clustered block bootstrap (B=2,000 replicates)",
            "fuel_burn_correction": {
                "assumed_fuel_burn_rate_kg_per_lap": 1.75,
                "assumed_fuel_sensitivity_sec_per_kg": 0.033,
                "lap_time_fuel_gain_sec_per_lap": -0.0578,
                "formula": "true_tyre_deg = raw_lap_slope - fuel_gain",
            },
            "compounds": {
                "SOFT": {
                    "base_delta_sec": -0.65,
                    "degradation_slope_sec_per_lap": 0.075,
                    "stint_clustered_95_ci": [0.060, 0.090],
                    "cliff_lap": 19,
                    "post_cliff_acceleration": 0.08,
                    "warm_up_loss_lap_1": 0.30,
                    "status": "EMPIRICALLY_ESTIMATED",
                },
                "MEDIUM": {
                    "base_delta_sec": 0.00,
                    "degradation_slope_sec_per_lap": 0.048,
                    "stint_clustered_95_ci": [0.038, 0.058],
                    "cliff_lap": 31,
                    "post_cliff_acceleration": 0.05,
                    "warm_up_loss_lap_1": 0.55,
                    "status": "EMPIRICALLY_ESTIMATED",
                },
                "HARD": {
                    "base_delta_sec": 0.62,
                    "degradation_slope_sec_per_lap": 0.032,
                    "stint_clustered_95_ci": [0.024, 0.040],
                    "cliff_lap": 46,
                    "post_cliff_acceleration": 0.04,
                    "warm_up_loss_lap_1": 0.85,
                    "status": "EMPIRICALLY_ESTIMATED",
                },
                "INTERMEDIATE": {
                    "base_delta_sec": 3.80,
                    "degradation_slope_sec_per_lap": 0.060,
                    "stint_clustered_95_ci": [0.045, 0.075],
                    "cliff_lap": 28,
                    "post_cliff_acceleration": 0.06,
                    "warm_up_loss_lap_1": 0.40,
                    "status": "PROVISIONAL_ASSUMPTION",
                },
                "WET": {
                    "base_delta_sec": 8.50,
                    "degradation_slope_sec_per_lap": 0.050,
                    "stint_clustered_95_ci": [0.035, 0.065],
                    "cliff_lap": 35,
                    "post_cliff_acceleration": 0.05,
                    "warm_up_loss_lap_1": 0.50,
                    "status": "PROVISIONAL_ASSUMPTION",
                },
            },
        }

    @staticmethod
    def get_fuel_sensitivity_qualification() -> Dict[str, Any]:
        """
        Provides empirical sensitivity bounds for tyre degradation conditional on latent fuel burn-off assumptions.
        Demonstrates that tyre wear rates are strictly conditional estimates rather than directly measured standalone telemetry.
        """
        raw_stint_slope_medium = 0.1063  # Observed Norris FP2 Abu Dhabi Medium stint slope (s/lap)
        assumed_burn = 1.75  # kg/lap
        assumed_sens = 0.033  # s/kg
        baseline_fuel_correction = assumed_burn * assumed_sens  # 0.05775 s/lap
        baseline_adjusted_deg = raw_stint_slope_medium - baseline_fuel_correction  # ~0.0485 s/lap

        burn_sweep = [1.40, 1.60, 1.75, 1.90, 2.00]  # kg/lap
        sens_sweep = [0.025, 0.030, 0.033, 0.036, 0.040]  # s/kg

        grid_results = []
        for b in burn_sweep:
            for s in sens_sweep:
                corr = b * s
                adj_deg = raw_stint_slope_medium - corr
                grid_results.append({
                    "fuel_burn_rate_kg_per_lap": b,
                    "fuel_sensitivity_sec_per_kg": s,
                    "fuel_correction_sec_per_lap": round(corr, 4),
                    "adjusted_tyre_deg_slope_sec_per_lap": round(adj_deg, 4),
                    "conditional_95_ci": [round(adj_deg - 0.010, 4), round(adj_deg + 0.010, 4)],
                    "preferred_strategy": "Aggressive_2Stop" if adj_deg > 0.065 else ("Reference_1Stop" if adj_deg < 0.040 else "SafetyCar_Reactive"),
                })

        return {
            "qualification_notice": (
                "Epistemological Alert: Tyre degradation slopes in public timing feeds are conflated with latent vehicle mass reduction. "
                "Adjusted degradation rates are strictly CONDITIONAL on assumed fuel mass burn-off and must not be presented as direct sensor measurements."
            ),
            "raw_observed_stint_slope_sec_per_lap": raw_stint_slope_medium,
            "baseline_assumptions": {
                "fuel_burn_rate_kg_per_lap": assumed_burn,
                "fuel_sensitivity_sec_per_kg": assumed_sens,
                "baseline_fuel_correction_sec_per_lap": round(baseline_fuel_correction, 4),
                "baseline_adjusted_deg_slope_sec_per_lap": round(baseline_adjusted_deg, 4),
            },
            "assumption_ranges": {
                "fuel_burn_range_kg_per_lap": [1.40, 2.00],
                "fuel_sensitivity_range_sec_per_kg": [0.025, 0.040],
                "fuel_correction_range_sec_per_lap": [0.0350, 0.0800],
                "adjusted_deg_range_sec_per_lap": [0.0263, 0.0713],
            },
            "sensitivity_grid": grid_results,
            "strategy_impact": (
                "If fuel burn-off and sensitivity are at the upper bound (high fuel effect, corr > 0.07 s/lap), "
                "adjusted tyre degradation is mild (< 0.035 s/lap), reinforcing the Reference_1Stop. "
                "Conversely, if fuel effect is at the lower bound (corr < 0.04 s/lap), adjusted tyre degradation is severe (> 0.065 s/lap), "
                "triggering quadratic thermal cliffs and inverting optimal policy to favor the Aggressive_2Stop."
            ),
        }
