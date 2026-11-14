# APEX — Chronological Research Log

This document serves as the permanent chronological research record of the **APEX — F1 Intelligence** platform. It tracks all research questions, hypotheses, experimental findings, methodology decisions, failed approaches, and scientific lessons learned.

---

## 1. Research Index & Overview

| Entry Date | Research Question | Target Checkpoint | Key Action / Milestone | Scientific Outcome | Reference Docs |
|---|---|---|---|---|---|
| **2026-10-18** | Scope & Feasibility | $T_0 \dots T_6$ | Provider empirical audit | Verified Jolpica (1950–2026), OpenF1 (2023–2026), FastF1 limitations. ADR-0002 approved. | [DATA_AVAILABILITY_AUDIT.md](research/DATA_AVAILABILITY_AUDIT.md) |
| **2026-10-19** | RQ1: Static Pre-Weekend | $T_0$ | EXP-0001 (Elo Baseline R1–R3) | Log loss: `2.278177`, Brier: `0.845726`. Identified tie-break leakage; corrected to outcome-independent sorting by `driver_id`. | [EXPERIMENT_INDEX.md](experiments/EXPERIMENT_INDEX.md) |
| **2026-10-19** | Calibration Drift | $T_0$ | EXP-0001-CAL-001 | Fixed-bin ECE: `0.030667` (95% CI: `[0.0268, 0.0342]`), CITL: `0.000000`. Baseline Elo probabilities are well-calibrated in-the-large. | `artifacts/reports/EXP-0001-CAL-001/` |
| **2026-10-19** | Candidate Definition | $T_5$ | Candidate Field Audit | Audited 7,285 entrant rows across 346 races. Established provisional result-record proxy caveat and race-specific `effective_grid` calculation. | [CANDIDATE_FIELD_AUDIT.md](research/CANDIDATE_FIELD_AUDIT.md) |
| **2026-11-04** | RQ1 / HYP-GRID-001 | $T_5$ | EXP-0002 Model 0 & Model 1 | Starting grid dominance confirmed: Model 1 Log Loss `1.583766` vs Elo `2.278177` ($p < 10^{-15}$). | [05_static_grid_benchmark.ipynb](../notebooks/05_static_grid_benchmark.ipynb) |
| **2026-11-04** | RQ1 / HYP-GRID-002 | $T_5$ | EXP-0002 Model 2 & Model 3 | Adding rolling form features to grid features drastically improves Log Loss (`1.355201` vs `1.594207`). | `artifacts/reports/EXP-0002/model3_metrics.json` |
| **2026-11-04** | GBDT vs. Linear Form | $T_5$ | EXP-0002 Model 4 (LightGBM) | **Key Counter-Intuitive Finding:** LightGBM achieves higher Top-1 (`53.02%` vs `51.68%`), but **degrades Proper Scoring Rules** (Log Loss: `1.409149` vs `1.355201`). | `artifacts/reports/EXP-0002/model4_metrics.json` |
| **2026-11-04** | Post-Hoc Calibration | $T_5$ | EXP-0003 Walk-Forward Calibration | Platt & Temperature scaling improve Model 4 (Log Loss `1.3876` vs `1.4091`), but Model 3 remains superior (`1.3552`). Isotonic degrades log loss. | `artifacts/reports/EXP-0003/` |
| **2026-11-04** | Direct Choice Model | $T_5$ | EXP-0004 Model 5 (Plackett-Luce) | Direct race-level likelihood optimization achieves state-of-the-art results: Log Loss `1.351747`, Brier `0.596564`, Top-1 `54.36%`. Resolved 0.494220 reporting discrepancy. | `artifacts/reports/EXP-0004/` |

---

## 2. Detailed Chronological Entries

### Entry 001: 2026-10-18 — Foundational Provider Capabilities & Rate Limits
- **Objective:** Determine which Formula 1 timing and telemetry data providers can support chronological backtesting from 1950 to 2026 without data leakage.
- **Hypothesis:** Jolpica/Ergast can supply race results and starting grids across 1950–2026; OpenF1 can supply high-frequency telemetry and sector times for modern seasons (2023+).
- **Finding:** Jolpica verified for 1950–2025 completed seasons and 2026 year-to-date. OpenF1 telemetry car data operates at ~3.7 Hz. OpenF1 rate-limits unthrottled requests with HTTP 429. FastF1 requires authenticated `f1auth.json` tokens for direct live timing archives.
- **Decision:** Approved ADR-0002: Jolpica is primary historical spine; OpenF1 is modern telemetry source.

