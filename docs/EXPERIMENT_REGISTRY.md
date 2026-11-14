# APEX — Master Experiment Registry

This document is the canonical, permanent registry of all formal machine learning experiments, baseline benchmarks, and ablation studies executed within the **APEX — F1 Intelligence** repository.

Every substantive experiment must be documented here with its exact configuration, temporal protocol, cohort sample size, verified scoring metrics, limitations, and artifact paths.

---

## 1. Registry Summary Table

| Exp ID | Model Title | Forecast Cutoff | Model Family | Primary Cohort Split | Primary Log Loss | Primary Brier Score | Primary Fract. Top-1 | Execution Status | Artifact Directory |
|---|---|---|---|---|---:|---:|---:|---|---|
| `EXP-0001-R1` | Pairwise Driver Elo (Exploratory) | $T_0$ | Dynamic Rating | Walk-Forward 2010–2026 (346 races) | 2.275307 | 0.844919 | 0.332370 | `COMPLETED` | `artifacts/reports/EXP-0001/` |
| `EXP-0001-R2` | Pairwise Driver Elo (Nonstarter Excl.) | $T_0$ | Dynamic Rating | Walk-Forward 2010–2026 (346 races) | 2.278177 | 0.845726 | 0.332490 | `COMPLETED` | `artifacts/reports/EXP-0001-R2/` |
| `EXP-0001-R3` | Pairwise Driver Elo (Outcome-Independent) | $T_0$ | Dynamic Rating | Walk-Forward 2010–2026 (346 races) | 2.278177 | 0.845726 | 0.332490 | `COMPLETED` | `artifacts/reports/EXP-0001-R3/` |
| `EXP-0001-CAL-001` | Candidate Probability Calibration Audit | $T_0$ | Calibration Audit | Walk-Forward 2010–2026 (7,285 cands) | ECE: 0.030667 | MCE: 0.185189 | CITL: 0.000000 | `COMPLETED` | `artifacts/reports/EXP-0001-CAL-001/` |
| `EXP-0002-M0` | Pre-Race Uniform Baseline ($1 / N_r$) | $T_5$ | Baseline | Primary 2018–2024 (149 races) | 2.995388 | 0.949982 | 0.050018 | `COMPLETED` | In-memory baseline |
| `EXP-0002-M1` | Empirical Grid Frequency Baseline | $T_5$ | Bayesian Table | Primary 2018–2024 (149 races) | 1.583766 | 0.682312 | 0.496644 | `COMPLETED` | `artifacts/reports/EXP-0002/` |
| `EXP-0002-M2` | Grid-Only Logistic Regression | $T_5$ | Linear / Softmax | Primary 2018–2024 (149 races) | 1.594207 | 0.683382 | 0.496644 | `COMPLETED` | `artifacts/reports/EXP-0002/` |
| `EXP-0002-M3` | Grid + Form Logistic Regression | $T_5$ | Linear / Softmax | Primary 2018–2024 (149 races) | **1.355201** | **0.612698** | 0.516779 | `COMPLETED` | `artifacts/reports/EXP-0002/` |
| `EXP-0002-M4` | LightGBM Gradient Boosted Trees | $T_5$ | Tree-Based GBDT | Primary 2018–2024 (149 races) | 1.409149 | 0.628561 | **0.530201** | `COMPLETED` | `artifacts/reports/EXP-0002/` |
| `EXP-0003` | Walk-Forward Probability Calibration | $T_5$ | Post-Hoc Calibrator | Primary 2018–2024 (149 races) | M3: 1.3552 / M4: 1.3876 | M3: 0.6127 / M4: 0.6225 | M3: 0.5168 / M4: 0.5302 | `COMPLETED` | `artifacts/reports/EXP-0003/` |
| `EXP-0004` | Direct Plackett-Luce Top-Choice Model | $T_5$ | Multinomial Choice | Primary 2018–2024 (149 races) | **1.351747** | **0.596564** | **0.543624** | `COMPLETED` | `artifacts/reports/EXP-0004/` |
| `EXP-0005` | FP2 Stint Pace Degradation GBDT | $T_2$ | GBDT + Telemetry | Modern 2021–2024 | `[TBD]` | `[TBD]` | `[TBD]` | `PLANNED` | — |
| `EXP-0006` | Telemetry Ablation Series | $T_4$ | GBDT + Car Telemetry | Modern 2023–2024 | `[TBD]` | `[TBD]` | `[TBD]` | `PLANNED` | — |

