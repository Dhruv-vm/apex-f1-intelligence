"""Unit tests for APEX Machine Learning Base Package (Phase 8.1).

Validates:
- ForecastResult validation rules, marginal invariants, and JSON serialization.
- BasePredictiveModel and BaseRankingModel contracts.
- ModelRegistry lookup, metadata, and unavailable factory error handling.
- Candidate pool validation, outcome-independent ordering, and effective grid encoding.
- Strictly proper scoring metrics against manually verified toy distributions.
"""

import json
import math
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
import pytest
from pydantic import ValidationError

from ml.base import BasePredictiveModel, BaseRankingModel, ForecastResult
from ml.data.candidate_schema import (
    FORBIDDEN_SORT_COLUMNS,
    GRID_ZERO_AUDIT_NOTE,
    encode_effective_grid,
    enforce_outcome_independent_ordering,
    validate_candidate_pool,
)
from ml.evaluation.metrics import (
    check_probability_simplex,
    compute_single_race_metrics,
    evaluate_race_predictions,
)
from ml.registry import (
    CANONICAL_MODELS,
    ModelFactoryUnavailableError,
    ModelRegistry,
    UnknownModelError,
)


# =====================================================================
# 1. ForecastResult Tests
# =====================================================================

def test_forecast_result_valid_minimal():
    """Valid minimal forecast with only winner probabilities."""
    res = ForecastResult(
        race_id=101,
        model_id="M0",
        driver_ids=[1, 44, 16],
        p_win=[0.5, 0.3, 0.2],
    )
    assert res.race_id == 101
    assert res.model_id == "M0"
    assert len(res.p_win) == 3
    assert math.isclose(sum(res.p_win), 1.0, abs_tol=1e-9)
    assert res.p_podium is None
    assert res.p_top5 is None
    assert res.expected_rank is None

    # Verify JSON serialization
    serialized = res.model_dump_json()
    data = json.loads(serialized)
    assert data["race_id"] == 101
    assert data["p_win"] == [0.5, 0.3, 0.2]


def test_forecast_result_full_marginals_valid():
    """Valid complete forecast with podium, top-5, and expected finishing rank."""
    # 5 drivers: sum(p_win)=1.0, sum(p_podium)=min(3, 5)=3.0, sum(p_top5)=min(5, 5)=5.0
    # expected rank sum = 5 * 6 / 2 = 15.0
    res = ForecastResult(
        race_id=202401,
        model_id="M5",
        driver_ids=[1, 4, 16, 44, 63],
        p_win=[0.40, 0.30, 0.15, 0.10, 0.05],
        p_podium=[0.85, 0.75, 0.60, 0.50, 0.30],
        p_top5=[1.0, 1.0, 1.0, 1.0, 1.0],
        expected_rank=[1.8, 2.3, 3.1, 3.6, 4.2],
    )
    assert math.isclose(sum(res.p_podium), 3.0, abs_tol=1e-9)
    assert math.isclose(sum(res.p_top5), 5.0, abs_tol=1e-9)
    assert math.isclose(sum(res.expected_rank), 15.0, abs_tol=1e-6)


def test_forecast_result_rejects_empty_candidates():
    """Empty candidate set must raise ValidationError."""
    with pytest.raises(ValidationError, match="cannot be empty"):
        ForecastResult(
            race_id=1,
            model_id="M0",
            driver_ids=[],
            p_win=[],
        )


def test_forecast_result_rejects_duplicate_driver_ids():
    """Duplicate driver IDs must raise ValidationError."""
    with pytest.raises(ValidationError, match="Duplicate driver IDs"):
        ForecastResult(
            race_id=1,
            model_id="M0",
            driver_ids=[1, 44, 1],  # Duplicate 1
            p_win=[0.4, 0.3, 0.3],
        )


