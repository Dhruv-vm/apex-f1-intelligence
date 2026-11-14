"""Data models and schemas for historical replay engine."""
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class ReplayDriver(BaseModel):
    """Driver metadata in replay manifest."""
    driver_number: int
    code: str
    name: str
    team: str
    color: str  # Hex string with # prefix


class ReplayManifest(BaseModel):
    """Replay session manifest and metadata."""
    session_id: int
    session_name: str
    circuit_ref: str
    circuit_name: str
    t_start: str
    t_end: str
    start_epoch_ms: int
    end_epoch_ms: int
    duration_seconds: float
    sample_rate_hz: float
    driver_count: int
    drivers: List[ReplayDriver]
    coverage_type: str = "OPENING_LAP_REPLAY_WINDOW"  # Explicitly documents window vs full race
    coverage_ratio_pct: Optional[float] = None


class CarState(BaseModel):
    """Point-in-time state for an individual car."""
    driver_number: int
    x: float
    y: float
    norm_x: float
    norm_y: float
    speed: Optional[int] = None
    throttle: Optional[int] = None
    brake: Optional[int] = None
    gear: Optional[int] = None
    rpm: Optional[int] = None
    drs: Optional[int] = None


class ReplayFrame(BaseModel):
    """Synchronized frame of all active cars at a specific timestamp."""
    timestamp_ms: int
    timestamp_iso: str
    cars: Dict[str, CarState] = Field(
        default_factory=dict,
        description="Map of driver_number string to CarState"
    )


class ReplayFramesResponse(BaseModel):
    """Batch of replay frames response."""
    session_id: int
    start_ms: int
    end_ms: int
    frame_count: int
    frames: List[ReplayFrame]


class TelemetryPoint(BaseModel):
    """Single telemetry observation for a car."""
    timestamp_ms: int
    timestamp_iso: str
    driver_number: int
    speed: int
    throttle: int
    brake: int
    gear: int
    rpm: int
    drs: int


class TelemetryResponse(BaseModel):
    """Telemetry stream response for a driver."""
    session_id: int
    driver_number: int
    point_count: int
    data: List[TelemetryPoint]
