"""APEX — EXP-0006 Numerical Integrity Gate & Phase 8 Authorization Regression Tests.

Verifies:
1. Race-time weighted-mean arithmetic identity:
   all_run_mean == (completed_count / total_count) * completed_mean + (dnf_count / total_count) * dnf_mean
2. DNF population span (laps 1-58, not restricted to 1-15) and retirement coupling under CRN.
3. SC/VSC transition classification and exact identity reconciliation (1,284 raw records).
4. Guard preventing VSC from spawning a new green-originating deployment in the simulation loop.
5. Integrity of exp_0006_final_closeout_v2.json artifact.
"""
import json
import math
from pathlib import Path
import numpy as np
import pytest

from backend.simulation.counterfactual import CounterfactualEngine
from backend.simulation.strategy import OneStopStrategy, SafetyCarReactiveStrategy
from backend.simulation.scenario import ScenarioGenerator
from backend.simulation.forecasting_bridge import ForecastingBridge
from backend.simulation.state import DriverStatus, SafetyCarState, TrackCondition, TyreCompound
from backend.simulation.safety_car import SafetyCarModel


def test_race_time_weighted_mean_identity_and_dnf_population():
    """
    Verifies that the weighted-mean arithmetic identity holds to machine precision,
    that DNFs occur across laps 1 through 58 (not bounded by lap 15),
    and that paired vehicles experience zero asymmetric retirements under CRN.
    """
    bridge = ForecastingBridge()
    base_race = bridge.build_initial_race_state(2024, 24)
    cf_engine = CounterfactualEngine()
    scenario_gen = ScenarioGenerator(master_seed=42)
    driver_ids = list(base_race.drivers.keys())

    s_ref = OneStopStrategy(target_pit_lap=22, secondary_compound=TyreCompound.HARD)
    s_sc = SafetyCarReactiveStrategy(fallback_pit_lap=26)

    n_test = 300
    times_ref_all = []
    times_ref_fin = []
    times_ref_dnf = []
    dnf_laps = []
    asymmetric_retirements = 0

    for run_idx in range(n_test):
        scen = scenario_gen.generate_scenario(run_idx, base_race.total_laps, driver_ids)

        r_ref = cf_engine.engine.run_race(
            base_race.model_copy(deep=True),
            {d: (s_ref if d == "norris" else s_ref) for d in driver_ids},
            scenario=scen,
        )
        d_ref = r_ref.drivers["norris"]

        r_sc = cf_engine.engine.run_race(
            base_race.model_copy(deep=True),
            {d: (s_sc if d == "norris" else s_ref) for d in driver_ids},
            scenario=scen,
        )
        d_sc = r_sc.drivers["norris"]

        times_ref_all.append(d_ref.accumulated_race_time)

        if d_ref.status == DriverStatus.FINISHED:
            times_ref_fin.append(d_ref.accumulated_race_time)
        elif d_ref.status == DriverStatus.RETIRED:
            times_ref_dnf.append(d_ref.accumulated_race_time)
            dnf_laps.append(d_ref.retirement_lap)

        # Check retirement coupling under CRN
        if (d_ref.status == DriverStatus.FINISHED) != (d_sc.status == DriverStatus.FINISHED):
            asymmetric_retirements += 1

    n_tot = len(times_ref_all)
    n_fin = len(times_ref_fin)
    n_dnf = len(times_ref_dnf)

    assert n_tot == n_test
    assert n_fin + n_dnf == n_tot
    assert n_dnf > 0, "Expected at least one DNF in 300 runs"

    # 1. Mandatory arithmetic identity
    m_all = float(np.mean(times_ref_all))
    m_fin = float(np.mean(times_ref_fin))
    m_dnf = float(np.mean(times_ref_dnf))
    weighted = (n_fin / n_tot) * m_fin + (n_dnf / n_tot) * m_dnf

    assert abs(m_all - weighted) < 1e-9, f"Weighted mean identity violated: abs diff = {abs(m_all - weighted)}"

    # 2. DNF distribution spans beyond lap 15
    assert max(dnf_laps) > 15, f"Expected mechanical failures beyond lap 15, got max lap {max(dnf_laps)}"

    # 3. Under CRN, paired drivers have zero asymmetric retirements
    assert asymmetric_retirements == 0, f"Found {asymmetric_retirements} asymmetric retirements under CRN"


