"""APEX — Race State Models for Discrete-Lap Simulation (Phase 7 / EXP-0006).

Defines canonical representations for driver and race-level state at discrete lap transitions.
Guarantees position tracking is strictly derived from accumulated progress and race time.
"""
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TyreCompound(str, Enum):
    SOFT = "SOFT"
    MEDIUM = "MEDIUM"
    HARD = "HARD"
    INTERMEDIATE = "INTERMEDIATE"
    WET = "WET"


class DriverStatus(str, Enum):
    RUNNING = "RUNNING"
    FINISHED = "FINISHED"
    RETIRED = "RETIRED"
    DNF = "DNF"
    DNS = "DNS"
    DISQUALIFIED = "DISQUALIFIED"


class SafetyCarState(str, Enum):
    NONE = "NONE"
    VSC = "VSC"
    FULL_SC = "FULL_SC"
    RED_FLAG = "RED_FLAG"


class TrackCondition(str, Enum):
    DRY = "DRY"
    DAMP = "DAMP"
    WET = "WET"


class PitStopRecord(BaseModel):
    """Record of a single pit stop execution."""
    lap: int
    stint_completed: int
    compound_fitted: TyreCompound
    stationary_duration_seconds: float
    transit_loss_seconds: float
    total_pit_loss_seconds: float
    pit_under_safety_car: bool
    pit_under_vsc: bool
    double_stacked: bool = False
    delay_seconds: float = 0.0


class DriverState(BaseModel):
    """Point-in-time state of an individual driver in the simulated race."""
    driver_id: str
    driver_name: str
    constructor_id: str
    starting_grid: int
    current_position: Optional[int] = None  # None if DISQUALIFIED or unclassified
    classified_position: Optional[int] = None  # Formal sporting classification rank
    classification_display: str = ""  # Human readable: "1", "P1", "DNF", "DSQ"
    is_classified: bool = True  # True if classified finisher; False if DNF or DSQ
    current_lap: int = 0
    accumulated_race_time: float = 0.0  # Total elapsed race time in seconds
    current_compound: TyreCompound = TyreCompound.MEDIUM
    current_tyre_age: int = 0  # Laps on current set
    current_stint: int = 1
    compounds_used: List[TyreCompound] = Field(default_factory=list)
    pit_stop_count: int = 0
    pit_stop_history: List[PitStopRecord] = Field(default_factory=list)
    status: DriverStatus = DriverStatus.RUNNING
    retirement_lap: Optional[int] = None
    retirement_reason: Optional[str] = None
    base_pace_seconds: float = 85.0
    driver_pace_sigma: float = 0.25
    gap_to_leader: float = 0.0
    gap_to_ahead: float = 0.0
    last_lap_time: Optional[float] = None
    fastest_lap_time: Optional[float] = None
    laps_led: int = 0
    overtakes_completed: int = 0
    times_overtaken: int = 0

    def is_active(self) -> bool:
        return self.status == DriverStatus.RUNNING


class RaceEventRecord(BaseModel):
    """Stochastic or regulatory event during simulation."""
    lap: int
    event_type: str  # SAFETY_CAR, VSC, RETIREMENT, OVERTAKE, WEATHER_CHANGE, PIT_STOP
    driver_id: Optional[str] = None
    description: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CircuitProfile(BaseModel):
    """Circuit-specific parameters governing race simulation dynamics."""
    circuit_id: str
    circuit_name: str
    total_laps: int
    base_lap_time_seconds: float
    pit_transit_loss_seconds: float  # Normal racing pit lane loss excluding stationary service
    overtaking_difficulty_index: float = 0.60  # [0.0 = very easy, 1.0 = near impossible]
    safety_car_hazard_rate_per_lap: float = 0.015  # Empirical prior (346 races)
    vsc_hazard_rate_per_lap: float = 0.012  # Empirical prior (2015-2024)
    track_evolution_gain_per_lap: float = 0.012  # Seconds shaved off per lap as rubber is laid
    fuel_effect_seconds_per_kg: float = 0.033  # Latent sensitivity
    drs_activation_zones: int = 2  # Predetermined FIA Article 22.1 activation zones
    drs_zone_lap_fraction: float = 0.20  # Fraction of lap distance spent inside activation zones
    drs_configuration_mode: str = "CIRCUIT_SPECIFIC"  # "CIRCUIT_SPECIFIC" or "SIMPLIFIED_ASSUMPTION"
    nominated_compounds: Dict[str, str] = Field(
        default_factory=lambda: {"SOFT": "C5", "MEDIUM": "C4", "HARD": "C3"}
    )  # Event-specific Pirelli compound allocations


class RaceState(BaseModel):
    """Complete race-level state at any discrete lap boundary."""
    race_id: str
    circuit: CircuitProfile
    season: int = 2024
    round_num: int = 24
    current_lap: int = 0
    total_laps: int = 58
    track_condition: TrackCondition = TrackCondition.DRY
    air_temp_celsius: float = 27.0
    track_temp_celsius: float = 34.0
    weather_state: str = "CLEAR"
    safety_car_state: SafetyCarState = SafetyCarState.NONE
    sc_laps_remaining: int = 0
    vsc_escalation_checked: bool = False  # Track whether active VSC episode already evaluated escalation
    drivers: Dict[str, DriverState] = Field(default_factory=dict)
    events_log: List[RaceEventRecord] = Field(default_factory=list)
    initial_fuel_kg: float = 105.0  # Latent assumed fuel mass
    fuel_burn_rate_kg_per_lap: float = 1.75  # Latent fuel burn-off rate
