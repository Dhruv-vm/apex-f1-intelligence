"""Unit tests for effective-dated 2026 regulation intelligence registry."""
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.regulations import get_regulation_registry

client = TestClient(app)


def test_registry_contains_approved_2026_regulations():
    reg = get_regulation_registry()
    rules = reg.get_applicable_regulations(season=2026, event_date="2026-03-01")
    assert len(rules) >= 10
    pu_rules = [r for r in rules if r.category == "POWER_UNIT"]
    assert len(pu_rules) >= 3

    # Verify MGU-K 350kW output
    mgu_k = next(r for r in rules if r.regulation_id == "REG-2026-PU-003")
    assert mgu_k.parameter_value == "350"
    assert mgu_k.units == "kW"
    assert mgu_k.approval_status == "APPROVED"

    # Verify fuel energy flow cap (3000 MJ/h, not mass flow)
    fuel_flow = next(r for r in rules if r.regulation_id == "REG-2026-PU-002")
    assert fuel_flow.parameter_value == "3000"
    assert fuel_flow.units == "MJ/h"

    # Verify official terminology: Corner Mode & Straight Mode
    aero = next(r for r in rules if r.regulation_id == "REG-2026-AERO-001")
    assert "Corner Mode" in aero.parameter_value
    assert "Straight Mode" in aero.parameter_value


def test_effective_date_compression_ratio_transition():
    """
    Verify the two-phase compression ratio regime:
    - Phase 1 (through 31 May 2026): Ambient conditions only (REG-2026-TECH-CR-001).
    - Phase 2 (from 1 June 2026): Ambient and 130°C dual-temp compliance (REG-2026-TECH-CR-002).
    """
    reg = get_regulation_registry()

    # Pre-June (March 2026, Bahrain GP)
    pre_rules = reg.get_applicable_regulations(season=2026, event_date="2026-03-15")
    assert any(r.regulation_id == "REG-2026-TECH-CR-001" for r in pre_rules)
    assert not any(r.regulation_id == "REG-2026-TECH-CR-002" for r in pre_rules)

    # Post-June (July 2026, British GP)
    post_rules = reg.get_applicable_regulations(season=2026, event_date="2026-07-05")
    assert not any(r.regulation_id == "REG-2026-TECH-CR-001" for r in post_rules)
    assert any(r.regulation_id == "REG-2026-TECH-CR-002" for r in post_rules)


def test_effective_date_miami_energy_amendments():
    """
    Verify Miami GP energy amendments (effective 1 May 2026):
    - Recharge: 8.0 MJ/lap pre-Miami -> 7.0 MJ/lap post-Miami.
    - Superclip power: 250 kW pre-Miami -> 350 kW post-Miami.
    """
    reg = get_regulation_registry()

    # Australian GP (March 2026) -> Pre-Miami rules
    aus_rules = reg.get_applicable_regulations(season=2026, event_date="2026-03-20", session_type="RACE")
    assert any(r.regulation_id == "REG-2026-ENERGY-RECHARGE-PRE" for r in aus_rules)
    assert not any(r.regulation_id == "REG-2026-ENERGY-RECHARGE-MIA" for r in aus_rules)
    assert any(r.regulation_id == "REG-2026-ENERGY-SUPERCLIP-PRE" for r in aus_rules)
    assert not any(r.regulation_id == "REG-2026-ENERGY-SUPERCLIP-MIA" for r in aus_rules)

    # Miami GP (May 2026) -> Post-Miami rules
    mia_rules = reg.get_applicable_regulations(season=2026, event_date="2026-05-03", session_type="RACE")
    assert not any(r.regulation_id == "REG-2026-ENERGY-RECHARGE-PRE" for r in mia_rules)
    assert any(r.regulation_id == "REG-2026-ENERGY-RECHARGE-MIA" for r in mia_rules)
    assert not any(r.regulation_id == "REG-2026-ENERGY-SUPERCLIP-PRE" for r in mia_rules)
    assert any(r.regulation_id == "REG-2026-ENERGY-SUPERCLIP-MIA" for r in mia_rules)


def test_session_applicability_filtering():
    reg = get_regulation_registry()

    # Manual Override Mode (MOM) applies to SPRINT and RACE only
    race_rules = reg.get_applicable_regulations(season=2026, event_date="2026-03-01", session_type="RACE")
    assert any(r.regulation_id == "REG-2026-OVERTAKE-001" for r in race_rules)

    fp1_rules = reg.get_applicable_regulations(season=2026, event_date="2026-03-01", session_type="FP1")
    assert not any(r.regulation_id == "REG-2026-OVERTAKE-001" for r in fp1_rules)


def test_season_isolation():
    reg = get_regulation_registry()
    rules_2024 = reg.get_applicable_regulations(season=2024, event_date="2024-03-01")
    assert len(rules_2024) == 0


def test_api_query_regulations_endpoint():
    resp = client.get("/api/v1/regulations?season=2026&event_date=2026-03-15")
    assert resp.status_code == 200
    data = resp.json()
    assert data["season"] == 2026
    assert data["record_count"] >= 10
    assert len(data["regulations"]) == data["record_count"]


def test_api_get_single_regulation_endpoint():
    resp = client.get("/api/v1/regulations/REG-2026-PU-001")
    assert resp.status_code == 200
    data = resp.json()
    assert data["regulation_id"] == "REG-2026-PU-001"
    assert "MGU-H" in data["parameter_value"]


def test_api_regulation_not_found():
    resp = client.get("/api/v1/regulations/NON-EXISTENT-REG")
    assert resp.status_code == 404