def test_sc_vsc_transition_classification_and_identities():
    """
    Verifies the transition-based classification and exact reconciliation identities
    across all 1,284 raw race-control messages.
    """
    decomp = SafetyCarModel.get_hazard_decomposition()
    assert "transition_classification" in decomp
    tc = decomp["transition_classification"]

    # Raw counts
    raw_total = tc["raw_race_control_records"]
    g_to_sc = tc["green_to_sc_direct_in_race"]
    g_to_vsc = tc["green_to_vsc_activations"]
    vsc_to_sc = tc["vsc_to_sc_escalations"]
    vsc_to_g = tc["vsc_to_green_standalone_concluded"]
    sc_to_g = tc["sc_to_green_concluded"]
    pre_race = tc["pre_race_or_processional_sc_intervention"]
    status_notices = tc["duplicate_status_or_sector_notices"]

    assert raw_total == 1284
    assert g_to_sc == 258
    assert g_to_vsc == 180
    assert vsc_to_sc == 52
    assert vsc_to_g == 128
    assert sc_to_g == 310
    assert pre_race == 1
    assert status_notices == 355

    # Identity 1: Total SC declarations == direct + escalation + pre-race
    assert g_to_sc + vsc_to_sc + pre_race == tc["total_sc_declarations"] == 311

    # Identity 2: In-race SC phases == direct + escalation
    assert g_to_sc + vsc_to_sc == tc["total_sc_in_race_phases"] == 310

    # Identity 3: Total VSC activations == standalone + escalation
    assert vsc_to_g + vsc_to_sc == tc["total_vsc_activations"] == 180

    # Identity 4: Total green-originating episodes
    assert g_to_sc + g_to_vsc == tc["total_distinct_green_originating_episodes"] == 438
    assert tc["total_sc_in_race_phases"] + tc["total_standalone_vsc_phases"] == 438

    # Identity 5: Complete raw records traceability
    sum_all_events = (
        tc["total_sc_declarations"]
        + tc["total_vsc_activations"]
        + sc_to_g
        + vsc_to_g
        + status_notices
    )
    assert sum_all_events == raw_total == 1284


def test_vsc_cannot_spawn_green_originating_incident():
    """
    Verifies that check_new_incident() strictly blocks new incident generation
    when the race is currently neutralised (VSC or FULL_SC), preventing an active
    VSC from being counted as a new green-originating incident in the discrete loop.
    """
    model = SafetyCarModel()
    rng = np.random.default_rng(42)

    # When in VSC
    state, duration, desc = model.check_new_incident(
        current_lap=10,
        total_laps=58,
        track_condition=TrackCondition.DRY,
        current_state=SafetyCarState.VSC,
        rng=rng,
    )
    assert state == SafetyCarState.VSC
    assert duration == 0
    assert desc is None

    # When in FULL_SC
    state_sc, duration_sc, desc_sc = model.check_new_incident(
        current_lap=15,
        total_laps=58,
        track_condition=TrackCondition.DRY,
        current_state=SafetyCarState.FULL_SC,
        rng=rng,
    )
    assert state_sc == SafetyCarState.FULL_SC
    assert duration_sc == 0
    assert desc_sc is None


def test_exp_0006_v2_closeout_artifact():
    """
    Verifies that exp_0006_final_closeout_v2.json exists, satisfies all gate criteria,
    and contains valid, machine-epsilon checked weighted-mean identities.
    """
    p = Path("artifacts/reports/EXP-0006/exp_0006_final_closeout_v2.json")
    assert p.exists(), "exp_0006_final_closeout_v2.json does not exist"

    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["gate_status"] == "PASS"
    assert data["phase_8_authorized"] is True

    item1 = data["audit_item_1_race_time_aggregation_and_weighted_mean_identity"]
    ref = item1["raw_record_counts"]["reference_1stop"]
    sc = item1["raw_record_counts"]["safetycar_reactive"]

    # Verify weighted mean identity
    assert ref["weighted_mean_identity_verification"]["identity_satisfied"] is True
    assert ref["weighted_mean_identity_verification"]["absolute_difference"] < 1e-9

    assert sc["weighted_mean_identity_verification"]["identity_satisfied"] is True
    assert sc["weighted_mean_identity_verification"]["absolute_difference"] < 1e-9

    # Verify DNF lap range
    assert ref["dnf_min_lap"] == 1
    assert ref["dnf_max_lap"] == 58
    assert math.isclose(ref["dnf_mean_lap"], 22.87, abs_tol=0.1)

    # Verify paired statistics
    paired = item1["recomputed_paired_statistics"]
    assert paired["retirement_coupling_under_crn"]["n_asymmetric_retired"] == 0
    assert paired["all_run_paired_time_difference"]["sample_size_N"] == 10000
    assert paired["matched_finished_run_paired_difference"]["sample_size_N"] == 9113


