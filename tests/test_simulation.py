"""APEX — Comprehensive Test Suite for Phase 7 & 7.1 Simulation Engine (EXP-0006 & EXP-0006-R2)."""

import pytest
import numpy as np
from fastapi.testclient import TestClient

from backend.main import app
from backend.simulation.state import (
    TyreCompound,
    DriverStatus,
    SafetyCarState,
    TrackCondition,
    CircuitProfile,
    DriverState,
    RaceState,
)
from backend.simulation.scenario import ExogenousScenario, ScenarioGenerator
from backend.simulation.tyre import TyreDegradationModel
from backend.simulation.pit_stop import PitStopModel, TyreComplianceResult
from backend.simulation.weather import WeatherModel
from backend.simulation.safety_car import SafetyCarModel
from backend.simulation.reliability import ReliabilityModel
from backend.simulation.traffic import TrafficOvertakingModel
from backend.simulation.lap_time import LapTimeModel
from backend.simulation.strategy import (
    OneStopStrategy,
    TwoStopStrategy,
    UndercutStrategy,
    OvercutStrategy,
    SafetyCarReactiveStrategy,
    FixedReferenceStrategy,
)
from backend.simulation.engine import RaceSimulationEngine
from backend.simulation.counterfactual import CounterfactualEngine
from backend.simulation.monte_carlo import MonteCarloSimulator
from backend.simulation.forecasting_bridge import ForecastingBridge, CIRCUIT_PROFILES


client = TestClient(app)


# =========================================================================
# 1. State & Circuit Model Tests
# =========================================================================

def test_circuit_profile_initialization():
    profile = CIRCUIT_PROFILES["yas_marina"]
    assert profile.circuit_id == "yas_marina"
    assert profile.total_laps == 58
    assert profile.pit_transit_loss_seconds == 20.5
    assert profile.overtaking_difficulty_index == 0.60


def test_driver_state_initialization():
    driver = DriverState(
        driver_id="NOR",
        driver_name="Lando Norris",
        constructor_id="mclaren",
        starting_grid=1,
        current_position=1,
        current_compound=TyreCompound.MEDIUM,
        accumulated_race_time=0.0,
    )
    assert driver.current_position == 1
    assert driver.status == DriverStatus.RUNNING
    assert driver.current_tyre_age == 0
    assert driver.is_active()


# =========================================================================
# 2. Exogenous Scenario & CRN Invariance Tests (Phase 7.1)
# =========================================================================

def test_crn_exogenous_scenario_invariance():
    gen = ScenarioGenerator(master_seed=42)
    driver_ids = ["norris", "verstappen", "leclerc", "piastri"]

    # Generate two scenarios from identical seed
    scen_a = gen.generate_scenario(run_index=1, total_laps=58, driver_ids=driver_ids)
    scen_b = gen.generate_scenario(run_index=1, total_laps=58, driver_ids=driver_ids)

    # Weather draws must be bitwise identical
    assert np.array_equal(scen_a.weather_rain_rolls, scen_b.weather_rain_rolls)
    assert np.array_equal(scen_a.weather_temp_drifts, scen_b.weather_temp_drifts)

    # Incident draws must be bitwise identical
    assert np.array_equal(scen_a.sc_incident_rolls, scen_b.sc_incident_rolls)
    assert np.array_equal(scen_a.sc_durations, scen_b.sc_durations)

    # Driver pace normals must be bitwise identical
    assert np.array_equal(scen_a.driver_pace_normals, scen_b.driver_pace_normals)


def test_crn_variance_reduction():
    bridge = ForecastingBridge()
    base_race = bridge.build_initial_race_state(2024, 24)
    base_race.total_laps = 12
    base_race.drivers = dict(list(base_race.drivers.items())[:4])

    strat_a = OneStopStrategy(target_pit_lap=5, secondary_compound=TyreCompound.HARD)
    strat_b = TwoStopStrategy(stop1_lap=4, stop2_lap=8)

    cf_engine = CounterfactualEngine()
    rep = cf_engine.compare_strategies(
        base_race_state=base_race,
        target_driver_id="norris",
        strategies_to_test={"StratA": strat_a, "StratB": strat_b},
        n_simulations=20,
        master_seed=42,
    )

    pair = rep.paired_comparisons[0]
    # Variance reduction under CRN must be positive and substantial
    assert pair.variance_reduction_percent > 50.0
    assert pair.time_correlation > 0.80


