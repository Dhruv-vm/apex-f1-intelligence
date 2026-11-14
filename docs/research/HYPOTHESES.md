# APEX — Research Hypotheses Registry

> **Status Notice:** All hypotheses listed in this registry are currently **PROPOSED**. They represent scientific conjectures derived from motorsport engineering theory, not demonstrated empirical findings. No outcomes are pre-judged.

---

## 1. Hypothesis Registry Overview

| Hypothesis ID | Title | Primary Metric | Required Checkpoint | Theoretical Grounding | Current Status |
|---|---|---|---|---|---|
| [HYP-0001](#hyp-0001-sequential-information-superiority) | Sequential Information Superiority | Multi-Class Log Loss, Brier Score | Pre-Weekend $\rightarrow$ Pre-Race | van Kesteren & Bergkamp (2023) | `PARTIALLY SUPPORTED` (Audited in Phase 6.2, EXP-0005) |
| [HYP-0002](#hyp-0002-incremental-value-of-free-practice-telemetry) | Incremental Value of Free Practice Data | Brier Score, Finishing Pos MAE | Post-FP2 vs Pre-Weekend | Cappello & Hoegh (2025), Heilmeier et al. (2020) | `PROPOSED` |
| [HYP-0003](#hyp-0003-modality-parsimony-and-leakage-sensitivity) | Modality Parsimony & Telemetry Noise | Log Loss, Expected Calibration Error | Post-Qualifying | Todd et al. (2025), Sasikumar et al. (2025) | `PROPOSED` |
| [HYP-0004](#hyp-0004-checkpoint-calibration-drift) | Checkpoint Calibration Drift | Expected Calibration Error (ECE) | T0 through T5 | Chalita & Hassanipak (2025) | `PROPOSED` |
| [HYP-GRID-001](#hyp-grid-001-pre-race-grid-position-dominance) | Pre-Race Grid Position Dominance | Multi-Class Log Loss, Brier Score | T5 (Pre-Race) | van Kesteren & Bergkamp (2023), Bell et al. (2016) | `PROPOSED` |
| [HYP-GRID-002](#hyp-grid-002-nonlinear-grid-representation-superiority) | Nonlinear Grid Representation Superiority | Multi-Class Log Loss, Brier Score, ECE | T5 (Pre-Race) | Henderson et al. (2016), Bansal et al. (2025) | `PROPOSED` |
| [HYP-STRAT-001](#hyp-strat-001-counterfactual-strategy-and-tactical-gain) | Counterfactual Strategy & Tactical Gain | Simulated Finishing Rank, Stint Delta (s) | Phase 7 (EXP-0006) | Thomas et al. (2026), Piccinotti et al. (2021) | `SUPPORTED_UNDER_SIMULATION_CONDITIONS` (Evaluated in Phase 7, EXP-0006) |

---

## 2. Hypothesis Specifications

### HYP-0001: Sequential Information Superiority
- **Rationale:** Formula 1 teams bring aerodynamic upgrades, circuit-specific wing setups, and engine performance modes that are unobservable prior to on-track running. As evidence accumulates over a race weekend, predictive uncertainty should contract.
- **Null Hypothesis ($H_0$):** Probabilistic race outcome forecasts generated sequentially across race weekend checkpoints (Post-FP2, Post-Qualifying) exhibit no statistically significant reduction in multi-class Brier score or log loss compared to a static pre-weekend baseline ($p \ge 0.05$ under a paired Wilcoxon signed-rank test).
- **Alternative Hypothesis ($H_1$):** Sequential models incorporating post-practice and post-qualifying checkpoints achieve statistically significant lower Brier score and log loss than static pre-weekend baselines ($p < 0.05$).
- **Required Data:** Multi-season historical race results (2018–2024), practice session lap times, official qualifying classifications.
- **Proposed Comparison:** Static Pre-Weekend Elo/GBDT vs. Sequential Checkpoint GBDT (`EXP-0001` vs `EXP-0002`).
- **Primary Metrics:** Multi-class Brier Score, Multi-class Log Loss.
- **Status:** `PARTIALLY SUPPORTED` (Audited in Phase 6.2 & 6.3 across 149-race historical cohort under invariant model family ablation, 3 independent cohorts, and genuine practice subset evaluations; qualifying grid arrival is strongly supported, while free practice transitions remain inconclusive at scale due to archive sparsity).
- **Implementation Status:** Checkpoint forecasting engine (`backend/forecasting/engine.py`, `evaluator.py`, `backtest.py`, `controlled_ablation.py`, `practice_audit.py`, `practice_subset_ablation.py`, `grid_penalty_audit.py`, `model_objective_comparison.py`, `replay_ledger.py`, `/api/v1/predictions`) validated across checkpoints ($T_0 \dots T_5$). Prediction ledger published at `artifacts/reports/EXP-0005/prediction_ledger.csv` (v1: 1,043 audited records) and `prediction_ledger_v2.jsonl` (v2: extended provenance with deterministic replay reproducibility $\le 2.24 \times 10^{-7}$). Plackett-Luce forward choice ranking enforces exact multi-output probability sums ($\sum p_{\text{podium}} = 3.0$, $\sum p_{\text{top5}} = 5.0$, $\sum E[\text{pos}] = N(N+1)/2$).
- **Evidence References:**
  1. **Phase 6.3 Genuine Practice Subset Ablation (Abu Dhabi 2024, Session 9461, 9656, 9657):**
     - $T_0$ (Pre-Weekend Form): Mean Log Loss `1.3341`, Brier `0.7341`, Fract. Top-1 `0.2634` (Verstappen favorite at 32.2%, Norris 26.3%)
     - $T_1$ (Post-FP1 Pace): Mean Log Loss `1.2536`, Brier `0.7171` (Leclerc fastest in FP1 at 84.321s, jumping to favorite at 38.5%; demonstrates Friday fuel non-monotonicity)
     - $T_2$ (Post-FP2 Pace + Degradation): Mean Log Loss `0.7547`, Brier `0.3785`, Top-1 Hit `1.0` (Norris fastest at 83.517s, -0.68s clear with strong +0.106 s/lap degradation slope; probability surges to 47.0%, contracting log loss by -0.5794)
     - $T_3$ (Post-FP3 Full Practice): Mean Log Loss `0.7256`, Brier `0.3659`, Fract. Top-1 `0.4840` (Norris confirms pace supremacy at 83.626s)
     - *Ablation Sensitivity:* FP2 pace alone reduces log loss to `0.5101`; FP2 degradation slope alone yields `1.2294`; all practice features combined yield `0.6725`.
  2. **Phase 6.3 Practice Coverage Audit (34 Standard Grand Prix Weekends, 102 Sessions):**
     - 3 of 102 sessions (2.9%) locally cached with valid lap/stint payloads (Abu Dhabi 2024 FP1, FP2, FP3).
     - 99 of 102 sessions provider-available via OpenF1 API but locally uncached in repository.
     - *Root Cause for Phase 6.2 Invariance:* Uncached practice sessions defaulted to neutral 0.0 with missing=1.0; because training history had zero variance on practice columns, L2 regularization drove fitted practice weights strictly to 0.000000, producing bitwise identical probabilities down to machine epsilon across T0–T3 on uncached races.
  3. **Phase 6.3 T4 vs T5 Grid Penalty & Pit-Lane Audit (2024 Season, 24 Rounds):**
     - 15 of 24 races (62.5%) had confirmed starting grid changes relative to qualifying classification (penalties, gearbox drops, pit-lane starts).
     - In all 15 races with grid changes, the model probability vector shifted (mean L1 shift: 0.1650).
     - In the 9 non-penalty races, input grids were identical and output probabilities were bitwise identical ($\Delta \text{LogLoss} \equiv 0.0000$).
  4. **Phase 6.3 Model Objective Comparison (149 Races, 2018–2024):**
     - Variant A (Candidate-level Binary Logistic + Post-hoc Softmax): Mean Log Loss `1.3551`, Brier `0.6130`, Top-1 Acc `51.68%`, ECE `0.0548`.
     - Variant B (Grouped Conditional Logit MLE / Plackett-Luce Rank-1): Mean Log Loss `3.4011`, Brier `0.7964`, Top-1 Acc `25.50%`, ECE `0.0166`. Standard L2 penalty without race-count rescaling shrinks weights aggressively in grouped multinomial estimation. Variant A provides superior numerical stability and score.
  5. **Phase 6.2 Controlled Ablation (Invariant Model Family: L2 Logistic Regression C=1.0):**
     - **Cohort A (Universal Historical Benchmark, 149 races, 2018–2024):**
       - $T_0$ (Pre-Weekend Form): Mean Log Loss `1.5646`, Brier `0.6692`, Conv Top-1 Acc `53.02%`
       - $T_4$ (Post-Qualifying Grid + Form): Mean Log Loss `1.3551`, Brier `0.6130`, Conv Top-1 Acc `51.68%`
       - Transition $T_4 \text{ vs } T_0$: $\Delta \text{LogLoss} = -0.2095$ (95% CI: $[-0.3844, -0.0325]$, Wilcoxon $p = 0.00081$, Holm-Bonferroni $p = 0.00244$, **statistically significant**).
     - **Cohort C (Modern Complete Checkpoint Coverage, 34 Standard races, 2023–2024):**
       - $T_0$ (Pre-Weekend Form): Mean Log Loss `1.4190`, Brier `0.5858`, Conv Top-1 Acc `58.82%`
       - $T_4$ (Post-Qualifying Grid + Form): Mean Log Loss `0.9467`, Brier `0.4440`, Conv Top-1 Acc `70.59%`
       - Transition $T_4 \text{ vs } T_3$: $\Delta \text{LogLoss} = -0.4723$ (95% CI: $[-0.7798, -0.1329]$, Wilcoxon $p = 0.000457$, Holm-Bonferroni $p = 0.00274$, **statistically significant**).
     - **Cohort B (Modern Sprint Format, 12 races, 2023–2024):**
       - $T_0$: Mean Log Loss `1.9771`, Brier `0.9053`, Conv Top-1 Acc `33.33%`
       - $T_4$: Mean Log Loss `2.5126`, Brier `1.0917` (High volatility; single practice session format).
  2. **Best-in-Class Multi-Model Benchmark (EXP-0001 through EXP-0004 Comparison):**
     - $T_0$ (Model 1 — Elo Prior): Mean Log Loss `2.0588`, Brier `0.8053`
     - $T_4$ (Model 2 — Logistic Grid-only): Mean Log Loss `1.5942`, Brier `0.6834`
     - $T_5$ (Model 3 — Logistic Grid + Form): Mean Log Loss `1.3552`, Brier `0.6127`
     - $T_5$ (Model 5 — Plackett-Luce): Mean Log Loss `1.3517`, Brier `0.5966`
     - *Provenance Note:* Phase 6.1 evaluated lookups/rescoring from EXP-0001-R3, EXP-0002, and EXP-0004. Over two-thirds of the apparent $\Delta \text{LogLoss} = -0.7036$ was attributable to model family differences (Elo vs Logistic) rather than evidence arrival.
  3. **Single-Event Demonstration (2024 Abu Dhabi Grand Prix):**
     - $T_0$ (Pre-Weekend): Log Loss `1.3006`, Brier `0.6327`
     - $T_1$ (Post-FP1): Log Loss `1.5471`, Brier `0.7508` (Leclerc fastest; demonstrates short-term FP1 non-monotonicity)
     - $T_2$ (Post-FP2): Log Loss `1.1421`, Brier `0.5439` (incorporates representative race simulation pace)
     - $T_3$ (Post-FP3): Log Loss `1.3890`, Brier `0.6607` (incorporates FP3 qualifying-simulation pace)
     - $T_4$ (Post-Qualifying): Log Loss `0.3869`, Brier `0.1317` (provisional qualifying grid)
     - $T_5$ (Final Pre-Race Lock): Log Loss `0.3796`, Brier `0.1288` (Hülkenberg 3-place penalty applied)

---

### HYP-0002: Incremental Value of Free Practice Data
- **Rationale:** Long-run stints during Free Practice 2 (FP2) are traditionally used by teams to evaluate race-trim tire degradation under high fuel loads, offering predictive signals distinct from single-lap qualifying pace.
- **Null Hypothesis ($H_0$):** Adding FP2 long-run tire degradation slopes and fuel-adjusted stint pace to historical features does not improve pre-qualifying forecast log loss.
- **Alternative Hypothesis ($H_1$):** Models incorporating FP2 long-run degradation estimates achieve a measurable decrease in out-of-sample log loss compared to historical-only models prior to qualifying.
- **Required Data:** FastF1 lap-by-lap timing, tire compound designations, stint lap counts for FP2 sessions.
- **Proposed Comparison:** Historical baseline model vs. Historical + FP2 feature model (`EXP-0003`).
- **Primary Metrics:** Log Loss, Top-3 Podium ROC-AUC.
- **Status:** `PROPOSED`
- **Evidence References:** Pending execution of `EXP-0003` in Milestone 4.

---

### HYP-0003: Modality Parsimony & Telemetry Noise
- **Rationale:** Raw high-frequency telemetry (10–50 Hz speed, throttle, brake traces) may introduce high dimensionality and noise relative to the limited number of Grand Prix events per season, leading to overfitting unless heavily regularized or distilled.
- **Null Hypothesis ($H_0$):** Models augmented with raw high-frequency telemetry features achieve equal or superior out-of-sample Brier scores compared to models using aggregated timing metrics (sector speeds, corner minimum speeds, delta to pole).
- **Alternative Hypothesis ($H_1$):** Models augmented with raw high-frequency telemetry overfit the training seasons, resulting in worse out-of-sample Brier scores and higher calibration error than models using aggregated timing and degradation features alone.
- **Required Data:** FastF1 full telemetry traces vs. FastF1 lap/sector aggregated summary tables.
- **Proposed Comparison:** Aggregated timing model vs. High-frequency telemetry model (`EXP-0004` ablation).
- **Primary Metrics:** Brier Score, Expected Calibration Error (ECE), Log Loss.
- **Status:** `PROPOSED`
- **Evidence References:** Pending execution of `EXP-0004` in Milestone 4.

---

### HYP-0004: Checkpoint Calibration Drift
- **Rationale:** Early forecast checkpoints (Pre-Weekend) carry high epistemic uncertainty, whereas late checkpoints (Post-Qualifying, Live Lap 20) are dominated by track position and grid order. Without explicit calibration, late-checkpoint models may become overconfident.
- **Null Hypothesis ($H_0$):** Uncalibrated model outputs maintain uniform calibration error across all weekend forecast checkpoints.
- **Alternative Hypothesis ($H_1$):** Expected Calibration Error increases significantly at late checkpoints (Post-Qualifying, Live Race) unless post-hoc calibration (e.g., isotonic regression or temperature scaling) is applied.
- **Required Data:** Out-of-sample probability outputs across all checkpoints T0 through T5.
- **Proposed Comparison:** Uncalibrated vs. Calibrated probabilities across checkpoints (`EXP-0005`).
- **Primary Metrics:** Expected Calibration Error (ECE), Maximum Calibration Error (MCE), Reliability Diagrams.
- **Status:** `PROPOSED`
- **Evidence References:** Pending execution of `EXP-0005` in Milestone 4/5.

---

### HYP-GRID-001: Pre-Race Grid Position Dominance
- **Rationale:** Starting grid position is historically the single most informative static feature for predicting Formula 1 Grand Prix winners. Conditioning forecasts on final starting grid order at $T_5$ should substantially outperform static pre-weekend rating baselines (such as the Elo baseline in `EXP-0001`) under strictly proper scoring rules.
- **Null Hypothesis ($H_0$):** A model conditioned on starting grid position alone ($P(\text{Win} \mid \text{Grid})$) does not achieve a statistically significant reduction in multi-class Brier score or log loss compared to the $T_0$ pre-weekend Elo baseline ($p \ge 0.05$ under a paired Wilcoxon signed-rank test across test rounds).
- **Alternative Hypothesis ($H_1$):** A starting grid-conditioned model achieves statistically significant lower multi-class Brier score and log loss than the pre-weekend Elo baseline ($p < 0.05$).
- **Required Data:** Multi-season historical starting grid positions and race winners (2010–2026, audited in `docs/research/CANDIDATE_FIELD_AUDIT.md`).
- **Proposed Comparison:** Static Pre-Weekend Elo (`EXP-0001-R3`) vs. Empirical Grid Baseline vs. Pre-Race GBDT (`EXP-0002`).
- **Primary Metrics:** Multi-Class Log Loss, Multi-Class Brier Score, Tie-Aware Top-1 Accuracy.
- **Status:** `PROPOSED`
- **Evidence References:** Pending execution of `EXP-0002` in `notebooks/05_static_grid_benchmark.ipynb`.

---

### HYP-GRID-002: Nonlinear Grid Representation Superiority
- **Rationale:** Historical win probability drops sharply and non-linearly with grid position: pole position (P1) and P2 capture the overwhelming majority of race wins, P3–P6 win occasionally, and P7+ exhibit heavy right-tail scarcity. Tree-based ensembles (LightGBM) or regularized multinomial logit models parameterized with nonlinear grid transformations ($\log(\text{grid})$, front-row indicator, team championship standings) will generalize better and achieve superior probability calibration than raw linear grid representations or unregularized empirical frequency tables.
- **Null Hypothesis ($H_0$):** A GBDT or regularized multinomial logit model incorporating nonlinear grid transformations and team context does not achieve lower out-of-sample log loss or Brier score than a smoothed empirical grid frequency table ($p \ge 0.05$).
- **Alternative Hypothesis ($H_1$):** Nonlinear modeling (multinomial logit / GBDT) achieves statistically significant lower log loss and superior probability calibration compared to smoothed empirical grid frequencies ($p < 0.05$).
- **Required Data:** Starting grid positions, constructor standings, and race winners (2018–2024 primary benchmark cohort; 2010–2017 warm-up).
- **Proposed Comparison:** Empirical Grid Baseline vs. Multinomial Logit Softmax vs. Pre-Race LightGBM (`EXP-0002`).
- **Primary Metrics:** Multi-Class Log Loss, Multi-Class Brier Score, Expected Calibration Error (ECE).
- **Status:** `PROPOSED`
- **Evidence References:** Pending execution of `EXP-0002` in `notebooks/05_static_grid_benchmark.ipynb`.

---

### HYP-STRAT-001: Counterfactual Strategy & Tactical Gain
- **Rationale:** While outcome forecasting models output probability distributions over the entire field ($P(\mathbf{Y} \mid \mathcal{I}_T)$), individual race outcomes are heavily governed by discrete tactical pit stop decisions under multi-car traffic and safety car hazards. Incorporating dynamic multi-agent interaction features (such as `Gap Ahead`, `Tyre Degradation`, and competitor pit triggers `DriverAheadPit`) into a downstream strategy simulation model allows discovering emergent tactics (e.g. undercut windows and extended hard-tire stints) that yield statistically significant rank improvements over fixed, pre-computed pit schedules.
- **Null Hypothesis ($H_0$):** In a calibrated Monte Carlo race simulation environment (calibrated against 2018–2024 races), dynamic strategy agents (Open-Loop MCTS or DRQN) achieve no statistically significant improvement in simulated finishing position compared to fixed baseline strategies derived from pre-race tire degradation curves ($p \ge 0.05$ under a paired Wilcoxon signed-rank test).
- **Alternative Hypothesis ($H_1$):** Dynamic strategy models taking into account live traffic gaps, competitor pit reactions, and safety car hazard probabilities achieve statistically significant finishing position gains over fixed baseline strategies ($p < 0.05$).
- **Theoretical Precedents:**
  - Thomas et al. (2026, *Machine Learning*): Demonstrated that an RL agent (RSRL) learning emergent undercuts achieved P5.33 vs Fixed Strategy P5.63 in the 2023 Bahrain GP over 1,920 Monte Carlo simulations.
  - Piccinotti et al. (2021, *PRL ICAPS*): Open-Loop MCTS with Q-learning TD updates outperformed hand-crafted strategies in 7 of 10 Grand Prix races.
  - Heilmeier et al. (2020, *Appl. Sci.*): Virtual Strategy Engineer improved average finishing rank under stochastic Safety Car phases from P3.5 to P2.7.
- **Required Data:** Lap-by-lap race timing, tire compound designations, stint lengths, and track status records from FastF1 / OpenF1.
- **Proposed Comparison:** Hand-crafted Stint Baseline vs. Open-Loop MCTS / DRQN Simulation Agent (`EXP-0006`).
- **Primary Metrics:** Simulated Finishing Rank, Cumulative Stint Race Time (s), Time Regret (s), Win Probability (%).
- **Status:** `SUPPORTED_UNDER_SIMULATION_CONDITIONS` (Evaluated in Phase 7 & 7.2 via `EXP-0006` with Common Random Numbers across 10,000 paired draws on 2024 Abu Dhabi GP, supported by holdout Set A vs Set B validation and historical smoke test across Abu Dhabi, Silverstone, and Bahrain).
- **Evidence References:**
  1. **EXP-0006 Final Closeout 10,000 Paired Draws Strategy Robustness & Multi-Seed CRN Validation (Abu Dhabi 2024):**
     - Target: Lando Norris (McLaren, Starting Grid P1, Master Seed 42, $N=10,000$).
     - `SafetyCar_Reactive`: Expected Position `3.743` (SE `0.043`), Win Prob `33.29%` (SE `0.47%`), Podium Prob `71.80%`, Top-5 `85.39%`, Completed Race Mean Time `5188.725s` (std `119.3s`), All-Runs Mean Time `4906.564s` (std `1038.2s`), DNF Rate `8.87%` (887 runs), Pit Stops `1.56`.
     - `Reference_1Stop`: Expected Position `3.812` (SE `0.041`), Win Prob `17.50%` (SE `0.38%`), Podium Prob `72.90%`, Top-5 `88.81%`, Completed Race Mean Time `5190.264s` (std `118.6s`), All-Runs Mean Time `4907.925s` (std `1038.6s`), DNF Rate `8.87%` (887 runs), Pit Stops `0.96`.
     - `Tactical_Overcut`: Expected Position `4.308` (SE `0.042`), Win Prob `19.32%` (SE `0.39%`).
     - `Tactical_Undercut`: Expected Position `4.633` (SE `0.043`), Win Prob `13.87%` (SE `0.35%`).
     - `Aggressive_2Stop`: Expected Position `4.804` (SE `0.042`), Win Prob `17.65%` (SE `0.38%`).
     - Race-Time Calibration & Provenance: Both policies match official 2024 Abu Dhabi GP winner Lando Norris (,193.291	ext{s}$) within $< 0.1\%$ error (569X3.03	ext{s}$ for 1-Stop; 569X4.57	ext{s}$ for SC-Reactive). Unconditional all-runs mean ($pprox 4,907	ext{s}$) includes the 887 retirements. Numerical integrity audit confirms the arithmetic weighted-mean identity holds to machine precision ($|all\_run\_mean - weighted| \le 9.09 	imes 10^{-13}	ext{s}$), with mechanical DNFs spanning laps 1–58 (mean lap 22.87, DNF mean elapsed time 2,007.19s), resolving an earlier prose note that inaccurately claimed DNFs stopped at lap 15. Standing start physical launch delay adds 0.8	ext{s}$ on Lap 1.
     - SC/VSC Transition Reconciliation: 1,284 raw race-control messages audited and reconciled into 258 direct green SCs, 180 green VSCs (128 standalone + 52 VSC-to-SC escalations), 1 pre-race, 310 SC returns, 128 VSC returns, and 355 duplicate notices. Initiation hazards calibrated against eligible green laps ({	ext{green}} = 19,420$ for SC; ,558$ for VSC).
     - Paired Race-Time Differences: On all $N=10,000$ runs, paired difference is $-1.361\text{s}$ (SE 0.0882s). On the 9,113 matched runs where both policies finish, paired difference is **$-1.539\text{s}$** (SE 0.0935s, 95% CI: $[-1.722, -1.355]$). Exactly 0 runs had asymmetric retirements. Prior text discrepancy citing $-16.36\text{s}$ is fully resolved.
     - Multi-Objective Trade-Offs: `SafetyCar_Reactive` maximizes Win % (33.29%) and minimizes Expected Position (P3.743); `Reference_1Stop` maximizes Podium % (72.90%) and Top-5 % (88.81%) with lower outcome variance ($\sigma = 2.81$). Head-to-head win rate on decisive runs shows `SafetyCar_Reactive` beats 1-stop in 59.07% of non-tied finishes (31.34% on all runs vs 21.72% for 1-stop, 46.94% tied).
     - Paired contrast `SafetyCar_Reactive` vs `Reference_1Stop`: $\Delta_{\text{pos}} = -0.069$ (SE `0.0176`, 95% CI: $[-0.104, -0.034]$, raw $p = 9 \times 10^{-5}$, step-down Holm-Bonferroni adjusted $p = 9 \times 10^{-5}$, **statistically significant**).
     - Multi-seed CRN audit across 5 independent master seeds (`[42, 101, 777, 1337, 2024]`): Mean race-time difference variance reduction **99.996%** (95% CI: $[99.996\%, 99.997\%]$, mean $\rho = 0.99996$); mean position difference variance reduction **90.64%** (95% CI: $[89.58\%, 91.68\%]$). Two-sample Kolmogorov-Smirnov tests confirm no statistically detectable marginal distribution difference in the tested samples ($p \ge 0.498, D \le 0.052 \le 0.060$).
  2. **Holdout Strategy Selection vs. Frozen Out-of-Sample Evaluation (Phase 7.2):**
     - Set A Selection ($N=2,500$, seed 42): `SafetyCar_Reactive` selected with $E[\text{pos}] = 3.748$, Win Prob $33.8\%$.
     - Set B Evaluation ($N=2,500$, seed 99991): `SafetyCar_Reactive` achieved $E[\text{pos}] = 3.541$, Win Prob $35.3\%$, beating 1-stop with $\Delta_{\text{pos}} = -0.121$ ($p = 0.00045$, Holm-Bonferroni $p = 0.00045$).
     - Theoretical Ex-Post Oracle on Set B: $E[\text{pos}] = 2.838$, Win Prob $44.4\%$. Online position regret is $+0.703$ positions.
  3. **Parameter Sensitivity & Boundary Conditions (Phase 7.1 & 7.2 Sweeps):**
     - Neutralisation Hazard Sweep: At `sc_scale = 0.0x` (zero safety cars), `SafetyCar_Reactive` loses its advantage (Exp Pos P3.49 vs 1-Stop P3.50, Win Prob 13% vs 12%), demonstrating that its superiority is conditional on neutralisation frequency and incurs time regret when holding degrading tyres waiting for a caution.
     - Tyre Degradation Sweep: At `deg_scale = 1.5x`, `Aggressive_2Stop` win probability surges from 12% to **27%**, outperforming the 1-Stop (17%), as high tyre wear causes 1-stoppers to enter quadratic cliff penalties.
     - Pit Transit Sweep: As transit loss increases from 16s to 25s, 2-stop win probability drops from 18% to 6%.
  4. **Historical Simulation Backtest Smoke Test (3 Grand Prix Cohort):**
     - Abu Dhabi 2024 (Round 24): Winner Norris, $p = 0.1600$, Log Loss $-\ln(0.1600) = \mathbf{1.8326}$, Brier $\mathbf{1.0689}$.
     - British GP 2024 (Round 12): Winner Hamilton, $p = 0.1200$, Log Loss $-\ln(0.1200) = \mathbf{2.1203}$, Brier $\mathbf{1.2719}$.
     - Bahrain GP 2024 (Round 1): Winner Verstappen, $p = 0.8267$, Log Loss $-\ln(0.8267) = \mathbf{0.1903}$, Brier $\mathbf{0.0504}$.
     - Cohort Mean: Log Loss $\mathbf{1.3811}$, Brier $\mathbf{0.7971}$, Top-1 Accuracy $\mathbf{33.33\%}$, MAE $\mathbf{3.45}$ positions.
     - Artifacts: `artifacts/reports/EXP-0006/historical_simulation_backtest.json`, `artifacts/reports/EXP-0006/exp_0006_v2_strategy_robustness_10000.json`, `artifacts/reports/EXP-0006/crn_variance_reduction_validation.json`, `artifacts/reports/EXP-0006/holdout_strategy_evaluation.json`, `artifacts/reports/EXP-0006/fuel_tyre_sensitivity_qualification.json`, `artifacts/reports/EXP-0006/simulation_experiment_summary.json`.
  5. **Methodological Note:** Status is strictly labelled `SUPPORTED_UNDER_SIMULATION_CONDITIONS` to reflect that fuel mass burn-off (1.75 kg/lap, 0.033 s/kg) is an assumed latent parameter, safety car hazard rates are empirical priors, and tyre degradation slopes follow calibrated model curves rather than full live sensor feeds.


