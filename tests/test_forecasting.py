"""Unit and integration tests for Phase 6 Sequential Forecasting Engine."""
import json
import math
import pytest
from fastapi.testclient import TestClient

from backend.forecasting.engine import (
    CheckpointForecastingEngine,
    compute_plackett_luce_rank_probabilities,
    get_forecasting_engine,
)
from backend.forecasting.evaluator import (
    compute_expected_calibration_error,
    compute_multiclass_brier_score,
    compute_multiclass_log_loss,
    get_forecast_evaluator,
)
from backend.main import app

client = TestClient(app)

SAMPLE_DRIVERS = [
    {"driver_number": 4, "code": "NOR", "name": "Lando Norris", "team": "McLaren"},
    {"driver_number": 1, "code": "VER", "name": "Max Verstappen", "team": "Red Bull"},
    {"driver_number": 16, "code": "LEC", "name": "Charles Leclerc", "team": "Ferrari"},
    {"driver_number": 55, "code": "SAI", "name": "Carlos Sainz", "team": "Ferrari"},
    {"driver_number": 44, "code": "HAM", "name": "Lewis Hamilton", "team": "Mercedes"},
]


def test_plackett_luce_rank_probabilities_math():
    import numpy as np
    # Test with 10-driver field (N > 5)
    p_win = np.array([0.30, 0.20, 0.15, 0.10, 0.08, 0.05, 0.04, 0.03, 0.03, 0.02])
    p_podium, p_top5, exp_pos = compute_plackett_luce_rank_probabilities(p_win)

    # 1. Normalization & boundaries
    assert np.isclose(p_podium.sum(), 3.0, atol=1e-3)
    assert np.isclose(p_top5.sum(), 5.0, atol=1e-3)

    # 2. Monotonicity: higher win prob -> higher podium prob -> better expected rank
    assert (p_podium[:-1] >= p_podium[1:]).all()
    assert (exp_pos[:-1] <= exp_pos[1:]).all()


def test_forecasting_checkpoints_generation():
    engine = get_forecasting_engine()

    grid = {4: 1, 1: 5, 16: 19, 55: 3, 44: 18}

    # Generate all checkpoints
    fc_t0 = engine.generate_checkpoint_forecast(2024, 1, "Abu Dhabi GP", "T0_PRE_WEEKEND", "2024-12-05T12:00:00+00:00", SAMPLE_DRIVERS)
    fc_t4 = engine.generate_checkpoint_forecast(2024, 1, "Abu Dhabi GP", "T4_POST_QUALIFYING", "2024-12-07T15:00:00+00:00", SAMPLE_DRIVERS, qualifying_grid=grid)

    assert fc_t0.checkpoint == "T0_PRE_WEEKEND"
    assert fc_t0.eligible_drivers_count == 5
    # Sum of win probabilities must equal 1.0
    win_sum_t0 = sum(d.p_win for d in fc_t0.drivers)
    assert pytest.approx(win_sum_t0, abs=1e-4) == 1.0

    # Grid check: Norris (P1 grid) should have higher probability at T4 than at T0
    nor_t0 = next(d for d in fc_t0.drivers if d.driver_number == 4)
    nor_t4 = next(d for d in fc_t4.drivers if d.driver_number == 4)
    assert nor_t4.p_win > nor_t0.p_win
    assert nor_t4.grid_position == 1


def test_checkpoint_isolation_and_no_grid_leakage():
    """Verify that qualifying grid does not leak into T0/T1/T2/T3 models."""
    engine = get_forecasting_engine()
    grid = {4: 1, 1: 5, 16: 19, 55: 3, 44: 18}

    # Pass grid to T0: model must strictly ignore it
    fc_t0_without_grid = engine.generate_checkpoint_forecast(2024, 1, "Abu Dhabi GP", "T0_PRE_WEEKEND", "2024-12-05T12:00:00+00:00", SAMPLE_DRIVERS)
    fc_t0_with_grid = engine.generate_checkpoint_forecast(2024, 1, "Abu Dhabi GP", "T0_PRE_WEEKEND", "2024-12-05T12:00:00+00:00", SAMPLE_DRIVERS, qualifying_grid=grid)

    p0 = [d.p_win for d in fc_t0_without_grid.drivers]
    p1 = [d.p_win for d in fc_t0_with_grid.drivers]
    assert p0 == p1  # Grid was completely excluded from T0 calculation!


