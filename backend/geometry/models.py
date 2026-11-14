"""Circuit geometry Pydantic schemas."""
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class Point2D(BaseModel):
    """2D coordinate representation."""
    x: float
    y: float


class CircuitBounds(BaseModel):
    """Bounding box for track coordinates."""
    min_x: float
    max_x: float
    min_y: float
    max_y: float
    width: float
    height: float


class SectorSplit(BaseModel):
    """Sector boundary marker."""
    sector: int = Field(..., ge=1, le=3)
    point: Point2D
    distance_pct: float = Field(..., ge=0.0, le=100.0)


class CornerMarker(BaseModel):
    """Corner / Turn representation on track."""
    number: int
    name: Optional[str] = None
    point: Point2D
    turn_type: Optional[str] = None  # e.g. "Hairpin", "High-speed", "Chicane"


class CircuitGeometry(BaseModel):
    """Full circuit geometry specification with provenance and validation status."""
    circuit_ref: str
    name: str
    alt_names: List[str] = Field(default_factory=list)
    country: str
    length_meters: float
    corners_count: int = 0
    bounds: CircuitBounds
    centerline: List[Point2D]
    normalized_centerline: List[Point2D]
    sectors: List[SectorSplit]
    start_finish: Point2D
    pit_entry: Optional[Point2D] = None
    pit_exit: Optional[Point2D] = None
    corners: List[CornerMarker] = Field(default_factory=list)
    rotation_deg: float = 0.0
    provenance: str = "Derived from verified telemetry samples"
    geometry_version: str = "v1.0"
    validation_status: str = "VERIFIED"  # "VERIFIED", "APPROXIMATE", "UNAVAILABLE"
