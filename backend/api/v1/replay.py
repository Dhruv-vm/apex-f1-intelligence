"""Historical race replay endpoints."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.replay.causal_filter import CausalReplayEngine, get_causal_replay_engine
from backend.replay.models import (
    ReplayFramesResponse,
    ReplayManifest,
    TelemetryPoint,
    TelemetryResponse,
)
from backend.replay.storage import ReplayStorage, epoch_ms_to_iso, get_replay_storage

router = APIRouter(prefix="/replay", tags=["replay"])


@router.get("/sessions/{session_id}/manifest", response_model=ReplayManifest)
def get_replay_manifest(
    session_id: int,
    storage: ReplayStorage = Depends(get_replay_storage),
):
    """Retrieve metadata, time boundaries, and driver list for a replay session."""
    manifest = storage.get_manifest(session_id)
    if not manifest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Replay dataset not found for session {session_id}",
        )
    return manifest


@router.get("/sessions/{session_id}/frames", response_model=ReplayFramesResponse)
def get_replay_frames(
    session_id: int,
    start_ms: Optional[int] = Query(None, description="Start millisecond timestamp"),
    end_ms: Optional[int] = Query(None, description="End millisecond timestamp"),
    interval_ms: int = Query(500, ge=100, le=2000, description="Sampling interval in ms"),
    storage: ReplayStorage = Depends(get_replay_storage),
    engine: CausalReplayEngine = Depends(get_causal_replay_engine),
):
    """
    Retrieve synchronized causal frames for all active cars within a time slice.
    Enforces strict temporal causality (zero lookahead).
    """
    manifest = storage.get_manifest(session_id)
    if not manifest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Replay dataset not found for session {session_id}",
        )

    req_start = start_ms if start_ms is not None else manifest.start_epoch_ms
    # Default to a 15-second window if end_ms not supplied
    req_end = end_ms if end_ms is not None else min(manifest.end_epoch_ms, req_start + 15000)

    # Restrict window size to maximum 60 seconds per request to prevent excessive payload
    if req_end - req_start > 60000:
        req_end = req_start + 60000

    return engine.get_frames_slice(
        session_id=session_id,
        start_ms=req_start,
        end_ms=req_end,
        interval_ms=interval_ms,
    )


@router.get("/sessions/{session_id}/telemetry", response_model=TelemetryResponse)
def get_replay_telemetry(
    session_id: int,
    driver_number: int = Query(..., description="Driver car number"),
    start_ms: Optional[int] = Query(None, description="Start millisecond timestamp"),
    end_ms: Optional[int] = Query(None, description="End millisecond timestamp"),
    storage: ReplayStorage = Depends(get_replay_storage),
):
    """Retrieve raw telemetry data for a specific driver within a time slice."""
    manifest = storage.get_manifest(session_id)
    if not manifest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Replay dataset not found for session {session_id}",
        )

    req_start = start_ms if start_ms is not None else manifest.start_epoch_ms
    req_end = end_ms if end_ms is not None else min(manifest.end_epoch_ms, req_start + 30000)

    df = storage.query_telemetry(
        session_id=session_id,
        start_ms=req_start,
        end_ms=req_end,
        driver_number=driver_number,
    )

    records = []
    if not df.empty:
        for _, row in df.iterrows():
            t_val = int(row["timestamp_ms"])
            records.append(
                TelemetryPoint(
                    timestamp_ms=t_val,
                    timestamp_iso=epoch_ms_to_iso(t_val),
                    driver_number=int(row["driver_number"]),
                    speed=int(row["speed"]),
                    throttle=int(row["throttle"]),
                    brake=int(row["brake"]),
                    gear=int(row["gear"]),
                    rpm=int(row["rpm"]),
                    drs=int(row["drs"]),
                )
            )

    return TelemetryResponse(
        session_id=session_id,
        driver_number=driver_number,
        point_count=len(records),
        data=records,
    )