---

## 2. Detailed Experiment Records

### EXP-0001-R3: Pairwise Driver-Only Elo Baseline (Outcome-Independent)
- **Objective:** Establish the foundational non-sequential pre-weekend ($T_0$) forecasting benchmark using pairwise logistic Elo ratings updated chronologically across historical race results.
- **Hypothesis:** Historical driver performance alone provides statistically significant predictive signal over a uniform baseline ($1/N_r$).
- **Dataset:** `data/interim/driver_race_results_2010_2026_v2_regulation_metadata.csv` (7,285 rows across 346 races).
- **Features:** Latent driver Elo rating ($R_{\text{init}} = 1500$, $K = 20$). Pairwise win probabilities converted to candidate simplex via softmax / normalization.
- **Candidate Ordering:** Deterministically sorted by `driver_id` prior to scoring to prevent tie-break selection leakage.
- **Evaluation:** Strict walk-forward rolling-origin across all 346 races (2010–2026).
- **Verified Metrics (Full Series, 346 Races):**
  - Mean Multiclass Log Loss: `2.278177` (vs Uniform: `3.044556`, delta: `-0.766379`)
  - Mean Multiclass Brier Score: `0.845726` (vs Uniform: `0.952264`, delta: `-0.106538`)
  - Tie-Aware Top-1 Accuracy: `0.335260` (116 / 346)
  - Fractional Top-1 Credit: `0.332490` (115.0417 / 346)
  - Legacy Argmax Top-1: `0.332370` (115 / 346)
- **Artifacts:**
  - `artifacts/reports/EXP-0001-R3/candidate_predictions.csv`
  - `artifacts/reports/EXP-0001-R3/race_predictions.csv`
  - `artifacts/reports/EXP-0001-R3/experiment_manifest.json`

---

### EXP-0001-CAL-001: Baseline Probability Calibration Audit
- **Objective:** Evaluate candidate-level probability calibration of the baseline Elo model to establish pre-calibration benchmark metrics.
- **Dataset:** Predictions from `EXP-0001-R3` (7,285 candidate observations across 346 races).
- **Protocol:** 10 uniform probability bins on $[0, 1]$; 1,000 race-clustered bootstrap iterations for 95% confidence intervals.
- **Verified Metrics:**
  - Expected Calibration Error (ECE, 8 non-empty bins): `0.030667` (95% CI: `[0.026800, 0.034156]`)
  - Maximum Calibration Error (MCE): `0.185189` (95% CI: `[0.133562, 0.268597]`)
  - Calibration-in-the-Large (CITL): `0.000000` (Mean pred `0.047495` == Mean obs `0.047495`)
  - Candidate Brier Score: `0.040168` (95% CI: `[0.039589, 0.040720]`)
  - Candidate Log Loss: `0.151746` (95% CI: `[0.149093, 0.154541]`)
- **Artifacts:**
  - `artifacts/reports/EXP-0001-CAL-001/calibration_metrics.json`
  - `artifacts/figures/EXP-0001-CAL-001/reliability_diagram.png`

---

### EXP-0002: Static Pre-Race Starting Grid Benchmarks (Models 0–4)
- **Objective:** Benchmark five static pre-race model architectures at forecast checkpoint $T_5$ (30 minutes prior to race start) to quantify starting grid predictive power and determine whether gradient boosting outperforms regularized logistic regression.
- **Dataset:** `data/interim/driver_race_results_2010_2026_v2_regulation_metadata.csv` (7,285 rows across 346 races).
- **Candidate Field Caveat:** Candidates represent a provisional result-record proxy from retrospective race results. Post-race status is not used to drop non-starters. Grid zero records (56 total) are encoded as `max(grid) + 1` with an `is_grid_zero` flag.
- **Evaluation Cohorts:**
  - **Primary Benchmark Cohort:** 2018–2024 (149 rounds, 2,979 candidate rows).
  - **Full Historical Series:** 2010–2026 (346 rounds, 7,285 candidate rows; first 20 races serve as cold start).
