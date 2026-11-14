"""APEX — REST API Endpoints Tests."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from backend.services.ingestion_service import IngestionService


def test_health_and_readiness_endpoints(client: TestClient):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "version" in data

    resp_ready = client.get("/api/v1/ready")
    assert resp_ready.status_code == 200
    ready_data = resp_ready.json()
    assert ready_data["status"] == "ready"
    assert ready_data["database_connected"] is True


def test_events_and_results_endpoints(client: TestClient, db_session: Session):
    # Ingest Abu Dhabi first
    service = IngestionService()
    service.ingest_event(db_session, season_year=2024, round_num=24)

    # 1. Seasons
    resp = client.get("/api/v1/seasons")
    assert resp.status_code == 200
    seasons = resp.json()
    assert len(seasons) >= 1
    assert seasons[0]["year"] == 2024

    # 2. Events list
    resp = client.get("/api/v1/events")
    assert resp.status_code == 200
    events = resp.json()
    assert len(events) >= 1
    event_names = [e["event_name"] for e in events]
    assert "Abu Dhabi Grand Prix" in event_names
    abu_dhabi = next(e for e in events if e["event_name"] == "Abu Dhabi Grand Prix")
    event_id = abu_dhabi["id"]

    # 3. Filter events by season
    resp = client.get("/api/v1/events?season=2024")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1

    resp_empty = client.get("/api/v1/events?season=1999")
    assert resp_empty.status_code == 200
    assert len(resp_empty.json()) == 0

    # 4. Event Detail
    resp = client.get(f"/api/v1/events/{event_id}")
    assert resp.status_code == 200
    detail = resp.json()
    assert detail["event_name"] == "Abu Dhabi Grand Prix"
    assert len(detail["sessions"]) >= 5
    assert detail["results_count"] == 20

    # 5. Event Sessions
    resp = client.get(f"/api/v1/events/{event_id}/sessions")
    assert resp.status_code == 200
    sessions = resp.json()
    assert len(sessions) >= 5
    first_session_id = sessions[0]["id"]

    # 6. Session Detail
    resp = client.get(f"/api/v1/sessions/{first_session_id}")
    assert resp.status_code == 200
    sess = resp.json()
    assert sess["id"] == first_session_id
    assert sess["event_id"] == event_id

    # 7. Event Results
    resp = client.get(f"/api/v1/events/{event_id}/results")
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) == 20
    assert results[0]["position_text"] == "1"
    assert results[0]["driver"]["driver_ref"] == "norris"
    assert results[0]["constructor"]["constructor_ref"] == "mclaren"


def test_admin_ingestion_security_and_execution(client: TestClient, db_session: Session):
    # 1. Unauthenticated request without X-Admin-Key header should fail with 401
    resp_unauth = client.post("/api/v1/admin/ingestion/events/2024_24")
    assert resp_unauth.status_code == 401
    err = resp_unauth.json()
    assert err["error"]["code"] == "UNAUTHORIZED"

    # 2. Invalid header should fail with 401
    resp_wrong_key = client.post(
        "/api/v1/admin/ingestion/events/2024_24",
        headers={"X-Admin-Key": "wrong_key"},
    )
    assert resp_wrong_key.status_code == 401

    # 3. Valid admin request succeeds
    resp_auth = client.post(
        "/api/v1/admin/ingestion/events/2024_24",
        headers={"X-Admin-Key": "test_admin_key_123"},
    )
    assert resp_auth.status_code == 200
    data = resp_auth.json()
    assert data["status"] == "SUCCESS"
    assert data["season"] == 2024
    assert data["round"] == 24
    assert data["records_ingested"]["results"] == 20
