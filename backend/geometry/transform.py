"""Circuit coordinate transformation and normalization engine."""
import math
from typing import List, Tuple
from backend.geometry.models import CircuitBounds, Point2D


class CoordinateTransformer:
    """Transforms raw circuit coordinates to normalized and screen projection coordinates."""

    def __init__(self, bounds: CircuitBounds, padding: float = 0.05, rotation_deg: float = 0.0):
        """
        Initialize transformer with bounding box.
        
        Args:
            bounds: CircuitBounds of the raw coordinates.
            padding: fractional margin around the bounds (default 5%).
            rotation_deg: rotation angle in degrees around the track centroid.
        """
        self.bounds = bounds
        self.padding = padding
        self.rotation_deg = rotation_deg
        
        self.center_x = (bounds.min_x + bounds.max_x) / 2.0
        self.center_y = (bounds.min_y + bounds.max_y) / 2.0
        
        span_x = bounds.width
        span_y = bounds.height
        
        # In case rotation is applied, determine new extents
        if rotation_deg != 0.0:
            rad = math.radians(rotation_deg)
            cos_r = abs(math.cos(rad))
            sin_r = abs(math.sin(rad))
            eff_span_x = span_x * cos_r + span_y * sin_r
            eff_span_y = span_x * sin_r + span_y * cos_r
            max_span = max(eff_span_x, eff_span_y)
        else:
            max_span = max(span_x, span_y)
            
        self.scale_span = max_span * (1.0 + 2.0 * padding)

    def rotate_point(self, x: float, y: float) -> Tuple[float, float]:
        """Rotate point around center by rotation_deg."""
        if self.rotation_deg == 0.0:
            return x, y
        rad = math.radians(self.rotation_deg)
        dx = x - self.center_x
        dy = y - self.center_y
        rx = dx * math.cos(rad) - dy * math.sin(rad) + self.center_x
        ry = dx * math.sin(rad) + dy * math.cos(rad) + self.center_y
        return rx, ry

    def normalize(self, x: float, y: float) -> Point2D:
        """
        Normalize raw coordinates to [0, 1] x [0, 1] range.
        Maintains aspect ratio and centers the circuit.
        """
        rx, ry = self.rotate_point(x, y)
        norm_x = (rx - self.center_x) / self.scale_span + 0.5
        norm_y = (ry - self.center_y) / self.scale_span + 0.5
        return Point2D(x=round(norm_x, 5), y=round(norm_y, 5))

    def normalize_list(self, points: List[Point2D]) -> List[Point2D]:
        """Normalize a sequence of points."""
        return [self.normalize(p.x, p.y) for p in points]

    def to_canvas(self, norm_x: float, norm_y: float, width: float, height: float, invert_y: bool = True) -> Tuple[float, float]:
        """
        Map normalized coordinates [0, 1] into pixel space for HTML5 Canvas.
        By default inverts Y to account for Canvas top-left origin vs Cartesian bottom-left.
        """
        px = norm_x * width
        py = (1.0 - norm_y) * height if invert_y else norm_y * height
        return px, py


def compute_bounds(points: List[Point2D]) -> CircuitBounds:
    """Compute axis-aligned bounding box for a set of 2D points."""
    if not points:
        return CircuitBounds(min_x=0.0, max_x=0.0, min_y=0.0, max_y=0.0, width=0.0, height=0.0)
    
    xs = [p.x for p in points]
    ys = [p.y for p in points]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    return CircuitBounds(
        min_x=min_x,
        max_x=max_x,
        min_y=min_y,
        max_y=max_y,
        width=max_x - min_x,
        height=max_y - min_y
    )
