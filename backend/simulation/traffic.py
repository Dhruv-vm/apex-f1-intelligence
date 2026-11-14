"""APEX — Traffic, DRS, and Overtaking Dynamics (Phase 7.1 / EXP-0006-R2).

Implements FIA 2024 Sporting Regulations Article 22.1 DRS rules:
- Detection point gap check (< 1.000s).
- Zone activation benefit (applied only in designated activation zones).
- Disabled on Lap 1 of the race.
- Disabled on first green-flag lap following a Safety Car restart.
- Disabled under Safety Car and Virtual Safety Car.
- Disabled in wet/damp conditions.
- Separates eligibility, activation advantage, and overtake probability.
"""
from typing import Dict, List, Optional, Tuple
import numpy as np

from backend.simulation.state import DriverState, SafetyCarState, TrackCondition


class TrafficOvertakingModel:
    """Simulates on-track interactions, DRS activation, and overtaking probability."""

    def __init__(
        self,
        drs_detection_threshold_seconds: float = 1.000,
        drs_speed_advantage_seconds: float = 0.35,
        dirty_air_loss_seconds: float = 0.25,
        base_overtake_threshold_seconds: float = 0.55,
    ):
        self.drs_threshold = drs_detection_threshold_seconds
        self.drs_advantage = drs_speed_advantage_seconds
        self.dirty_air_penalty = dirty_air_loss_seconds
        self.base_overtake_threshold = base_overtake_threshold_seconds

    def check_drs_eligibility(
        self,
        gap_at_detection_sec: float,
        current_lap: int,
        laps_since_sc_restart: int,
        safety_car_state: SafetyCarState,
        track_condition: TrackCondition,
        season: int = 2024,
        in_drs_activation_zone: bool = True,
        race_director_drs_enabled: bool = True,
        poor_visibility: bool = False,
        yellow_flags_in_zone: bool = False,
    ) -> Tuple[bool, Optional[str]]:
        """
        FIA 2024 Sporting Regulations Article 22.1 (Issue 7):
        Checks whether DRS can be activated on the current lap.
        - Eligible strictly when gap < 1.000s at detection point.
        - Activation only within predetermined activation zones.
        - Enabled after one lap completed following start or SC restart.
        - Race Director discretion to disable in poor visibility, yellow flags, or track conditions.
        """
        # 1. Race Director discretionary disablement
        if not race_director_drs_enabled:
            return False, "DRS Disabled: Race Director instruction"
        if poor_visibility:
            return False, "DRS Disabled: Poor visibility in activation zone"
        if yellow_flags_in_zone:
            return False, "DRS Disabled: Yellow flags displayed in activation zone"

        # 2. Designated activation zone check
        if not in_drs_activation_zone:
            return False, "DRS Inactive: Car outside designated activation zone"

        # 3. Neutralisation check
        if safety_car_state != SafetyCarState.NONE:
            return False, f"DRS Disabled: Race under {safety_car_state.value}"

        # 4. Wet track check (Under Art 22.1, Race Director disables DRS in wet/damp conditions)
        if track_condition in (TrackCondition.DAMP, TrackCondition.WET):
            return False, f"DRS Disabled: Track condition is {track_condition.value} (Race Director instruction)"

        # 5. Lap 1 check (In 2024, DRS enabled after 1 lap = starting lap 2; pre-2024 was lap 3)
        min_start_lap = 2 if season >= 2024 else 3
        if current_lap < min_start_lap:
            return False, f"DRS Disabled: Permitted only from Lap {min_start_lap} onwards"

        # 6. Restart check (Enabled after 1 full lap completed after SC restart)
        if laps_since_sc_restart < 1:
            return False, "DRS Disabled: Neutralisation restart lap (must complete 1 lap)"

        # 7. Strict gap detection check (< 1.000s at detection point)
        if gap_at_detection_sec >= self.drs_threshold:
            return False, f"DRS Ineligible: Gap {gap_at_detection_sec:.4f}s is not strictly less than {self.drs_threshold:.3f}s"

        return True, f"DRS Eligible: Gap {gap_at_detection_sec:.4f}s < {self.drs_threshold:.3f}s at detection point"

    def evaluate_pairwise_interaction(
        self,
        chaser: DriverState,
        leader: DriverState,
        overtaking_difficulty_index: float,
        chaser_raw_lap: float,
        leader_raw_lap: float,
        safety_car_state: SafetyCarState,
        current_lap: int = 1,
        laps_since_sc_restart: int = 5,
        track_condition: TrackCondition = TrackCondition.DRY,
        drs_zone_fraction: float = 0.20,
        in_drs_activation_zone: bool = True,
        race_director_drs_enabled: bool = True,
        poor_visibility: bool = False,
        yellow_flags_in_zone: bool = False,
        rng: Optional[np.random.Generator] = None,
        overtake_roll_override: Optional[float] = None,
    ) -> Tuple[float, bool]:
        """
        Evaluates interaction between chaser and leader on the current lap.
        Returns (effective_chaser_lap, did_overtake).
        """
        if safety_car_state != SafetyCarState.NONE:
            # No overtaking permitted under Safety Car / VSC
            return max(chaser_raw_lap, leader_raw_lap), False

        gap = chaser.gap_to_ahead

        # Clean air (not proximate)
        if gap > 1.80:
            return chaser_raw_lap, False

        # DRS Evaluation under FIA Sporting Regulations Art 22.1
        is_drs_eligible, _ = self.check_drs_eligibility(
            gap_at_detection_sec=gap,
            current_lap=current_lap,
            laps_since_sc_restart=laps_since_sc_restart,
            safety_car_state=safety_car_state,
            track_condition=track_condition,
            in_drs_activation_zone=in_drs_activation_zone,
            race_director_drs_enabled=race_director_drs_enabled,
            poor_visibility=poor_visibility,
            yellow_flags_in_zone=yellow_flags_in_zone,
        )
        # DRS advantage applied strictly to designated activation zone fraction
        drs_boost = (self.drs_advantage * drs_zone_fraction) if is_drs_eligible else 0.0

        # Tyre age advantage
        tyre_advantage = max(-0.6, min(0.6, (leader.current_tyre_age - chaser.current_tyre_age) * 0.035))

        # Intrinsic pace advantage
        raw_pace_delta = leader_raw_lap - chaser_raw_lap

        net_advantage = raw_pace_delta + drs_boost + tyre_advantage

        # Required margin to overcome circuit defense
        required_advantage = self.base_overtake_threshold * (0.6 + 0.8 * overtaking_difficulty_index)

        # Overtake probability sigmoid
        z = (net_advantage - required_advantage) / 0.30
        p_overtake = 1.0 / (1.0 + np.exp(-z)) if abs(z) < 20 else (1.0 if z > 0 else 0.0)

        # Coin-flip draw (either pre-indexed from scenario or local rng)
        roll = overtake_roll_override if overtake_roll_override is not None else (
            rng.random() if rng is not None else 0.5
        )
        did_overtake = bool(roll < p_overtake)

        if did_overtake:
            chaser.overtakes_completed += 1
            leader.times_overtaken += 1
            return chaser_raw_lap, True
        else:
            # Trapped behind leader: suffers dirty air turbulence (+0.25s)
            constrained_lap = max(chaser_raw_lap, leader_raw_lap + self.dirty_air_penalty)
            return constrained_lap, False
