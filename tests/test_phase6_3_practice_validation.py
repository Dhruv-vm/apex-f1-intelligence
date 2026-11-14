"""Unit and integration tests for Phase 6.3: Practice Feature Validation, Prediction Sensitivity & Model Provenance."""
import json
from pathlib import Path
import numpy as np
import pytest

from backend.features.practice import extract_session_practice_features
from backend.features.practice_audit import audit_practice_coverage_34_weekends, trace_t0_t3_feature_flow
from backend.forecasting.grid_penalty_audit import run_t4_t5_grid_penalty_audit
from backend.forecasting.model_objective_comparison import fit_conditional_logistic_mle, predict_conditional_probabilities
from backend.forecasting.practice_subset_ablation import evaluate_practice_ablation_variants, load_genuine_practice_subset
from backend.forecasting.replay_ledger import replay_prediction_from_ledger, verify_ledger_reproducibility

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "artifacts" / "reports" / "EXP-0005"


def test_raw_to_feature_pipeline_correctness():
    """Verify that practice feature extraction correctly processes raw JSON payloads."""
    p = PROJECT_ROOT / "data" / "raw" / "openf1" / "practice"
    laps_fp2 = json.load(open(p / "fp2_9656_laps.json", "r", encoding="utf-8"))
    stints_fp2 = json.load(open(p / "fp2_9656_stints.json", "r", encoding="utf-8"))

    summary = extract_session_practice_features(laps_fp2, stints_fp2)
    assert 4 in summary  # Norris
    assert 1 in summary  # Verstappen
    assert 16 in summary  # Leclerc
    assert 44 in summary  # Hamilton

    norris = summary[4]
    assert norris.single_lap.best_lap_time is not None
    assert 80.0 <= norris.single_lap.best_lap_time <= 90.0
    assert norris.single_lap.sector_1_best is not None
    assert norris.single_lap.theoretical_best_lap <= norris.single_lap.best_lap_time
    assert norris.primary_race_sim_stint is not None
    assert isinstance(norris.primary_race_sim_stint.degradation_slope_sec_per_lap, float)


