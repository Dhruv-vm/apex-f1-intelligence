"""Analytical Parquet storage layer for replay telemetry and positions with multi-session support."""
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from backend.geometry import get_circuit_registry
from backend.replay.models import ReplayDriver, ReplayManifest

logger = logging.getLogger("apex.replay.storage")

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
REPLAY_DATA_DIR = PROJECT_ROOT / "data" / "processed" / "replay"


def parse_iso_to_epoch_ms(iso_str: str) -> int:
    """Parse ISO8601 string to millisecond unix timestamp."""
    dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    return int(dt.timestamp() * 1000)


def epoch_ms_to_iso(epoch_ms: int) -> str:
    """Format millisecond unix timestamp to ISO8601 UTC string."""
    dt = datetime.fromtimestamp(epoch_ms / 1000.0, tz=timezone.utc)
    return dt.isoformat()


class ReplayStorage:
    """Manages reading and writing time-partitioned Parquet telemetry and position frames."""

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or REPLAY_DATA_DIR

    def session_dir(self, session_id: int) -> Path:
        """Get storage directory for a specific session."""
        path = self.base_dir / str(session_id)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def manifest_path(self, session_id: int) -> Path:
        return self.session_dir(session_id) / "manifest.json"

    def positions_path(self, session_id: int) -> Path:
        return self.session_dir(session_id) / "positions.parquet"

    def telemetry_path(self, session_id: int) -> Path:
        return self.session_dir(session_id) / "telemetry.parquet"

    def get_manifest(self, session_id: int) -> Optional[ReplayManifest]:
        """Read manifest JSON for session."""
        path = self.manifest_path(session_id)
        if not path.exists():
            # If not built, attempt auto-build for known sessions
            if session_id in (9662, 9558):
                return self.build_replay_data(session_id)
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return ReplayManifest(**data)
        except Exception as e:
            logger.error("Failed loading manifest for session %s: %s", session_id, e)
            return None

    def query_positions(
        self, session_id: int, start_ms: int, end_ms: int, driver_number: Optional[int] = None
    ) -> pd.DataFrame:
        """Query vehicle positions within time window using PyArrow pushdown filters."""
        path = self.positions_path(session_id)
        if not path.exists():
            return pd.DataFrame()

        filters = [
            ("timestamp_ms", ">=", start_ms),
            ("timestamp_ms", "<=", end_ms),
        ]
        if driver_number is not None:
            filters.append(("driver_number", "==", driver_number))

        table = pq.read_table(path, filters=filters)
        df = table.to_pandas()
        return df.sort_values(by=["timestamp_ms", "driver_number"]).reset_index(drop=True)

    def query_telemetry(
        self, session_id: int, start_ms: int, end_ms: int, driver_number: Optional[int] = None
    ) -> pd.DataFrame:
        """Query vehicle telemetry within time window using PyArrow pushdown filters."""
        path = self.telemetry_path(session_id)
        if not path.exists():
            return pd.DataFrame()

        filters = [
            ("timestamp_ms", ">=", start_ms),
            ("timestamp_ms", "<=", end_ms),
        ]
        if driver_number is not None:
            filters.append(("driver_number", "==", driver_number))

        table = pq.read_table(path, filters=filters)
        df = table.to_pandas()
        return df.sort_values(by=["timestamp_ms", "driver_number"]).reset_index(drop=True)

    def build_abu_dhabi_replay_data(self, session_id: int = 9662) -> Optional[ReplayManifest]:
        """Backward-compatible alias for session 9662 build."""
        return self.build_replay_data(session_id)

    def build_replay_data(self, session_id: int) -> Optional[ReplayManifest]:
        """
        Build Parquet datasets and manifest for historical sessions.
        Dynamically selects inputs and circuit geometry based on session ID.
        """
        session_config: Dict[int, Dict[str, str]] = {
            9662: {
                "session_name": "Race",
                "circuit_ref": "yas_marina",
                "circuit_name": "Yas Marina Circuit",
                "loc_file": "yas_marina_lap.json",
                "car_file": "yas_marina_lap_car_data.json",
            },
            9558: {
                "session_name": "Race",
                "circuit_ref": "silverstone",
                "circuit_name": "Silverstone Circuit",
                "loc_file": "silverstone_replay_loc.json",
                "car_file": "silverstone_replay_car.json",
            },
        }

        if session_id not in session_config:
            logger.error("No replay configuration available for session %s", session_id)
            return None

        cfg = session_config[session_id]
        raw_loc_path = PROJECT_ROOT / "data" / "raw" / "openf1" / "geometry" / cfg["loc_file"]
        raw_car_path = PROJECT_ROOT / "data" / "raw" / "openf1" / "geometry" / cfg["car_file"]
        raw_drv_path = PROJECT_ROOT / "data" / "raw" / "openf1" / "drivers" / f"{session_id}.json"

        if not raw_loc_path.exists() or not raw_drv_path.exists():
            logger.error("Missing raw input files for session %s replay build", session_id)
            return None

        # 1. Load Drivers
        with open(raw_drv_path, "r", encoding="utf-8") as f:
            drv_raw = json.load(f)

        drivers_list: List[ReplayDriver] = []
        for d in drv_raw:
            col = d.get("team_colour", "888888")
            if not col.startswith("#"):
                col = f"#{col}"
            drivers_list.append(
                ReplayDriver(
                    driver_number=d["driver_number"],
                    code=d.get("name_acronym", str(d["driver_number"])),
                    name=d.get("broadcast_name", d.get("full_name", f"Driver {d['driver_number']}")),
                    team=d.get("team_name", "Unknown"),
                    color=col,
                )
            )
        drivers_list.sort(key=lambda x: x.driver_number)

        # 2. Load Location Data & Normalize Coordinates with the correct circuit bounds
        registry = get_circuit_registry()
        circuit_geom = registry.get_circuit_geometry(cfg["circuit_ref"])
        transformer = None
        if circuit_geom:
            from backend.geometry.transform import CoordinateTransformer
            transformer = CoordinateTransformer(circuit_geom.bounds, padding=0.05, rotation_deg=0.0)

        with open(raw_loc_path, "r", encoding="utf-8") as f:
            loc_raw = json.load(f)

        pos_records = []
        for r in loc_raw:
            t_ms = parse_iso_to_epoch_ms(r["date"])
            x_val = float(r["x"])
            y_val = float(r["y"])
            z_val = float(r.get("z", 0.0))

            if transformer:
                pt_norm = transformer.normalize(x_val, y_val)
                norm_x = pt_norm.x
                norm_y = pt_norm.y
            else:
                norm_x = 0.5
                norm_y = 0.5

            pos_records.append({
                "timestamp_ms": t_ms,
                "driver_number": int(r["driver_number"]),
                "x": x_val,
                "y": y_val,
                "z": z_val,
                "norm_x": norm_x,
                "norm_y": norm_y,
            })

        pos_df = pd.DataFrame(pos_records).sort_values(by=["timestamp_ms", "driver_number"])
        pos_schema = pa.schema([
            ("timestamp_ms", pa.int64()),
            ("driver_number", pa.int32()),
            ("x", pa.float32()),
            ("y", pa.float32()),
            ("z", pa.float32()),
            ("norm_x", pa.float32()),
            ("norm_y", pa.float32()),
        ])
        pos_table = pa.Table.from_pandas(pos_df, schema=pos_schema, preserve_index=False)
        pq.write_table(pos_table, self.positions_path(session_id), compression="snappy")
        logger.info("Wrote %d position records for session %s", len(pos_df), session_id)

        # 3. Load Telemetry Data (car_data)
        tel_records = []
        if raw_car_path.exists():
            with open(raw_car_path, "r", encoding="utf-8") as f:
                car_raw = json.load(f)
            for r in car_raw:
                tel_records.append({
                    "timestamp_ms": parse_iso_to_epoch_ms(r["date"]),
                    "driver_number": int(r["driver_number"]),
                    "speed": int(r.get("speed", 0)),
                    "throttle": int(r.get("throttle", 0)),
                    "brake": int(r.get("brake", 0)),
                    "gear": int(r.get("n_gear", 0)),
                    "rpm": int(r.get("rpm", 0)),
                    "drs": int(r.get("drs", 0)),
                })
        tel_df = pd.DataFrame(tel_records).sort_values(by=["timestamp_ms", "driver_number"])
        tel_schema = pa.schema([
            ("timestamp_ms", pa.int64()),
            ("driver_number", pa.int32()),
            ("speed", pa.int32()),
            ("throttle", pa.int32()),
            ("brake", pa.int32()),
            ("gear", pa.int32()),
            ("rpm", pa.int32()),
            ("drs", pa.int32()),
        ])
        tel_table = pa.Table.from_pandas(tel_df, schema=tel_schema, preserve_index=False)
        pq.write_table(tel_table, self.telemetry_path(session_id), compression="snappy")
        logger.info("Wrote %d telemetry records for session %s", len(tel_df), session_id)

        # 4. Manifest metadata
        min_ms = int(pos_df["timestamp_ms"].min())
        max_ms = int(pos_df["timestamp_ms"].max())
        duration_sec = round((max_ms - min_ms) / 1000.0, 2)
        # Full Grand Prix is approx 110-120 minutes (6600-7200 seconds)
        coverage_pct = round((duration_sec / 7000.0) * 100, 3)

        manifest = ReplayManifest(
            session_id=session_id,
            session_name=cfg["session_name"],
            circuit_ref=cfg["circuit_ref"],
            circuit_name=cfg["circuit_name"],
            t_start=epoch_ms_to_iso(min_ms),
            t_end=epoch_ms_to_iso(max_ms),
            start_epoch_ms=min_ms,
            end_epoch_ms=max_ms,
            duration_seconds=duration_sec,
            sample_rate_hz=3.8,
            driver_count=len(drivers_list),
            drivers=drivers_list,
            coverage_type="OPENING_LAP_REPLAY_WINDOW",
            coverage_ratio_pct=coverage_pct,
        )

        with open(self.manifest_path(session_id), "w", encoding="utf-8") as f:
            f.write(manifest.model_dump_json(indent=2))
        logger.info("Wrote manifest for session %s to %s", session_id, self.manifest_path(session_id))

        return manifest


storage = ReplayStorage()


def get_replay_storage() -> ReplayStorage:
    return storage
