# APEX — Research Paper Traceability Matrix

This document maps all theoretical claims, empirical arguments, methodology choices, tables, and figures slated for academic publication to exact experimental artifacts, code versions, and verified numerical results within the repository.

---

## 1. Paper Overview & Publication Target

- **Working Paper Title:** *Probabilistic Forecasting in Formula 1: Temporal Integrity, Grid Dominance, and the Limits of Gradient Tree Boosting under Proper Scoring Rules*
- **Primary Research Focus:**
  1. Evaluating probabilistic race-winner forecasting across discrete race-weekend checkpoints ($T_0 \dots T_6$).
  2. Demonstrating the dominance of starting grid position over pre-weekend dynamic ratings.
  3. Proving that optimizing for argmax accuracy (Top-1) produces deceptive model selections, whereas strictly proper scoring rules (Log Loss, Brier score) expose probability tail distortions in uncalibrated gradient boosted trees.
  4. Formulating direct race-level Plackett-Luce choice models that improve probability calibration over post-hoc normalized binary classifiers.
- **Related Literature Foundations (see [docs/research/LITERATURE_REVIEW.md](research/LITERATURE_REVIEW.md)):**
  - Driver vs constructor variance decomposition: van Kesteren & Bergkamp (JQAS 2023), Bell et al. (2016).
  - Telemetry and GBDT performance in motorsport: Todd et al. (ACM SAC 2025).
  - Bayesian state-space modeling for pace and degradation: Cappello & Hoegh (2025).
  - Target leakage & evaluation protocol failure modes in motorsport AI: Urdhwareshe (Preprints 2025), Bansal et al. (2025).

---

## 2. Section-by-Section Traceability Mapping

### Section 1: Abstract & Core Claims

| Paper Claim / Statement | Verification Status | Exact Measured Value | Supporting Experiment | Supporting Artifact Path |
|---|---|---|---|---|
| *"Starting grid position accounts for the vast majority of static pre-race predictive information, reducing multiclass log loss from 2.278 to 1.584."* | **VERIFIED** | Log Loss: `2.278177` (Elo $T_0$) vs `1.583766` (Grid Freq $T_5$, $p < 10^{-15}$) | `EXP-0001-R3` vs `EXP-0002-M1` | `artifacts/reports/EXP-0001-R3/experiment_manifest.json`, `artifacts/reports/EXP-0002/model1_grid_frequency_metrics.json` |
| *"Adding rolling driver and constructor form features to starting grid features reduces primary cohort log loss to 1.355."* | **VERIFIED** | Log Loss: `1.355201` (Model 3) vs `1.594207` (Model 2 Grid-Only, $\Delta = -0.239$) | `EXP-0002-M3` | `artifacts/reports/EXP-0002/model3_metrics.json` |
| *"Direct race-level choice modeling (Plackett-Luce conditional logit) outperforms post-hoc normalized binary classifiers on proper scoring rules and top-1 accuracy."* | **VERIFIED** | Log Loss: `1.351747` (Model 5) vs `1.355201` (Model 3); Brier: `0.596564` vs `0.612698`; Top-1: `54.36%` vs `51.68%` | `EXP-0004-M5` | `artifacts/reports/EXP-0004/model5_metrics.json` |
| *"Sequential arrival of on-track evidence across race weekend checkpoints ($T_0 \rightarrow T_4 \rightarrow T_5$) monotonically contracts predictive uncertainty across the primary cohort."* | **VERIFIED** | Log Loss: `2.058759` ($T_0$) $\rightarrow$ `1.594207` ($T_4$) $\rightarrow$ `1.355201` ($T_5$, $\Delta = -0.7036$, Wilcoxon $p = 1.22 \times 10^{-12}$) | `EXP-0005` | `artifacts/reports/EXP-0005/walk_forward_checkpoint_metrics.json`, `paired_statistical_tests.json` |
| *"Gradient boosted trees (LightGBM) achieve higher raw top-1 accuracy (53.02% vs 51.68%), but degrade strictly proper scoring rules (Log Loss: 1.409 vs 1.355)."* | **VERIFIED** | Top-1: `53.02%` vs `51.68%`; Log Loss: `1.409149` vs `1.355201`; Brier: `0.628561` vs `0.612698` | `EXP-0002-M4` vs `EXP-0002-M3` | `artifacts/reports/EXP-0002/model4_metrics.json`, `artifacts/reports/EXP-0002/model3_metrics.json` |
| *"Pre-race entrant pools cannot assume zero post-race leakage without independently timestamped entry lists."* | **METHODOLOGY PRINCIPLE** | 56 grid-zero records identified; 49 active pit starts, 7 anomalies; 72 nonstarter/DNS instances audited. | Candidate Field Audit | `docs/research/CANDIDATE_FIELD_AUDIT.md` |

