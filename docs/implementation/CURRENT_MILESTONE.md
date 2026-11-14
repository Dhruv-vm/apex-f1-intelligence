# Current Milestone: Phase 8.1 — Shared ML Package Foundation

- **Milestone Code:** `Phase 8.1` / `ML-FOUNDATION`
- **Milestone Title:** Shared ML Package Foundation, Base Contracts, Canonical Registry & Scoring Rules
- **Start Date:** 2026-11-14
- **Completion Date:** 2026-11-14
- **Current Lifecycle Status:** `COMPLETED (Stage 8.1 Delivered; Stage 8.2 Ready)`

---

## 1. Milestone Objective

Construct the production-quality, reusable machine learning foundation at the repository root (`ml/`). Establish explicit model contracts (`ForecastResult`, `BasePredictiveModel`, `BaseRankingModel`), a canonical model registry preserving research nomenclature (`ELO_R3`, `M0`–`M5`), outcome-independent candidate validation schemas, and independently tested multiclass proper scoring rules matching EXP-0001 through EXP-0005 standards.

---

## 2. Acceptance Criteria Checklist

- [x] **Core Model Contracts (`ml/base.py`):**
  - `ForecastResult`: Pydantic v2 validated container guaranteeing unique driver IDs, length consistency, simplex normalization ($\sum p_{\text{win}} = 1.0 \pm 10^{-9}$), Plackett-Luce consistent marginal bounds ($\sum p_{\text{podium}} = \min(3, N)$, $\sum p_{\text{top5}} = \min(5, N)$, $p_{\text{win}}[i] \le p_{\text{podium}}[i] \le p_{\text{top5}}[i]$), and expected finishing rank invariants ($\sum E[\text{rank}] = N(N+1)/2$, $1 \le E[\text{rank}]_i \le N$).
  - `BasePredictiveModel`: Abstract base class enforcing canonical `model_id`, `feature_names`, `fit`, `predict_proba` with race-level probability normalization, and `predict_race_forecast`.
  - `BaseRankingModel`: Dedicated ranking interface enforcing independence from classification models; outputs utility scores and predicted driver ordering without treating raw ranking scores as probabilities.
- [x] **Canonical Model Registry (`ml/registry.py`):**
  - Canonical models registered: `ELO_R3`, `M0`, `M1`, `M2`, `M3`, `M4`, `M5`.
  - Distinguishes canonical research metadata (`ModelMetadata`) from active factories (`_FACTORIES`).
  - Raises informative `ModelFactoryUnavailableError` for unextracted canonical models detailing their scheduled stage (e.g. Stage 8.4), avoiding fake or premature implementations.
- [x] **Candidate Data Schema (`ml/data/candidate_schema.py`):**
  - Candidate pool validation ensuring exactly one candidate per driver per race and binary target consistency.
  - Outcome-independent candidate ordering (`enforce_outcome_independent_ordering`) sorting strictly by `race_id` and `driver_id`; rejects sorting by finishing position or any post-race outcome field.
  - Retains empirical grid-zero handling: race-specific effective starting-grid position ($\max_{j: \text{grid}_j > 0}(\text{grid}_j) + 1$) and binary `is_grid_zero` flag with explicit audit note regarding timing ambiguity (49 pit-lane starts, 7 steward verifications).
- [x] **Proper Scoring Metrics (`ml/evaluation/metrics.py`):**
  - Single-race and multi-race evaluation functions for multiclass log loss, multiclass Brier score, tie-aware top-1 accuracy, and fractional top-1 credit.
  - Probability simplex normalization checker (`check_probability_simplex`).
  - Verified against manually computed analytical toy distributions with exact agreement.
- [x] **Automated Testing & Regression Gate (`tests/test_ml_base.py`):**
  - 35 new unit tests covering forecast invariants, model contracts, registry behavior, candidate ordering, grid semantics, and scoring rules.
  - Full backend test suite passing with zero regressions: **162 passed, 0 failed**.
- [x] **Preservation of Existing Functionality:**
  - `backend/forecasting/` and `backend/features/practice.py` preserved intact.
  - EXP-0001 through EXP-0006 historical experiment artifacts preserved without modification.

---

## 3. Transition to Stage 8.2

Stage 8.1 is complete. The foundation is ready for:
1. **Stage 8.2:** Implement point-in-time data and feature processing in `ml/features/point_in_time.py` (rolling driver and constructor form with strict temporal cutoff guards).
2. **Stage 8.3:** Implement multi-model walk-forward evaluation harness in `ml/evaluation/harness.py`.
3. **Stage 8.4:** Port Models 0–5 and Elo R3 to `ml/models/` and execute baseline reproduction within strict parity bounds.
4. **Stage 8.5:** Implement LightGBM LambdaMART listwise ranking.
5. **Stage 8.6:** Hierarchical Bayesian skill decomposition research design.