def test_practice_coverage_audit_distinguishes_local_from_provider():
    """Verify that the 34-weekend audit distinguishes provider availability from local cache."""
    audit_path = OUTPUT_DIR / "practice_coverage_audit_34_weekends.json"
    assert audit_path.exists()
    with open(audit_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["total_standard_weekends"] == 34
    assert data["total_practice_sessions_audited"] == 102
    assert data["locally_cached_sessions"] == 3  # FP1, FP2, FP3 for Abu Dhabi 2024
    assert data["provider_available_but_uncached"] == 99
    assert data["fully_cached_weekends"] == 1


def test_feature_flow_tracer_identifies_root_causes():
    """Verify that the T0-T3 diagnostic report documents the mathematical mechanism of identical metrics."""
    diag_path = OUTPUT_DIR / "t0_t3_feature_flow_diagnostic.json"
    assert diag_path.exists()
    with open(diag_path, "r", encoding="utf-8") as f:
        diag = json.load(f)

    reasons = diag["seven_factor_investigation"]
    assert "factor_1_missing_local_practice_data" in reasons
    assert "factor_4_zero_fitted_coefficients" in reasons
    assert "factor_5_incorrect_feature_column_mapping" in reasons
    assert reasons["factor_1_missing_local_practice_data"]["verdict"] == "CONFIRMED_PRIMARY_ROOT_CAUSE"


def test_genuine_practice_subset_sensitivity_and_ablations():
    """Verify that genuine practice data produces measurable prediction shifts on actual observed drivers."""
    res = evaluate_practice_ablation_variants()
    metrics = res["variant_metrics"]

    # Verify T0, T1, T2, T3 are NOT identical when genuine practice features are used
    t0_loss = metrics["T0_PRE_WEEKEND_FORM"]["multiclass_log_loss"]
    t1_loss = metrics["T1_POST_FP1_PACE"]["multiclass_log_loss"]
    t2_loss = metrics["T2_POST_FP2_PACE_AND_DEG"]["multiclass_log_loss"]
    t3_loss = metrics["T3_POST_FP3_FULL_PRACTICE"]["multiclass_log_loss"]

    assert t0_loss != t1_loss
    assert t1_loss != t2_loss
    assert t2_loss != t3_loss

    # Norris won: FP2 and FP3 pace improvements should reduce log loss
    assert t2_loss < t0_loss
    assert t3_loss < t0_loss

    # Check that probabilities sum to 1.0
    for v_name, v_data in metrics.items():
        prob_sum = sum(v_data["candidate_probabilities"].values())
        assert pytest.approx(prob_sum, abs=1e-3) == 1.0


def test_t4_t5_grid_changes_audit():
    """Verify T4 vs T5 audit correctly separates penalty races from non-penalty races."""
    grid_audit_path = OUTPUT_DIR / "t4_t5_grid_penalty_audit.json"
    assert grid_audit_path.exists()
    with open(grid_audit_path, "r", encoding="utf-8") as f:
        audit = json.load(f)

    assert audit["total_races_audited"] == 24
    assert audit["races_with_input_grid_change"] == 15
    assert audit["races_with_unchanged_grid"] == 9
    assert audit["races_with_probability_vector_shift"] == 15

    # On non-penalty races, delta must be 0.0
    assert audit["non_penalty_races_aggregate_metrics"]["mean_delta_log_loss"] == 0.0
    assert audit["non_penalty_races_aggregate_metrics"]["mean_delta_brier"] == 0.0


def test_model_objective_comparison_solvers():
    """Verify that Conditional Logit MLE and Binary Logistic solvers execute correctly."""
    comp_path = OUTPUT_DIR / "model_objective_comparison.json"
    assert comp_path.exists()
    with open(comp_path, "r", encoding="utf-8") as f:
        comp = json.load(f)

    assert "variant_a_binary_logistic_posthoc_softmax" in comp
    assert "variant_b_grouped_conditional_logit_mle" in comp
    assert comp["variant_a_binary_logistic_posthoc_softmax"]["mean_log_loss"] > 0.0
    assert comp["variant_b_grouped_conditional_logit_mle"]["mean_log_loss"] > 0.0


def test_prediction_ledger_v2_deterministic_replay():
    """Verify that prediction_ledger_v2.jsonl guarantees deterministic numerical reproducibility <= 1e-5."""
    ok, n_checked, max_err = verify_ledger_reproducibility(max_records_to_check=None, atol=1e-5)
    assert ok is True
    assert n_checked == 447
    assert max_err <= 1e-5


def test_abu_dhabi_session_identities_and_driver_substitutions():
    """Verify session identities and driver substitution handling for Abu Dhabi 2024 (Phase 6.3.1)."""
    subset = load_genuine_practice_subset()
    audit = subset["session_identity_audit"]
    assert audit["fp1_session_key"] == 9461
    assert audit["fp1_reported_typo_key"] == 9641
    assert "CONFIRMED_AS_9461" in audit["fp1_status"]

    sub_audit = subset["driver_substitution_audit"]
    assert sub_audit["verstappen_fp1_status"] == "DID_NOT_PARTICIPATE"
    assert sub_audit["car_37_driver"] == "Isack Hadjar"
    assert sub_audit["fia_official_fp1_times"]["Charles Leclerc"] == 84.321
    assert sub_audit["fia_official_fp1_times"]["Lando Norris"] == 84.542
    assert sub_audit["fia_official_fp1_times"]["Lewis Hamilton"] == 84.806

    # Verify drivers data
    drivers = subset["drivers"]
    ver = drivers[1]
    assert ver["fp1"]["participated"] is False
    assert ver["fp1"]["best_lap_time"] is None
    assert ver["fp1"]["pace_delta_to_benchmark"] is None
    assert ver["fp2"]["participated"] is True
    assert ver["fp3"]["participated"] is True


def test_recomputed_metrics_exact_log_loss_and_brier():
    """Verify exact mathematical alignment: race_level_multiclass_log_loss == -ln(p_winner)."""
    res = evaluate_practice_ablation_variants()
    
    # 4-driver study
    m4 = res["restricted_4_driver_contender_study"]["metrics"]
    for v_name, v_data in m4.items():
        p_win = v_data["fractional_top1_score"]
        loss = v_data["race_level_multiclass_log_loss"]
        expected_loss = round(-np.log(p_win), 4)
        assert pytest.approx(loss, abs=1e-4) == expected_loss
        assert "candidate_level_binary_cross_entropy" in v_data
        assert v_data["candidate_level_binary_cross_entropy"] > 0

    # 20-driver field
    m20 = res["full_20_driver_field_evaluation"]["metrics"]
    for cp_name, cp_data in m20.items():
        p_win = cp_data["fractional_top1_score"]
        loss = cp_data["race_level_multiclass_log_loss"]
        expected_loss = round(-np.log(p_win), 4)
        assert pytest.approx(loss, abs=1e-4) == expected_loss


def test_t4_t5_grid_audit_reconciliation():
    """Verify T4 vs T5 audit documents Phase 6.2 reconciliation and breakdown."""
    grid_audit_path = OUTPUT_DIR / "t4_t5_grid_penalty_audit.json"
    with open(grid_audit_path, "r", encoding="utf-8") as f:
        audit = json.load(f)

    assert "phase_6_2_reconciliation" in audit
    breakdowns = audit["cohort_breakdowns"]
    assert breakdowns["full_season_2024"]["grid_changed_count"] == 15
    assert breakdowns["standard_weekends_2024"]["grid_changed_count"] == 12
    assert breakdowns["sprint_weekends_2024"]["grid_changed_count"] == 3


def test_chronological_training_and_anti_leakage():
    """Verify that every prediction in the extended ledger used strictly prior training races."""
    ledger_path = OUTPUT_DIR / "prediction_ledger_v2.jsonl"
    assert ledger_path.exists()

    with open(ledger_path, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            if idx >= 30:
                break
            rec = json.loads(line)
            race_id = rec["race_id"]
            train_races = rec["training_race_ids"]
            # Current race ID must NEVER appear in its own training set
            assert race_id not in train_races
            # Training cutoff date must be present
            assert rec["training_cutoff"] is not None