---

### Section 2: Methodology & Evaluation Framework

| Framework Component | Repository Implementation | Anti-Leakage Mechanism | Verification Script / Notebook |
|---|---|---|---|
| **Chronological Rolling-Origin Backtesting** | `race_table` ordered by `race_date, season, round` | Train sets strictly contain $\{r' \mid r' < r\}$; current race $r$ is scored before updating form histories. | `notebooks/05_static_grid_benchmark.ipynb` (Cells 17, 19, 21, 23) |
| **Simplex Normalization** | Grouped by `race_id`, normalized via $\sum_{i=1}^{N_r} p_i = 1$ | Assertions enforce `np.isclose(sum, 1.0, atol=1e-10)` and $0 \le p_i \le 1$. | `model1_walk_forward_audit.csv`, `model2_walk_forward_audit.csv`, `model3_walk_forward_audit.csv`, `model4_walk_forward_audit.csv` |
| **Outcome-Independent Candidate Ordering** | Deterministic sorting by `driver_id` prior to inference | Prevents `np.argmax()` from picking the true winner in case of top-probability ties (e.g. 2010 R1 24-way tie). | Audited in `EXP-0001-R3` vs `EXP-0001-R2` |
| **Grid-Zero Representation** | $\text{effective\_grid} = \max_{i, \text{grid}_i > 0}(\text{grid}_i) + 1$ with `is_grid_zero` binary indicator | Avoids arbitrary magic-number penalties (e.g. `grid=21`) while preserving slot order. | `notebooks/05_static_grid_benchmark.ipynb` (Cell 9) |
| **Primary Evaluation Cohort** | Modern era: 2018–2024 (149 rounds, 2,979 candidate rows) | High regulatory consistency, standard 20-car grid format, zero engine formula disruption. | `docs/research/CANDIDATE_FIELD_AUDIT.md` |

---

### Section 3: Empirical Benchmark Results (Tables 1 & 2 in Paper)

**Table 1: Pre-Race Forecast Benchmarks ($T_5$ Checkpoint, 2018–2024 Primary Cohort, $N = 149$ Races)**

| Paper Model Notation | Model Description | Algorithm & Key Hyperparameters | Multiclass Log Loss | Multiclass Brier Score | Fractional Top-1 | Tie-Aware Top-1 | Source Artifact |
|---|---|---|---:|---:|---:|---:|---|
| $\mathcal{M}_0$ | Uniform Baseline | $p_{r,i} = 1 / N_r$ | 2.995388 | 0.949982 | 0.050018 | 1.000000 | In-memory evaluation |
| $\mathcal{M}_{\text{Elo}}$ | Baseline Driver Elo ($T_0$) | Pairwise logistic ratings ($K=20$) | 2.278177 | 0.845726 | 0.332490 | 0.335260 | `EXP-0001-R3` |
| $\mathcal{M}_1$ | Empirical Grid Frequency | Bayesian Dirichlet/Laplace ($\alpha=10.0$) | 1.583766 | 0.682312 | 0.496644 | 0.496644 | `EXP-0002/model1_grid_frequency_metrics.json` |
| $\mathcal{M}_2$ | Grid-Only Logistic | L2 Regularized Logit ($C=1.0$), 5 grid features | 1.594207 | 0.683382 | 0.496644 | 0.496644 | `EXP-0002/model2_logistic_metrics.json` |
| $\mathcal{M}_3$ | Grid + Form Logistic | L2 Regularized Logit ($C=1.0$), 16 grid + form features | 1.355201 | 0.612698 | 0.516779 | 0.516779 | `EXP-0002/model3_driver_constructor_metrics.json` |
| $\mathcal{M}_4$ | Tree-Based GBDT | LightGBM (`num_leaves=15`, `lr=0.03`, `n_est=250`) | 1.409149 | 0.628561 | 0.530201 | 0.530201 | `EXP-0002/model4_metrics.json` |
| $\mathcal{M}_5$ | Plackett-Luce / Cond. Logit | Direct Softmax Choice ($\lambda=1.0$), 16 grid + form features | **1.351747** | **0.596564** | **0.543624** | **0.543624** | `EXP-0004/model5_metrics.json` |

