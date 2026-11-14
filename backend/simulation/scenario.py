"""APEX — Exogenous Scenario Generation & Common Random Numbers (Phase 7.1 / EXP-0006-R2).

Generates decoupled, deterministic random scenario streams indexed by:
- Run ID / Seed
- Lap number
- Driver ID
- Event Category (Weather, Incident/SC, Driver Pace, Stint Degradation, Reliability, Traffic, Pit Service)

This guarantees that alternative strategy policies evaluated in the same paired simulation
draw receive bitwise identical exogenous environmental conditions, eliminating random stream
contamination and desynchronization.
"""
from typing import Dict, List, Optional, Tuple
import numpy as np
from pydantic import BaseModel, Field

from backend.simulation.state import SafetyCarState, TrackCondition


class ExogenousScenario:
    """
    Complete pre-drawn or deterministically accessible exogenous random variables for a single race.
    Strictly independent of any driver's tactical pit stop decisions or policy execution.
    """

    def __init__(
        self,
        run_id: str,
        master_seed: int,
        total_laps: int,
        driver_ids: List[str],
    ):
        self.run_id = run_id
        self.master_seed = master_seed
        self.total_laps = total_laps
        self.driver_ids = list(driver_ids)
        self.num_drivers = len(driver_ids)
        self.driver_index_map = {d_id: i for i, d_id in enumerate(driver_ids)}

        # Seed independent generators for each orthogonal event category using distinct salt offsets
        rng_weather = np.random.default_rng(master_seed + 1013)
        rng_sc = np.random.default_rng(master_seed + 2027)
        rng_pace = np.random.default_rng(master_seed + 3037)
        rng_stint = np.random.default_rng(master_seed + 4049)
        rng_pit = np.random.default_rng(master_seed + 5051)
        rng_rel = np.random.default_rng(master_seed + 6073)
        rng_traffic = np.random.default_rng(master_seed + 7079)
        rng_escalation = np.random.default_rng(master_seed + 8089)

        # 1. Weather: Per-lap rain transition roll and temperature drift
        # Array shape: (total_laps + 2,)
        self.weather_rain_rolls = rng_weather.uniform(0.0, 1.0, size=total_laps + 2)
        self.weather_temp_drifts = rng_weather.normal(0.0, 0.4, size=total_laps + 2)

        # 2. Safety Car / VSC: Per-lap incident trigger uniform and duration draws
        self.sc_incident_rolls = rng_sc.uniform(0.0, 1.0, size=total_laps + 2)
        self.sc_durations = rng_sc.integers(3, 7, size=total_laps + 2)  # 3 to 6 laps for SC
        self.vsc_durations = rng_sc.integers(1, 4, size=total_laps + 2) # 1 to 3 laps for VSC
        self.vsc_escalation_rolls = rng_escalation.uniform(0.0, 1.0, size=total_laps + 2)  # Orthogonal VSC->SC escalation stream
        # Restart compression gaps per driver per lap
        self.restart_gaps = rng_sc.normal(0.95, 0.20, size=(self.num_drivers, total_laps + 2))

        # 3. Driver Baseline Pace Noise: shape (num_drivers, total_laps + 2)
        # Standard normal Z ~ N(0, 1), scaled at runtime by each driver's individual sigma
        self.driver_pace_normals = rng_pace.normal(0.0, 1.0, size=(self.num_drivers, total_laps + 2))

        # 4. Stint Tyre Degradation Noise: shape (num_drivers, 10 max stints)
        self.stint_degradation_normals = rng_stint.normal(0.0, 0.008, size=(self.num_drivers, 10))

        # 5. Pit Stop Service: shape (num_drivers, 10 max pit stops)
        self.pit_stationary_normals = rng_pit.normal(2.45, 0.35, size=(self.num_drivers, 10))
        self.pit_stuck_wheel_rolls = rng_pit.uniform(0.0, 1.0, size=(self.num_drivers, 10))
        self.pit_stuck_wheel_delays = rng_pit.uniform(2.5, 6.5, size=(self.num_drivers, 10))

        # 6. Mechanical Reliability & Collisions: shape (num_drivers, total_laps + 2)
        self.mechanical_failure_rolls = rng_rel.uniform(0.0, 1.0, size=(self.num_drivers, total_laps + 2))
        self.lap1_collision_rolls = rng_rel.uniform(0.0, 1.0, size=self.num_drivers)

        # 7. Traffic & Overtaking: shape (num_drivers, total_laps + 2)
        self.overtake_uniforms = rng_traffic.uniform(0.0, 1.0, size=(self.num_drivers, total_laps + 2))

    def get_weather_draws(self, lap: int) -> Tuple[float, float]:
        """Returns (rain_roll, temp_drift) for the specified lap."""
        idx = min(lap, len(self.weather_rain_rolls) - 1)
        return float(self.weather_rain_rolls[idx]), float(self.weather_temp_drifts[idx])

    def get_incident_draw(self, lap: int) -> Tuple[float, int, int]:
        """Returns (incident_roll, sc_duration, vsc_duration) for the specified lap."""
        idx = min(lap, len(self.sc_incident_rolls) - 1)
        return (
            float(self.sc_incident_rolls[idx]),
            int(self.sc_durations[idx]),
            int(self.vsc_durations[idx]),
        )

    def get_vsc_escalation_draw(self, lap: int) -> float:
        """Returns deterministic escalation uniform draw for evaluating VSC -> SC transition."""
        idx = min(lap, len(self.vsc_escalation_rolls) - 1)
        return float(self.vsc_escalation_rolls[idx])

    def get_restart_gap(self, driver_id: str, lap: int) -> float:
        """Returns deterministic restart gap for a driver on a restart lap."""
        d_idx = self.driver_index_map.get(driver_id, 0)
        l_idx = min(lap, self.total_laps + 1)
        return float(np.clip(self.restart_gaps[d_idx, l_idx], 0.65, 2.0))

    def get_driver_pace_noise(self, driver_id: str, lap: int, pace_sigma: float) -> float:
        """Returns deterministic lap pace noise for a driver on a given lap."""
        d_idx = self.driver_index_map.get(driver_id, 0)
        l_idx = min(lap, self.total_laps + 1)
        return float(self.driver_pace_normals[d_idx, l_idx] * pace_sigma)

    def get_stint_noise(self, driver_id: str, stint_number: int) -> float:
        """Returns deterministic degradation slope noise for driver's stint."""
        d_idx = self.driver_index_map.get(driver_id, 0)
        s_idx = min(max(0, stint_number - 1), 9)
        return float(self.stint_degradation_normals[d_idx, s_idx])

    def get_pit_service_time(self, driver_id: str, stop_index: int, stuck_prob: float = 0.025) -> Tuple[float, float]:
        """
        Returns (stationary_service_seconds, delay_seconds).
        Draws from pre-indexed streams so other drivers' stops do not alter this driver's time.
        """
        d_idx = self.driver_index_map.get(driver_id, 0)
        p_idx = min(max(0, stop_index), 9)
        raw_service = float(np.clip(self.pit_stationary_normals[d_idx, p_idx], 1.80, 8.0))
        delay = 0.0
        if self.pit_stuck_wheel_rolls[d_idx, p_idx] < stuck_prob:
            delay = float(self.pit_stuck_wheel_delays[d_idx, p_idx])
            raw_service += delay
        return round(raw_service, 3), round(delay, 3)

    def check_mechanical_failure(self, driver_id: str, lap: int, hazard_threshold: float) -> bool:
        """Checks mechanical failure roll against driver-lap threshold."""
        d_idx = self.driver_index_map.get(driver_id, 0)
        l_idx = min(lap, self.total_laps + 1)
        return bool(self.mechanical_failure_rolls[d_idx, l_idx] < hazard_threshold)

    def check_lap1_collision(self, driver_id: str, hazard_threshold: float) -> bool:
        """Checks lap 1 collision roll."""
        d_idx = self.driver_index_map.get(driver_id, 0)
        return bool(self.lap1_collision_rolls[d_idx] < hazard_threshold)

    def get_overtake_roll(self, chaser_id: str, lap: int) -> float:
        """Returns deterministic uniform roll for overtaking coin-flip on this lap."""
        d_idx = self.driver_index_map.get(chaser_id, 0)
        l_idx = min(lap, self.total_laps + 1)
        return float(self.overtake_uniforms[d_idx, l_idx])


class ScenarioGenerator:
    """Factory generating reproducible ExogenousScenario instances with master seed management."""

    def __init__(self, master_seed: int = 42):
        self.master_seed = master_seed

    def generate_scenario(
        self,
        run_index: int,
        total_laps: int,
        driver_ids: List[str],
        salt_multiplier: int = 10007,
    ) -> ExogenousScenario:
        """Generates the i-th paired scenario for Common Random Numbers."""
        seed = self.master_seed + run_index * salt_multiplier
        run_id = f"scen_{seed}_{run_index:05d}"
        return ExogenousScenario(
            run_id=run_id,
            master_seed=seed,
            total_laps=total_laps,
            driver_ids=driver_ids,
        )