- **Features Used:**
  - **Grid Features (5):** `effective_grid`, `log_grid`, `is_front_row`, `is_pole`, `is_grid_zero`
  - **Driver Form Features (5):** `driver_prior_races`, `driver_win_rate_all`, `driver_win_rate_last5`, `driver_mean_finish_last5`, `driver_finish_std_last5`
  - **Constructor Form Features (4):** `constructor_prior_races`, `constructor_win_rate_all`, `constructor_win_rate_last5`, `constructor_mean_finish_last5`
  - **Points Features (2):** `driver_mean_points_last5`, `constructor_mean_points_last5`
- **Models Evaluated:**
  - **Model 0:** Uniform distribution $P_i = 1/N_r$
  - **Model 1:** Empirical Grid Table with Laplacian smoothing ($\alpha = 10.0$)
  - **Model 2:** Logistic Regression on 5 Grid Features ($C = 1.0$)
  - **Model 3:** Logistic Regression on 16 Grid + Form Features ($C = 1.0$)
  - **Model 4:** LightGBM GBDT on 16 Grid + Form Features (`n_estimators=250`, `learning_rate=0.03`, `num_leaves=15`, `min_child_samples=20`, `subsample=0.8`, `colsample_bytree=0.8`, `reg_lambda=1.0`)

#### Verified Primary Cohort Metrics (2018–2024, 149 Races)

| Metric | Model 0 (Uniform) | Model 1 (Grid Freq) | Model 2 (Grid Logit) | Model 3 (Form Logit) | Model 4 (LightGBM) |
|---|---:|---:|---:|---:|---:|
| **Mean Multiclass Log Loss** | 2.995388 | 1.583766 | 1.594207 | **1.355201** | 1.409149 |
| **Mean Multiclass Brier Score** | 0.949982 | 0.682312 | 0.683382 | **0.612698** | 0.628561 |
| **Fractional Top-1 Accuracy** | 0.050018 | 0.496644 | 0.496644 | 0.516779 | **0.530201** |
| **Tie-Aware Top-1 Accuracy** | 1.000000 | 0.496644 | 0.496644 | 0.516779 | **0.530201** |

#### Verified Full Series Metrics (2010–2026, 346 Races)

| Metric | Model 0 (Uniform) | Model 1 (Grid Freq) | Model 2 (Grid Logit) | Model 3 (Form Logit) | Model 4 (LightGBM) |
|---|---:|---:|---:|---:|---:|
| **Mean Multiclass Log Loss** | 3.044556 | 1.519516 | 1.541942 | **1.419383** | 1.522650 |
| **Mean Multiclass Brier Score** | 0.952264 | 0.657880 | 0.662375 | **0.624583** | 0.650861 |
| **Fractional Top-1 Accuracy** | 0.047736 | 0.523242 | 0.508200 | **0.525541** | 0.516870 |
| **Tie-Aware Top-1 Accuracy** | 1.000000 | 0.531792 | 0.563584 | **0.580925** | 0.572254 |

- **Artifacts:**
  - `artifacts/reports/EXP-0002/model1_grid_frequency_predictions.csv`
  - `artifacts/reports/EXP-0002/model1_walk_forward_audit.csv`
  - `artifacts/reports/EXP-0002/model1_grid_frequency_metrics.json`
  - `artifacts/reports/EXP-0002/model2_logistic_predictions.csv`
  - `artifacts/reports/EXP-0002/model2_walk_forward_audit.csv`
  - `artifacts/reports/EXP-0002/model2_logistic_metrics.json`
  - `artifacts/reports/EXP-0002/model3_driver_constructor_predictions.csv`
  - `artifacts/reports/EXP-0002/model3_walk_forward_audit.csv`
  - `artifacts/reports/EXP-0002/model3_metrics.json`
  - `artifacts/reports/EXP-0002/model4_lightgbm_predictions.csv`
  - `artifacts/reports/EXP-0002/model4_walk_forward_audit.csv`
  - `artifacts/reports/EXP-0002/model4_metrics.json`