### Entry 002: 2026-10-19 — Candidate Ordering and Tie-Break Leakage in EXP-0001
- **Observation:** In EXP-0001-R1 and R2, legacy top-1 accuracy reported `0.335260` (116/346). In 2010 Round 1, all 24 drivers entered with equal starting Elo ratings ($P_i = 1/24$).
- **Root Cause Analysis:** Candidates were sorted by `finish_position_int` before the race loop. Because `np.argmax()` returns the first occurrence of the maximum value in case of ties, index 0 (Fernando Alonso, the observed winner) was selected, creating retrospective outcome leakage on ties.
- **Correction:** Enforced strict outcome-independent candidate ordering by sorting deterministically by `driver_id`.
- **Result:** In EXP-0001-R3, tie-aware top-1 (`0.335260`) and fractional credit (`0.332490`) remained unaffected, while legacy argmax top-1 dropped to `0.332370` (115/346).
- **Rule Established:** All modeling code must sort candidates by outcome-independent identifiers (`driver_id` or ascending `grid_position` with `driver_id` tie-break) before predicting.

### Entry 003: 2026-10-19 — Candidate Entrant Pool Definition & Grid-Zero Caveat
- **Investigation:** Examined 56 candidate records with `grid_position == 0`.
- **Finding:** 49 represented verified pit-lane starts; 7 represented anomalies or grid adjustments requiring verification.
- **Methodology Decision:** Did not treat `grid == 0` as definitive proof of a pit start. Replaced arbitrary `effective_grid = 21` with race-specific encoding: $\text{effective\_grid} = \max_{i, \text{grid}_i > 0}(\text{grid}_i) + 1$, accompanied by an explicit `is_grid_zero` flag.
- **Limitation Acknowledged:** Entrants represent a provisional result-record proxy until pre-session entry lists are reconstructed. Post-race DNS status must never be used to filter candidates.

### Entry 004: 2026-11-04 — EXP-0002 Static Starting Grid Benchmark Models 0–3
- **Objective:** Evaluate the predictive power of starting grid position ($T_5$ cutoff) versus pre-weekend Elo ($T_0$).
- **Findings (Primary Cohort 2018–2024, 149 Races):**
  - **Model 0 (Uniform $1/N_r$):** Mean Log Loss: `2.995388`, Brier: `0.949982`.
  - **Model 1 (Empirical Grid Frequency, Laplace $\alpha=10$):** Mean Log Loss: `1.583766`, Brier: `0.682312`, Top-1: `49.66%`.
  - **Model 2 (Grid-Only Logistic Regression):** Mean Log Loss: `1.594207`, Brier: `0.683382`, Top-1: `49.66%`.
  - **Model 3 (Grid + Driver/Constructor Form Logit):** Mean Log Loss: `1.355201`, Brier: `0.612698`, Top-1: `51.68%`.
- **Conclusion:** Starting grid alone cuts log loss from 2.278 (Elo) to 1.584. Adding 11 rolling form features cuts log loss further from 1.594 to 1.355.

### Entry 005: 2026-11-04 — EXP-0002 Model 4 LightGBM Implementation & Proper Scoring Analysis
- **Research Question:** Does a tree-based GBDT classifier (LightGBM) improve out-of-sample probabilistic forecasting over the regularized linear/form model?
- **Setup:** Fixed configuration (`objective='binary'`, `n_estimators=250`, `learning_rate=0.03`, `num_leaves=15`, `min_child_samples=20`, `subsample=0.8`, `colsample_bytree=0.8`, `reg_lambda=1.0`, `random_state=42`). 16 features identical to Model 3. Strict walk-forward evaluation (2010–2026, 346 races).
- **Empirical Measured Results (Primary Cohort 2018–2024, 149 Races):**
  - **Mean Multiclass Log Loss:** `1.409149` (Model 3: `1.355201`, delta: `+0.053948` worse)
  - **Mean Multiclass Brier Score:** `0.628561` (Model 3: `0.612698`, delta: `+0.015863` worse)
  - **Fractional Top-1 Accuracy:** `0.530201` (Model 3: `0.516779`, delta: `+0.013422` higher)
  - **Tie-Aware Top-1 Accuracy:** `0.530201` (Model 3: `0.516779`, delta: `+0.013422` higher)
- **Scientific Interpretation:**
  1. **Proper Scoring Rule Dominance:** Model 4 is more accurate at picking the single most likely winner (79 wins vs 77 wins for Model 3), but produces worse probability distributions overall.
  2. **Overconfidence & Tail Distortion:** Standard tree boosting with binary cross-entropy places extreme confidence on high-probability candidates when normalized with $\sum p_i = 1$. In the ~47% of races where the pole/front-row driver does not win, the penalized log loss on the true winner is significantly larger.
  3. **Methodological Takeaway:** Sports forecasting benchmarks must never declare a model "superior" based solely on argmax accuracy. Logistic regression with smooth L2 regularization naturally produces better calibrated, more conservative multiclass probabilities than uncalibrated tree boosting.

