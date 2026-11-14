# EXP-0005: Walk-Forward Prediction Provenance Audit & Controlled Ablation Protocol

**Milestone:** Phase 6.2  
**Author:** Antigravity (Engineering & Infrastructure)  
**Verification Date:** 2026-11-05  
**Evaluation Scope:** Primary Historical Benchmark Cohort (2018–2024, 149 Grand Prix, 2,979 Candidate Records)

---

## 1. Executive Provenance Audit Statement

In Phase 6.1, historical walk-forward benchmark metrics were reported across checkpoints $T_0$, $T_4$, and $T_5$:

| Reported Checkpoint | Reported Model Label | Reported Log Loss | Reported Brier Score |
|:---|:---|:---:|:---:|
| **$T_0$ (Pre-Weekend)** | Model 1 — Elo Prior | 2.0588 | 0.8053 |
| **$T_4$ (Post-Qualifying)** | Model 2 — Logistic Grid | 1.5942 | 0.6834 |
| **$T_5$ (Final Pre-Race)** | Model 3 — Grid + Form | 1.3552 | 0.6127 |
| **$T_5$ (Final Pre-Race)** | Model 5 — Plackett-Luce | 1.3517 | 0.5966 |

### Provenance Audit Finding
An empirical code and artifact audit reveals that **the Phase 6.1 results were lookups and rescorings of predictions previously generated during EXP-0001-R3, EXP-0002, and EXP-0004**.
Specifically, `backend/forecasting/backtest.py` directly read:
1. `artifacts/reports/EXP-0001-R3/candidate_predictions.csv` (Elo rating probabilities)
2. `artifacts/reports/EXP-0002/model2_logistic_predictions.csv` (Grid-only logistic regression)
3. `artifacts/reports/EXP-0002/model3_driver_constructor_predictions.csv` (Grid + driver/constructor form)
4. `artifacts/reports/EXP-0004/model5_predictions.csv` (Plackett-Luce multinomial choice)

These predictions were **not** recomputed independently as an incremental sequential pipeline during Phase 6.1. They were pre-computed static artifacts re-evaluated across the 149-race cohort.

---

## 2. Methodological Confounding in Phase 6.1

The Phase 6.1 comparison suffered from an acute scientific confound: **information arrival was completely confounded with model architecture differences**.

1. **Architecture Discrepancy:**
   - At $T_0$, the model was a Bradley-Terry / Elo pairwise rating model with fixed $K$-factor and exponential logistic mapping ($P \propto 10^{R/400}$).
   - At $T_4$, the model was an L2-regularized logistic regression model on starting grid features.
   - At $T_5$, the model was an L2-regularized logistic regression model or Plackett-Luce choice model on starting grid and rolling form features.
2. **Missing Form Features in $T_4$:**
   - In EXP-0002 Model 2 ($T_4$), the feature set contained **only** grid features (`effective_grid`, `log_grid`, `is_front_row`, `is_pole`, `is_grid_zero`) and contained **zero** historical driver or constructor form features.
   - In EXP-0002 Model 3 ($T_5$), driver and constructor form features were added back.
   - Consequently, the observed improvement from $T_4$ to $T_5$ ($\Delta \text{Log Loss} = -0.2390$) was **not** merely pre-race grid adjustments or penalty drops: it was primarily the re-introduction of rolling form features!
3. **Apparent vs Real Information Gain:**
   - Comparing an Elo prior ($T_0$: 2.0588) to a Grid + Form Logistic model ($T_5$: 1.3552) yielded an apparent delta of $-0.7036$ in log loss.
   - Over two-thirds of this apparent gain was simply the superior calibration and flexibility of regularized logistic regression over the uncalibrated Elo prior, rather than evidence arrival.

---

## 3. Phase 6.2 Controlled Ablation Architecture

To isolate the true marginal value of information arrival and evaluate Hypothesis HYP-0001 with scientific validity, Phase 6.2 enforces **model architecture invariance**:

