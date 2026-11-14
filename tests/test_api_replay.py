"""API tests for circuit geometry and replay endpoints."""
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_get_circuit_geometry_success():
    resp = client.get("/api/v1/circuits/yas_marina/geometry")
    assert resp.status_code == 200
    data = resp.json()
    assert data["circuit_ref"] == "yas_marina"
    assert data["name"] == "Yas Marina Circuit"
    assert "bounds" in data
    assert len(data["normalized_centerline"]) > 0
    assert len(data["sectors"]) == 3


def test_get_circuit_geometry_not_found():
    resp = client.get("/api/v1/circuits/unknown_circuit_999/geometry")
    assert resp.status_code == 404
    body = resp.json()
    err_msg = body.get("error", {}).get("message", body.get("detail", ""))
    assert "not found" in err_msg.lower()


def test_get_replay_manifest_success():
    resp = client.get("/api/v1/replay/sessions/9662/manifest")
    assert resp.status_code == 200
    data = resp.json()
    assert data["session_id"] == 9662
    assert data["circuit_ref"] == "yas_marina"
    assert data["driver_count"] == 20
    assert len(data["drivers"]) == 20


def test_get_replay_manifest_not_found():
    resp = client.get("/api/v1/replay/sessions/999999/manifest")
    assert resp.status_code == 404


def test_get_replay_frames_slice():
    resp = client.get("/api/v1/replay/sessions/9662/frames?interval_ms=500")
    assert resp.status_code == 200
    data = resp.json()
    assert data["session_id"] == 9662
    assert data["frame_count"] > 0
    assert len(data["frames"]) == data["frame_count"]

    first_frame = data["frames"][0]
    assert "timestamp_ms" in first_frame
    assert "cars" in first_frame
    assert len(first_frame["cars"]) > 0


def test_list_circuits_endpoint():
    resp = client.get("/api/v1/circuits")
    assert resp.status_code == 200
    circuits = resp.json()
    assert len(circuits) >= 2
    refs = [c["circuit_ref"] for c in circuits]
    assert "yas_marina" in refs
    assert "silverstone" in refs


def test_get_circuit_geometry_silverstone():
    resp = client.get("/api/v1/circuits/silverstone/geometry")
    assert resp.status_code == 200
    data = resp.json()
    assert data["circuit_ref"] == "silverstone"
    assert data["name"] == "Silverstone Circuit"
    assert len(data["corners"]) >= 8


def test_get_replay_manifest_silverstone():
    resp = client.get("/api/v1/replay/sessions/9558/manifest")
    assert resp.status_code == 200
    data = resp.json()
    assert data["session_id"] == 9558
    assert data["circuit_ref"] == "silverstone"
    assert data["driver_count"] == 20


def test_get_replay_frames_silverstone():
    resp = client.get("/api/v1/replay/sessions/9558/frames?interval_ms=500")
    assert resp.status_code == 200
    data = resp.json()
    assert data["session_id"] == 9558
    assert data["frame_count"] > 0
    assert len(data["frames"]) == data["frame_count"]
    first_frame = data["frames"][0]
    assert len(first_frame["cars"]) > 0


def test_get_replay_telemetry():
    resp = client.get("/api/v1/replay/sessions/9662/telemetry?driver_number=4")
    assert resp.status_code == 200
    data = resp.json()
    assert data["session_id"] == 9662
    assert data["driver_number"] == 4
    assert data["point_count"] > 0
    assert len(data["data"]) == data["point_count"]
    first_pt = data["data"][0]
    assert "speed" in first_pt
    assert "throttle" in first_pt
    assert "gear" in first_pt