def test_raw_message_ledger_uniqueness_and_partition():
    """
    Verifies Table A: Exactly 1,284 source records partitioned into mutually exclusive
    broadcast categories with zero duplication or double counting.
    """
    decomp = SafetyCarModel.get_hazard_decomposition()
    assert "raw_message_ledger" in decomp
    ledger = decomp["raw_message_ledger"]
    cats = ledger["categories"]

    sc_dep = cats["SAFETY_CAR_DEPLOYED"]["count"]
    vsc_dep = cats["VSC_DEPLOYED"]["count"]
    sc_end = cats["SAFETY_CAR_ENDING"]["count"]
    vsc_end = cats["VSC_ENDING"]["count"]
    status_notices = cats["STATUS_SECTOR_AND_TRACK_CLEAR_NOTICES"]["count"]

    assert sc_dep == 311
    assert vsc_dep == 180
    assert sc_end == 310
    assert vsc_end == 128
    assert status_notices == 355

    # Exactly 1,284 total source records
    assert ledger["total_unique_records"] == 1284
    assert sc_dep + vsc_dep + sc_end + vsc_end + status_notices == 1284


def test_event_lifecycle_ledger_and_conservation():
    """
    Verifies Table B: Derived Event Lifecycle Ledger tracks on-track physical episodes
    and satisfies state conservation identities without confounding raw message counts.
    """
    decomp = SafetyCarModel.get_hazard_decomposition()
    assert "derived_event_lifecycle_ledger" in decomp
    lifecycle = decomp["derived_event_lifecycle_ledger"]
    events = lifecycle["lifecycle_events"]

    g_to_sc = events["green_to_sc_direct_in_race"]["count"]
    g_to_vsc = events["green_to_vsc_activations"]["count"]
    vsc_esc = events["vsc_to_sc_escalations"]["count"]
    vsc_standalone = events["vsc_to_green_standalone_conclusions"]["count"]
    sc_end = events["sc_to_green_conclusions"]["count"]
    pre_race = events["pre_race_or_processional_sc_intervention"]["count"]

    assert g_to_sc == 258
    assert g_to_vsc == 180
    assert vsc_esc == 52
    assert vsc_standalone == 128
    assert sc_end == 310
    assert pre_race == 1

    # Identity 1: VSC episode conservation (180 == 52 + 128)
    assert g_to_vsc == vsc_esc + vsc_standalone == 180

    # Identity 2: Physical SC phase conservation (310 == 258 + 52)
    assert sc_end == g_to_sc + vsc_esc == 310

    # Identity 3: Total distinct green-originating episodes (438)
    assert g_to_sc + g_to_vsc == 438
    assert sc_end + vsc_standalone == 438
    assert lifecycle["total_distinct_green_originating_episodes"] == 438


def test_calibrated_initiation_hazard_definitions():
    """
    Verifies that direct green initiation hazards, conditional escalation probabilities,
    and descriptive macro exposure ratios are strictly separated and mathematically accurate.
    """
    decomp = SafetyCarModel.get_hazard_decomposition()
    assert "hazard_definition_standards" in decomp
    h = decomp["hazard_definition_standards"]

    # 1. Direct green -> SC initiation hazard (258 / 19,420)
    sc_init = h["direct_green_to_sc_initiation_hazard"]
    assert sc_init["numerator"] == 258
    assert sc_init["exposure_denominator_laps"] == 19420
    assert math.isclose(sc_init["value_per_lap"], 258 / 19420, rel_tol=1e-3)

    # 2. Green -> VSC initiation hazard (180 / 13,558)
    vsc_init = h["green_to_vsc_initiation_hazard"]
    assert vsc_init["numerator"] == 180
    assert vsc_init["exposure_denominator_laps"] == 13558
    assert math.isclose(vsc_init["value_per_lap"], 180 / 13558, rel_tol=1e-3)

    # 3. Conditional VSC -> SC escalation probability (52 / 180)
    esc = h["conditional_vsc_to_sc_escalation_probability"]
    assert esc["numerator"] == 52
    assert esc["denominator_vsc_activations"] == 180
    assert math.isclose(esc["value"], 52 / 180, rel_tol=1e-4)

    # 4. Conditional standalone VSC outcome probability (128 / 180)
    standalone = h["conditional_standalone_vsc_outcome_probability"]
    assert standalone["numerator"] == 128
    assert standalone["denominator_vsc_activations"] == 180
    assert math.isclose(standalone["value"], 128 / 180, rel_tol=1e-4)

    # 5. Descriptive aggregate SC phase ratio (310 / 19,420) - MUST NOT be initiation hazard
    macro_sc = h["descriptive_aggregate_sc_phase_to_green_ratio"]
    assert macro_sc["numerator"] == 310
    assert macro_sc["denominator_laps"] == 19420
    assert "MUST NOT be described or used as conditional green-state initiation hazard" in macro_sc["standard"]

    # 6. Descriptive standalone outcome rate (128 / 13,558) - MUST NOT be initiation hazard
    descriptive_vsc = h["descriptive_standalone_vsc_outcome_rate"]
    assert descriptive_vsc["numerator"] == 128
    assert descriptive_vsc["denominator_laps"] == 13558
    assert "MUST NOT be described or used as the VSC initiation hazard" in descriptive_vsc["standard"]