def test_event_specific_random_streams_no_contamination():
    gen = ScenarioGenerator(master_seed=1234)
    scen = gen.generate_scenario(run_index=0, total_laps=20, driver_ids=["norris", "verstappen"])

    # Drawing pit service noise on lap 5 must not affect weather or incident on lap 6
    w_lap6_before = scen.get_weather_draws(6)
    inc_lap6_before = scen.get_incident_draw(6)

    # Simulate pit stop draws for driver
    _ = scen.get_pit_service_time("norris", stop_index=1)
    _ = scen.get_pit_service_time("norris", stop_index=2)

    w_lap6_after = scen.get_weather_draws(6)
    inc_lap6_after = scen.get_incident_draw(6)

    assert w_lap6_before == w_lap6_after
    assert inc_lap6_before == inc_lap6_after


# =========================================================================
# 3. FIA Sporting Regulations 2024 Art 30.5 Tests (Phase 7.1)
# =========================================================================

def test_fia_art_30_5_dry_race_two_compounds_compliant():
    pit_model = PitStopModel()
    res = pit_model.validate_sporting_tyre_rules(
        compounds_used=[TyreCompound.MEDIUM, TyreCompound.HARD],
        track_condition=TrackCondition.DRY,
        is_race_suspended_and_not_restarted=False,
    )
    assert res.is_compliant is True
    assert res.penalty_type is None
    # Backward compatible unpacking
    valid, msg = res
    assert valid is True


def test_fia_art_30_5_dry_race_one_compound_disqualification():
    pit_model = PitStopModel()
    # Normal completed dry race with 1 compound fitted -> DISQUALIFICATION
    res = pit_model.validate_sporting_tyre_rules(
        compounds_used=[TyreCompound.MEDIUM],
        track_condition=TrackCondition.DRY,
        is_race_suspended_and_not_restarted=False,
    )
    assert res.is_compliant is False
    assert res.penalty_type == "DISQUALIFICATION"
    assert "DISQUALIFICATION" in res.description


def test_fia_art_30_5_suspended_race_30s_penalty():
    pit_model = PitStopModel()
    # Suspended race not restarted with 1 compound fitted -> 30 seconds penalty
    res = pit_model.validate_sporting_tyre_rules(
        compounds_used=[TyreCompound.MEDIUM],
        track_condition=TrackCondition.DRY,
        is_race_suspended_and_not_restarted=True,
    )
    assert res.is_compliant is False
    assert res.penalty_type == "TIME_PENALTY_30S"
    assert "+30.0s" in res.description


def test_fia_art_30_5_wet_intermediate_exemption():
    pit_model = PitStopModel()
    # Intermediate tyre used -> mandatory 2 dry compounds rule suspended
    res = pit_model.validate_sporting_tyre_rules(
        compounds_used=[TyreCompound.INTERMEDIATE, TyreCompound.MEDIUM],
        track_condition=TrackCondition.DRY,
    )
    assert res.is_compliant is True

    # Wet track condition -> rule suspended even with 1 compound
    res_wet = pit_model.validate_sporting_tyre_rules(
        compounds_used=[TyreCompound.WET],
        track_condition=TrackCondition.WET,
    )
    assert res_wet.is_compliant is True


def test_fia_art_30_5_missing_compound_information():
    pit_model = PitStopModel()
    res = pit_model.validate_sporting_tyre_rules(
        compounds_used=[],
        track_condition=TrackCondition.DRY,
    )
    assert res.is_compliant is False
    assert res.penalty_type == "DISQUALIFICATION"


# =========================================================================
# 4. DRS & FIA Article 22.1 Logic Tests (Phase 7.1)
# =========================================================================

def test_drs_lap_1_disabled():
    traffic_model = TrafficOvertakingModel()
    eligible, reason = traffic_model.check_drs_eligibility(
        gap_at_detection_sec=0.5,
        current_lap=1,
        laps_since_sc_restart=10,
        safety_car_state=SafetyCarState.NONE,
        track_condition=TrackCondition.DRY,
        season=2024,
    )
    assert eligible is False
    assert "Lap 2" in reason


def test_drs_restart_lap_disabled():
    traffic_model = TrafficOvertakingModel()
    eligible, reason = traffic_model.check_drs_eligibility(
        gap_at_detection_sec=0.5,
        current_lap=15,
        laps_since_sc_restart=0,  # Just restarted this lap
        safety_car_state=SafetyCarState.NONE,
        track_condition=TrackCondition.DRY,
        season=2024,
    )
    assert eligible is False
    assert "restart lap" in reason


