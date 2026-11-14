"""APEX — Centralized Error Handling and Data Validation Tests."""

from fastapi.testclient import TestClient


def test_404_entity_not_found(client: TestClient):
    resp = client.get("/api/v1/events/999999")
    assert resp.status_code == 404
    body = resp.json()
    assert "error" in body
    assert body["error"]["code"] == "ENTITY_NOT_FOUND"
    assert "999999" in body["error"]["message"]


def test_404_session_not_found(client: TestClient):
    resp = client.get("/api/v1/sessions/888888")
    assert resp.status_code == 404
    body = resp.json()
    assert body["error"]["code"] == "ENTITY_NOT_FOUND"


def test_422_validation_error(client: TestClient):
    # Pass non-integer for event_id in a route expecting int
    resp = client.get("/api/v1/events/not-a-number")
    assert resp.status_code == 422
    body = resp.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert "details" in body["error"]


def test_admin_invalid_event_id_format(client: TestClient):
    # Pass an invalid event format to admin endpoint
    resp = client.post(
        "/api/v1/admin/ingestion/events/invalid_event_id",
        headers={"X-Admin-Key": "test_admin_key_123"},
    )
    assert resp.status_code == 400
    body = resp.json()
    assert body["error"]["code"] == "INGESTION_ERROR"
