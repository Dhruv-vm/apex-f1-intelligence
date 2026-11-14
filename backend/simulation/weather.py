"""APEX — Weather and Track Condition Evolution (Phase 7 / EXP-0006).

Models ambient and track temperatures, stochastic rain onset,
and track surface drying / wetting transitions.
"""
from typing import Optional, Tuple
import numpy as np

from backend.simulation.state import TrackCondition


class WeatherModel:
    """Manages stochastic environmental conditions during race simulation."""

    def __init__(
        self,
        base_air_temp_celsius: float = 27.0,
        base_track_temp_celsius: float = 34.0,
        rain_probability_per_lap: float = 0.005,  # Empirical prior for dry races
        drying_rate_per_lap: float = 0.08,
    ):
        self.air_temp = base_air_temp_celsius
        self.track_temp = base_track_temp_celsius
        self.rain_prob = rain_probability_per_lap
        self.drying_rate = drying_rate_per_lap

    def step_weather(
        self,
        current_lap: int,
        total_laps: int,
        current_condition: TrackCondition,
        rng: Optional[np.random.Generator] = None,
    ) -> Tuple[TrackCondition, float, float]:
        """
        Steps environmental state by one lap.
        Returns (new_condition, air_temp, track_temp).
        """
        if rng is None:
            rng = np.random.default_rng()

        # Slight diurnal / dusk cooling at Yas Marina (or cloud cover)
        cooling_drift = -0.05 * (current_lap / max(1, total_laps))
        air_t = self.air_temp + cooling_drift + float(rng.normal(0, 0.1))
        track_t = self.track_temp + 1.5 * cooling_drift + float(rng.normal(0, 0.2))

        new_condition = current_condition

        # Rain onset check
        if current_condition == TrackCondition.DRY:
            if rng.random() < self.rain_prob:
                new_condition = TrackCondition.DAMP
        elif current_condition == TrackCondition.DAMP:
            roll = rng.random()
            if roll < 0.25:
                new_condition = TrackCondition.WET
            elif roll > 0.70:
                new_condition = TrackCondition.DRY
        elif current_condition == TrackCondition.WET:
            if rng.random() < self.drying_rate:
                new_condition = TrackCondition.DAMP

        return new_condition, round(air_t, 1), round(track_t, 1)