def test_drs_safety_car_disabled():
    traffic_model = TrafficOvertakingModel()
    eligible, reason = traffic_model.check_drs_eligibility(
        gap_at_detection_sec=0.5,
        current_lap=10,
        laps_since_sc_restart=10,
        safety_car_state=SafetyCarState.FULL_SC,
        track_condition=TrackCondition.DRY,
    )
    assert eligible is False
    assert "under FULL_SC" in reason


def test_drs_gap_threshold_detection():
    traffic_model = TrafficOvertakingModel()
    # Gap < 1.000s on Lap 5 is eligible
    eligible_close, _ = traffic_model.check_drs_eligibility(
        gap_at_detection_sec=0.850,
        current_lap=5,
        laps_since_sc_restart=10,
        safety_car_state=SafetyCarState.NONE,
        track_condition=TrackCondition.DRY,
    )
    assert eligible_close is True

    # Gap > 1.000s is ineligible
    eligible_far, _ = traffic_model.check_drs_eligibility(
        gap_at_detection_sec=1.150,
        current_lap=5,
        laps_since_sc_restart=10,
        safety_car_state=SafetyCarState.NONE,
        track_condition=TrackCondition.DRY,
    )
    assert eligible_far is False


def test_drs_exact_1_second_boundary_ineligible():
    """FIA Art 22.1: Car must be strictly LESS than 1.000s behind. Exactly 1.0000s is ineligible."""
    traffic_model = TrafficOvertakingModel()
    eligible, reason = traffic_model.check_drs_eligibility(
        gap_at_detection_sec=1.0000,
        current_lap=5,
        laps_since_sc_restart=10,
        safety_car_state=SafetyCarState.NONE,
        track_condition=TrackCondition.DRY,
    )
    assert eligible is False
    assert "not strictly less than" in reason


def test_drs_activation_zone_restriction():
    """DRS may only be activated in designated predetermined activation zones."""
    traffic_model = TrafficOvertakingModel()
    # Close gap but outside activation zone
    eligible, reason = traffic_model.check_drs_eligibility(
        gap_at_detection_sec=0.450,
        current_lap=5,
        laps_since_sc_restart=10,
        safety_car_state=SafetyCarState.NONE,
        track_condition=TrackCondition.DRY,
        in_drs_activation_zone=False,
    )
    assert eligible is False
    assert "outside designated activation zone" in reason


def test_drs_race_director_discretionary_disablement():
    """Race Director discretion to disable DRS in poor visibility, yellow flags, or instruction."""
    traffic_model = TrafficOvertakingModel()

    # Poor visibility
    el_vis, r_vis = traffic_model.check_drs_eligibility(
        gap_at_detection_sec=0.50,
        current_lap=5,
        laps_since_sc_restart=10,
        safety_car_state=SafetyCarState.NONE,
        track_condition=TrackCondition.DRY,
        poor_visibility=True,
    )
    assert el_vis is False
    assert "Poor visibility" in r_vis

    # Yellow flags in activation zone
    el_yel, r_yel = traffic_model.check_drs_eligibility(
        gap_at_detection_sec=0.50,
        current_lap=5,
        laps_since_sc_restart=10,
        safety_car_state=SafetyCarState.NONE,
        track_condition=TrackCondition.DRY,
        yellow_flags_in_zone=True,
    )
    assert el_yel is False
    assert "Yellow flags" in r_yel

    # Explicit Race Director instruction
    el_rd, r_rd = traffic_model.check_drs_eligibility(
        gap_at_detection_sec=0.50,
        current_lap=5,
        laps_since_sc_restart=10,
        safety_car_state=SafetyCarState.NONE,
        track_condition=TrackCondition.DRY,
        race_director_drs_enabled=False,
    )
    assert el_rd is False
    assert "Race Director instruction" in r_rd