def test_forecast_result_rejects_length_mismatch():
    """Array length mismatch between driver_ids and p_win must fail."""
    with pytest.raises(ValidationError, match="p_win length"):
        ForecastResult(
            race_id=1,
            model_id="M0",
            driver_ids=[1, 44, 16],
            p_win=[0.6, 0.4],  # Only 2 probabilities for 3 drivers
        )


def test_forecast_result_rejects_out_of_range_probabilities():
    """Probabilities outside [0, 1] must fail."""
    with pytest.raises(ValidationError, match="outside valid probability interval"):
        ForecastResult(
            race_id=1,
            model_id="M0",
            driver_ids=[1, 44],
            p_win=[-0.1, 1.1],
        )


def test_forecast_result_rejects_non_simplex_sum():
    """Winner probabilities not summing to 1.0 must fail."""
    with pytest.raises(ValidationError, match="does not sum to 1.0"):
        ForecastResult(
            race_id=1,
            model_id="M0",
            driver_ids=[1, 44],
            p_win=[0.6, 0.3],  # Sum = 0.9 != 1.0
        )


def test_forecast_result_rejects_invalid_podium_sum():
    """Podium probabilities not summing to min(3, N) must fail."""
    with pytest.raises(ValidationError, match="p_podium sum"):
        ForecastResult(
            race_id=1,
            model_id="M5",
            driver_ids=[1, 44, 16, 4],
            p_win=[0.4, 0.3, 0.2, 0.1],
            p_podium=[0.8, 0.8, 0.8, 0.8],  # Sum = 3.2 != 3.0
        )


def test_forecast_result_rejects_inconsistent_marginal_ordering():
    """p_win > p_podium must be rejected as an impossible marginal."""
    with pytest.raises(ValidationError, match="p_win .* > p_podium"):
        ForecastResult(
            race_id=1,
            model_id="M5",
            driver_ids=[1, 44, 16],
            p_win=[0.6, 0.3, 0.1],
            p_podium=[0.5, 1.0, 1.5],  # Index 0 has p_win 0.6 > p_podium 0.5
        )


def test_forecast_result_rejects_invalid_expected_rank_sum():
    """Expected rank sum violating N*(N+1)/2 must fail."""
    with pytest.raises(ValidationError, match="expected_rank sum"):
        ForecastResult(
            race_id=1,
            model_id="M5",
            driver_ids=[1, 44, 16],
            p_win=[0.5, 0.3, 0.2],
            expected_rank=[1.0, 2.0, 4.0],  # Sum = 7.0 != 3*4/2=6.0
        )


# =====================================================================
# 2. Base Model Contracts Tests
# =====================================================================

class DummyPredictiveModel(BasePredictiveModel):
    """Concrete implementation for testing base predictive contract."""

    @property
    def model_id(self) -> str:
        return "DUMMY_PRED"

    @property
    def feature_names(self) -> List[str]:
        return ["feat_a", "feat_b"]

    def fit(self, X: pd.DataFrame, y: np.ndarray, race_ids: Optional[np.ndarray] = None) -> "DummyPredictiveModel":
        return self

    def predict_proba(self, X: pd.DataFrame, race_ids: Optional[np.ndarray] = None) -> np.ndarray:
        # Uniform within race
        if race_ids is None:
            n = len(X)
            return np.full(n, 1.0 / n)
        probs = np.zeros(len(X), dtype=float)
        for r_id in np.unique(race_ids):
            mask = race_ids == r_id
            probs[mask] = 1.0 / np.sum(mask)
        return probs


class DummyRankingModel(BaseRankingModel):
    """Concrete implementation for testing base ranking contract."""

    @property
    def model_id(self) -> str:
        return "DUMMY_RANK"

    @property
    def feature_names(self) -> List[str]:
        return ["feat_score"]

    def fit(self, X: pd.DataFrame, y_ranks: np.ndarray, race_ids: np.ndarray) -> "DummyRankingModel":
        return self

    def predict_scores(self, X: pd.DataFrame, race_ids: Optional[np.ndarray] = None) -> np.ndarray:
        return X["feat_score"].to_numpy(dtype=float)

    def predict_order(
        self, X: pd.DataFrame, race_ids: np.ndarray, driver_ids: List[int]
    ) -> Dict[int, List[int]]:
        scores = self.predict_scores(X, race_ids)
        df = pd.DataFrame({"race_id": race_ids, "driver_id": driver_ids, "score": scores})
        order_dict = {}
        for r_id, grp in df.groupby("race_id"):
            sorted_drivers = grp.sort_values("score", ascending=False)["driver_id"].tolist()
            order_dict[int(r_id)] = sorted_drivers
        return order_dict