def test_simulator_vsc_to_sc_escalation_logic():
    """
    Verifies that the simulation engine evaluates explicit VSC -> SC escalation
    while VSC is active without double counting as a new green initiation,
    and blocks green-originating incidents during neutralisation.
    """
    model = SafetyCarModel()
    assert model.enable_vsc_escalation is True
    assert math.isclose(model.conditional_vsc_escalation_prob, 52 / 180, rel_tol=1e-4)

    # Test check_vsc_escalation method directly
    # 1. Roll below 0.28889 triggers escalation
    did_esc, dur, desc = model.check_vsc_escalation(
        current_state=SafetyCarState.VSC,
        escalation_roll_override=0.15,
    )
    assert did_esc is True
    assert 3 <= dur <= 6
    assert "escalated to Full Safety Car" in desc

    # 2. Roll above 0.28889 does not escalate (standalone VSC)
    did_esc_no, dur_no, desc_no = model.check_vsc_escalation(
        current_state=SafetyCarState.VSC,
        escalation_roll_override=0.50,
    )
    assert did_esc_no is False
    assert dur_no == 0
    assert desc_no is None

    # 3. Non-VSC states never escalate via this method
    for state in [SafetyCarState.NONE, SafetyCarState.FULL_SC]:
        esc_other, _, _ = model.check_vsc_escalation(current_state=state, escalation_roll_override=0.01)
        assert esc_other is False

    # 4. Scenario has dedicated orthogonal escalation stream
    from backend.simulation.scenario import ScenarioGenerator
    scen_gen = ScenarioGenerator(master_seed=42)
    scen = scen_gen.generate_scenario(0, 58, ["norris", "piastri"])
    esc_draw = scen.get_vsc_escalation_draw(5)
    assert 0.0 <= esc_draw <= 1.0


def test_exp_0006_v3_closeout_artifact():
    """
    Verifies that exp_0006_final_closeout_v3.json exists, satisfies all gate criteria,
    and contains Table A, Table B, and the calibrated hazard standards.
    """
    p = Path("artifacts/reports/EXP-0006/exp_0006_final_closeout_v3.json")
    assert p.exists(), "exp_0006_final_closeout_v3.json does not exist"

    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["gate_status"] == "PASS"
    assert data["phase_8_authorized"] is True

    # Check Table A
    assert "table_a_raw_message_ledger" in data
    assert data["table_a_raw_message_ledger"]["total_unique_source_records"] == 1284
    assert data["table_a_raw_message_ledger"]["sum_verification"]["identity_satisfied"] is True

    # Check Table B
    assert "table_b_derived_event_lifecycle_ledger" in data
    assert data["table_b_derived_event_lifecycle_ledger"]["total_green_originating_incident_episodes"] == 438

    # Check Calibrated Hazards
    assert "calibrated_hazard_definitions" in data
    hazards = data["calibrated_hazard_definitions"]
    assert math.isclose(hazards["direct_green_to_sc_initiation_hazard"]["value_per_lap"], 258 / 19420, rel_tol=1e-3)
    assert math.isclose(hazards["green_to_vsc_initiation_hazard"]["value_per_lap"], 180 / 13558, rel_tol=1e-3)
    assert math.isclose(hazards["conditional_vsc_to_sc_escalation_probability"]["value"], 52 / 180, rel_tol=1e-4)


def test_calibrated_initiation_hazard_engine_configuration():
    """
    Verifies that the simulation engine is configured with direct green initiation hazards
    (SC: 258/19420 ~ 0.013285; VSC: 180/13558 ~ 0.013276) rather than macro phase ratios
    which confound VSC escalations, and verifies legacy macro ratios are preserved under descriptive names.
    """
    model = SafetyCarModel()
    assert math.isclose(model.base_sc_hazard, 258 / 19420, rel_tol=1e-4)
    assert math.isclose(model.base_vsc_hazard, 180 / 13558, rel_tol=1e-4)
    assert model.legacy_macro_sc_hazard_total_lap == 0.0150
    assert model.legacy_macro_vsc_hazard_total_lap == 0.0120
    assert math.isclose(model.aggregate_sc_phase_ratio, 310 / 19420, rel_tol=1e-4)

    # get_chronological_hazard returns direct green initiation hazards
    sc_2024, vsc_2024 = SafetyCarModel.get_chronological_hazard(2024)
    assert math.isclose(sc_2024, 258 / 19420, rel_tol=1e-4)
    assert math.isclose(vsc_2024, 180 / 13558, rel_tol=1e-4)

    # get_legacy_macro_chronological_hazard returns macro phase ratios
    sc_m, vsc_m = SafetyCarModel.get_legacy_macro_chronological_hazard(2024)
    assert sc_m == 0.0150
    assert vsc_m == 0.0120