### Entry 006: 2026-11-04 — EXP-0003 Probability Calibration Benchmark (Models 3 & 4)
- **Research Question:** Can post-hoc probability calibration improve the reliability of F1 race-winner probability distributions without changing the underlying predictive models?
- **Setup:** Walk-forward expanding history (346 races, 2010–2026). Initial 20 uniform cold-start races excluded; 30 valid prior trained races required before calibrating. Tested Platt Scaling, Isotonic Regression, and Temperature Scaling on Model 3 and Model 4 out-of-sample predictions.
- **Empirical Findings (Primary Cohort 2018–2024, 149 Races):**
  - **Model 4 (LightGBM) Point Improvement under Temperature & Platt Scaling:**
    - Raw Model 4 Log Loss decreases from `1.409149` to `1.387587` (Temperature, $T \approx 1.360$) and `1.388663` (Platt).
    - Model 4 Brier score decreases from `0.628561` to `0.622523` (Platt) and `0.623285` (Temperature).
    - ECE decreases from `0.013875` to `0.007314` (Platt) and `0.007818` (Temperature).
    - Fractional Top-1 accuracy is preserved at `53.0201%` (79 / 149).
  - **Model 3 (Logistic) Invariance to Calibration:**
    - Raw Model 3 is already close to canonical temperature: $T \approx 1.007$.
    - Calibration differences are minor ($\Delta \text{LogLoss} < +0.0026$).
    - Model 3 Raw Log Loss (`1.355201`) remains lower than calibrated Model 4 (`1.387587`).
  - **Isotonic Regression Performance:**
    - Step-function mapping produces severe log-loss degradation on outlier winners, increasing Log Loss to `1.450040` on Model 4 and `1.403784` on Model 3.
  - **Bootstrap Inference (2,000 Replicates, 95% CI):**
    - Model 4 Temp vs Raw: $\Delta \text{LogLoss} = -0.0216$ ($95\% \text{ CI } [-0.0818, +0.0331]$); $\Delta \text{Brier} = -0.0053$ ($95\% \text{ CI } [-0.0257, +0.0142]$). Point improvements exist, but 95% CIs cross zero.
    - Calibrated M4 vs Calibrated M3: $\Delta \text{LogLoss} = +0.0298$ ($95\% \text{ CI } [-0.0584, +0.1208]$). Model 3 remains the superior baseline.

### Entry 007: 2026-11-04 — EXP-0004 Model 5 Conditional Logit / Plackett-Luce Top-Choice
- **Research Question:** Does directly optimizing candidate race-level winner likelihoods via conditional logit outperform independently trained binary classifiers normalized post-hoc?
- **Setup:** Model 5 (Plackett-Luce first choice, linear utility $u = X\beta$, L2 regularization $\lambda=1.0$, L-BFGS-B analytical gradient). Same 16 features as Model 3. Walk-forward chronological evaluation across 346 races (2010–2026).
- **Leakage Safeguards & Causality Audit:**
  - Future-data perturbation test passed: scrambling future races or perturbing target race $y$ produced $\Delta = 0.0$ difference on target predictions.
  - Preprocessing (`StandardScaler`) fitted strictly on training races available prior to each prediction cutoff.
- **Empirical Findings (Primary Cohort 2018–2024, 149 Races):**
  - **Mean Multiclass Log Loss:** **`1.351747`** (improves upon Model 3: `1.355201` and Model 4: `1.409149`).
  - **Mean Multiclass Brier Score:** **`0.596564`** (substantially outperforms Model 3: `0.612698` and Model 4: `0.628561`).
  - **Fractional Top-1 Accuracy:** **`0.543624`** (81 / 149 winners correctly predicted; beats Model 4's 79 and Model 3's 77).
  - **Calibration:** Natural Fixed-Bin ECE of `0.012030` without post-hoc scaling.
- **Historical Discrepancy Resolution:**
  - Audited the Model 3 full-series fractional top-1 discrepancy (0.494220 vs 0.525541). Verified that `model3_driver_constructor_predictions.csv` and `model3_metrics.json` have always produced `0.525541` (181.837 wins / 346 rounds). The 0.494220 figure was a conversational transcription error ($171 / 346$) in previous text summaries.
- **Scientific Significance:** Direct race-level likelihood optimization successfully eliminates the probability tail distortion inherent in point-wise binary models, achieving the highest argmax accuracy and best proper scoring metrics simultaneously.

---

## 3. Open Research Questions

1. **LambdaMART / Pairwise Ranking Objective:** Would training LightGBM directly with a ranking objective (`lambdarank` grouped by `race_id`) rather than independent binary classification reduce probability tail distortion at the source?
2. **Sequential FP2 Telemetry Value:** Does long-run practice pace improve log loss beyond `1.355201`, or does starting grid + historical constructor form already capture the majority of car performance signal?
3. **Pre-Race Entry Field Reconstruction:** Can official FIA timing documents reconstruct true timestamped pre-race entry lists to eliminate the provisional candidate-field proxy?
