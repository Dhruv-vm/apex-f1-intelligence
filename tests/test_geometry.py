"""Unit tests for circuit geometry and coordinate transformation."""
import pytest
from backend.geometry import (
    CircuitBounds,
    CoordinateTransformer,
    Point2D,
    compute_bounds,
    get_circuit_registry,
)


def test_compute_bounds():
    points = [
        Point2D(x=10.0, y=20.0),
        Point2D(x=-5.0, y=50.0),
        Point2D(x=100.0, y=-10.0),
    ]
    bounds = compute_bounds(points)
    assert bounds.min_x == -5.0
    assert bounds.max_x == 100.0
    assert bounds.min_y == -10.0
    assert bounds.max_y == 50.0
    assert bounds.width == 105.0
    assert bounds.height == 60.0


def test_coordinate_transformer_normalization():
    bounds = CircuitBounds(min_x=0.0, max_x=100.0, min_y=0.0, max_y=100.0, width=100.0, height=100.0)
    # With 0 padding, corners map to [0, 1]
    transformer = CoordinateTransformer(bounds, padding=0.0)
    
    p_center = transformer.normalize(50.0, 50.0)
    assert p_center.x == pytest.approx(0.5, abs=1e-3)
    assert p_center.y == pytest.approx(0.5, abs=1e-3)

    p_bottom_left = transformer.normalize(0.0, 0.0)
    assert p_bottom_left.x == pytest.approx(0.0, abs=1e-3)
    assert p_bottom_left.y == pytest.approx(0.0, abs=1e-3)

    p_top_right = transformer.normalize(100.0, 100.0)
    assert p_top_right.x == pytest.approx(1.0, abs=1e-3)
    assert p_top_right.y == pytest.approx(1.0, abs=1e-3)


def test_coordinate_transformer_canvas_projection():
    bounds = CircuitBounds(min_x=0.0, max_x=100.0, min_y=0.0, max_y=100.0, width=100.0, height=100.0)
    transformer = CoordinateTransformer(bounds, padding=0.0)
    
    # Top-right Cartesian (1.0, 1.0) maps to Canvas top-right (width, 0)
    cx, cy = transformer.to_canvas(1.0, 1.0, width=800, height=600, invert_y=True)
    assert cx == 800.0
    assert cy == 0.0

    # Bottom-left Cartesian (0.0, 0.0) maps to Canvas bottom-left (0, height)
    cx0, cy0 = transformer.to_canvas(0.0, 0.0, width=800, height=600, invert_y=True)
    assert cx0 == 0.0
    assert cy0 == 600.0


def test_circuit_registry_yas_marina():
    registry = get_circuit_registry()
    geom = registry.get_circuit_geometry("yas_marina")
    assert geom is not None
    assert geom.circuit_ref == "yas_marina"
    assert geom.length_meters == 5281.0
    assert len(geom.centerline) > 300
    assert len(geom.normalized_centerline) == len(geom.centerline)
    assert len(geom.sectors) == 3
    assert len(geom.corners) > 0
    assert geom.validation_status == "VERIFIED"
    
    # Verify all normalized points are strictly within [0, 1]
    for pt in geom.normalized_centerline:
        assert 0.0 <= pt.x <= 1.0
        assert 0.0 <= pt.y <= 1.0


def test_circuit_registry_silverstone():
    registry = get_circuit_registry()
    geom = registry.get_circuit_geometry("silverstone")
    assert geom is not None
    assert geom.circuit_ref == "silverstone"
    assert geom.length_meters == 5891.0
    assert len(geom.centerline) > 300
    assert len(geom.sectors) == 3
    assert len(geom.corners) >= 8
    assert geom.validation_status == "VERIFIED"

    # Test alias resolution
    geom_alias = registry.get_circuit_geometry("british")
    assert geom_alias is not None
    assert geom_alias.circuit_ref == "silverstone"


def test_circuit_registry_list_available():
    registry = get_circuit_registry()
    circuits = registry.list_available_circuits()
    assert len(circuits) >= 2
    refs = [c["circuit_ref"] for c in circuits]
    assert "yas_marina" in refs
    assert "silverstone" in refs


def test_circuit_registry_unknown_circuit():
    registry = get_circuit_registry()
    assert registry.get_circuit_geometry("non_existent_circuit") is None
