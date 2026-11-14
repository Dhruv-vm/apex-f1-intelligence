"""APEX — Mechanical Reliability and Retirement Dynamics (Phase 7 / EXP-0006).

Simulates component reliability failures (PU, hydraulics, transmission)
and traffic collisions, drawing from historical constructor reliability priors.
"""
from typing import Dict, Optional, Tuple
import numpy as np

from backend.simulation.state import DriverState, DriverStatus


class ReliabilityModel:
    """Evaluates stochastic retirement probability per lap for running cars."""

    def __init__(
        self,
        base_mechanical_failure_hazard_per_lap: float = 0.0015,
        lap1_collision_hazard: float = 0.020,
    ):
        self.base_mech_hazard = base_mechanical_failure_hazard_per_lap
        self.lap1_collision_hazard = lap1_collision_hazard

        # Constructor reliability multipliers derived from historical DNF records
        self.constructor_multipliers: Dict[str, float] = {
            "red_bull": 0.70,
            "ferrari": 0.85,
            "mercedes": 0.75,
            "mclaren": 0.80,
            "aston_martin": 0.95,
            "alpine": 1.25,
            "williams": 1.30,
            "rb": 1.15,
            "haas": 1.20,
            "sauber": 1.35,
        }

        self.failure_reasons = [
            "Power Unit Failure (Internal Combustion Engine / MGU-K)",
            "Hydraulic Pressure Loss",
            "Gearbox Failure",
            "Brake System Failure",
            "Electrical Shutdown",
            "Suspension Damage",
        ]

    def check_driver_retirement(
        self,
        driver: DriverState,
        current_lap: int,
        rng: Optional[np.random.Generator] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Evaluates whether driver suffers a race-ending retirement on the current lap.
        Returns (is_retired, reason).
        """
        if not driver.is_active():
            return False, None

        if rng is None:
            rng = np.random.default_rng()

        # Lap 1 elevated contact/collision risk
        if current_lap == 1:
            if rng.random() < self.lap1_collision_hazard:
                return True, "Lap 1 Multi-Car Collision Damage"

        # Ongoing mechanical hazard
        team_mult = self.constructor_multipliers.get(driver.constructor_id, 1.0)
        p_failure = self.base_mech_hazard * team_mult

        if rng.random() < p_failure:
            reason_idx = int(rng.integers(0, len(self.failure_reasons)))
            return True, self.failure_reasons[reason_idx]

        return False, None