def test_predictive_model_contract():
    """Predictive model contract enforces feature metadata and forecast generation."""
    model = DummyPredictiveModel()
    assert model.model_id == "DUMMY_PRED"
    assert model.feature_names == ["feat_a", "feat_b"]
    assert "class_name" in model.model_metadata

    X = pd.DataFrame({"feat_a": [1.0, 2.0], "feat_b": [3.0, 4.0]})
    y = np.array([1, 0])
    model.fit(X, y)

    res = model.predict_race_forecast(race_id=1, X_race=X, driver_ids=[44, 63])
    assert isinstance(res, ForecastResult)
    assert res.race_id == 1
    assert res.p_win == [0.5, 0.5]


def test_ranking_model_contract_independence():
    """Ranking model is strictly independent and does not inherit from predictive model."""
    rank_model = DummyRankingModel()
    assert not isinstance(rank_model, BasePredictiveModel)
    assert rank_model.model_metadata["is_ranking_model"] is True

    X = pd.DataFrame({"feat_score": [12.5, 45.0, 30.0]})
    race_ids = np.array([1, 1, 1])
    drivers = [11, 1, 4]
    orders = rank_model.predict_order(X, race_ids, drivers)
    # Highest score 45.0 (driver 1), then 30.0 (driver 4), then 12.5 (driver 11)
    assert orders[1] == [1, 4, 11]


# =====================================================================
# 3. ModelRegistry Tests
# =====================================================================

def test_registry_canonical_models_present():
    """Canonical model identities must be defined with metadata."""
    canonical_ids = ModelRegistry.list_canonical_models()
    expected = ["ELO_R3", "M0", "M1", "M2", "M3", "M4", "M5"]
    for m in expected:
        assert m in canonical_ids
        meta = ModelRegistry.get_metadata(m)
        assert meta.model_id == m
        assert meta.family != ""
        assert meta.literature_reference != ""


def test_registry_unknown_model_raises():
    """Querying an unknown model raises UnknownModelError."""
    with pytest.raises(UnknownModelError, match="Unknown model_id 'NON_EXISTENT'"):
        ModelRegistry.get_metadata("NON_EXISTENT")

    with pytest.raises(UnknownModelError):
        ModelRegistry.create_model("NON_EXISTENT")


def test_registry_unavailable_factory_raises():
    """Accessing an unextracted canonical model raises informative ModelFactoryUnavailableError."""
    # Ensure factories are clear
    ModelRegistry.clear_factories_for_testing()
    with pytest.raises(ModelFactoryUnavailableError) as exc_info:
        ModelRegistry.create_model("M4")
    assert "M4" in str(exc_info.value)
    assert "Stage 8.4" in str(exc_info.value)


def test_registry_factory_registration_and_creation():
    """Registering a custom factory enables creation."""
    ModelRegistry.clear_factories_for_testing()
    ModelRegistry.register_factory("M0", lambda: DummyPredictiveModel())
    assert ModelRegistry.is_available("M0")
    inst = ModelRegistry.create_model("M0")
    assert isinstance(inst, DummyPredictiveModel)
    ModelRegistry.clear_factories_for_testing()


# =====================================================================
# 4. Candidate Pool & Ordering Tests
# =====================================================================

