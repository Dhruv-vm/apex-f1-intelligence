"""Circuit geometry module."""
from backend.geometry.models import (
    CircuitBounds,
    CircuitGeometry,
    CornerMarker,
    Point2D,
    SectorSplit,
)
from backend.geometry.registry import CircuitRegistry, get_circuit_registry
from backend.geometry.transform import CoordinateTransformer, compute_bounds

__all__ = [
    "Point2D",
    "CircuitBounds",
    "SectorSplit",
    "CornerMarker",
    "CircuitGeometry",
    "CoordinateTransformer",
    "compute_bounds",
    "CircuitRegistry",
    "get_circuit_registry",
]
