"""APEX — Data Provider Adapters Tests."""

import os
import pytest
from backend.providers.jolpica import JolpicaProvider
from backend.providers.openf1 import OpenF1Provider
from backend.providers.fastf1 import FastF1Provider


def test_jolpica_get_race_results_from_cache():
    provider = JolpicaProvider()
    # Abu Dhabi 2024 is pre-cached in data/raw/jolpica/results/2024/results_offset_0400.json
    race_data = provider.get_race_results(season=2024, round_num=24, force_refresh=False)
    assert race_data is not None
    assert race_data.get("raceName") == "Abu Dhabi Grand Prix"
    assert race_data.get("season") == "2024"
    assert race_data.get("round") == "24"
    assert "Circuit" in race_data
    assert race_data["Circuit"]["circuitId"] == "yas_marina"
    assert len(race_data.get("Results", [])) == 20


def test_jolpica_payload_hash_deterministic():
    provider = JolpicaProvider()
    p1 = {"a": 1, "b": [2, 3]}
    p2 = {"b": [2, 3], "a": 1}
    assert provider.compute_payload_hash(p1) == provider.compute_payload_hash(p2)


def test_openf1_get_sessions_from_cache():
    provider = OpenF1Provider()
    # Abu Dhabi sessions cached in data/raw/openf1/sessions/2024_abu_dhabi.json
    sessions = provider.get_sessions(year=2024, country_name="United Arab Emirates", force_refresh=False)
    assert isinstance(sessions, list)
    assert len(sessions) >= 5
    types = [s.get("session_type") for s in sessions]
    assert "Practice" in types
    assert "Qualifying" in types
    assert "Race" in types


def test_openf1_get_drivers_from_cache():
    provider = OpenF1Provider()
    # Drivers for session 9662 cached in data/raw/openf1/drivers/9662.json
    drivers = provider.get_drivers(session_key=9662, force_refresh=False)
    assert isinstance(drivers, list)
    assert len(drivers) > 0
    # Check that driver fields exist
    first = drivers[0]
    assert "driver_number" in first or "name_acronym" in first


def test_fastf1_adapter_safe_fallback():
    provider = FastF1Provider()
    # FastF1 should not crash the system even if unavailable or session load fails
    session_data = provider.get_session(year=1950, race_round=1)
    # Returns None or dict safely
    assert session_data is None or isinstance(session_data, dict)