def test_validate_candidate_pool_valid():
    """Valid candidate DataFrame passes validation cleanly."""
    df = pd.DataFrame({
        "race_id": [1, 1, 2, 2],
        "driver_id": [1, 44, 1, 44],
        "y": [1, 0, 0, 1],
    })
    res = validate_candidate_pool(df)
    assert len(res) == 4


def test_validate_candidate_pool_rejects_duplicates():
    """Duplicate candidate per race must be caught."""
    df = pd.DataFrame({
        "race_id": [1, 1],
        "driver_id": [44, 44],  # Duplicate Hamilton in race 1
        "y": [1, 0],
    })
    with pytest.raises(ValueError, match="duplicate candidate rows"):
        validate_candidate_pool(df)


def test_validate_candidate_pool_rejects_missing_winner():
    """Race without exactly one winner must fail target validation."""
    df = pd.DataFrame({
        "race_id": [1, 1],
        "driver_id": [1, 44],
        "y": [0, 0],  # Zero winners
    })
    with pytest.raises(ValueError, match="exactly one winner per race"):
        validate_candidate_pool(df, require_target=True)


def test_enforce_outcome_independent_ordering():
    """Sorting must order by driver_id and race_id, rejecting finish position."""
    df = pd.DataFrame({
        "race_id": [1, 1, 1],
        "driver_id": [44, 1, 16],
        "finish_position": [3, 1, 2],
        "y": [0, 1, 0],
    })
    # Valid sort
    ordered = enforce_outcome_independent_ordering(df)
    assert ordered["driver_id"].tolist() == [1, 16, 44]

    # Rejection of outcome columns in sorting
    for forbidden in FORBIDDEN_SORT_COLUMNS:
        with pytest.raises(ValueError, match="Refusing to sort candidates by outcome column"):
            enforce_outcome_independent_ordering(df, additional_sort_cols=[forbidden])


def test_encode_effective_grid_and_grid_zero():
    """Grid 0 is assigned max(positive)+1 and flagged with is_grid_zero."""
    df = pd.DataFrame({
        "race_id": [1, 1, 1, 1],
        "driver_id": [1, 44, 16, 55],
        "grid": [1, 2, 0, 4],  # 16 started from pit lane / grid zero
    })
    res = encode_effective_grid(df)
    assert "effective_grid" in res.columns
    assert "is_grid_zero" in res.columns

    # Driver 16 had grid 0; max positive grid was 4; effective grid must be 4 + 1 = 5.0
    row_16 = res[res["driver_id"] == 16].iloc[0]
    assert row_16["is_grid_zero"] == 1
    assert row_16["effective_grid"] == 5.0

    # Driver 1 had grid 1; effective grid must be 1.0
    row_1 = res[res["driver_id"] == 1].iloc[0]
    assert row_1["is_grid_zero"] == 0
    assert row_1["effective_grid"] == 1.0


# =====================================================================
# 5. Evaluation Metrics & Scoring Rules Tests
# =====================================================================

def test_check_probability_simplex():
    """Simplex verification accurately detects valid and invalid vectors."""
    assert check_probability_simplex(np.array([0.5, 0.5])) is True
    assert check_probability_simplex(np.array([0.7, 0.2, 0.1])) is True
    assert check_probability_simplex(np.array([0.6, 0.3])) is False  # Sum = 0.9
    assert check_probability_simplex(np.array([-0.1, 1.1])) is False  # Out of range
    assert check_probability_simplex(np.array([])) is False  # Empty


def test_single_race_metrics_analytical_toy_example_1():
    """
    Toy case 1: 2 candidates, y=[1, 0], p=[0.8, 0.2].
    - Log loss: -ln(0.8) = 0.2231435513142097
    - Brier score: (0.8 - 1)^2 + (0.2 - 0)^2 = (-0.2)^2 + (0.2)^2 = 0.04 + 0.04 = 0.08
    - Tie-aware top-1: 1.0 (argmax is index 0, winner is index 0)
    - Fractional top-1: 1.0 (single argmax winner)
    """
    y = np.array([1, 0])
    p = np.array([0.8, 0.2])
    metrics = compute_single_race_metrics(y, p)

    expected_ll = -math.log(0.8)
    expected_brier = 0.08

    assert math.isclose(metrics["log_loss"], expected_ll, abs_tol=1e-12)
    assert math.isclose(metrics["brier_score"], expected_brier, abs_tol=1e-12)
    assert metrics["tie_aware_top1"] == 1.0
    assert metrics["fractional_top1"] == 1.0