---

### EXP-0003: Walk-Forward Probability Calibration Benchmark (Models 3 & 4)
- **Objective:** Determine whether post-hoc probability calibration improves reliability and proper scoring rules of static pre-race forecasts without altering underlying models.
- **Hypothesis:** Tree-based GBDT models (Model 4) suffer from overconfidence that post-hoc scaling (Platt, Temperature) can mitigate, whereas linear logistic models (Model 3) are already well-calibrated.
- **Methods Evaluated:**
  - **Platt Scaling:** Logistic regression fit on candidate logit-probabilities with race normalization.
  - **Isotonic Regression:** Non-parametric monotonic mapping with $10^{-6}$ tail floor and race normalization.
  - **Temperature Scaling:** Race-level scalar parameter $T > 0$ optimizing multiclass historical NLL: $p_i(T) = \text{softmax}(\log(p_i) / T)$.
- **Temporal Integrity Protocol:** Expanding walk-forward history; 20 initial uniform cold-start rounds excluded from training; minimum 30 valid prior trained races required before calibrating; target-race winner never accessed.
- **Verified Primary Cohort Metrics (2018–2024, 149 Races):**

| Base Model | Variant | Multiclass Log Loss | Multiclass Brier | Fract. Top-1 | ECE | MCE |
|---|---|:---:|:---:|:---:|:---:|:---:|
| **Model 3 (Logistic)** | Raw (Uncalibrated) | **1.355201** | **0.612698** | 0.516779 | 0.009618 | 0.073911 |
| Model 3 (Logistic) | Platt Scaling | 1.357407 | 0.613388 | 0.516779 | 0.009385 | 0.078753 |
| Model 3 (Logistic) | Isotonic Regression | 1.403784 | 0.613623 | **0.533557** | 0.005006 | 0.117718 |
| Model 3 (Logistic) | Temperature Scaling ($T \approx 1.007$) | 1.357764 | 0.613515 | 0.516779 | 0.009560 | 0.077360 |
| **Model 4 (LightGBM)** | Raw (Uncalibrated) | 1.409149 | 0.628561 | 0.530201 | 0.013875 | 0.133525 |
| Model 4 (LightGBM) | Platt Scaling | 1.388663 | **0.622523** | 0.530201 | **0.007314** | 0.054807 |
| Model 4 (LightGBM) | Isotonic Regression | 1.450040 | 0.623208 | 0.528523 | 0.007846 | **0.047980** |
| Model 4 (LightGBM) | Temperature Scaling ($T \approx 1.360$) | **1.387587** | 0.623285 | 0.530201 | 0.007818 | 0.078645 |

- **Paired Race-Clustered Bootstrap Inferences (2,000 Replicates, 95% CI):**
  - Model 4 Temp vs Raw: $\Delta \text{LogLoss} = -0.0216$ ($95\% \text{ CI } [-0.0818, +0.0331]$); $\Delta \text{Brier} = -0.0053$ ($95\% \text{ CI } [-0.0257, +0.0142]$). Point improvement observed, but CI crosses zero due to inter-race variance.
  - Model 3 Temp vs Raw: $\Delta \text{LogLoss} = +0.0026$ ($95\% \text{ CI } [0.0003, 0.0048]$). Slight penalty; model already calibrated ($T \approx 1.0$).
  - Calibrated M4 vs Calibrated M3 (Temp): $\Delta \text{LogLoss} = +0.0298$ ($95\% \text{ CI } [-0.0584, +0.1208]$). Model 3 remains superior.