def test_fia_art_30_5_mandatory_dry_compound_check():
    """FIA Art 30.5: Must use at least one nominated mandatory dry-weather specification."""
    pit_model = PitStopModel()
    mandatory = {TyreCompound.HARD, TyreCompound.MEDIUM}

    # 1. Used Soft and Hard -> Compliant (Hard is mandatory)
    res_compliant = pit_model.validate_sporting_tyre_rules(
        compounds_used=[TyreCompound.SOFT, TyreCompound.HARD],
        track_condition=TrackCondition.DRY,
        mandatory_dry_compounds=mandatory,
    )
    assert res_compliant.is_compliant is True
    assert res_compliant.penalty_type is None

    # 2. Used Soft and Medium -> Compliant (Medium is mandatory)
    res_med = pit_model.validate_sporting_tyre_rules(
        compounds_used=[TyreCompound.SOFT, TyreCompound.MEDIUM],
        track_condition=TrackCondition.DRY,
        mandatory_dry_compounds=mandatory,
    )
    assert res_med.is_compliant is True

    # 3. Pirelli designated ONLY Hard as mandatory, driver used Soft and Medium -> Non-compliant!
    res_missing_mand = pit_model.validate_sporting_tyre_rules(
        compounds_used=[TyreCompound.SOFT, TyreCompound.MEDIUM],
        track_condition=TrackCondition.DRY,
        mandatory_dry_compounds={TyreCompound.HARD},
    )
    assert res_missing_mand.is_compliant is False
    assert res_missing_mand.penalty_type == "DISQUALIFICATION"
    assert "Failed to use at least one mandatory nominated" in res_missing_mand.description

    # 4. Suspended race without restart missing mandatory specification -> 30s penalty
    res_susp = pit_model.validate_sporting_tyre_rules(
        compounds_used=[TyreCompound.SOFT, TyreCompound.MEDIUM],
        track_condition=TrackCondition.DRY,
        is_race_suspended_and_not_restarted=True,
        mandatory_dry_compounds={TyreCompound.HARD},
    )
    assert res_susp.is_compliant is False
    assert res_susp.penalty_type == "TIME_PENALTY_30S"
    assert "+30.0s" in res_susp.description


def test_safety_car_and_vsc_separation_and_chronological_cutoff():
    """Safety Car and VSC processes must be modeled separately with historical chronology."""
    model = SafetyCarModel()
    assert model.base_sc_hazard == 0.0150
    assert model.base_vsc_hazard == 0.0120

    # Chronological cutoff check
    # 2024 season: both SC and VSC active
    sc_2024, vsc_2024 = SafetyCarModel.get_chronological_hazard(2024)
    assert sc_2024 == 0.0150
    assert vsc_2024 == 0.0120

    # 2012 season (pre-VSC era): VSC hazard must be strictly 0.0
    sc_2012, vsc_2012 = SafetyCarModel.get_chronological_hazard(2012)
    assert sc_2012 == 0.0150
    assert vsc_2012 == 0.0

    # Hazard decomposition audit
    decomp = SafetyCarModel.get_hazard_decomposition()
    assert decomp["historical_races_audited"] == 346
    assert decomp["physical_sc"]["deployments"] == 310
    assert decomp["virtual_sc"]["introduced_season"] == 2015
    assert decomp["combined_neutralisation_rate_per_lap"] == 0.0270


def test_pit_stop_canonical_decomposition():
    """Verifies canonical decomposition of pit stop time components."""
    pit_model = PitStopModel()
    assert pit_model.base_transit_loss == 20.5
    assert pit_model.stationary_mean == 2.45
    assert pit_model.stationary_std == 0.35
    assert pit_model.stuck_wheel_prob == 0.035
    # Transit loss without service is 20.5s at Yas Marina
    record = pit_model.execute_pit_stop(
        lap=20,
        stint_completed=1,
        target_compound=TyreCompound.HARD,
        safety_car_state=SafetyCarState.NONE,
        service_override=(2.45, 0.0),
    )
    assert record.transit_loss_seconds == 20.5
    assert record.stationary_duration_seconds == 2.45
    assert record.total_pit_loss_seconds == 22.95


# =========================================================================
# 5. Tyre & Pit Model Calibration Tests
# =========================================================================

def test_tyre_degradation_cliff_progression():
    tyre_model = TyreDegradationModel()
    delta_pre = tyre_model.compute_tyre_delta(compound=TyreCompound.SOFT, tyre_age=5, track_condition=TrackCondition.DRY)
    delta_post = tyre_model.compute_tyre_delta(compound=TyreCompound.SOFT, tyre_age=25, track_condition=TrackCondition.DRY)
    assert delta_post > delta_pre + 1.0


def test_tyre_sensitivity_scaling():
    model_1x = TyreDegradationModel.create_scaled_model(1.0)
    model_2x = TyreDegradationModel.create_scaled_model(2.0)
    delta_1x = model_1x.compute_tyre_delta(compound=TyreCompound.MEDIUM, tyre_age=10, track_condition=TrackCondition.DRY)
    delta_2x = model_2x.compute_tyre_delta(compound=TyreCompound.MEDIUM, tyre_age=10, track_condition=TrackCondition.DRY)
    assert delta_2x > delta_1x


