# APEX — Chronological Experiment Log

This document tracks all formal machine learning executions, baseline evaluations, and calibration audits within the repository.

---

## 1. Execution Log

| Run Date | Exp ID | Model Architecture | Checkpoint | Dataset Split | Primary Metric | Baseline Metric | Status | Execution Link |
|---|---|---|---|---|---|---|---|---|
| 2026-10-19 | `EXP-0001-R1` | Driver-Only Pairwise Elo | $T_0$ (Pre-Weekend) | Walk-Forward 2010–2026 (346 races) | Log Loss: 2.275307, Brier: 0.844919, Top-1 (legacy): 0.332370 | Uniform Log Loss: 3.044556, Uniform Brier: 0.952264 | `COMPLETED_EXPLORATORY` | [artifacts/reports/EXP-0001/](../../artifacts/reports/EXP-0001/) |
| 2026-10-19 | `EXP-0001-R2` | Driver-Only Pairwise Elo (Corrected Nonstarters) | $T_0$ (Pre-Weekend) | Walk-Forward 2010–2026 (346 races) | Log Loss: 2.278177, Brier: 0.845726, Top-1 (tie-aware): 0.335260, Fract. Top-1: 0.332490, Legacy Top-1: 0.335260* | Uniform Log Loss: 3.044556, Uniform Brier: 0.952264 | `COMPLETED_EXPLORATORY` | [artifacts/reports/EXP-0001-R2/](../../artifacts/reports/EXP-0001-R2/) |
| 2026-10-19 | `EXP-0001-R3` | Driver-Only Pairwise Elo (Outcome-Independent Order) | $T_0$ (Pre-Weekend) | Walk-Forward 2010–2026 (346 races) | Log Loss: 2.278177, Brier: 0.845726, Top-1 (tie-aware): 0.335260, Fract. Top-1: 0.332490, Legacy Top-1: 0.332370 | Uniform Log Loss: 3.044556, Uniform Brier: 0.952264 | `COMPLETED_EXPLORATORY` | [artifacts/reports/EXP-0001-R3/](../../artifacts/reports/EXP-0001-R3/) |
| 2026-10-19 | `EXP-0001-CAL-001` | Candidate Probability Calibration Audit | $T_0$ (Pre-Weekend) | Walk-Forward 2010–2026 (7,285 candidates, 346 races) | Fixed-bin ECE: 0.030667 (95% CI: [0.026800, 0.034156]), MCE: 0.185189, CITL: 0.000000, Cand. Brier: 0.040168 | N/A | `COMPLETED_EXPLORATORY` | [artifacts/reports/EXP-0001-CAL-001/](../../artifacts/reports/EXP-0001-CAL-001/) |
| 2026-11-04 | `EXP-0002-M0` | Pre-Race Uniform Baseline ($1 / N_r$) | $T_5$ (Pre-Race) | Primary Cohort 2018–2024 (149 rounds) | Log Loss: 2.995388, Brier: 0.949982, Fract. Top-1: 0.050018 | N/A | `COMPLETED` | [notebooks/05_static_grid_benchmark.ipynb](../../notebooks/05_static_grid_benchmark.ipynb) |
| 2026-11-04 | `EXP-0002-M1` | Empirical Grid Frequency Baseline ($\alpha=10$) | $T_5$ (Pre-Race) | Primary Cohort 2018–2024 (149 rounds) | Log Loss: 1.583766, Brier: 0.682312, Fract. Top-1: 0.496644 | Uniform: Log Loss 2.995388, Brier 0.949982 | `COMPLETED` | [artifacts/reports/EXP-0002/model1_grid_frequency_predictions.csv](../../artifacts/reports/EXP-0002/model1_grid_frequency_predictions.csv) |
| 2026-11-04 | `EXP-0002-M2` | Grid-Only Logistic Regression (5 features) | $T_5$ (Pre-Race) | Primary Cohort 2018–2024 (149 rounds) | Log Loss: 1.594207, Brier: 0.683382, Fract. Top-1: 0.496644 | Uniform: Log Loss 2.995388, Brier 0.949982 | `COMPLETED` | [artifacts/reports/EXP-0002/model2_logistic_predictions.csv](../../artifacts/reports/EXP-0002/model2_logistic_predictions.csv) |
| 2026-11-04 | `EXP-0002-M3` | Grid + Driver/Constructor Form Logit (16 features) | $T_5$ (Pre-Race) | Primary Cohort 2018–2024 (149 rounds) | **Log Loss: 1.355201, Brier: 0.612698**, Fract. Top-1: 0.516779 | Model 1: Log Loss 1.583766, Brier 0.682312 | `COMPLETED` | [artifacts/reports/EXP-0002/model3_driver_constructor_predictions.csv](../../artifacts/reports/EXP-0002/model3_driver_constructor_predictions.csv) |
| 2026-11-04 | `EXP-0002-M4` | LightGBM GBDT (16 features, `num_leaves=15`) | $T_5$ (Pre-Race) | Primary Cohort 2018–2024 (149 rounds) | Log Loss: 1.409149, Brier: 0.628561, **Fract. Top-1: 0.530201** | Model 3: Log Loss 1.355201, Brier 0.612698 | `COMPLETED` | [artifacts/reports/EXP-0002/model4_lightgbm_predictions.csv](../../artifacts/reports/EXP-0002/model4_lightgbm_predictions.csv) |
| *Pending M4* | `EXP-0003` | *GBDT + FP2 Stint Pace* | $T_2$ | *Walk-Forward 2021–2024* | `[NOT RUN YET]` | `[NOT RUN YET]` | `PLANNED` | — |
| *Pending M4* | `EXP-0004` | *Telemetry Ablation* | $T_4$ | *Walk-Forward 2021–2024* | `[NOT RUN YET]` | `[NOT RUN YET]` | `PLANNED` | — |
| *Pending M4* | `EXP-0005` | *Calibrated Ensemble* | $T_0 \dots T_5$ | *Walk-Forward 2021–2024* | `[NOT RUN YET]` | `[NOT RUN YET]` | `PLANNED` | — |

*\*Note on EXP-0001-R2 Legacy Top-1: In R2, candidates were sorted by finishing position before forecasting, causing argmax to select the winner in the 24-way tie of 2010 Round 1. EXP-0001-R3 sorts candidates by driver_id (outcome-independent), correcting legacy top-1 to 0.332370.*