def test_single_race_metrics_analytical_toy_example_2_tied_probabilities():
    """
    Toy case 2: 2 candidates tied for top probability, y=[1, 0], p=[0.5, 0.5].
    - Log loss: -ln(0.5) = 0.6931471805599453
    - Brier score: (0.5 - 1)^2 + (0.5 - 0)^2 = 0.25 + 0.25 = 0.50
    - Tie-aware top-1: 1.0 (winner is among the tied argmax set)
    - Fractional top-1: 0.5 (1 winner / 2 tied candidates in argmax)
    """
    y = np.array([1, 0])
    p = np.array([0.5, 0.5])
    metrics = compute_single_race_metrics(y, p)

    expected_ll = -math.log(0.5)
    expected_brier = 0.50

    assert math.isclose(metrics["log_loss"], expected_ll, abs_tol=1e-12)
    assert math.isclose(metrics["brier_score"], expected_brier, abs_tol=1e-12)
    assert metrics["tie_aware_top1"] == 1.0
    assert metrics["fractional_top1"] == 0.5


def test_single_race_metrics_analytical_toy_example_3_incorrect_prediction():
    """
    Toy case 3: 3 candidates, winner is index 1, y=[0, 1, 0], p=[0.6, 0.2, 0.2].
    - Log loss: -ln(0.2) = 1.6094379124341003
    - Brier score: (0.6 - 0)^2 + (0.2 - 1)^2 + (0.2 - 0)^2 = 0.36 + 0.64 + 0.04 = 1.04
    - Tie-aware top-1: 0.0 (argmax is index 0, winner is index 1)
    - Fractional top-1: 0.0
    """
    y = np.array([0, 1, 0])
    p = np.array([0.6, 0.2, 0.2])
    metrics = compute_single_race_metrics(y, p)

    expected_ll = -math.log(0.2)
    expected_brier = 1.04

    assert math.isclose(metrics["log_loss"], expected_ll, abs_tol=1e-12)
    assert math.isclose(metrics["brier_score"], expected_brier, abs_tol=1e-12)
    assert metrics["tie_aware_top1"] == 0.0
    assert metrics["fractional_top1"] == 0.0


def test_single_race_metrics_rejects_malformed_inputs():
    """Rejects length mismatch, no winner, or invalid simplex."""
    # Length mismatch
    with pytest.raises(ValueError, match="Length mismatch"):
        compute_single_race_metrics(np.array([1, 0]), np.array([1.0]))

    # No winner
    with pytest.raises(ValueError, match="at least one recorded winner"):
        compute_single_race_metrics(np.array([0, 0]), np.array([0.5, 0.5]))

    # Non-simplex sum
    with pytest.raises(ValueError, match="Malformed probability vector"):
        compute_single_race_metrics(np.array([1, 0]), np.array([0.6, 0.6]))


