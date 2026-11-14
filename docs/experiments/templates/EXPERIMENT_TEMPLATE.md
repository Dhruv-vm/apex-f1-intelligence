# EXP-XXXX: [Experiment Short Title]

- **Experiment ID:** `EXP-XXXX`
- **Execution Date:** YYYY-MM-DD
- **Author / Agent:** [Name / AI Agent]
- **Target Research Question(s):** [e.g., RQ1, RQ2] (Link: [RESEARCH_QUESTIONS.md](../../research/RESEARCH_QUESTIONS.md))
- **Target Hypothesis ID(s):** [e.g., HYP-0001] (Link: [HYPOTHESES.md](../../research/HYPOTHESES.md))
- **Status:** [PLANNED | RUNNING | COMPLETED | FAILED | INVALIDATED]
- **Code Commit / Hash:** `[git commit hash when run]`

---

## 1. Scientific Context & Objectives
*Describe the rationale for this experiment. What specific hypothesis or architectural question is being tested?*

---

## 2. Dataset Version & Information Boundary

- **Dataset Identifier:** `[e.g., apex_dataset_v1.0.0]`
- **Seasons & Rounds Covered:** `[e.g., 2018–2024 FIA Formula 1 World Championship]`
- **Prediction Target:** `[RACE_WINNER | PODIUM | TOP_10 | FINISHING_ORDER | DNF]`
- **Forecast Checkpoint:** `[T0_PRE_WEEKEND | T1_POST_FP1 | T2_POST_FP2 | T3_POST_FP3 | T4_POST_QUALI | T5_PRE_RACE | T6_LAP_K]`
- **Information Cutoff Rule:** `[Exact timestamp or event trigger boundary, e.g., "Official checkered flag of Q3 + 60 minutes"]`
- **Leakage Prevention Verification:** `[Describe automated checks proving future data was blocked]`

---

## 3. Evaluation & Split Protocol

- **Split Methodology:** Rolling-origin walk-forward validation
- **Training Seasons:** `[e.g., 2018–2021]`
- **Validation Seasons:** `[e.g., 2022]`
- **Out-of-Sample Test Seasons:** `[e.g., 2023–2024]`
- **Primary Benchmark Comparison:** `[e.g., Static Elo Baseline EXP-0001]`
- **Acceptance Criteria:** `[e.g., Reduction in multi-class Log Loss by >= 0.02 with p < 0.05]`

---

## 4. Model Architecture & Hyperparameters

- **Model Family:** `[e.g., LightGBM Multi-Class Classifier | Hierarchical Bayesian]`
- **Key Hyperparameters:**
  - `learning_rate`: `[value]`
  - `num_leaves`: `[value]`
  - `min_child_samples`: `[value]`
  - `feature_fraction`: `[value]`
  - `random_seed`: `42`
- **Calibration Method:** `[None | Temperature Scaling | Isotonic Regression | Platt Scaling]`

---

## 5. Measured Experimental Results

> *Notice: Fill only after actual script execution. Do not populate with synthetic values.*

| Metric | Baseline Value | Model Value | Delta ($\Delta$) | 95% Confidence Interval | Statistically Significant? |
|---|---|---|---|---|---|
| **Multi-Class Log Loss** | `[Unfilled]` | `[Unfilled]` | `[Unfilled]` | `[Unfilled]` | `[Yes / No]` |
| **Multi-Class Brier Score** | `[Unfilled]` | `[Unfilled]` | `[Unfilled]` | `[Unfilled]` | `[Yes / No]` |
| **Expected Calibration Error (ECE)**| `[Unfilled]`| `[Unfilled]` | `[Unfilled]` | `[Unfilled]` | `[Yes / No]` |
| **Finishing Pos MAE** | `[Unfilled]` | `[Unfilled]` | `[Unfilled]` | `[Unfilled]` | `[Yes / No]` |

---

## 6. Calibration & Reliability Analysis
*Analyze reliability diagrams, probability bin alignment, and overconfidence/underconfidence tendencies.*

---

## 7. Error Analysis & Outliers
*Examine races where the model made significant forecast errors (e.g., chaotic wet races, first-lap multi-car incidents, mechanical retirements).*

---

## 8. Limitations & Threats to Validity
*Identify potential confounds, sample size limitations, or remaining sources of noise.*

---

## 9. Reproduction Command & Artifact Paths

- **Reproduction Script:**
  ```bash
  python -m scripts.experiments.run_experiment --config configs/experiments/EXP-XXXX.yaml --seed 42
  ```
- **Generated Figures:** `artifacts/figures/EXP-XXXX/`
- **Output Metrics & Logs:** `artifacts/reports/EXP-XXXX/`
- **Model Checkpoints:** `models/EXP-XXXX/`

---

## 10. Conclusion & Next Decision
- **Hypothesis Outcome:** `[SUPPORTED | NOT SUPPORTED | INCONCLUSIVE]`
- **Next Recommended Action / ADR:** `[e.g., Adopt feature in baseline, proceed to EXP-YYYY]`