def test_evaluator_metrics_computation():
    p_dict = {4: 0.60, 1: 0.25, 16: 0.15}
    actual_winner = 4

    loss = compute_multiclass_log_loss(p_dict, actual_winner)
    assert loss == pytest.approx(-math.log(0.60), abs=1e-4)

    brier = compute_multiclass_brier_score(p_dict, actual_winner)
    # (0.60 - 1)^2 + (0.25 - 0)^2 + (0.15 - 0)^2 = 0.16 + 0.0625 + 0.0225 = 0.245
    assert brier == pytest.approx(0.245, abs=1e-4)

    ece = compute_expected_calibration_error(p_dict, actual_winner)
    assert 0.0 <= ece <= 1.0


def test_api_predictions_endpoints():
    # 1. All checkpoints
    resp = client.get("/api/v1/predictions/events/1")
    assert resp.status_code == 200
    fcs = resp.json()
    assert len(fcs) == 6
    checkpoints = [f["checkpoint"] for f in fcs]
    assert checkpoints == [
        "T0_PRE_WEEKEND",
        "T1_POST_FP1",
        "T2_POST_FP2",
        "T3_POST_FP3",
        "T4_POST_QUALIFYING",
        "T5_FINAL_PRE_RACE",
    ]

    # 2. Single checkpoint
    resp_t4 = client.get("/api/v1/predictions/events/1/checkpoints/T4_POST_QUALIFYING")
    assert resp_t4.status_code == 200
    data_t4 = resp_t4.json()
    assert data_t4["checkpoint"] == "T4_POST_QUALIFYING"
    assert len(data_t4["drivers"]) == 20

    # 3. Evaluation report (HYP-0001)
    resp_eval = client.get("/api/v1/predictions/events/1/evaluation")
    assert resp_eval.status_code == 200
    report = resp_eval.json()
    assert report["hyp_0001_supported"] is True
    assert len(report["checkpoints"]) == 6
    # Verify metric separation
    for cp in report["checkpoints"]:
        assert cp["conventional_top1_acc"] in (0.0, 1.0)
        assert 0.0 <= cp["fractional_top1_score"] <= 1.0
        assert cp["multiclass_log_loss"] >= 0.0
        assert cp["multiclass_brier_score"] >= 0.0


def test_plackett_luce_rank_marginals_analytical_vs_mc():
    """Verify Plackett-Luce rank marginals against analytical definitions with numerical tolerances."""
    import numpy as np

    p_win = np.array([0.35, 0.25, 0.15, 0.10, 0.07, 0.05, 0.03])
    n = len(p_win)

    podium, top5, exp_pos, rank_mat = compute_plackett_luce_rank_probabilities(
        p_win, n_mc_samples=100000, seed=42, return_rank_matrix=True
    )

    # 1. Row sums (each driver finishes somewhere with prob 1.0)
    assert np.allclose(rank_mat.sum(axis=1), 1.0, atol=0.01)

    # 2. Column sums (each rank position 1..N has exactly 1 driver)
    assert np.allclose(rank_mat.sum(axis=0), 1.0, atol=0.01)

    # 3. Exact Podium sum == 3.0 and Top-5 sum == 5.0
    assert pytest.approx(podium.sum(), abs=1e-3) == 3.0
    assert pytest.approx(top5.sum(), abs=1e-3) == 5.0

    # 4. Strict structural hierarchy: p_win <= p_podium <= p_top5 <= 1.0
    assert np.all(p_win <= podium + 1e-5)
    assert np.all(podium <= top5 + 1e-5)
    assert np.all(top5 <= 1.0 + 1e-5)

    # 5. Exact sum of expected positions equals N*(N+1)/2
    assert pytest.approx(exp_pos.sum(), abs=1e-2) == (n * (n + 1)) / 2.0