def test_evaluate_race_predictions_multi_race_macro_average():
    """
    Evaluates multi-race aggregation:
    Race 1: y=[1, 0], p=[0.8, 0.2] -> LL = -ln(0.8), Brier = 0.08, TieTop1 = 1.0, FracTop1 = 1.0
    Race 2: y=[0, 1], p=[0.5, 0.5] -> LL = -ln(0.5), Brier = 0.50, TieTop1 = 1.0, FracTop1 = 0.5

    Mean LL = (-ln(0.8) - ln(0.5)) / 2 = (0.22314355 + 0.69314718) / 2 = 0.458145366
    Mean Brier = (0.08 + 0.50) / 2 = 0.29
    Mean TieTop1 = (1.0 + 1.0) / 2 = 1.0
    Mean FracTop1 = (1.0 + 0.5) / 2 = 0.75
    """
    df = pd.DataFrame({
        "race_id": [1, 1, 2, 2],
        "driver_id": [1, 2, 1, 2],
        "y": [1, 0, 0, 1],
        "probability": [0.8, 0.2, 0.5, 0.5],
    })
    summary = evaluate_race_predictions(df)
    assert summary["races"] == 2

    expected_mean_ll = (-math.log(0.8) - math.log(0.5)) / 2.0
    expected_mean_brier = (0.08 + 0.50) / 2.0
    expected_tie_top1 = 1.0
    expected_frac_top1 = 0.75

    assert math.isclose(summary["mean_log_loss"], expected_mean_ll, abs_tol=1e-12)
    assert math.isclose(summary["mean_brier_score"], expected_mean_brier, abs_tol=1e-12)
    assert math.isclose(summary["tie_aware_top1"], expected_tie_top1, abs_tol=1e-12)
    assert math.isclose(summary["fractional_top1"], expected_frac_top1, abs_tol=1e-12)


# =====================================================================
# 6. Additional Contract, Serialization & Grid Semantics Regression Tests
# =====================================================================

def test_encode_effective_grid_comprehensive_semantics():
    """
    Verifies comprehensive starting grid information semantics:
    - Positive grid values (grid > 0)
    - Verified zero-grid records (grid == 0 with independent pre-race evidence)
    - Ambiguous zero-grid records (grid == 0 without pre-race verification)
    - Missing grid values (NaN / null)
    - Negative and corrupted grid values (grid < 0 or invalid strings)
    """
    df = pd.DataFrame({
        "race_id": [1, 1, 1, 1, 1, 1],
        "driver_id": [1, 2, 3, 4, 5, 6],
        "grid": [1, 0, 0, np.nan, -1, "corrupted"],
        "pre_race_pit_lane": [0, 1, 0, 0, 0, 0],
    })
    res = encode_effective_grid(df, pre_race_verification_col="pre_race_pit_lane")

    # Max positive grid in race is 1. Effective grid for all non-positive/missing is 1 + 1 = 2.0
    # Driver 1: Positive grid 1
    row1 = res[res["driver_id"] == 1].iloc[0]
    assert row1["effective_grid"] == 1.0
    assert row1["is_grid_zero"] == 0
    assert row1["is_grid_missing"] == 0
    assert row1["is_grid_invalid"] == 0
    assert row1["is_grid_ambiguous"] == 0
    assert row1["is_pit_lane_verified"] == 0

    # Driver 2: Verified zero-grid via pre-race evidence (grid == 0, pre_race_pit_lane == 1)
    row2 = res[res["driver_id"] == 2].iloc[0]
    assert row2["effective_grid"] == 2.0
    assert row2["is_grid_zero"] == 1
    assert row2["is_grid_missing"] == 0
    assert row2["is_grid_invalid"] == 0
    assert row2["is_grid_ambiguous"] == 0
    assert row2["is_pit_lane_verified"] == 1

    # Driver 3: Ambiguous zero-grid (grid == 0, no pre-race verification)
    row3 = res[res["driver_id"] == 3].iloc[0]
    assert row3["effective_grid"] == 2.0
    assert row3["is_grid_zero"] == 1
    assert row3["is_grid_missing"] == 0
    assert row3["is_grid_invalid"] == 0
    assert row3["is_grid_ambiguous"] == 1
    assert row3["is_pit_lane_verified"] == 0

    # Driver 4: Missing grid (NaN)
    row4 = res[res["driver_id"] == 4].iloc[0]
    assert row4["effective_grid"] == 2.0
    assert row4["is_grid_zero"] == 0
    assert row4["is_grid_missing"] == 1
    assert row4["is_grid_invalid"] == 0
    assert row4["is_grid_ambiguous"] == 0
    assert row4["is_pit_lane_verified"] == 0

    # Driver 5: Negative grid (-1) -> marked invalid
    row5 = res[res["driver_id"] == 5].iloc[0]
    assert row5["effective_grid"] == 2.0
    assert row5["is_grid_zero"] == 0
    assert row5["is_grid_missing"] == 0
    assert row5["is_grid_invalid"] == 1
    assert row5["is_grid_ambiguous"] == 0
    assert row5["is_pit_lane_verified"] == 0

    # Driver 6: Corrupted string grid ("corrupted") -> marked invalid
    row6 = res[res["driver_id"] == 6].iloc[0]
    assert row6["effective_grid"] == 2.0
    assert row6["is_grid_zero"] == 0
    assert row6["is_grid_missing"] == 0
    assert row6["is_grid_invalid"] == 1
    assert row6["is_grid_ambiguous"] == 0
    assert row6["is_pit_lane_verified"] == 0


