"""Circuit geometry registry and loader with multi-circuit support."""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from backend.geometry.models import (
    CircuitBounds,
    CircuitGeometry,
    CornerMarker,
    Point2D,
    SectorSplit,
)
from backend.geometry.transform import CoordinateTransformer, compute_bounds

logger = logging.getLogger("apex.geometry")

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class CircuitRegistry:
    """Registry maintaining verified circuit geometry representations with multi-circuit support."""

    def __init__(self):
        self._cache: Dict[str, CircuitGeometry] = {}
        # Alias map for canonical lookup
        self._aliases: Dict[str, str] = {
            "yas_marina": "yas_marina",
            "abu_dhabi": "yas_marina",
            "yas_marina_circuit": "yas_marina",
            "silverstone": "silverstone",
            "silverstone_circuit": "silverstone",
            "british": "silverstone",
            "uk": "silverstone",
        }

    def resolve_canonical_ref(self, ref_or_name: str) -> Optional[str]:
        """Normalize circuit reference or name to canonical identifier."""
        norm_key = ref_or_name.strip().lower().replace(" ", "_").replace("-", "_")
        return self._aliases.get(norm_key, norm_key if norm_key in self._cache else None)

    def list_available_circuits(self) -> List[Dict[str, str]]:
        """List all available circuits and their validation status."""
        return [
            {
                "circuit_ref": "yas_marina",
                "name": "Yas Marina Circuit",
                "country": "United Arab Emirates",
                "length_meters": "5281",
                "validation_status": "VERIFIED",
                "provenance": "OpenF1 telemetry Lap 4 Norris (Session 9662)",
            },
            {
                "circuit_ref": "silverstone",
                "name": "Silverstone Circuit",
                "country": "United Kingdom",
                "length_meters": "5891",
                "validation_status": "VERIFIED",
                "provenance": "OpenF1 telemetry Lap 5 Hamilton/Norris cross-validated (Session 9558)",
            },
        ]

    def get_circuit_geometry(self, circuit_ref: str) -> Optional[CircuitGeometry]:
        """Retrieve geometry for a given circuit reference key."""
        canonical = self.resolve_canonical_ref(circuit_ref)
        if not canonical:
            logger.warning("No canonical mapping for circuit '%s'", circuit_ref)
            return None

        if canonical in self._cache:
            return self._cache[canonical]

        if canonical == "yas_marina":
            geom = self._build_yas_marina_geometry()
            if geom:
                self._cache[canonical] = geom
                return geom

        if canonical == "silverstone":
            geom = self._build_silverstone_geometry()
            if geom:
                self._cache[canonical] = geom
                return geom

        logger.warning("No circuit geometry available for '%s' (canonical: '%s')", circuit_ref, canonical)
        return None

    def _build_yas_marina_geometry(self) -> Optional[CircuitGeometry]:
        """Construct canonical geometry for Yas Marina Circuit from Lap 4 ground truth."""
        raw_path = PROJECT_ROOT / "data" / "raw" / "openf1" / "geometry" / "yas_marina_lap4_centerline.json"
        
        raw_points: List[Point2D] = []
        if raw_path.exists():
            try:
                with open(raw_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for pt in data:
                        raw_points.append(Point2D(x=float(pt["x"]), y=float(pt["y"])))
            except Exception as e:
                logger.error("Failed loading raw geometry from %s: %s", raw_path, e)

        if not raw_points:
            return None

        bounds = compute_bounds(raw_points)
        transformer = CoordinateTransformer(bounds=bounds, padding=0.05, rotation_deg=0.0)
        norm_centerline = transformer.normalize_list(raw_points)

        dists = [0.0]
        for i in range(1, len(raw_points)):
            dx = raw_points[i].x - raw_points[i-1].x
            dy = raw_points[i].y - raw_points[i-1].y
            dists.append(dists[-1] + (dx**2 + dy**2)**0.5)
        total_dist = dists[-1] if dists[-1] > 0 else 1.0

        idx_s1 = min(range(len(dists)), key=lambda i: abs(dists[i] - total_dist * 0.205))
        idx_s2 = min(range(len(dists)), key=lambda i: abs(dists[i] - total_dist * 0.633))

        sectors = [
            SectorSplit(sector=1, point=norm_centerline[idx_s1], distance_pct=round(dists[idx_s1] / total_dist * 100, 2)),
            SectorSplit(sector=2, point=norm_centerline[idx_s2], distance_pct=round(dists[idx_s2] / total_dist * 100, 2)),
            SectorSplit(sector=3, point=norm_centerline[-1], distance_pct=100.0),
        ]

        # Key turns on Yas Marina layout
        corners = [
            CornerMarker(number=1, name="Turn 1", point=norm_centerline[int(len(norm_centerline) * 0.05)], turn_type="Medium-speed Left"),
            CornerMarker(number=5, name="Turn 5 (Hairpin)", point=norm_centerline[idx_s1], turn_type="Hairpin"),
            CornerMarker(number=6, name="Turn 6/7 Chicane", point=norm_centerline[int(len(norm_centerline) * 0.35)], turn_type="Chicane"),
            CornerMarker(number=9, name="Turn 9", point=norm_centerline[idx_s2], turn_type="Banked Sweeper"),
            CornerMarker(number=12, name="Turn 12", point=norm_centerline[int(len(norm_centerline) * 0.78)], turn_type="Right 90 deg"),
        ]

        return CircuitGeometry(
            circuit_ref="yas_marina",
            name="Yas Marina Circuit",
            alt_names=["Abu Dhabi", "Yas Marina Circuit", "Yas Island"],
            country="United Arab Emirates",
            length_meters=5281.0,
            corners_count=16,
            bounds=bounds,
            centerline=raw_points,
            normalized_centerline=norm_centerline,
            sectors=sectors,
            start_finish=norm_centerline[0],
            corners=corners,
            rotation_deg=0.0,
            provenance="OpenF1 telemetry Lap 4 Norris (Session 9662, closure < 62 units)",
            geometry_version="v1.1-verified",
            validation_status="VERIFIED",
        )

    def _build_silverstone_geometry(self) -> Optional[CircuitGeometry]:
        """Construct canonical geometry for Silverstone Circuit from Hamilton/Norris Lap 5."""
        raw_path = PROJECT_ROOT / "data" / "raw" / "openf1" / "geometry" / "silverstone_lap5_centerline.json"
        
        raw_points: List[Point2D] = []
        if raw_path.exists():
            try:
                with open(raw_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for pt in data:
                        raw_points.append(Point2D(x=float(pt["x"]), y=float(pt["y"])))
            except Exception as e:
                logger.error("Failed loading raw geometry from %s: %s", raw_path, e)

        if not raw_points:
            return None

        bounds = compute_bounds(raw_points)
        transformer = CoordinateTransformer(bounds=bounds, padding=0.05, rotation_deg=0.0)
        norm_centerline = transformer.normalize_list(raw_points)

        dists = [0.0]
        for i in range(1, len(raw_points)):
            dx = raw_points[i].x - raw_points[i-1].x
            dy = raw_points[i].y - raw_points[i-1].y
            dists.append(dists[-1] + (dx**2 + dy**2)**0.5)
        total_dist = dists[-1] if dists[-1] > 0 else 1.0

        # S1 split: ~32.14% of lap distance, S2 split: ~72.75% of lap distance
        idx_s1 = min(range(len(dists)), key=lambda i: abs(dists[i] - total_dist * 0.3214))
        idx_s2 = min(range(len(dists)), key=lambda i: abs(dists[i] - total_dist * 0.7275))

        sectors = [
            SectorSplit(sector=1, point=norm_centerline[idx_s1], distance_pct=round(dists[idx_s1] / total_dist * 100, 2)),
            SectorSplit(sector=2, point=norm_centerline[idx_s2], distance_pct=round(dists[idx_s2] / total_dist * 100, 2)),
            SectorSplit(sector=3, point=norm_centerline[-1], distance_pct=100.0),
        ]

        # Legendary Silverstone corners
        corners = [
            CornerMarker(number=1, name="Abbey", point=norm_centerline[int(len(norm_centerline) * 0.08)], turn_type="Fast Right"),
            CornerMarker(number=3, name="Village", point=norm_centerline[int(len(norm_centerline) * 0.16)], turn_type="Slow Right"),
            CornerMarker(number=4, name="The Loop", point=norm_centerline[int(len(norm_centerline) * 0.22)], turn_type="Hairpin"),
            CornerMarker(number=6, name="Brooklands", point=norm_centerline[idx_s1], turn_type="Medium Left"),
            CornerMarker(number=9, name="Copse", point=norm_centerline[int(len(norm_centerline) * 0.48)], turn_type="Ultra High-speed Right"),
            CornerMarker(number=11, name="Maggotts / Becketts", point=norm_centerline[int(len(norm_centerline) * 0.60)], turn_type="High-speed S-bends"),
            CornerMarker(number=15, name="Stowe", point=norm_centerline[idx_s2], turn_type="Fast Right"),
            CornerMarker(number=16, name="Vale", point=norm_centerline[int(len(norm_centerline) * 0.88)], turn_type="Chicane"),
            CornerMarker(number=18, name="Club", point=norm_centerline[-1], turn_type="Medium Right"),
        ]

        return CircuitGeometry(
            circuit_ref="silverstone",
            name="Silverstone Circuit",
            alt_names=["British Grand Prix", "Silverstone", "UK"],
            country="United Kingdom",
            length_meters=5891.0,
            corners_count=18,
            bounds=bounds,
            centerline=raw_points,
            normalized_centerline=norm_centerline,
            sectors=sectors,
            start_finish=norm_centerline[0],
            corners=corners,
            rotation_deg=0.0,
            provenance="OpenF1 telemetry Lap 5 Hamilton/Norris cross-validated (Session 9558, divergence < 53 units)",
            geometry_version="v1.0-verified",
            validation_status="VERIFIED",
        )


registry = CircuitRegistry()


def get_circuit_registry() -> CircuitRegistry:
    """Dependency injector for circuit registry."""
    return registry