**Table 2: Walk-Forward Probability Calibration Benchmark (EXP-0003, Primary Cohort, $N = 149$ Races)**

| Base Model | Calibration Method | Multiclass Log Loss | Multiclass Brier | Fract. Top-1 | ECE | MCE | Source Artifact |
|---|---|:---:|:---:|:---:|:---:|:---:|---|
| $\mathcal{M}_3$ (Logistic) | Raw (Uncalibrated) | **1.355201** | **0.612698** | 0.516779 | 0.009618 | 0.073911 | `EXP-0003/calibration_comparison.json` |
| $\mathcal{M}_3$ (Logistic) | Platt Scaling | 1.357407 | 0.613388 | 0.516779 | 0.009385 | 0.078753 | `EXP-0003/calibration_comparison.json` |
| $\mathcal{M}_3$ (Logistic) | Isotonic Regression | 1.403784 | 0.613623 | **0.533557** | **0.005006** | 0.117718 | `EXP-0003/calibration_comparison.json` |
| $\mathcal{M}_3$ (Logistic) | Temperature Scaling ($T \approx 1.007$) | 1.357764 | 0.613515 | 0.516779 | 0.009560 | 0.077360 | `EXP-0003/calibration_comparison.json` |
| $\mathcal{M}_4$ (LightGBM) | Raw (Uncalibrated) | 1.409149 | 0.628561 | 0.530201 | 0.013875 | 0.133525 | `EXP-0003/calibration_comparison.json` |
| $\mathcal{M}_4$ (LightGBM) | Platt Scaling | 1.388663 | **0.622523** | 0.530201 | **0.007314** | 0.054807 | `EXP-0003/calibration_comparison.json` |
| $\mathcal{M}_4$ (LightGBM) | Isotonic Regression | 1.450040 | 0.623208 | 0.528523 | 0.007846 | **0.047980** | `EXP-0003/calibration_comparison.json` |
| $\mathcal{M}_4$ (LightGBM) | Temperature Scaling ($T \approx 1.360$) | **1.387587** | 0.623285 | 0.530201 | 0.007818 | 0.078645 | `EXP-0003/calibration_comparison.json` |

---

### Section 4: Scientific Discussion Points

1. **Why Model 3 beats Model 4 on Proper Scoring Rules:**
   - Logistic regression maps linear score combinations smoothly via the sigmoid function, bounded by L2 weight decay.
   - LightGBM builds step-function partition boundaries. In small-sample regimes (149–346 races, ~20 candidates per race), tree leaf splits produce spiky, overconfident positive-class scores for clear favorites. When re-normalized across 20 drivers, this leaves non-favorites with overly suppressed probabilities.
   - When a high-probability favorite fails to win (e.g. mechanical failure, safety car, turn 1 collision), the log penalty $-\log(p_{\text{winner}})$ on the surprise winner is severe, degrading the overall mean log loss.
2. **Proper Scoring Rules as an Antidote to "Accuracy Hype":**
   - If evaluated purely on Top-1 accuracy, a practitioner would erroneously conclude that LightGBM is the "best" model (`53.02%` vs `51.68%`).
   - Evaluating multiclass log loss and Brier score prevents this false conclusion and highlights the necessity of probability calibration.
3. **Direct Multinomial vs. Normalized Binary Likelihood (EXP-0004):**
   - Directly optimizing the conditional logit likelihood over entrant choice sets achieves the best overall primary Brier score (0.5966 vs Model 3's 0.6127 and Model 4's 0.6286) and top-1 accuracy (54.36% vs 51.68% and 53.02%), while attaining slightly lower log loss (1.3517 vs 1.3552).
   - This empirically confirms that direct race-level probability modeling avoids the probability distortion introduced by normalizing independently trained binary classifiers.

---

### Section 5: Threats to Validity & Limitations

- **Retrospective Result Record Proxy:** The 7,285 entrant rows originate from historical race-result tables, not timestamped pre-race pit-lane declarations. Drivers who failed to start but held starting slots may be missing from historical Ergast records.
- **Independence of Irrelevant Alternatives (IIA):** Plackett-Luce models assume the relative odds between any two drivers are independent of the presence or absence of other drivers. In motorsport, intra-team dynamics, blocking, and safety car interventions violate strict IIA.
- **Tree-Based Ranking Objectives:** LightGBM pairwise/listwise ranking objectives (`lambdarank`) remain unbenchmarked and should be explored in future work.