### 3.1 Invariant Model Family
- **Estimator:** L2-regularized binary logistic regression fitted via Newton-Raphson (Iteratively Reweighted Least Squares) with exact Hessian formulation.
- **Regularization:** Fixed penalty parameter $C = 1.0$ ($\lambda = 1.0$), with intercept strictly unpenalized.
- **Preprocessing:** Z-score standardization ($\mu, \sigma$) computed strictly from historical training races ($r' < r$), with zero forward leakage.
- **Candidate Normalization:** Raw candidate probabilities are normalized via softmax over the active race candidate simplex $\sum_{i \in \text{candidates}} p_i = 1.0$.
- **Candidate Ordering:** Deterministically sorted by `driver_id`.

### 3.2 Incrementally Expanding Checkpoint Features
1. **$T_0$ (Pre-Weekend Form):**
   - 11 rolling historical features: `driver_prior_races`, `driver_win_rate_all`, `driver_win_rate_last5`, `driver_mean_finish_last5`, `driver_finish_std_last5`, `constructor_prior_races`, `constructor_win_rate_all`, `constructor_win_rate_last5`, `constructor_mean_finish_last5`, `driver_mean_points_last5`, `constructor_mean_points_last5`.
2. **$T_1$ (Post-FP1):**
   - $T_0$ Form + `fp1_pace_delta` + `fp1_missing`.
3. **$T_2$ (Post-FP2):**
   - $T_1$ + `fp2_pace_delta` + `fp2_degradation_slope` + `fp2_missing`.
4. **$T_3$ (Post-FP3):**
   - $T_2$ + `fp3_pace_delta` + `fp3_missing`.
5. **$T_4$ (Post-Qualifying):**
   - $T_0$ Form + practice + Qualifying Grid (`effective_grid`, `log_grid`, `is_front_row`, `is_pole`, `is_grid_zero`).
6. **$T_5$ (Final Pre-Race):**
   - $T_0$ Form + practice + Final Starting Grid (accounting for post-qualifying penalties, gearbox drops, and pit-lane starts).

---

## 4. Canonical Prediction Ledger Specification

Every prediction evaluated in Phase 6.2 is materialized in `artifacts/reports/EXP-0005/prediction_ledger.csv`.
No aggregate metric in any report or JSON artifact is accepted unless verifiable from this ledger.

### Ledger Schema
- `race_id`: String (e.g. `"2024_24"`)
- `season`: Integer (2018–2024)
- `round`: Integer (1–24)
- `checkpoint`: String (`"T0_PRE_WEEKEND"`, `"T1_POST_FP1"`, `"T2_POST_FP2"`, `"T3_POST_FP3"`, `"T4_POST_QUALIFYING"`, `"T4_CONTROLLED"`, `"T5_FINAL_PRE_RACE"`)
- `training_cutoff_date`: ISO 8601 Date
- `model_family`: String (`"L2_Regularized_Logistic_Regression"`)
- `model_version`: String (`"v1.2-controlled-ablation"`)
- `model_fit_timestamp`: UTC ISO 8601 Timestamp
- `n_candidates`: Integer (typically 20)
- `candidate_driver_ids`: JSON string array of sorted candidate driver IDs
- `predicted_probabilities`: JSON string array of normalized candidate probabilities ($\sum P = 1.0$)
- `actual_winner_driver_id`: String (e.g. `"norris"`)
- `top1_correct`: Integer (0 or 1, deterministic tie-breaking on lowest candidate ID)
- `fractional_top1_score`: Float ($p_{\text{winner}}$)
- `multiclass_log_loss`: Float ($-\ln(p_{\text{winner}})$)
- `multiclass_brier`: Float ($\sum (p_i - y_i)^2$)
- `expected_calibration_error`: Float (10-bin ECE)

Total ledger records: $149 \text{ races} \times 7 \text{ checkpoint configurations} = 1,043 \text{ rows}$.
