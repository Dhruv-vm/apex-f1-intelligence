"""Causal replay filter and synchronized frame generator.

Enforces strict temporal causality: state at evaluation time t is constructed
exclusively using observations recorded at or before t (t_obs <= t).
Zero lookahead leakage is guaranteed.
"""
import logging
from typing import Dict, List, Optional
import pandas as pd

from backend.replay.models import CarState, ReplayFrame, ReplayFramesResponse
from backend.replay.storage import ReplayStorage, epoch_ms_to_iso, get_replay_storage

logger = logging.getLogger("apex.replay.causal_filter")


class CausalReplayEngine:
    """Synchronized frame engine enforcing causal temporal boundaries."""

    def __init__(self, storage: Optional[ReplayStorage] = None, max_staleness_ms: int = 3500):
        """
        Initialize causal replay engine.
        
        Args:
            storage: ReplayStorage analytical layer instance.
            max_staleness_ms: Maximum allowable observation age before marking a car inactive.
        """
        self.storage = storage or get_replay_storage()
        self.max_staleness_ms = max_staleness_ms

    def get_frame_at(self, session_id: int, target_ms: int) -> ReplayFrame:
        """
        Compute vehicle states strictly at or before target_ms.
        Guarantees causal invariant: for all included observations, t_obs <= target_ms.
        """
        # Look back only within the staleness window: [target_ms - max_staleness_ms, target_ms]
        start_ms = max(0, target_ms - self.max_staleness_ms)
        pos_df = self.storage.query_positions(session_id, start_ms=start_ms, end_ms=target_ms)
        tel_df = self.storage.query_telemetry(session_id, start_ms=start_ms, end_ms=target_ms)

        cars: Dict[str, CarState] = {}

        if not pos_df.empty:
            # Group by driver and pick the latest observation <= target_ms
            # Since pos_df is filtered to timestamp_ms <= target_ms, the tail observation is the latest valid point
            latest_pos = pos_df.groupby("driver_number").last().reset_index()

            # Latest telemetry per driver
            latest_tel = {}
            if not tel_df.empty:
                latest_tel = tel_df.groupby("driver_number").last().to_dict(orient="index")

            for _, row in latest_pos.iterrows():
                drv_num = int(row["driver_number"])
                obs_time = int(row["timestamp_ms"])

                # Causal assertion: strictly verify zero lookahead
                assert obs_time <= target_ms, f"Causal violation: obs_time {obs_time} > target {target_ms}"

                tel_data = latest_tel.get(drv_num, {})

                car_state = CarState(
                    driver_number=drv_num,
                    x=float(row["x"]),
                    y=float(row["y"]),
                    norm_x=float(row["norm_x"]),
                    norm_y=float(row["norm_y"]),
                    speed=int(tel_data["speed"]) if "speed" in tel_data else None,
                    throttle=int(tel_data["throttle"]) if "throttle" in tel_data else None,
                    brake=int(tel_data["brake"]) if "brake" in tel_data else None,
                    gear=int(tel_data["gear"]) if "gear" in tel_data else None,
                    rpm=int(tel_data["rpm"]) if "rpm" in tel_data else None,
                    drs=int(tel_data["drs"]) if "drs" in tel_data else None,
                )
                cars[str(drv_num)] = car_state

        return ReplayFrame(
            timestamp_ms=target_ms,
            timestamp_iso=epoch_ms_to_iso(target_ms),
            cars=cars,
        )

    def get_frames_slice(
        self,
        session_id: int,
        start_ms: int,
        end_ms: int,
        interval_ms: int = 500,  # 2.0 Hz default playback frame rate
    ) -> ReplayFramesResponse:
        """
        Generate time-sequenced replay frames between start_ms and end_ms.
        Every single frame t_k strictly satisfies causal ordering.
        """
        # Validate time bounds against manifest
        manifest = self.storage.get_manifest(session_id)
        if not manifest:
            return ReplayFramesResponse(
                session_id=session_id,
                start_ms=start_ms,
                end_ms=end_ms,
                frame_count=0,
                frames=[],
            )

        eff_start = max(manifest.start_epoch_ms, start_ms)
        eff_end = min(manifest.end_epoch_ms, end_ms)

        if eff_start > eff_end:
            return ReplayFramesResponse(
                session_id=session_id,
                start_ms=start_ms,
                end_ms=end_ms,
                frame_count=0,
                frames=[],
            )

        # Batch query position & telemetry for the entire range plus lookback window
        query_start = max(0, eff_start - self.max_staleness_ms)
        all_pos_df = self.storage.query_positions(session_id, query_start, eff_end)
        all_tel_df = self.storage.query_telemetry(session_id, query_start, eff_end)

        frames: List[ReplayFrame] = []
        curr_t = eff_start

        while curr_t <= eff_end:
            # Strict causal slice: only observations <= curr_t within staleness window
            window_start = curr_t - self.max_staleness_ms
            
            sub_pos = all_pos_df[
                (all_pos_df["timestamp_ms"] >= window_start) & (all_pos_df["timestamp_ms"] <= curr_t)
            ]
            sub_tel = all_tel_df[
                (all_tel_df["timestamp_ms"] >= window_start) & (all_tel_df["timestamp_ms"] <= curr_t)
            ]

            cars: Dict[str, CarState] = {}
            if not sub_pos.empty:
                latest_pos = sub_pos.groupby("driver_number").last().reset_index()
                latest_tel = {}
                if not sub_tel.empty:
                    latest_tel = sub_tel.groupby("driver_number").last().to_dict(orient="index")

                for _, row in latest_pos.iterrows():
                    drv_num = int(row["driver_number"])
                    obs_time = int(row["timestamp_ms"])
                    assert obs_time <= curr_t, f"Lookahead violation: {obs_time} > {curr_t}"

                    tel_data = latest_tel.get(drv_num, {})
                    cars[str(drv_num)] = CarState(
                        driver_number=drv_num,
                        x=float(row["x"]),
                        y=float(row["y"]),
                        norm_x=float(row["norm_x"]),
                        norm_y=float(row["norm_y"]),
                        speed=int(tel_data["speed"]) if "speed" in tel_data else None,
                        throttle=int(tel_data["throttle"]) if "throttle" in tel_data else None,
                        brake=int(tel_data["brake"]) if "brake" in tel_data else None,
                        gear=int(tel_data["gear"]) if "gear" in tel_data else None,
                        rpm=int(tel_data["rpm"]) if "rpm" in tel_data else None,
                        drs=int(tel_data["drs"]) if "drs" in tel_data else None,
                    )

            frames.append(
                ReplayFrame(
                    timestamp_ms=curr_t,
                    timestamp_iso=epoch_ms_to_iso(curr_t),
                    cars=cars,
                )
            )
            curr_t += interval_ms

        return ReplayFramesResponse(
            session_id=session_id,
            start_ms=eff_start,
            end_ms=eff_end,
            frame_count=len(frames),
            frames=frames,
        )


engine = CausalReplayEngine()


def get_causal_replay_engine() -> CausalReplayEngine:
    return engine