def test_post_race_result_field_cannot_influence_pre_race_grid_features():
    """
    Strict anti-leakage test:
    1. Passing a post-race result field as pre_race_verification_col raises ValueError.
    2. Changing post-race result fields produces zero change on pre-race grid classification.
    """
    df1 = pd.DataFrame({
        "race_id": [1, 1, 1],
        "driver_id": [1, 2, 3],
        "grid": [1, 0, np.nan],
        "position_text": ["1", "10", "12"],
        "finish_position": [1, 10, 12],
        "status": ["Finished", "Finished", "Finished"],
        "y": [1, 0, 0],
    })

    # Passing post-race column must raise ValueError
    for forbidden in ["position_text", "finish_position", "status", "y"]:
        with pytest.raises(ValueError, match="Temporal leakage violation"):
            encode_effective_grid(df1, pre_race_verification_col=forbidden)

    # Encode features on baseline dataframe
    res1 = encode_effective_grid(df1)

    # Create perturbed dataframe where post-race outcomes are heavily modified
    # (driver 2 was 'Finished' P10, now changed to 'W' / DNS / Withdrawn)
    df2 = df1.copy()
    df2["position_text"] = ["2", "W", "DNF"]
    df2["finish_position"] = [2, 0, 0]
    df2["status"] = ["Finished", "Withdrawn", "Accident"]
    df2["y"] = [0, 0, 0]

    res2 = encode_effective_grid(df2)

    # Pre-race grid features must be bit-for-bit identical regardless of post-race outcome changes
    feature_cols = [
        "effective_grid",
        "is_grid_zero",
        "is_grid_missing",
        "is_grid_invalid",
        "is_grid_ambiguous",
        "is_pit_lane_verified",
    ]
    pd.testing.assert_frame_equal(res1[feature_cols], res2[feature_cols])


def test_audit_historical_grid_zero_retrospective():
    """Retrospective audit helper correctly identifies 49 active starters vs 7 withdrawals."""
    df = pd.DataFrame({
        "grid": [0] * 56,
        "position_text": ["10"] * 40 + ["R"] * 9 + ["W"] * 7,
    })
    from ml.data.candidate_schema import audit_historical_grid_zero_retrospective
    audit = audit_historical_grid_zero_retrospective(df)
    assert audit["total_zero_grid"] == 56
    assert audit["active_starters"] == 49
    assert audit["withdrawn_dns"] == 7
    assert math.isclose(audit["active_starter_proportion"], 49 / 56)


def test_forecast_result_rejects_invalid_nesting_podium_top5():
    """p_podium > p_top5 violates P(win) <= P(podium) <= P(top5)."""
    # 6 candidates: sum(p_podium) == 3.0, sum(p_top5) == 5.0
    with pytest.raises(ValidationError, match="p_podium .* > p_top5"):
        ForecastResult(
            race_id=1,
            model_id="M5",
            driver_ids=[1, 2, 3, 4, 5, 6],
            p_win=[0.35, 0.25, 0.20, 0.10, 0.05, 0.05],
            p_podium=[0.90, 0.70, 0.60, 0.40, 0.25, 0.15],  # Sum = 3.0
            p_top5=[0.85, 0.95, 0.95, 0.85, 0.70, 0.70],    # Sum = 5.0, but index 0 has p_podium (0.90) > p_top5 (0.85)
        )


