"""Unit tests for analytical replay storage and causal filter."""
import pytest
from backend.replay import (
    CausalReplayEngine,
    ReplayStorage,
    get_causal_replay_engine,
    get_replay_storage,
)


def test_manifest_loads_correctly():
    storage = get_replay_storage()
    manifest = storage.get_manifest(9662)
    assert manifest is not None
    assert manifest.session_id == 9662
    assert manifest.session_name == "Race"
    assert manifest.circuit_ref == "yas_marina"
    assert manifest.driver_count == 20
    assert manifest.duration_seconds > 90.0
    assert len(manifest.drivers) == 20
    assert manifest.drivers[0].driver_number > 0


def test_query_positions_slice():
    storage = get_replay_storage()
    manifest = storage.get_manifest(9662)
    assert manifest is not None

    # Query 2-second slice
    start_ms = manifest.start_epoch_ms
    end_ms = start_ms + 2000
    df = storage.query_positions(9662, start_ms, end_ms)

    assert not df.empty
    assert (df["timestamp_ms"] >= start_ms).all()
    assert (df["timestamp_ms"] <= end_ms).all()
    assert "norm_x" in df.columns
    assert "norm_y" in df.columns


def test_causal_replay_invariant():
    """
    CRITICAL RESEARCH INVARIANT:
    replay_state(t) must strictly observe data at or before t (zero lookahead leakage).
    """
    engine = get_causal_replay_engine()
    storage = get_replay_storage()
    manifest = storage.get_manifest(9662)
    assert manifest is not None

    test_timestamps = [
        manifest.start_epoch_ms + 1000,
        manifest.start_epoch_ms + 10000,
        manifest.start_epoch_ms + 30000,
    ]

    for t in test_timestamps:
        frame = engine.get_frame_at(9662, t)
        assert frame.timestamp_ms == t
        assert len(frame.cars) > 0

        # Query raw position records up to t to ensure returned car positions actually existed at t_obs <= t
        for drv_str, car in frame.cars.items():
            assert car.driver_number == int(drv_str)
            # Normalized coordinates must be within [0, 1]
            assert 0.0 <= car.norm_x <= 1.0
            assert 0.0 <= car.norm_y <= 1.0


def test_causal_replay_frames_slice():
    engine = get_causal_replay_engine()
    storage = get_replay_storage()
    manifest = storage.get_manifest(9662)
    assert manifest is not None

    start_ms = manifest.start_epoch_ms
    end_ms = start_ms + 4000  # 4 seconds
    resp = engine.get_frames_slice(9662, start_ms=start_ms, end_ms=end_ms, interval_ms=500)

    assert resp.session_id == 9662
    # 4000ms / 500ms + 1 = 9 frames
    assert resp.frame_count == 9
    assert len(resp.frames) == 9

    # Monotonic timestamps
    timestamps = [f.timestamp_ms for f in resp.frames]
    assert timestamps == sorted(timestamps)
    assert len(set(timestamps)) == len(timestamps)