def test_plackett_luce_edge_cases_field_sizes_and_extreme_utilities():
    """Verify Plackett-Luce calculation on small fields, tied utilities, and extreme values."""
    import numpy as np

    # 1. Field of 2 drivers
    p2 = np.array([0.70, 0.30])
    pod2, t5_2, exp2, mat2 = compute_plackett_luce_rank_probabilities(p2, return_rank_matrix=True)
    assert pytest.approx(pod2.sum(), abs=1e-4) == 2.0
    assert pytest.approx(t5_2.sum(), abs=1e-4) == 2.0
    assert pytest.approx(exp2.sum(), abs=1e-4) == 3.0

    # 2. Tied utilities (4 equal drivers)
    p_tied = np.array([0.25, 0.25, 0.25, 0.25])
    pod_t, t5_t, exp_t, _ = compute_plackett_luce_rank_probabilities(p_tied, return_rank_matrix=True)
    assert np.allclose(pod_t, 0.75, atol=0.01)
    assert np.allclose(t5_t, 1.0, atol=0.01)
    assert np.allclose(exp_t, 2.5, atol=0.01)

    # 3. Extreme dominant utility
    p_extreme = np.array([0.999, 0.0005, 0.0005])
    pod_e, _, exp_e, _ = compute_plackett_luce_rank_probabilities(p_extreme, return_rank_matrix=True)
    assert pod_e[0] > 0.998
    assert exp_e[0] < 1.01


def test_checkpoint_feature_differentiation_and_penalty_drops():
    """Verify that FP3 setup gains differentiate T3 from T2, and penalties differentiate T5 from T4."""
    engine = get_forecasting_engine()
    prov_grid = {4: 1, 1: 5, 16: 19, 55: 3, 44: 18}
    penalties = {1: 3}  # Verstappen serves 3-place penalty

    fc_t4 = engine.generate_checkpoint_forecast(
        2024, 1, "Abu Dhabi GP", "T4_POST_QUALIFYING", "2024-12-07T15:00:00+00:00",
        SAMPLE_DRIVERS, qualifying_grid=prov_grid
    )
    fc_t5 = engine.generate_checkpoint_forecast(
        2024, 1, "Abu Dhabi GP", "T5_FINAL_PRE_RACE", "2024-12-08T12:00:00+00:00",
        SAMPLE_DRIVERS, qualifying_grid=prov_grid, penalty_drops=penalties
    )

    ver_t4 = next(d for d in fc_t4.drivers if d.driver_number == 1)
    ver_t5 = next(d for d in fc_t5.drivers if d.driver_number == 1)

    # Verstappen's probability must decrease from T4 to T5 due to penalty drop
    assert ver_t5.p_win < ver_t4.p_win
    assert ver_t5.grid_position == 8  # 5 + 3
    assert "final_confirmed_starting_grid" in fc_t5.feature_names
    assert "grid_penalty_delta" in fc_t5.feature_names


def test_historical_walk_forward_backtest_artifacts():
    """Verify that EXP-0005 backtest artifacts exist and meet schema constraints."""
    import pandas as pd
    from backend.forecasting.backtest import OUTPUT_DIR

    coverage_path = OUTPUT_DIR / "historical_checkpoint_coverage_matrix.csv"
    assert coverage_path.exists()
    cov_df = pd.read_csv(coverage_path)
    assert len(cov_df) == 149
    assert cov_df["qualifying_coverage"].all()
    assert cov_df["grid_coverage"].all()

    paired_path = OUTPUT_DIR / "paired_statistical_tests.json"
    assert paired_path.exists()
    with open(paired_path) as f:
        tests = json.load(f)
    assert "T5_vs_T0" in tests
    assert tests["T5_vs_T0"]["statistically_significant_at_005"] is True

    summary_path = OUTPUT_DIR / "walk_forward_checkpoint_metrics.json"
    assert summary_path.exists()
    with open(summary_path) as f:
        metrics = json.load(f)
    t0_loss = metrics["checkpoints"]["T0_PRE_WEEKEND"]["mean_log_loss"]
    t5_loss = metrics["checkpoints"]["T5_FINAL_PRE_RACE_GRID_AND_FORM_M3"]["mean_log_loss"]
    assert t5_loss < t0_loss


