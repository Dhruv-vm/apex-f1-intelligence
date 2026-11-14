"""APEX — Database Models and Constraints Tests."""

from datetime import date, datetime, timezone
import pytest
from sqlalchemy.exc import IntegrityError
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


def test_create_season(db_session: Session):
    season = Season(year=2024, url="https://f1.com/2024")
    db_session.add(season)
    db_session.commit()

    saved = db_session.query(Season).filter_by(year=2024).first()
    assert saved is not None
    assert saved.year == 2024
    assert saved.created_at is not None


def test_create_circuit_and_unique_constraint(db_session: Session):
    c1 = Circuit(
        circuit_ref="yas_marina",
        name="Yas Marina Circuit",
        country="UAE",
        latitude=24.4672,
        longitude=54.6031,
    )
    db_session.add(c1)
    db_session.commit()

    # Attempting duplicate circuit_ref must raise IntegrityError
    c2 = Circuit(circuit_ref="yas_marina", name="Duplicate Yas")
    db_session.add(c2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_event_unique_season_round_constraint(db_session: Session):
    season = Season(year=2024)
    circuit = Circuit(circuit_ref="monza", name="Autodromo Nazionale Monza")
    db_session.add_all([season, circuit])
    db_session.commit()

    ev1 = Event(
        season_year=2024,
        round=16,
        event_name="Italian Grand Prix",
        circuit_id=circuit.id,
        date=date(2024, 9, 1),
    )
    db_session.add(ev1)
    db_session.commit()

    # Duplicate (season_year, round)
    ev2 = Event(
        season_year=2024,
        round=16,
        event_name="Duplicate Italian GP",
        circuit_id=circuit.id,
        date=date(2024, 9, 1),
    )
    db_session.add(ev2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_race_result_relationships_and_constraint(db_session: Session):
    season = Season(year=2024)
    circuit = Circuit(circuit_ref="silverstone", name="Silverstone Circuit")
    driver = Driver(driver_ref="hamilton", first_name="Lewis", last_name="Hamilton", code="HAM")
    constructor = Constructor(constructor_ref="mercedes", name="Mercedes")
    db_session.add_all([season, circuit, driver, constructor])
    db_session.commit()

    event = Event(
        season_year=2024,
        round=12,
        event_name="British Grand Prix",
        circuit_id=circuit.id,
        date=date(2024, 7, 7),
    )
    db_session.add(event)
    db_session.commit()

    res = RaceResult(
        event_id=event.id,
        driver_id=driver.id,
        constructor_id=constructor.id,
        grid_position=2,
        position=1,
        position_text="1",
        position_order=1,
        points=25.0,
        laps=52,
        status="Finished",
    )
    db_session.add(res)
    db_session.commit()

    saved_res = db_session.query(RaceResult).first()
    assert saved_res is not None
    assert saved_res.driver.full_name == "Lewis Hamilton"
    assert saved_res.constructor.name == "Mercedes"
    assert saved_res.event.event_name == "British Grand Prix"

    # Duplicate result for same event and driver
    duplicate_res = RaceResult(
        event_id=event.id,
        driver_id=driver.id,
        constructor_id=constructor.id,
        grid_position=2,
        position_order=1,
        position_text="1",
        status="Finished",
    )
    db_session.add(duplicate_res)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_ingestion_log_persistence(db_session: Session):
    log = IngestionLog(
        provider="jolpica",
        entity_type="event",
        identifier="2024_24",
        status="SUCCESS",
        records_ingested=20,
        payload_hash="abcd1234hash",
    )
    db_session.add(log)
    db_session.commit()

    saved_log = db_session.query(IngestionLog).first()
    assert saved_log is not None
    assert saved_log.identifier == "2024_24"
    assert saved_log.status == "SUCCESS"
    assert saved_log.records_ingested == 20