def test_forecast_result_rejects_invalid_nesting_win_top5_without_podium():
    """When p_podium is omitted, p_win > p_top5 must still be rejected."""
    # 6 candidates: sum(p_win) == 1.0, sum(p_top5) == 5.0
    with pytest.raises(ValidationError, match="p_win .* > p_top5"):
        ForecastResult(
            race_id=1,
            model_id="M5",
            driver_ids=[1, 2, 3, 4, 5, 6],
            p_win=[0.40, 0.25, 0.15, 0.10, 0.05, 0.05],     # Sum = 1.0
            p_top5=[0.35, 0.95, 0.95, 0.95, 0.90, 0.90],    # Sum = 5.0, but index 0 has p_win (0.40) > p_top5 (0.35)
        )


def test_forecast_result_rejects_out_of_range_marginal_probabilities():
    """Marginal probabilities must be bounded strictly in [0, 1]."""
    with pytest.raises(ValidationError, match="outside \\[0, 1\\]"):
        ForecastResult(
            race_id=1,
            model_id="M5",
            driver_ids=[1, 44],
            p_win=[0.6, 0.4],
            p_podium=[-0.1, 2.1],  # Negative and > 1.0
        )


def test_forecast_result_json_roundtrip_and_alignment():
    """ForecastResult preserves candidate alignment and precision through JSON roundtrip."""
    original = ForecastResult(
        race_id=202424,
        model_id="M5",
        driver_ids=[4, 1, 16, 44],
        p_win=[0.40, 0.35, 0.15, 0.10],
        p_podium=[0.90, 0.85, 0.70, 0.55],
        p_top5=[1.0, 1.0, 1.0, 1.0],
        expected_rank=[1.8, 2.1, 2.9, 3.2],
        metadata={"checkpoint": "T5", "version": "v1.0.0"},
    )
    serialized = original.model_dump_json()
    reconstructed = ForecastResult.model_validate_json(serialized)

    assert reconstructed.race_id == original.race_id
    assert reconstructed.model_id == original.model_id
    assert reconstructed.driver_ids == [4, 1, 16, 44]
    assert reconstructed.p_win == [0.40, 0.35, 0.15, 0.10]
    assert reconstructed.p_podium == [0.90, 0.85, 0.70, 0.55]
    assert reconstructed.expected_rank == [1.8, 2.1, 2.9, 3.2]
    assert reconstructed.metadata["checkpoint"] == "T5"


def test_compute_single_race_metrics_multiple_actual_winners_tie():
    """
    Handling of dead-heat / multiple actual winners (sum(y) > 1):
    y = [1, 1, 0], p = [0.4, 0.4, 0.2]
    Log loss: average of -ln(0.4) and -ln(0.4) = -ln(0.4)
    Brier score: (0.4 - 1)^2 + (0.4 - 1)^2 + (0.2 - 0)^2 = 0.36 + 0.36 + 0.04 = 0.76
    Argmax candidates: indices 0 and 1 (both tied at 0.4)
    Winner hits in top: 2
    Tie-aware top-1: 1.0
    Fractional top-1: 2 / 2 = 1.0
    """
    y = np.array([1, 1, 0])
    p = np.array([0.4, 0.4, 0.2])
    metrics = compute_single_race_metrics(y, p)

    expected_ll = -math.log(0.4)
    expected_brier = 0.76

    assert math.isclose(metrics["log_loss"], expected_ll, abs_tol=1e-12)
    assert math.isclose(metrics["brier_score"], expected_brier, abs_tol=1e-12)
    assert metrics["tie_aware_top1"] == 1.0
    assert metrics["fractional_top1"] == 1.0
