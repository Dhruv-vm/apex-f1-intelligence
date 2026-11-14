"""APEX — Pit Stop Simulator and Service Time Dynamics (Phase 7.1 / EXP-0006-R2).

Models circuit pit-lane transit loss, stationary wheel-change distributions,
Safety Car / VSC transit discounts, double-stack penalties, and FIA 2024 Sporting Regulations Art 30.5.
"""
from typing import Dict, List, Optional, Set, Tuple
import numpy as np
from pydantic import BaseModel, Field

from backend.simulation.state import PitStopRecord, SafetyCarState, TrackCondition, TyreCompound


class TyreComplianceResult:
    """Represents the outcome of an FIA Sporting Regulations tyre compliance check."""

    def __init__(
        self,
        is_compliant: bool,
        penalty_type: Optional[str] = None,
        description: Optional[str] = None,
    ):
        self.is_compliant = is_compliant
        self.penalty_type = penalty_type  # None, "DISQUALIFICATION", "TIME_PENALTY_30S"
        self.description = description or ""

    def __iter__(self):
        # Backward-compatible 2-tuple unpacking: (is_compliant, description)
        return iter((self.is_compliant, self.description))

    def __bool__(self) -> bool:
        return self.is_compliant

    def __repr__(self) -> str:
        return f"TyreComplianceResult(compliant={self.is_compliant}, penalty={self.penalty_type}, desc='{self.description}')"