- **Key Conclusions:** Calibration substantially improves point scoring and reliability for overconfident tree ensembles (reducing Model 4 ECE from 0.0139 to 0.0078 and Log Loss by 0.0216), but Model 3 remains the best overall probabilistic predictor.
- **Artifacts:**
  - `artifacts/reports/EXP-0003/model3_calibrated_predictions.csv`
  - `artifacts/reports/EXP-0003/model4_calibrated_predictions.csv`
  - `artifacts/reports/EXP-0003/calibration_walk_forward_audit.csv`
  - `artifacts/reports/EXP-0003/reliability_bins.csv`
  - `artifacts/reports/EXP-0003/bootstrap_results.json`
  - `artifacts/reports/EXP-0003/calibration_comparison.json`
  - `artifacts/reports/EXP-0003/reliability_diagrams_model3.png`
  - `artifacts/reports/EXP-0003/reliability_diagrams_model4.png`
  - `artifacts/reports/EXP-0003/temperature_trajectories.png`
  - `artifacts/reports/EXP-0003/manifest.json`

---

### EXP-0004: Direct Race-Level Winner Model (Plackett-Luce / Conditional Logit)
- **Objective:** Evaluate whether directly optimizing the race-level winner choice likelihood across all candidates outperforms independent binary classifiers normalized post-hoc.
- **Model Architecture:** Model 5 (Conditional Logit / Plackett-Luce first-choice). Linear utility $u_i = \mathbf{x}_i^\top \boldsymbol{\beta}$, race winner probability $P(i \mid r) = \text{softmax}(\mathbf{u}_r)_i$.
- **Objective Function:** Multiclass NLL with L2 regularization ($\lambda = 1.0$), solved via L-BFGS-B with analytical gradient: $\nabla_{\boldsymbol{\beta}} L = \frac{1}{R} \sum_r X_r^\top (\mathbf{p}_r - \mathbf{y}_r) + \lambda \boldsymbol{\beta}$.
- **Features (16):** Identical to Model 3 (5 grid, 5 driver form, 4 constructor form, 2 points features).
- **Anti-Leakage Safeguards:** Expanding chronological window, training-only standardization (`StandardScaler`), 20 uniform cold-start rounds, explicit future-data perturbation tests passed.
- **Verified Primary Cohort Metrics (2018–2024, 149 Races):**
  - **Mean Multiclass Log Loss:** **`1.351747`** (vs Model 3: `1.355201`, vs Model 4: `1.409149`)
  - **Mean Multiclass Brier Score:** **`0.596564`** (vs Model 3: `0.612698`, vs Model 4: `0.628561`)
  - **Fractional Top-1 Accuracy:** **`0.543624`** (81 / 149 race winners correctly picked; vs Model 4: `53.02%`, Model 3: `51.68%`)
  - **Fixed-Bin ECE:** `0.012030`
  - **Optimizer Convergence:** 0 failures across 326 trained races, mean iterations 14.3.
- **Verified Full Series Metrics (2010–2026, 346 Races):**
  - Mean Log Loss: `1.440419`
  - Mean Brier Score: `0.617250`
  - Fractional Top-1 Accuracy: `0.528431` (182.837 / 346)
  - Tie-Aware Top-1 Accuracy: `0.583815` (202 / 346)
- **Paired Race-Clustered Bootstrap Inferences (2,000 Replicates, 95% CI):**
  - Model 5 vs Model 3 Brier Difference: $\Delta = -0.0161$ ($95\% \text{ CI } [-0.0374, +0.0049]$).
  - Model 5 vs Model 4 Brier Difference: $\Delta = -0.0320$ ($95\% \text{ CI } [-0.0680, +0.0043]$).
  - Model 5 vs Model 3 Log Loss: $\Delta = -0.0035$ ($95\% \text{ CI } [-0.0811, +0.0695]$).
- **Artifacts:**
  - `artifacts/reports/EXP-0004/model5_predictions.csv`
  - `artifacts/reports/EXP-0004/model5_walk_forward_audit.csv`
  - `artifacts/reports/EXP-0004/model5_metrics.json`
  - `artifacts/reports/EXP-0004/model_comparison.json`
  - `artifacts/reports/EXP-0004/bootstrap_results.json`
  - `artifacts/reports/EXP-0004/reliability_bins.csv`
  - `artifacts/reports/EXP-0004/reliability_diagram.png`
  - `artifacts/reports/EXP-0004/manifest.json`