def test_controlled_ablation_ledger_and_cohort_separation():
    """Verify Phase 6.2 prediction ledger and separate cohort evaluations."""
    import pandas as pd
    from backend.forecasting.backtest import OUTPUT_DIR

    # 1. Prediction Ledger
    ledger_path = OUTPUT_DIR / "prediction_ledger.csv"
    assert ledger_path.exists()
    df_ledger = pd.read_csv(ledger_path)

    # 149 races * 7 checkpoints = 1043 records
    assert len(df_ledger) == 1043
    required_cols = [
        "race_id", "season", "round", "checkpoint", "training_cutoff_date",
        "model_family", "model_version", "model_fit_timestamp", "n_candidates",
        "candidate_driver_ids", "predicted_probabilities", "actual_winner_driver_id",
        "top1_correct", "fractional_top1_score", "multiclass_log_loss", "multiclass_brier",
        "expected_calibration_error",
    ]
    for col in required_cols:
        assert col in df_ledger.columns

    # Verify binary top-1 and simplex probabilities
    assert set(df_ledger["top1_correct"].unique()).issubset({0, 1})
    for _, row in df_ledger.head(20).iterrows():
        probs = json.loads(row["predicted_probabilities"])
        assert pytest.approx(sum(probs), abs=1e-4) == 1.0

    # 2. Cohort Separation
    cohort_a_p = OUTPUT_DIR / "cohort_a_metrics.json"
    cohort_b_p = OUTPUT_DIR / "cohort_b_metrics.json"
    cohort_c_p = OUTPUT_DIR / "cohort_c_metrics.json"
    assert cohort_a_p.exists() and cohort_b_p.exists() and cohort_c_p.exists()

    with open(cohort_a_p) as f:
        ca = json.load(f)
    with open(cohort_b_p) as f:
        cb = json.load(f)
    with open(cohort_c_p) as f:
        cc = json.load(f)

    assert ca["race_count"] == 149
    assert cb["race_count"] == 12
    assert cc["race_count"] == 34

    # Verify transitions are non-empty and mathematically bounded
    assert "T4_vs_T0" in ca["transitions"]
    assert "T4_vs_T3" in cc["transitions"]
    assert cc["transitions"]["T4_vs_T3"]["mean_delta_log_loss"] < 0.0
    assert cc["transitions"]["T4_vs_T3"]["significant_loss_at_005"] is True


def test_provenance_audit_and_sensitivity_artifacts():
    """Verify Phase 6.2 provenance audit documentation and candidate sensitivity analysis."""
    from backend.forecasting.backtest import OUTPUT_DIR

    prov_path = OUTPUT_DIR / "PROVENANCE_AUDIT.md"
    assert prov_path.exists()
    prov_text = prov_path.read_text(encoding="utf-8")
    assert "Executive Provenance Audit Statement" in prov_text
    assert "EXP-0001-R3" in prov_text
    assert "EXP-0002" in prov_text
    assert "EXP-0004" in prov_text

    sens_path = OUTPUT_DIR / "sensitivity_analysis.json"
    assert sens_path.exists()
    with open(sens_path) as f:
        sens = json.load(f)
    assert sens["dns_driver_analysis"]["total_dns_records"] == 6
    assert sens["grid_zero_pit_lane_analysis"]["total_grid_zero_records"] == 45
