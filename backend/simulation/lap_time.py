"""APEX — Stochastic Lap-Time Model (Phase 7 / EXP-0006).

Combines deterministic driver/constructor baseline pace, latent fuel burn-off,
track surface evolution, tyre compound deltas and degradation, environmental effects,
and driver consistency variation.
"""
from typing import Optional
import numpy as np

from backend.simulation.state import DriverState, RaceState, SafetyCarState
from backend.simulation.tyre import TyreDegradationModel


class LapTimeModel:
    """Computes point-in-time lap durations combining physics-based factors and stochastic draws."""

    def __init__(self, tyre_model: Optional[TyreDegradationModel] = None):
        self.tyre_model = tyre_model or TyreDegradationModel()

    def compute_single_lap_time(
        self,
        driver: DriverState,
        race_state: RaceState,
        stint_noise: float = 0.0,
        rng: Optional[np.random.Generator] = None,
    ) -> float:
        """
        Calculates raw single-lap time before traffic constraints.
        """
        if rng is None:
            rng = np.random.default_rng()

        lap = race_state.current_lap
        total_laps = race_state.total_laps
        circuit = race_state.circuit

        # 1. Base pace for this driver on this circuit
        base_pace = driver.base_pace_seconds

        # 2. Latent fuel burn-off effect (lighter car = faster lap times)
        # Fuel mass remaining: M_fuel = initial - lap * burn_rate
        fuel_remaining_kg = max(2.0, race_state.initial_fuel_kg - lap * race_state.fuel_burn_rate_kg_per_lap)
        fuel_delta = fuel_remaining_kg * circuit.fuel_effect_seconds_per_kg

        # 3. Track evolution (circuit rubbers in and grips up across the race)
        track_evolution_delta = -float(lap) * circuit.track_evolution_gain_per_lap

        # 4. Tyre compound selection, age, warm-up, and degradation
        tyre_delta = self.tyre_model.compute_tyre_delta(
            compound=driver.current_compound,
            tyre_age=driver.current_tyre_age,
            track_condition=race_state.track_condition,
            stint_noise=stint_noise,
        )

        # 5. Stochastic driver variability (consistency distribution)
        driver_noise = float(rng.normal(0.0, driver.driver_pace_sigma))

        # Total clean-air raw racing lap time
        raw_lap = base_pace + fuel_delta + track_evolution_delta + tyre_delta + driver_noise

        # 6. Safety Car / VSC neutralisation pace scaling
        if race_state.safety_car_state == SafetyCarState.FULL_SC:
            raw_lap *= 1.35
        elif race_state.safety_car_state == SafetyCarState.VSC:
            raw_lap *= 1.30

        return float(max(60.0, raw_lap))