def test_pit_stop_service_and_discount():
    pit_model = PitStopModel(base_transit_loss_seconds=20.0)
    stop_green = pit_model.execute_pit_stop(lap=15, stint_completed=1, target_compound=TyreCompound.HARD, safety_car_state=SafetyCarState.NONE, service_override=(2.45, 0.0))
    stop_sc = pit_model.execute_pit_stop(lap=15, stint_completed=1, target_compound=TyreCompound.HARD, safety_car_state=SafetyCarState.FULL_SC, service_override=(2.45, 0.0))
    # Green pit loss: 20s transit + 2.45s service = 22.45s
    assert round(stop_green.total_pit_loss_seconds, 2) == 22.45
    # SC pit loss: 10s transit (50% discount) + 2.45s service = 12.45s (exactly 10.0s time advantage)
    assert round(stop_sc.total_pit_loss_seconds, 2) == 12.45
    assert stop_green.total_pit_loss_seconds - stop_sc.total_pit_loss_seconds == 10.0


# =========================================================================
# 6. Safety Car, Reliability, Traffic & Policy Tests
# =========================================================================

def test_safety_car_restart_compression():
    sc_model = SafetyCarModel()
    rng = np.random.default_rng(101)
    driver1 = DriverState(driver_id="D1", driver_name="D1", constructor_id="T1", starting_grid=1, current_position=1, accumulated_race_time=100.0)
    driver2 = DriverState(driver_id="D2", driver_name="D2", constructor_id="T2", starting_grid=2, current_position=2, accumulated_race_time=125.0)
    sc_model.apply_restart_field_compression([driver1, driver2], rng=rng)
    assert (driver2.accumulated_race_time - driver1.accumulated_race_time) < 2.5


def test_strategy_policy_zero_future_knowledge():
    strat = SafetyCarReactiveStrategy(fallback_pit_lap=26)
    race_state = RaceState(
        race_id="test_zero_knowledge",
        circuit=CIRCUIT_PROFILES["yas_marina"],
        current_lap=12,
        total_laps=58,
        safety_car_state=SafetyCarState.NONE,
    )
    driver = DriverState(driver_id="norris", driver_name="Norris", constructor_id="mclaren", starting_grid=1, current_position=1, current_tyre_age=12)
    # When no SC is active, policy must NOT pit early on lap 12
    decision = strat.evaluate_strategy(driver, race_state)
    assert decision.should_pit is False

    # When SC activates on lap 12, policy reacts to observed current state
    race_state.safety_car_state = SafetyCarState.FULL_SC
    decision_sc = strat.evaluate_strategy(driver, race_state)
    assert decision_sc.should_pit is True


# =========================================================================
# 7. Engine Execution & Monte Carlo Convergence Tests
# =========================================================================

def test_full_race_engine_execution():
    bridge = ForecastingBridge()
    race_state = bridge.build_initial_race_state(2024, 24)
    race_state.drivers = dict(list(race_state.drivers.items())[:4])
    race_state.total_laps = 10
    engine = RaceSimulationEngine()
    strategies = {d_id: OneStopStrategy(target_pit_lap=5) for d_id in race_state.drivers.keys()}
    final_state = engine.run_race(race_state, strategies=strategies, seed=42)
    assert final_state.current_lap == 10
    assert len(final_state.drivers) == 4
    finishing_positions = [d.current_position for d in final_state.drivers.values()]
    assert sorted(finishing_positions) == [1, 2, 3, 4]


def test_monte_carlo_convergence_checkpoints():
    mc = MonteCarloSimulator()
    bridge = ForecastingBridge()
    base_state = bridge.build_initial_race_state(2024, 24)
    base_state.total_laps = 6
    base_state.drivers = dict(list(base_state.drivers.items())[:4])

    result = mc.run_simulations(base_state, n_iterations=50, master_seed=42)
    assert len(result.convergence_history) >= 1
    assert result.convergence_history[0].iteration_count == 50
    assert result.convergence_history[0].leader_win_standard_error >= 0.0


# =========================================================================
# 8. FastAPI Simulation Endpoints & Async Lifecycle (Phase 7.1)
# =========================================================================

def test_api_simulation_circuits():
    response = client.get("/api/v1/simulation/circuits")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 5
    circuit_ids = [c["circuit_id"] for c in data]
    assert "yas_marina" in circuit_ids


