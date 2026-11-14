"""APEX — Ingestion Service & Idempotency Tests."""

import pytest
from sqlalchemy.orm import Session
from backend.models import (
    Season,
    Circuit,
    Event,
    Session as F1Session,
    Driver,
    Constructor,
    RaceResult,
    IngestionLog,
)
from backend.services.ingestion_service import IngestionService


def test_ingest_abu_dhabi_2024_complete_workflow(db_session: Session):
    service = IngestionService()
    result = service.ingest_event(db=db_session, season_year=2024, round_num=24, force_refresh=False)

    assert result["status"] == "SUCCESS"
    assert result["event_name"] == "Abu Dhabi Grand Prix"
    assert result["season"] == 2024
    assert result["round"] == 24
    assert result["records_ingested"]["results"] == 20
    assert result["records_ingested"]["sessions"] >= 5

    # Verify database contents
    event = db_session.query(Event).filter_by(season_year=2024, round=24).first()
    assert event is not None
    assert event.event_name == "Abu Dhabi Grand Prix"
    assert event.circuit.circuit_ref == "yas_marina"

    # Verify sessions
    sessions = db_session.query(F1Session).filter_by(event_id=event.id).all()
    assert len(sessions) >= 5
    session_types = {s.session_type for s in sessions}
    assert "race" in session_types
    assert "qualifying" in session_types

    # Verify race results
    results = db_session.query(RaceResult).filter_by(event_id=event.id).order_by(RaceResult.position_order).all()
    assert len(results) == 20
    p1 = results[0]
    assert p1.position_text == "1"
    assert p1.driver.driver_ref == "norris"
    assert p1.constructor.constructor_ref == "mclaren"
    assert p1.points == 25.0

    # Verify ingestion log
    log = db_session.query(IngestionLog).filter_by(identifier="2024_24").first()
    assert log is not None
    assert log.status == "SUCCESS"
    assert log.records_ingested == 20


def test_ingestion_idempotency(db_session: Session):
    """Running ingestion multiple times should update existing records without creating duplicates."""
    service = IngestionService()

    # Pass 1
    r1 = service.ingest_event(db=db_session, season_year=2024, round_num=24, force_refresh=False)
    assert r1["records_ingested"]["drivers_new"] == 20
    assert r1["records_ingested"]["constructors_new"] == 10

    event_count_1 = db_session.query(Event).count()
    result_count_1 = db_session.query(RaceResult).count()
    session_count_1 = db_session.query(F1Session).count()
    driver_count_1 = db_session.query(Driver).count()
    constructor_count_1 = db_session.query(Constructor).count()

    # Pass 2 (Immediate re-ingestion)
    r2 = service.ingest_event(db=db_session, season_year=2024, round_num=24, force_refresh=False)
    assert r2["records_ingested"]["drivers_new"] == 0
    assert r2["records_ingested"]["constructors_new"] == 0

    assert db_session.query(Event).count() == event_count_1
    assert db_session.query(RaceResult).count() == result_count_1
    assert db_session.query(F1Session).count() == session_count_1
    assert db_session.query(Driver).count() == driver_count_1
    assert db_session.query(Constructor).count() == constructor_count_1