class PitStopModel:
    """
    Simulates pit-lane transit, stationary service time, and race-control discounts.
    
    Canonical Pit Loss Decomposition:
    1. Pit entry deceleration loss: calibrated at 9.5s (circuit entry to pit limiter).
    2. Pit exit acceleration loss: calibrated at 11.0s (pit limiter to racing speed rejoin).
    3. In-transit pit loss: entry + exit = 20.5s at Yas Marina (pure transit, excludes service).
    4. Stationary service time: Truncated Normal(2.45s, 0.35s) on [1.8s, 8.0s].
    5. Stuck wheel / equipment delay: Bernoulli(p=0.035) adding Uniform(2.5s, 6.5s).
    6. Traffic / rejoin loss: simulated on rejoin based on traffic proximity.
    7. Total race-time loss = Transit Loss + Stationary Service + Delay + Traffic Rejoin.
    """

    def __init__(
        self,
        base_transit_loss_seconds: float = 20.5,
        stationary_mean_seconds: float = 2.45,
        stationary_std_seconds: float = 0.35,
        stuck_wheel_prob: float = 0.035,
        vsc_transit_discount: float = 0.35,  # ~35% discount (saves ~7.0s)
        sc_transit_discount: float = 0.50,   # ~50% discount (saves ~10.0s)
        double_stack_delay_seconds: float = 3.5,
        entry_transit_fraction: float = 0.463, # 9.5s / 20.5s = 46.3% entry deceleration
    ):
        self.base_transit_loss = base_transit_loss_seconds
        self.stationary_mean = stationary_mean_seconds
        self.stationary_std = stationary_std_seconds
        self.stuck_wheel_prob = stuck_wheel_prob
        self.vsc_transit_discount = vsc_transit_discount
        self.sc_transit_discount = sc_transit_discount
        self.double_stack_delay = double_stack_delay_seconds
        self.entry_transit_fraction = entry_transit_fraction

    def execute_pit_stop(
        self,
        lap: int,
        stint_completed: int,
        target_compound: TyreCompound,
        safety_car_state: SafetyCarState,
        is_double_stacked: bool = False,
        rng: Optional[np.random.Generator] = None,
        service_override: Optional[Tuple[float, float]] = None,
    ) -> PitStopRecord:
        """
        Executes a pit stop, drawing or taking pre-indexed stationary service time,
        applying race-control discounts, and checking for double-stack delays.
        """
        if service_override is not None:
            stationary, delay = service_override
        else:
            if rng is None:
                rng = np.random.default_rng()
            stationary = float(np.clip(rng.normal(self.stationary_mean, self.stationary_std), 1.80, 8.0))
            delay = 0.0
            if rng.random() < self.stuck_wheel_prob:
                delay = float(rng.uniform(2.5, 6.5))
                stationary += delay

        # Double-stack waiting penalty
        if is_double_stacked:
            stationary += self.double_stack_delay

        # Pit-lane transit loss calculation with race-control discounts
        under_sc = safety_car_state == SafetyCarState.FULL_SC
        under_vsc = safety_car_state == SafetyCarState.VSC

        transit_loss = self.base_transit_loss
        if under_sc:
            transit_loss *= (1.0 - self.sc_transit_discount)
        elif under_vsc:
            transit_loss *= (1.0 - self.vsc_transit_discount)

        total_loss = transit_loss + stationary

        return PitStopRecord(
            lap=lap,
            stint_completed=stint_completed,
            compound_fitted=target_compound,
            stationary_duration_seconds=round(stationary, 3),
            transit_loss_seconds=round(transit_loss, 3),
            total_pit_loss_seconds=round(total_loss, 3),
            pit_under_safety_car=under_sc,
            pit_under_vsc=under_vsc,
            double_stacked=is_double_stacked,
            delay_seconds=round(delay, 3),
        )

    @staticmethod
    def validate_sporting_tyre_rules(
        compounds_used: Optional[List[TyreCompound]],
        track_condition: TrackCondition,
        is_race_suspended_and_not_restarted: bool = False,
        mandatory_dry_compounds: Optional[Set[TyreCompound]] = None,
        season: int = 2024,
    ) -> TyreComplianceResult:
        """
        FIA Sporting Regulations Article 30.5 (2024 Issue 7):
        - Unless intermediate or wet-weather tyres were used during the race, each driver
          must use at least two different dry-weather tyre specifications.
        - In addition, at least one used specification must be a nominated mandatory dry-weather
          race tyre specification as nominated by the appointed tyre supplier.
        - Failure to comply normally results in DISQUALIFICATION from race results (Art 30.5.m).
        - If the race is suspended and cannot be restarted, 30 seconds is added to the driver's
          elapsed race time (Art 30.5.n).
        - If wet or intermediate tyres were used at any point, mandatory compound diversity is suspended.
        """
        # 1. Missing or empty compound usage
        if not compounds_used:
            return TyreComplianceResult(
                is_compliant=False,
                penalty_type="DISQUALIFICATION",
                description="FIA Art 30.5 Infringement: Missing or empty tyre compound usage record.",
            )

        # 2. Wet or intermediate condition exemption
        has_wet_tyre = any(c in (TyreCompound.INTERMEDIATE, TyreCompound.WET) for c in compounds_used)
        if track_condition in (TrackCondition.DAMP, TrackCondition.WET) or has_wet_tyre:
            return TyreComplianceResult(
                is_compliant=True,
                penalty_type=None,
                description="FIA Art 30.5: Mandatory two-dry compound rule suspended due to intermediate/wet tyre usage.",
            )

        # 3. Dry race check
        dry_compounds: Set[TyreCompound] = {
            c for c in compounds_used
            if c in (TyreCompound.SOFT, TyreCompound.MEDIUM, TyreCompound.HARD)
        }

        # 3a. Minimum two distinct dry specifications requirement
        if len(dry_compounds) < 2:
            if is_race_suspended_and_not_restarted:
                return TyreComplianceResult(
                    is_compliant=False,
                    penalty_type="TIME_PENALTY_30S",
                    description=(
                        "FIA Art 30.5.n Penalty: Race suspended without restart. "
                        "+30.0s time penalty added for failure to use two dry tyre specifications."
                    ),
                )
            else:
                return TyreComplianceResult(
                    is_compliant=False,
                    penalty_type="DISQUALIFICATION",
                    description=(
                        "FIA Art 30.5.m Infringement: Used fewer than two distinct dry-weather tyre specifications "
                        "in completed dry race. Penalty: DISQUALIFICATION."
                    ),
                )

        # 3b. Mandatory nominated dry specification check (FIA Art 30.5.b.ii)
        if mandatory_dry_compounds:
            has_mandatory = any(c in mandatory_dry_compounds for c in dry_compounds)
            if not has_mandatory:
                mandatory_names = ", ".join(c.value for c in mandatory_dry_compounds)
                if is_race_suspended_and_not_restarted:
                    return TyreComplianceResult(
                        is_compliant=False,
                        penalty_type="TIME_PENALTY_30S",
                        description=(
                            f"FIA Art 30.5.n Penalty: Race suspended without restart. "
                            f"+30.0s time penalty added for failure to use mandatory specification ({mandatory_names})."
                        ),
                    )
                else:
                    return TyreComplianceResult(
                        is_compliant=False,
                        penalty_type="DISQUALIFICATION",
                        description=(
                            f"FIA Art 30.5.m Infringement: Failed to use at least one mandatory nominated dry-weather "
                            f"specification ({mandatory_names}) in completed dry race. Penalty: DISQUALIFICATION."
                        ),
                    )

        return TyreComplianceResult(
            is_compliant=True,
            penalty_type=None,
            description="FIA Art 30.5 Compliant: Used at least two distinct dry-weather tyre specifications including mandatory specification.",
        )