def test_api_parameters_modality_classifications():
    response = client.get("/api/v1/simulation/parameters")
    assert response.status_code == 200
    params = response.json()
    assert "observed" in params
    assert "empirically_estimated" in params
    assert "assumed" in params
    assert "user_configured" in params
    assert "synthetic" in params


def test_api_simulation_run_lifecycle_and_jobs():
    # Sync run
    payload = {
        "season": 2024,
        "round_num": 24,
        "n_iterations": 10,
        "master_seed": 42,
        "track_condition": "DRY",
        "async_mode": False,
    }
    response = client.post("/api/v1/simulation/runs", json=payload)
    assert response.status_code == 200
    run_data = response.json()
    assert "run_id" in run_data
    run_id = run_data["run_id"]
    assert len(run_data["candidates"]) == 20

    # Async run submission
    async_payload = dict(payload, async_mode=True)
    async_res = client.post("/api/v1/simulation/runs", json=async_payload)
    assert async_res.status_code == 200
    job_id = async_res.json()["job_id"]

    # Poll status
    job_res = client.get(f"/api/v1/simulation/jobs/{job_id}")
    assert job_res.status_code == 200
    assert job_res.json()["status"] in ("PENDING", "RUNNING", "COMPLETED")


def test_api_counterfactual_endpoint():
    payload = {
        "season": 2024,
        "round_num": 24,
        "target_driver_id": "norris",
        "n_iterations": 10,
        "master_seed": 42,
        "track_condition": "DRY",
    }
    response = client.post("/api/v1/simulation/counterfactual", json=payload)
    assert response.status_code == 200
    cf_data = response.json()
    assert cf_data["target_driver_id"] == "norris"
    assert len(cf_data["evaluated_strategies"]) >= 5
    assert "Reference_1Stop_M_H" in [s["strategy_name"] for s in cf_data["evaluated_strategies"]]


def test_edge_case_2_car_field():
    engine = RaceSimulationEngine()
    circuit = CIRCUIT_PROFILES["monza"]
    driver1 = DriverState(driver_id="verstappen", driver_name="Verstappen", constructor_id="red_bull", starting_grid=1, current_position=1)
    driver2 = DriverState(driver_id="leclerc", driver_name="Leclerc", constructor_id="ferrari", starting_grid=2, current_position=2)
    state = RaceState(
        race_id="edge_2car",
        circuit=circuit,
        current_lap=0,
        total_laps=5,
        drivers={"verstappen": driver1, "leclerc": driver2},
    )
    strategies = {
        "verstappen": OneStopStrategy(target_pit_lap=3),
        "leclerc": OneStopStrategy(target_pit_lap=3),
    }
    final_state = engine.run_race(state, strategies=strategies, seed=999)
    assert final_state.current_lap == 5
    assert {d.current_position for d in final_state.drivers.values()} == {1, 2}


def test_evaluator_multi_seed_crn_variance_reduction():
    from backend.simulation.evaluator import run_multi_seed_crn_variance_reduction_audit
    res = run_multi_seed_crn_variance_reduction_audit(master_seeds=[42, 101], n_draws=25)
    assert res["n_master_seeds_evaluated"] == 2
    assert res["mean_race_time_variance_reduction_percent"] > 95.0
    assert res["mean_position_variance_reduction_percent"] > 60.0
    assert res["mean_paired_time_correlation_rho"] > 0.90


def test_evaluator_holdout_strategy_selection():
    from backend.simulation.evaluator import run_holdout_strategy_evaluation
    res = run_holdout_strategy_evaluation(n_train=25, n_eval=25, train_seed=42, eval_seed=999)
    assert "selection_set_a" in res
    assert "evaluation_set_b" in res
    assert "ex_post_oracle_comparison" in res
    assert res["selection_set_a"]["selected_strategy"] in ("SafetyCar_Reactive", "Reference_1Stop", "Tactical_Undercut")
    assert res["ex_post_oracle_comparison"]["online_vs_oracle_position_regret"] >= 0.0


def test_tyre_calibration_provenance():
    prov = TyreDegradationModel.get_tyre_calibration_provenance()
    assert prov["estimation_method"].startswith("Stint-clustered")
    assert "SOFT" in prov["compounds"]
    assert "MEDIUM" in prov["compounds"]
    assert "HARD" in prov["compounds"]
    assert prov["compounds"]["MEDIUM"]["degradation_slope_sec_per_lap"] == 0.048
    assert prov["fuel_burn_correction"]["lap_time_fuel_gain_sec_per_lap"] == -0.0578
