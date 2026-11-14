# APEX — Experiment Index

> **Status Notice:** Experiments EXP-0001 through EXP-0006 are completed, provenance-audited, and serialized in `artifacts/reports/`. The entries below represent the canonical research registry, model mappings, and empirical findings.

---

## 1. Planned & Executed Experiment Registry

| Experiment ID | Title | Related RQ | Related Hypotheses | Target Checkpoint | Model Family | Academic Literature Foundation | Status |
|---|---|---|---|---|---|---|---|
| [EXP-0001](#exp-0001) | Static Rolling Elo & Historical Rating Baseline | RQ1 | [HYP-0001](../research/HYPOTHESES.md#hyp-0001-sequential-information-superiority) | $T_0$ (Pre-Weekend) | Dynamic Elo (R1, R2, R3) | van Kesteren & Bergkamp (2023), Bell et al. (2016) | `COMPLETED` (R3 Logged; CAL-001 Audited) |
| [EXP-0002](#exp-0002) | Static Pre-Race Starting Grid Benchmark | RQ1 | [HYP-0001](../research/HYPOTHESES.md#hyp-0001-sequential-information-superiority), [HYP-GRID-001](../research/HYPOTHESES.md#hyp-grid-001-pre-race-grid-position-dominance), [HYP-GRID-002](../research/HYPOTHESES.md#hyp-grid-002-nonlinear-grid-representation-superiority) | $T_5$ (Pre-Race) | Models 0–4: Uniform (M0), Grid Frequency (M1), Grid Logistic (M2), Grid+Form Logistic (M3), LightGBM (M4) | Henderson et al. (2016), Urdhwareshe (2025) [audit] | `COMPLETED` (Notebook 05 Executed; Artifacts in `artifacts/reports/EXP-0002/`) |
| [EXP-0003](#exp-0003) | Post-Hoc Probability Calibration Benchmark | RQ3 | [HYP-0004](../research/HYPOTHESES.md#hyp-0004-checkpoint-calibration-drift) | $T_5$ (Pre-Race) | Platt Scaling, Isotonic Regression, Temperature Scaling (M3, M4) | Niculescu-Mizil & Caruana (2005), Guo et al. (2017) | `COMPLETED` (Notebook 06 Executed; Artifacts in `artifacts/reports/EXP-0003/`) |
| [EXP-0004](#exp-0004) | Direct Race-Level Winner Probability Model (Plackett-Luce Ranking) | RQ1 | [HYP-0001](../research/HYPOTHESES.md#hyp-0001-sequential-information-superiority) | $T_5$ (Pre-Race) | Model 5: Plackett-Luce Ranking / Conditional Logit MLE | Plackett (1975), Luce (1959), Hunter (2004) | `COMPLETED` (Notebook 07 Executed; Artifacts in `artifacts/reports/EXP-0004/`) |
| [EXP-0005](#exp-0005) | Multi-Checkpoint Walk-Forward Validation & Calibration Drift | RQ1, RQ3 | [HYP-0001](../research/HYPOTHESES.md#hyp-0001-sequential-information-superiority), [HYP-0004](../research/HYPOTHESES.md#hyp-0004-checkpoint-calibration-drift) | $T_0 \dots T_5$ | Calibrated Sequential Ensemble / Plackett-Luce | van Kesteren & Bergkamp (2023), Chalita & Hassanipak (2025) | `COMPLETED` (149 Races Backtested; Artifacts in `artifacts/reports/EXP-0005/`) |
| [EXP-0006](#exp-0006) | Counterfactual Strategy & Tactical Undercut Simulation | RQ4 | [HYP-STRAT-001](../research/HYPOTHESES.md#hyp-strat-001-counterfactual-strategy-and-tactical-gain) | Phase 7 (Simulation) | Monte Carlo Simulation / Common Random Numbers / Counterfactual Rollouts | Thomas et al. (2026), Piccinotti et al. (2021), Heilmeier et al. (2020) | `COMPLETED` (Artifacts in `artifacts/reports/EXP-0006/`) |

---

## 2. Planned & Executed Experiment Overviews

### EXP-0001
- **Focus:** Establish the foundational non-sequential baseline using historical race results across 2010–2026 ($T_0$ Pre-Weekend).
- **Initial Run (EXP-0001-R1):** Exploratory walk-forward baseline run (346 races; Driver Elo log loss: 2.275307 vs uniform 3.044556; Driver Elo Brier score: 0.844919 vs uniform 0.952264; legacy top-1 accuracy: 0.332370). Preserved in `artifacts/reports/EXP-0001/`.
- **Corrected Run (EXP-0001-R2):** Executed collaborative walk-forward run across 346 races (2010–2026, 7,285 candidate records). Serialized full candidate probability distributions, verified simplex normalization ($\sum P = 1 \pm 10^{-5}$), and implemented non-starter / DSQ rating exclusion (72 skips audited). Preserved in `artifacts/reports/EXP-0001-R2/`:
  - **Elo mean log loss:** 2.278177 (Uniform: 3.044556, improvement: +0.766379).
  - **Elo multiclass Brier score:** 0.845726 (Uniform: 0.952264, improvement: +0.106538).
  - **Tie-aware top-1 accuracy:** 0.335260 (116 / 346).
  - **Fractional top-1 credit:** 0.332490 (115.0417 / 346).
  - **Legacy argmax top-1 accuracy:** 0.335260 (116 / 346).
  - **Top-probability ties:** 1 race (2010 Round 1, 24-way tie at $P = 1/24$).
  - **Candidate Ordering Audit Finding:** In R2, candidates were sorted by `finish_position_int` before the race loop. For the 24-way tie in 2010 Round 1, `np.argmax` selected index 0 (Alonso), which artificially gave `legacy_top1` a hit using post-race finishing position order.
- **Outcome-Independent Corrected Run (EXP-0001-R3):** Enforces strictly outcome-independent candidate ordering by sorting candidates by `driver_id` prior to forecasting. Preserved in `artifacts/reports/EXP-0001-R3/`:
  - Log loss (2.278177), Brier score (0.845726), tie-aware top-1 (0.335260), and fractional credit (0.332490) remain identical.
  - `legacy_top1_accuracy` is 0.332370 (115 / 346), properly exposing the arbitrary tie-break behavior on outcome-independent ordering.
- **Probability Calibration Audit (EXP-0001-CAL-001):** Evaluated candidate-level probability calibration over EXP-0001-R3 (7,285 candidates, 346 races). Executed in `notebooks/04_probability_calibration.ipynb` and preserved in `artifacts/reports/EXP-0001-CAL-001/`:
  - Fixed-bin ECE (8 non-empty bins): 0.030667 (95% race-clustered bootstrap CI: [0.026800, 0.034156]).
  - Fixed-bin MCE: 0.185189 (95% CI: [0.133562, 0.268597]).
  - Calibration-in-the-Large: 0.000000 (mean observed win rate 0.047495 matches mean predicted probability 0.047495).
  - Empty bins: 2 bins (`[0.30, 0.50)` and `[0.50, 1.00]`) cleanly excluded from ECE/MCE.
  - Candidate one-vs-rest Brier score: 0.040168 (95% CI: [0.039589, 0.040720]).
  - Candidate one-vs-rest log loss: 0.151746 (95% CI: [0.149093, 0.154541]).
- **Scheduled Phase:** Baseline Prototyping (M3).

### EXP-0002
- **Focus:** Establish the standard pre-race starting-grid race-winner benchmark at forecast checkpoint $T_5$ (30 minutes prior to formation lap / official FIA final grid).
- **Related Hypotheses:** [HYP-0001](../research/HYPOTHESES.md#hyp-0001-sequential-information-superiority), [HYP-GRID-001](../research/HYPOTHESES.md#hyp-grid-001-pre-race-grid-position-dominance), [HYP-GRID-002](../research/HYPOTHESES.md#hyp-grid-002-nonlinear-grid-representation-superiority).
- **Pre-Race Candidate Field Audit:** Documented in [docs/research/CANDIDATE_FIELD_AUDIT.md](../research/CANDIDATE_FIELD_AUDIT.md). Entrant lists represent a provisional result-record proxy until entry-field reconstruction is verified against official pre-session timing manifests; zero post-race leakage is not claimed as proven; drivers are not excluded using post-race status; and race-specific grid-zero encoding ($\max_{i, \text{grid}_i > 0}(\text{grid}_i) + 1$, with `is_grid_zero` indicator) is enforced without assuming grid zero is definitive pit-lane proof.
- **Active Research Notebook:** [notebooks/05_static_grid_benchmark.ipynb](../../notebooks/05_static_grid_benchmark.ipynb).
- **Candidate Models Compared:**
  - **Model 0 (Uniform Baseline):** $P_i = 1/N_r$ over all $N_r$ pre-race entrants.
  - **Model 1 (Empirical Grid Baseline):** Historical win frequency by starting grid position with Laplacian smoothing ($P(\text{Win} \mid \text{Grid})$, $\alpha=10$).
  - **Model 2 (Grid-Only Logistic Regression):** Univariate logistic regression on 5 grid features.
  - **Model 3 (Grid + Driver/Constructor Form Logistic Regression):** Multivariate logistic regression on 16 grid and rolling form features.
  - **Model 4 (Pre-Race LightGBM Benchmark):** Gradient boosted decision tree model on 16 features.
- **Evaluation Cohort & Protocol:** Rolling-origin backtesting across 2018–2024 primary test cohort (149 rounds, 2,979 candidate rows) with 2010–2017 historical sensitivity/warm-up (156 rounds, 3,453 candidate rows), totaling 305 completed races and 6,432 records across 2010–2024.
- **Proper Scoring Rules:** Multi-Class Log Loss, Multi-Class Brier Score, Tie-Aware Top-1 Accuracy, Fractional Top-1 Credit, Expected Calibration Error (ECE).
- **Status:** `COMPLETED` (Executed in `notebooks/05_static_grid_benchmark.ipynb`; artifacts in `artifacts/reports/EXP-0002/`).
- **Key Empirical Results (Primary Cohort, 2018–2024, 149 Races):**
  - Model 0 (Uniform): Log Loss `2.995388`, Brier `0.949982`, Fract. Top-1 `0.050018`.
  - Model 1 (Grid Frequency): Log Loss `1.583766`, Brier `0.682312`, Fract. Top-1 `0.496644`.
  - Model 2 (Grid Logistic): Log Loss `1.594207`, Brier `0.683382`, Fract. Top-1 `0.496644`.
  - Model 3 (Grid + Form Logistic): Log Loss `1.355201`, Brier `0.612698`, Fract. Top-1 `0.516779` (**Best Overall Probabilistic Performance**).
  - Model 4 (LightGBM): Log Loss `1.409149`, Brier `0.628561`, Fract. Top-1 `0.530201` (**Best Argmax Accuracy**, but inferior under proper scoring rules due to uncalibrated overconfident probability tails).

### EXP-0003
- **Focus:** Post-hoc probability calibration benchmark across pre-race models (Model 3 Logistic Regression and Model 4 LightGBM GBDT) to correct probability overconfidence.
- **Academic Foundation:** Niculescu-Mizil & Caruana (2005) calibration analysis; Guo et al. (2017) temperature scaling for modern neural and tree architectures.
- **Related Hypothesis:** [HYP-0004](../research/HYPOTHESES.md#hyp-0004-checkpoint-calibration-drift).
- **Target Checkpoint:** $T_5$ (Pre-Race).
- **Active Research Notebook:** [notebooks/06_probability_calibration.ipynb](../../notebooks/06_probability_calibration.ipynb).
- **Calibration Methods Evaluated:**
  - Raw uncalibrated probabilities.
  - Platt Scaling (parametric sigmoid mapping).
  - Isotonic Regression (non-parametric monotonic mapping).
  - Temperature Scaling ($P_i \propto \exp(z_i / T)$).
- **Status:** `COMPLETED` (Executed in `notebooks/06_probability_calibration.ipynb`; artifacts in `artifacts/reports/EXP-0003/`).
- **Key Empirical Results (Primary Cohort, 2018–2024, 149 Races):**
  - Model 3 Logistic is naturally well-calibrated (Raw Log Loss `1.355201`, ECE `0.009618`, $T \approx 1.007$). Calibration yields negligible change.
  - Model 4 LightGBM benefits significantly from calibration: Temperature scaling ($T \approx 1.360$) reduces Log Loss from `1.409149` to `1.387587` and ECE from `0.013875` to `0.007818`. Platt scaling yields Log Loss `1.388663` and ECE `0.007314`.
  - Isotonic regression overfits and degrades log loss on candidate probability simplexes (Model 4 Isotonic Log Loss: `1.450040`).

### EXP-0004
- **Focus:** Direct race-level winner probability modeling using Plackett-Luce ranking and grouped conditional logit maximum likelihood estimation (Model 5).
- **Academic Foundation:** Plackett (1975), Luce (1959) choice axioms; Hunter (2004) MM algorithms for generalized Bradley-Terry models.
- **Related Hypothesis:** [HYP-0001](../research/HYPOTHESES.md#hyp-0001-sequential-information-superiority).
- **Target Checkpoint:** $T_5$ (Pre-Race).
- **Active Research Notebook:** [notebooks/07_plackett_luce_ranking.ipynb](../../notebooks/07_plackett_luce_ranking.ipynb).
- **Status:** `COMPLETED` (Executed in `notebooks/07_plackett_luce_ranking.ipynb`; artifacts in `artifacts/reports/EXP-0004/`).
- **Key Empirical Results (Primary Cohort, 2018–2024, 149 Races):**
  - Model 5 (Plackett-Luce Ranking Model): Log Loss `1.351747`, Brier `0.596564`, Fract. Top-1 `0.543624`.
  - Establishes mathematical consistency across full candidate simplexes ($\sum P = 1.0$) with joint multi-output predictions ($\sum p_{\text{podium}} = 3.0$, $\sum p_{\text{top5}} = 5.0$, $\sum E[\text{pos}] = N(N+1)/2$).

### EXP-0005
- **Focus:** Systematic evaluation of predictive performance (multiclass log loss, Brier score, ECE, top-1 accuracy) across discrete weekend checkpoints ($T_0 \dots T_5$) on the 149-race historical primary cohort (2018–2024), and sequential practice analysis.
- **Academic Foundation:** van Kesteren & Bergkamp (2023) [REF-01]; Chalita & Hassanipak (2025) [REF-08].
- **Related Hypotheses:** [HYP-0001](../research/HYPOTHESES.md#hyp-0001-sequential-information-superiority), [HYP-0004](../research/HYPOTHESES.md#hyp-0004-checkpoint-calibration-drift).
- **Target Checkpoints:** $T_0 \dots T_5$.
- **Status:** `COMPLETED (Phase 6.2 Provenance Audited & Controlled Ablation Validated)`
- **Artifacts:**
  - `artifacts/reports/EXP-0005/PROVENANCE_AUDIT.md` (Detailed provenance report and confound analysis)
  - `artifacts/reports/EXP-0005/prediction_ledger.csv` (1,043 per-race prediction records with exact probability vectors)
  - `artifacts/reports/EXP-0005/historical_checkpoint_coverage_matrix.csv` (149-race session availability audit)
  - `artifacts/reports/EXP-0005/cohort_a_metrics.json` (Cohort A: 149 races, Universal coverage T0, T4, T5)
  - `artifacts/reports/EXP-0005/cohort_b_metrics.json` (Cohort B: 12 modern Sprint races, T0, T1, T4, T5)
  - `artifacts/reports/EXP-0005/cohort_c_metrics.json` (Cohort C: 34 modern Standard races, Complete T0-T5)
  - `artifacts/reports/EXP-0005/cohort_c_transitions.json` (Cohort C pairwise transitions with Holm-Bonferroni corrections)
  - `artifacts/reports/EXP-0005/controlled_checkpoint_metrics.json`
  - `artifacts/reports/EXP-0005/paired_statistical_tests.json`
  - `artifacts/reports/EXP-0005/sensitivity_analysis.json` (DNS drivers & grid-zero pit-lane start analysis)
  - `artifacts/reports/EXP-0005/era_and_season_breakdown.csv`
  - `artifacts/reports/EXP-0005/race_level_checkpoint_evaluations.csv`
  - `artifacts/reports/EXP-0005/practice_coverage_audit_34_weekends.csv` (102 practice sessions audit: 2.9% cached locally, 97.1% provider-available)
  - `artifacts/reports/EXP-0005/practice_coverage_audit_34_weekends.json`
  - `artifacts/reports/EXP-0005/t0_t3_feature_flow_diagnostic.json` (Root-cause diagnosis of T0-T3 metric invariance)
  - `artifacts/reports/EXP-0005/genuine_practice_subset_ablation.json` (Abu Dhabi 2024 genuine practice telemetry ablation)
  - `artifacts/reports/EXP-0005/t4_t5_grid_penalty_audit.json` (2024 24-round audit: 15 races with confirmed grid changes)
  - `artifacts/reports/EXP-0005/model_objective_comparison.json` (Binary logistic + softmax vs conditional logit MLE solver)
  - `artifacts/reports/EXP-0005/prediction_ledger_v2.jsonl` (447 records with deterministic replay reproducibility $\le 10^{-5}$)
- **Key Empirical Results (Phase 6.2 Controlled Invariant Model Family: L2 Logistic Regression C=1.0):**
  - **Cohort A (149 races, 2018–2024):**
    - $T_0$ (Form-only): Log Loss `1.5646`, Brier `0.6692`, Top-1 Acc `53.02%`
    - $T_4$ (Form + Grid): Log Loss `1.3551`, Brier `0.6130`, Top-1 Acc `51.68%`
    - $\Delta \text{LogLoss} (T_4 - T_0) = -0.2095$ (95% CI: $[-0.3844, -0.0325]$, Wilcoxon $p = 0.00081$, Holm-Bonferroni $p = 0.00244$, **statistically significant**)
  - **Cohort C (34 Standard races, 2023–2024):**
    - $T_0$ (Form-only): Log Loss `1.4190`, Brier `0.5858`, Top-1 Acc `58.82%`
    - $T_1 \dots T_3$ (Free Practice): Log Loss `1.4190`, Brier `0.5858` (unobserved practice records in historical archive fallback to rolling form)
    - $T_4$ (Form + Grid): Log Loss `0.9467`, Brier `0.4440`, Top-1 Acc `70.59%`
    - $\Delta \text{LogLoss} (T_4 - T_3) = -0.4723$ (95% CI: $[-0.7798, -0.1329]$, Wilcoxon $p = 0.000457$, Holm-Bonferroni $p = 0.00274$, **statistically significant**)
    - $\Delta \text{Brier} (T_5 - T_0) = -0.1418$ (95% CI: $[-0.2566, -0.0238]$, Wilcoxon $p = 0.000457$, Holm-Bonferroni $p = 0.03826$, **statistically significant**)
  - **Multi-Model Benchmark (EXP-0001 through EXP-0004 Comparison):**
    - $T_0$ Elo Prior: Log Loss `2.0588`, Brier `0.8053`
    - $T_4$ Grid-only Logistic: Log Loss `1.5942`, Brier `0.6834`
    - $T_5$ Grid + Form Logistic: Log Loss `1.3552`, Brier `0.6127`
    - $T_5$ Plackett-Luce: Log Loss `1.3517`, Brier `0.5966`
  - **Provenance Finding:** Phase 6.1 evaluated lookups/rescorings of EXP-0001-R3, EXP-0002, and EXP-0004. Over two-thirds of the apparent $\Delta \text{LogLoss} = -0.7036$ was attributable to model family differences (Elo vs Logistic) rather than evidence arrival. In the controlled ablation, true information gain from starting grid is $\Delta \text{LogLoss} = -0.2095$ (Cohort A) and $-0.4723$ (Cohort C).
- **Key Empirical Results (Phase 6.3 & 6.3.1 Practice Sensitivity & Provenance Reconciliation):**
  - **Session Identity Audit:** Confirmed Abu Dhabi 2024 FP1 is OpenF1 session `9461` (resolving the `9641` transcription typo), FP2 is `9656`, and FP3 is `9657`.
  - **Driver Substitution Handling:** In FP1, car 37 was piloted by rookie Isack Hadjar (FIA time 85.877s); Max Verstappen did not drive FP1. Verstappen's FP1 telemetry is strictly marked missing (`missing=1.0`, `pace_delta=None`), eliminating fabricated defaults or Hadjar pace leakage.
  - **Reconciled Practice Lap Observations:**
    - FP1 Benchmark: Leclerc 84.321s; Norris 84.542s ($\Delta = +0.221$s); Hamilton 84.806s ($\Delta = +0.485$s); Verstappen N/A.
    - FP2 Benchmark: Norris 83.517s; Hamilton 84.119s ($\Delta = +0.602$s); Leclerc 84.201s ($\Delta = +0.684$s); Verstappen 84.598s ($\Delta = +1.081$s). Medium tyre deg: Norris +0.1063 s/lap, Leclerc +0.0919 s/lap, Hamilton -0.0177 s/lap, Verstappen -0.1439 s/lap (fuel burn-off confounding noted).
    - FP3 Benchmark: Norris 83.626s; Hamilton 83.823s ($\Delta = +0.197$s); Verstappen 83.844s ($\Delta = +0.218$s); Leclerc 84.098s ($\Delta = +0.472$s).
  - **Metric Reconciliation & Decoupled Scope:**
    - **4-Driver Restricted Contender Study:** Norris, Verstappen, Leclerc, Hamilton:
      - $T_0$ Form: $p_{\text{Norris}} = 0.2634$, Race Log Loss `1.3341`, Multiclass Brier `0.7341`, Cand-BCE `0.5472`.
      - $T_1$ FP1 Pace: $p_{\text{Norris}} = 0.2183$, Race Log Loss `1.5219`, Multiclass Brier `0.8633`, Cand-BCE `0.6178` (Friday non-monotonicity: Leclerc fastest, Verstappen unpenalized, Norris back).
      - $T_2$ FP2 Pace + Deg: $p_{\text{Norris}} = 0.4701$, Race Log Loss `0.7548`, Multiclass Brier `0.3785`, Cand-BCE `0.3352` (Norris dominates single-lap pace and Medium stint).
      - $T_3$ FP3 Pace: $p_{\text{Norris}} = 0.4840$, Race Log Loss `0.7257`, Multiclass Brier `0.3659`, Cand-BCE `0.3250`.
      - Mathematical alignment strictly verified: Race Log Loss $\equiv -\ln(p_{\text{Norris}})$ for all variants.
    - **20-Driver Full Entrant Field Evaluation:**
      - $T_0 \dots T_3$: $p_{\text{Norris}} = 0.0515$, Race Log Loss `2.9662`, Multiclass Brier `1.0813` (practice features unpopulated in historical training races shrink weights to zero).
      - $T_4 \dots T_5$: $p_{\text{Norris}} = 0.3961$, Race Log Loss `0.9261`, Multiclass Brier `0.4500`, Podium Prob `0.8532` (Norris captures pole).
  - **T4 vs T5 Grid Change Audit (2024 Season, 24 Rounds):** 15 of 24 races (62.5%) exhibited grid penalties/changes between provisional qualifying and confirmed starting grids. Output probability vectors shifted in all 15 rounds (mean $L_1$ shift: 0.1650). In 9 non-penalty races, vectors were bitwise identical ($\Delta \text{LogLoss} \equiv 0.0000$). On standard weekends, 12 of 18 races had grid changes. Reconciles Phase 6.2 invariance where identical inputs were evaluated by construction.
  - **Model Objective Comparison (Walk-Forward 2018–2024, 149 Races):**
    - Binary Logistic + Softmax: Log Loss `1.3551`, Brier `0.6130`, Top-1 `51.68%`.
    - Grouped Conditional Logit MLE with nested chronological regularization tuning ($\lambda \in [0.05, 1.0]$): Log Loss `1.3526`, Top-1 `51.01%`, matching binary logistic when regularization scaling is treated fairly.
  - **Ledger v2 Deterministic Replay Across All 447 Records:** Replay verification achieved 447 / 447 exact matches with maximum absolute difference $3.298 \times 10^{-7}$ ($\le 10^{-5}$ tolerance). Original ledger version preserved intact.

### EXP-0006
- **Focus:** Evaluate downstream counterfactual pit stop strategy optimization, tactical undercut emergence, and safety car opportunism using multi-agent stochastic Monte Carlo race simulation with Common Random Numbers (CRN).
- **Academic Foundation:** Thomas et al. (2026, *Machine Learning*) [REF-04] RSRL framework; Piccinotti et al. (2021) [REF-06] Open-Loop MCTS; Heilmeier et al. (2020) [REF-05] TUM open-source race simulation engine; Fieni et al. (2026b) [REF-10] aerodynamic wake interaction model.
- **Related Hypothesis:** [HYP-STRAT-001](../research/HYPOTHESES.md#hyp-strat-001-counterfactual-strategy-and-tactical-gain).
- **Target Checkpoint:** Phase 7 (Monte Carlo Strategy Dynamics Simulator).
- **Status:** `COMPLETED`
- **Artifacts:**
  - `artifacts/reports/EXP-0006/exp_0006_final_closeout_v3.json` (Final methodology correction artifact: Table A 1,284 raw message ledger, Table B 438 derived event lifecycle ledger, green initiation hazards 258/19420 and 180/13558, conditional escalation 52/180, and Phase 8 authorization)
  - `artifacts/reports/EXP-0006/exp_0006_final_closeout_v2.json` (Numerical integrity gate artifact: machine-verified weighted-mean identity residual <= 9.09e-13s, DNF lap span 1-58, transition reconciliation of 1,284 raw race-control messages, green initiation hazards, and Phase 8 authorization)
  - `artifacts/reports/EXP-0006/exp_0006_final_closeout.json` (Frozen final closeout artifact containing reconciled race times, DNF decomposition, SC/VSC exposures, and marginal equivalence proofs)
  - `artifacts/reports/EXP-0006/simulation_experiment_summary.json` (Full 5-strategy counterfactual comparison on 2024 Abu Dhabi Grand Prix with Common Random Numbers)
  - `artifacts/reports/EXP-0006/exp_0006_v2_strategy_robustness_10000.json` (True 10,000 paired iterations across all 5 strategies with convergence checkpoints at 1000, 2500, 5000, and 10000, position distributions, tyre usage, and Holm-Bonferroni adjusted $p$-values)
  - `artifacts/reports/EXP-0006/scaled_strategy_robustness_10000.json` (Canonical artifact updated with true 10,000-draw evaluation, standard errors, bootstrap CIs, and step-down Holm-Bonferroni adjustments)
  - `artifacts/reports/EXP-0006/crn_variance_reduction_validation.json` (Common Random Numbers multi-seed audit across seeds 42, 101, 777, 1337, 2024: 99.996% race time variance reduction, 90.64% position variance reduction, $\rho=0.99996$, with scenario alignment and KS-test marginal equivalence verification)
  - `artifacts/reports/EXP-0006/holdout_strategy_evaluation.json` (Holdout Strategy Selection on Set A [$N=2,500$] vs frozen evaluation on Set B [$N=2,500$] with regret vs Ex-Post Oracle)
  - `artifacts/reports/EXP-0006/fuel_tyre_sensitivity_qualification.json` (Latent fuel burn-off sensitivity grid across 1.4–2.0 kg/lap and 0.025–0.040 s/kg bounding adjusted tyre degradation slopes to 0.0263–0.0713 s/lap)
  - `artifacts/reports/EXP-0006/historical_simulation_backtest.json` (Chronological 3-race simulation backtest with full-field probability vectors and mathematically exact log-loss scoring across Abu Dhabi, Silverstone, and Bahrain)
  - `artifacts/reports/EXP-0006/parameter_sensitivity_analysis.json` (Parameter sensitivity sweeps across SC hazard, tyre degradation scale, and pit transit loss)
- **Key Empirical Results (Phase 7.2 & EXP-0006 Final Closeout):**
  - **Multi-Seed CRN Variance Reduction & Marginal Equivalence:**
    - Evaluated across 5 independent master seeds (`[42, 101, 777, 1337, 2024]`).
    - Mean Independent Race Time Diff Variance: $2,258,072.1$
    - Mean CRN Paired Race Time Diff Variance: $88.8$
    - **Mean Variance Reduction: 99.996%** (95% CI: $[99.996\%, 99.997\%]$), Correlation $\rho = 0.99996$.
    - **Mean Position Difference Variance Reduction: 90.64%** (95% CI: $[89.58\%, 91.68\%]$).
    - Variance Cancellation Mechanism: Exogenous weather shifts and safety car deployments alter total race times by 30–150s ($\text{Var}(\Delta_{\text{exog}}) > 1.1 \times 10^6\text{s}^2$), dominating independent comparison ($\approx 2.26 \times 10^6\text{s}^2$). CRN couples these exogenous events identically across runs, cancelling them out and isolating the pure tactical differential ($\approx 60\text{s}^2$).
    - Two-sample Kolmogorov-Smirnov test verifies no statistically detectable marginal distribution difference in the tested samples across all 5 master seeds ($D \le 0.052, p \ge 0.498$), satisfying practical equivalence tolerance $\Delta_{\text{equiv}} \le 0.060$.
  - **Reconciled 10,000 Paired Draws Strategy Comparison (Abu Dhabi 2024, Lando Norris starting P1):**
    - `SafetyCar_Reactive`: Expected Position `3.743` (SE 0.0429), Win Prob `33.29%` (SE 0.0047), Podium Prob `71.80%`, Top-5 `85.39%`, Completed Race Mean Time `5188.725s` (std 119.3s), All-Runs Mean Time `4906.564s` (std 1038.2s), DNF Rate `8.87%` (887 runs), Pit Stops `1.56`. Tyre Usage: Medium 1.000, Hard 0.956.
    - `Reference_1Stop`: Expected Position `3.812` (SE 0.0406), Win Prob `17.50%` (SE 0.0038), Podium Prob `72.90%`, Top-5 `88.81%`, Completed Race Mean Time `5190.264s` (std 118.6s), All-Runs Mean Time `4907.925s` (std 1038.6s), DNF Rate `8.87%` (887 runs), Pit Stops `0.96`.
    - `Tactical_Overcut`: Expected Position `4.308` (SE 0.0423), Win Prob `19.32%` (SE 0.0039).
    - `Tactical_Undercut`: Expected Position `4.633` (SE 0.0428), Win Prob `13.87%` (SE 0.0035).
    - `Aggressive_2Stop`: Expected Position `4.804` (SE 0.0420), Win Prob `17.65%` (SE 0.0038).
    - Paired difference `SafetyCar_Reactive` vs `Reference_1Stop`: $\Delta_{\text{pos}} = -0.069$ (SE 0.0176, 95% CI: $[-0.104, -0.034]$, raw $p = 9 \times 10^{-5}$, Holm-Bonferroni adjusted $p = 9 \times 10^{-5}$).
    - Multi-Objective Trade-Offs: `SafetyCar_Reactive` maximizes Win % and minimizes Expected Position; `Reference_1Stop` maximizes Podium % and Top-5 % with lower outcome variance. On decisive runs, `SafetyCar_Reactive` beats 1-stop in 59.07% of non-tied finishes (31.34% vs 21.72% on all runs, 46.94% tied).
    - Race-Time Calibration & Reconciliation: Completed race duration ($5,188.73\text{s}$ vs $5,190.26\text{s}$) closely matches official 2024 Abu Dhabi GP winner Norris ($5,193.291\text{s}$, error $< 0.1\%$). Unconditional all-runs paired time diff is $-1.361\text{s}$ (SE 0.0882s); conditional matched completed-runs paired time diff is $-1.539\text{s}$ (SE 0.0935s, 95% CI: $[-1.722, -1.355]$ across 9,113 matched finishes). Prior $-16.36\text{s}$ text discrepancy resolved. Standing start physical launch delay adds $+4.8\text{s}$ on Lap 1.
    - Safety Car & VSC Exposure Calibration: SC (310 distinct phases / 311 total deployments including Spa 2021, $\lambda_{\text{total}} = 0.0150, \lambda_{\text{green}} = 0.0160$) and VSC (128 standalone / 180 total activations including 52 compound escalations, $\lambda_{\text{total}} = 0.0120, \lambda_{\text{green}} = 0.0133$, with chronological pre-2015 zero cutoff). Denominator $L_{\text{green}}$ is selected as mechanistically appropriate for green-flag incident initiation.
  - **Holdout Strategy Selection vs. Frozen Evaluation (Set A vs Set B, $N=2,500$ each):**
    - Set A Selection: `SafetyCar_Reactive` selected based on lowest expected position ($E[\text{pos}] = 3.748$, win prob $33.8\%$).
    - Set B Frozen Evaluation: `SafetyCar_Reactive` achieved $E[\text{pos}] = 3.541$, win prob $35.3\%$, beating 1-stop with $\Delta_{\text{pos}} = -0.121$ ($p = 0.00045$, Holm-Bonferroni adjusted $p = 0.00045$).
    - Ex-Post Oracle performance on Set B: $E[\text{pos}] = 2.838$, win prob $44.4\%$. Online strategy position regret is $+0.703$ positions.
  - **Boundary Conditions & Strategy Inversion:**
    - At `sc_scale = 0.0x`, `SafetyCar_Reactive` loses its advantage (Exp Pos P3.49 vs 1-Stop P3.50, Win Prob 13% vs 12%), showing its benefit depends strictly on neutralisation likelihood.
    - At `deg_scale = 1.5x`, `Aggressive_2Stop` win prob jumps from 12% to **27%**, overtaking the 1-Stop (17%), as high degradation drives 1-stoppers into quadratic tyre cliffs.
  - **Historical Simulation Backtest (3 Grand Prix Sanity Check):**
    - Races: Abu Dhabi 2024 (Round 24), Silverstone 2024 (Round 12), Bahrain 2024 (Round 1).
    - Abu Dhabi: Winner Norris ($p=0.1600$), Log Loss $-\ln(0.1600) = \mathbf{1.8326}$, Brier $\mathbf{1.0689}$.
    - Silverstone: Winner Hamilton ($p=0.1200$), Log Loss $-\ln(0.1200) = \mathbf{2.1203}$, Brier $\mathbf{1.2719}$.
    - Bahrain: Winner Verstappen ($p=0.8267$), Log Loss $-\ln(0.8267) = \mathbf{0.1903}$, Brier $\mathbf{0.0504}$.
    - Cohort Mean: Log Loss $\mathbf{1.3811}$, Brier $\mathbf{0.7971}$, Top-1 Accuracy $\mathbf{33.33\%}$, MAE $\mathbf{3.45}$ positions.
    - Explicitly documented as a preliminary pipeline sanity check, not full multi-season model calibration.
  - **Epistemological Integrity Note:** In accordance with APEX rules, fuel mass burn-off (1.75 kg/lap, 0.033 s/kg) is classified as an assumed latent parameter (unobserved in public timing feeds), safety car hazard rates are calibrated empirical priors, and tyre degradation follows non-linear thermal/tread curves. The results support **HYP-STRAT-001** under simulation conditions.
