"""APEX — Strategy Policy Engine and Decision Policies (Phase 7 / EXP-0006).

Defines modular strategy policy interfaces and concrete tactics:
Fixed Reference, One-Stop, Two-Stop, Undercut, Overcut, and Safety-Car-Reactive.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel

from backend.simulation.state import DriverState, RaceState, SafetyCarState, TyreCompound


class StrategyDecision(BaseModel):
    """Output of a strategy policy evaluation for a driver on a given lap."""
    should_pit: bool
    target_compound: Optional[TyreCompound] = None
    reason: Optional[str] = None


class BaseStrategyPolicy(ABC):
    """Abstract interface for pit-stop strategy controllers."""

    @abstractmethod
    def evaluate_strategy(self, driver: DriverState, race_state: RaceState) -> StrategyDecision:
        """Evaluates whether the driver should pit on the current lap and which compound to fit."""
        pass


class FixedReferenceStrategy(BaseStrategyPolicy):
    """Executes pre-determined pit stops at fixed lap numbers with explicit compound sequences."""

    def __init__(self, plan: List[Tuple[int, TyreCompound]], name: str = "Fixed Reference Strategy"):
        # plan: [(pit_lap, compound_to_fit), ...]
        self.plan = sorted(plan, key=lambda x: x[0])
        self.name = name

    def evaluate_strategy(self, driver: DriverState, race_state: RaceState) -> StrategyDecision:
        current_lap = race_state.current_lap
        for pit_lap, target_comp in self.plan:
            if current_lap == pit_lap and driver.pit_stop_count < len(self.plan):
                # Ensure we haven't already stopped for this target
                if not any(r.lap == current_lap for r in driver.pit_stop_history):
                    return StrategyDecision(
                        should_pit=True,
                        target_compound=target_comp,
                        reason=f"Scheduled fixed pit stop on lap {current_lap} for {target_comp.value}",
                    )
        return StrategyDecision(should_pit=False)


class OneStopStrategy(BaseStrategyPolicy):
    """Standard 1-stop strategy (Medium -> Hard or Soft -> Hard)."""

    def __init__(
        self,
        target_pit_lap: int = 22,
        secondary_compound: TyreCompound = TyreCompound.HARD,
        sc_reactive: bool = True,
    ):
        self.target_pit_lap = target_pit_lap
        self.secondary_compound = secondary_compound
        self.sc_reactive = sc_reactive

    def evaluate_strategy(self, driver: DriverState, race_state: RaceState) -> StrategyDecision:
        if driver.pit_stop_count >= 1:
            return StrategyDecision(should_pit=False)

        current_lap = race_state.current_lap

        # SC opportunism within acceptable window
        if self.sc_reactive and race_state.safety_car_state in (SafetyCarState.FULL_SC, SafetyCarState.VSC):
            if current_lap >= self.target_pit_lap - 6 and driver.current_tyre_age >= 10:
                return StrategyDecision(
                    should_pit=True,
                    target_compound=self.secondary_compound,
                    reason=f"Opportunistic 1-stop under {race_state.safety_car_state.value} on lap {current_lap}",
                )

        if current_lap >= self.target_pit_lap:
            return StrategyDecision(
                should_pit=True,
                target_compound=self.secondary_compound,
                reason=f"Planned 1-stop window reached on lap {current_lap}",
            )

        return StrategyDecision(should_pit=False)


class TwoStopStrategy(BaseStrategyPolicy):
    """Aggressive 2-stop strategy (e.g., Soft -> Hard -> Medium or Medium -> Hard -> Medium)."""

    def __init__(
        self,
        stop1_lap: int = 16,
        stop1_compound: TyreCompound = TyreCompound.HARD,
        stop2_lap: int = 38,
        stop2_compound: TyreCompound = TyreCompound.MEDIUM,
        sc_reactive: bool = True,
    ):
        self.stop1_lap = stop1_lap
        self.stop1_compound = stop1_compound
        self.stop2_lap = stop2_lap
        self.stop2_compound = stop2_compound
        self.sc_reactive = sc_reactive

    def evaluate_strategy(self, driver: DriverState, race_state: RaceState) -> StrategyDecision:
        current_lap = race_state.current_lap

        if driver.pit_stop_count == 0:
            if self.sc_reactive and race_state.safety_car_state in (SafetyCarState.FULL_SC, SafetyCarState.VSC):
                if current_lap >= self.stop1_lap - 4 and driver.current_tyre_age >= 8:
                    return StrategyDecision(
                        should_pit=True,
                        target_compound=self.stop1_compound,
                        reason=f"Opportunistic Stop 1 under {race_state.safety_car_state.value}",
                    )
            if current_lap >= self.stop1_lap:
                return StrategyDecision(
                    should_pit=True,
                    target_compound=self.stop1_compound,
                    reason=f"Planned Stop 1 window reached on lap {current_lap}",
                )

        elif driver.pit_stop_count == 1:
            if self.sc_reactive and race_state.safety_car_state in (SafetyCarState.FULL_SC, SafetyCarState.VSC):
                if current_lap >= self.stop2_lap - 5 and driver.current_tyre_age >= 10:
                    return StrategyDecision(
                        should_pit=True,
                        target_compound=self.stop2_compound,
                        reason=f"Opportunistic Stop 2 under {race_state.safety_car_state.value}",
                    )
            if current_lap >= self.stop2_lap:
                return StrategyDecision(
                    should_pit=True,
                    target_compound=self.stop2_compound,
                    reason=f"Planned Stop 2 window reached on lap {current_lap}",
                )

        return StrategyDecision(should_pit=False)


class UndercutStrategy(BaseStrategyPolicy):
    """
    Tactical Undercut: Triggers early pit stop when tracking closely behind rival
    to seize track position via out-lap pace advantage.
    """

    def __init__(
        self,
        base_window_start: int = 17,
        base_window_end: int = 24,
        max_undercut_gap_seconds: float = 2.2,
        target_compound: TyreCompound = TyreCompound.HARD,
    ):
        self.window_start = base_window_start
        self.window_end = base_window_end
        self.max_gap = max_undercut_gap_seconds
        self.target_compound = target_compound

    def evaluate_strategy(self, driver: DriverState, race_state: RaceState) -> StrategyDecision:
        if driver.pit_stop_count >= 1:
            return StrategyDecision(should_pit=False)

        current_lap = race_state.current_lap

        # Inside undercut window
        if self.window_start <= current_lap <= self.window_end:
            # Check proximity to car ahead
            if 0.3 <= driver.gap_to_ahead <= self.max_gap:
                return StrategyDecision(
                    should_pit=True,
                    target_compound=self.target_compound,
                    reason=f"Tactical undercut triggered against car ahead on lap {current_lap} (Gap: {driver.gap_to_ahead:.2f}s)",
                )

        # Forced pit at window end if undercut wasn't triggered
        if current_lap >= self.window_end:
            return StrategyDecision(
                should_pit=True,
                target_compound=self.target_compound,
                reason=f"Window limit reached on lap {current_lap}",
            )

        return StrategyDecision(should_pit=False)


class OvercutStrategy(BaseStrategyPolicy):
    """
    Tactical Overcut: Stays out when rival pits, utilizing clear air to set fast flying laps
    before making a later stop.
    """

    def __init__(
        self,
        nominal_pit_lap: int = 24,
        overcut_extension_laps: int = 4,
        target_compound: TyreCompound = TyreCompound.HARD,
    ):
        self.nominal_pit_lap = nominal_pit_lap
        self.extension_laps = overcut_extension_laps
        self.target_compound = target_compound

    def evaluate_strategy(self, driver: DriverState, race_state: RaceState) -> StrategyDecision:
        if driver.pit_stop_count >= 1:
            return StrategyDecision(should_pit=False)

        current_lap = race_state.current_lap
        max_lap = self.nominal_pit_lap + self.extension_laps

        # Extend stint in clear air
        if current_lap >= max_lap:
            return StrategyDecision(
                should_pit=True,
                target_compound=self.target_compound,
                reason=f"Overcut extension concluded on lap {current_lap}",
            )

        return StrategyDecision(should_pit=False)


class SafetyCarReactiveStrategy(BaseStrategyPolicy):
    """
    Opportunistic safety-car reactive policy:
    Pits whenever Full SC or VSC occurs, provided tyres have completed at least 7 laps.
    """

    def __init__(
        self,
        fallback_pit_lap: int = 28,
        primary_compound: TyreCompound = TyreCompound.HARD,
        secondary_compound: TyreCompound = TyreCompound.MEDIUM,
    ):
        self.fallback_pit_lap = fallback_pit_lap
        self.primary_compound = primary_compound
        self.secondary_compound = secondary_compound

    def evaluate_strategy(self, driver: DriverState, race_state: RaceState) -> StrategyDecision:
        current_lap = race_state.current_lap

        # SC or VSC reactive stop
        if race_state.safety_car_state in (SafetyCarState.FULL_SC, SafetyCarState.VSC):
            if driver.current_tyre_age >= 7 and current_lap < race_state.total_laps - 4:
                # Select different compound if required by regulation
                next_comp = (
                    self.primary_compound
                    if driver.current_compound != self.primary_compound
                    else self.secondary_compound
                )
                return StrategyDecision(
                    should_pit=True,
                    target_compound=next_comp,
                    reason=f"SC/VSC Opportunistic pit stop on lap {current_lap} (Saved ~10s transit loss)",
                )

        # Fallback stop if no SC occurs
        if driver.pit_stop_count == 0 and current_lap >= self.fallback_pit_lap:
            return StrategyDecision(
                should_pit=True,
                target_compound=self.primary_compound,
                reason=f"Scheduled fallback 1-stop on lap {current_lap}",
            )

        return StrategyDecision(should_pit=False)
