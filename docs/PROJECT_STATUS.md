# APEX — F1 Intelligence: Project Status

**Last Updated:** 2026-11-06  
**Current Phase:** EXP-0006 SC/VSC Final Methodology Correction & Phase 8 Authorization (Completed & Authorized)  
**Overall Status:** GREEN (EXP-0006 final methodology correction completed and authorized; weighted-mean arithmetic identity verified to machine precision [residual <= 9.09e-13s]; raw-message accounting strictly separated into Table A [1,284 mutually exclusive source broadcast records: 311 SC deployed, 180 VSC deployed, 310 SC ending, 128 VSC ending, 355 status notices = 1,284] from Table B [438 on-track event lifecycles: 258 direct green SC, 180 green VSC partitioned into 52 escalations and 128 standalone conclusions, 310 SC conclusions, 1 pre-race]; green-state initiation hazards strictly distinguished [direct green SC 258/19,420 = 0.01328; green VSC 180/13,558 = 0.01328; conditional escalation 52/180 = 0.28889; 310/19,420 labeled as descriptive aggregate phase ratio]; explicit VSC->SC escalation implemented in simulator with orthogonal random stream [master_seed+8089] and neutralisation guard; versioned artifact exp_0006_final_closeout_v3.json published; 126 tests passing; clean Next.js build; Phase 8 authorized)

---

## 1. Executive Summary

APEX has completed foundational repository setup (Milestone 0), empirical provider data audits (Milestone 1), pre-race candidate-field reconstruction audits, and comprehensive static pre-race forecasting benchmarks under `EXP-0002` (Milestone 3).

Following the **Notebook-First Research Workflow**:
- The **Project Owner, ChatGPT, and Antigravity** have collaboratively implemented, audited, and verified 5 distinct model families in `notebooks/05_static_grid_benchmark.ipynb`.
- Strict chronological walk-forward evaluation (2010–2026, 346 races, 7,285 candidate records) was enforced with zero temporal leakage.
- All models were scored on the prespecified **Primary Benchmark Cohort (2018–2024, 149 rounds)** using strictly proper scoring rules (multiclass log loss and Brier score) alongside fractional and tie-aware top-1 accuracy.

**Key Empirical Finding:**
Model 3 (Grid + Driver/Constructor Form Logistic Regression) achieves the strongest probabilistic forecasting performance (Primary Log Loss: `1.355201`, Brier: `0.612698`). While Model 4 (LightGBM GBDT) achieves slightly higher argmax accuracy (`53.02%` vs `51.68%`), it is inferior under strictly proper scoring rules (Log Loss: `1.409149`, Brier: `0.628561`), demonstrating that gradient boosting without specialized probability calibration produces overconfident probability tails in candidate simplexes.

---

## 2. Milestone Progress Tracker

| Milestone | Title | Status | Target Completion | Progress Notes |
|---|---|---|---|---|
| **Phase 0** | **Master Architecture & Data-Readiness Audit** | **COMPLETED** | 2026-11-04 | Platform blueprint, provider licensing, 2026 regulations, checkpoint lifecycle, and threat model delivered. |
| **M0** | **Project Initialization & Documentation Foundation** | **COMPLETED** | 2026-10-18 | Scaffolding complete; Markdown documentation and 114 internal links verified. |
| **M1** | **Data Availability, Research Specification & Notebook Source Validation** | **COMPLETED** | 2026-10-19 | Audit scripts complete; ADR-0002 approved; `notebooks/00` and `01` verified; candidate field audit complete (`CANDIDATE_FIELD_AUDIT.md`). |
| **M2 / Phase 1** | **Data Pipeline, Ingestion & Backend Foundation** | **COMPLETED** | 2026-11-05 | FastAPI modular monolith (`backend/`), PostgreSQL relational schema via Alembic migrations, Jolpica & OpenF1 adapters, idempotent ingestion service validated on 2024 Abu Dhabi GP, REST API v1 (`/api/v1`), minimal Next.js typed client, and 19 passing tests. |
| **Phase 2** | **Circuit Geometry & Multi-Circuit Race Replay Engine** | **COMPLETED** | 2026-11-05 | Multi-circuit geometry registry (`backend/geometry/`) with Yas Marina and Silverstone cross-validated centerline models, turn markers, sectors, and provenance metadata; analytical Parquet replay partitions (`positions.parquet`, `telemetry.parquet`). Explicitly verified and labeled as `OPENING_LAP_REPLAY_WINDOW` (1.35% for Abu Dhabi, 0.85% for Silverstone); causal replay engine with zero lookahead; interactive 60fps HTML5 Canvas track map supporting dynamic event switching, driver-following mode, and zoom controls. Replay audit confirms 0 NaN values, 0 duplicate timestamps, and uniform ~3.8 Hz telemetry cadence. |
| **M3** | **Static Baseline Forecasting & Proper Scoring Benchmarks** | **COMPLETED** | 2026-11-04 | Pre-weekend Elo (`EXP-0001-R3`), calibration audit (`EXP-0001-CAL-001`), pre-race grid benchmarks Models 0–4 (`EXP-0002`), calibration benchmark (`EXP-0003`), and Plackett-Luce Model 5 (`EXP-0004`). |
| Phase 3 | Live Data & Real-Time Track Map | NOT STARTED | Future | WebSocket fan-out, live timing tower, stale-feed handling. |
| **Phase 4 (Reg. Engine)** | **2026 Regulation Intelligence Registry** | **COMPLETED** | 2026-11-05 | Effective-dated technical/sporting rules engine (`backend/regulations/`) audited against official FIA Category 2182 (Issue 21, published 19 Oct 2026). Correctly separates dual-temp 16.0:1 compression ratio (ambient through 31 May 2026, dual-temp ambient+130°C from 1 June 2026), Miami GP amendments (recharge 8.0 MJ -> 7.0 MJ, peak superclip 250 kW -> 350 kW), fuel energy flow (3000 MJ/h), and aerodynamic modes (Corner Mode / Straight Mode). REST API v1 (`/api/v1/regulations`). |
| **Phase 5 (Practice Pipeline)** | **Practice Session Feature Pipelines ($T_1 \dots T_3$)** | **COMPLETED** | 2026-11-05 | Point-in-time practice intelligence pipeline (`backend/features/practice.py`) extracting single-lap pace, trimmed means, best sectors, theoretical best lap, and long-run stint degradation slopes. Constructs immutable sequential snapshots (T1: Post-FP1, T2: Post-FP2, T3: Post-FP3) with strict temporal cutoffs, unmeasured fuel-confounding caveats, and automated `TemporalLeakageError` anti-leakage checks. |
| **Phase 6 / 6.1 / 6.2 / 6.3 / 6.3.1** | **Multi-Checkpoint Forecasting Engine, Practice Audit & Metric Reconciliation** | **COMPLETED** | 2026-11-05 | Point-in-time sequential probabilistic forecasting engine (`backend/forecasting/engine.py`, `evaluator.py`, `backtest.py`, `controlled_ablation.py`, `practice_subset_ablation.py`, `grid_penalty_audit.py`, `model_objective_comparison.py`, `replay_ledger.py`, `/api/v1/predictions`). Implements exact Plackett-Luce rank marginals guaranteeing mathematical consistency ($\sum p_{\text{podium}} = 3.0$, $\sum p_{\text{top5}} = 5.0$, $\sum E[\text{pos}] = N(N+1)/2$). Comprehensive provenance audit published in `PROVENANCE_AUDIT.md`. Canonical per-race prediction ledger v1 (1,043 rows) and extended ledger v2 (447 rows with exact weights, parameters, and deterministic replay verified on all 447 records $\le 3.3 \times 10^{-7}$). Reconciled Abu Dhabi 2024 session identity (FP1 9461), FP1 driver substitutions (Hadjar #37, Verstappen missing), exact pace/degradation features, race-level log loss $-\ln(p_{\text{winner}})$ strictly verified, 20-driver full entrant field and 4-driver contender study decoupled, T4 vs T5 audit reconciled with Phase 6.2. 73 passing tests. |
| **Phase 7 / 7.1 / 7.2 / 7.2.1 / EXP-0006 Closeout & Gate** | **Monte Carlo Race & Strategy Dynamics Simulator (EXP-0006 Final Closeout & Phase 8 Gate)** | **COMPLETED & AUTHORIZED** | 2026-11-06 | Stochastic discrete-lap simulator (`backend/simulation/`) with decoupled exogenous random streams (`scenario.py`) for Common Random Numbers (CRN), achieving 99.997% variance reduction in paired race time difference across 5 master seeds (mean $\rho=0.99996$) and 92.33% position difference variance reduction. Full 10,000 paired draws across 5 strategies with Holm-Bonferroni adjusted $p$-values. CRN marginal equivalence audited via two-sample KS tests confirming no statistically detectable difference ($p \ge 0.498, D \le 0.052 \le 0.060$). Numerical integrity audit confirms race-time weighted-mean identity to machine precision ($|all\_run\_mean - weighted| \le 9.09 \times 10^{-13}$s), proving root cause of prior ~2,007s discrepancy was an erroneous prose note asserting DNFs only occur on laps 1-15, whereas simulation models failures across all laps 1-58 (mean lap 22.87, times 0.0s to 5,571.66s). Matched completed-runs evaluated on 9,113 runs with zero asymmetric DNF (both finished in 91.13%, both retired in 8.87%). SC/VSC methodology correction separates raw message accounting (Table A: 1,284 mutually exclusive records: 311 SC deploy, 180 VSC deploy, 310 SC end, 128 VSC end, 355 notices) from derived event lifecycles (Table B: 258 direct green SC, 180 green VSC [128 standalone, 52 escalations], 310 SC conclusions, 1 pre-race). Calibrated green initiation hazards strictly distinguished (direct green SC $258 / 19,420 = 0.01328$, green VSC $180 / 13,558 = 0.01328$, conditional escalation $52 / 180 = 0.28889$, while $310 / 19,420$ is labeled strictly as descriptive aggregate phase ratio). Explicit VSC->SC escalation implemented in `engine.py` using orthogonal random stream (`master_seed+8089`), preventing double counting. Versioned closeout artifacts published (`exp_0006_final_closeout.json`, `exp_0006_final_closeout_v2.json`, `exp_0006_final_closeout_v3.json`). 126 tests passing; clean frontend build; Phase 8 authorized. |
| Phase 8 | Research Model Benchmarks & Paper Traceability | NOT STARTED | Future | Shared pipeline experiments, LambdaMART, research paper compilation. |
| Phase 9 | Integrated APEX Web Terminal | NOT STARTED | Future | Next.js production frontend, 11 analytical views, Model Lab. |

---

## 3. Verified Benchmark Results Overview

### Pre-Race Benchmark (`EXP-0002` & `EXP-0004`, Primary Cohort: 2018–2024, 149 Races)

| Model | Architecture | Primary Log Loss | Primary Brier Score | Primary Fract. Top-1 | Full Series Log Loss (346 races) | Artifact Path |
|---|---|---:|---:|---:|---:|---|
| **Model 0** | Uniform Baseline ($1 / N_r$) | `2.995388` | `0.949982` | `0.050018` | `3.044556` | In-memory baseline |
| **Model 1** | Empirical Grid Frequency (Laplace $\alpha=10$) | `1.583766` | `0.682312` | `0.496644` | `1.519516` | `artifacts/reports/EXP-0002/model1_grid_frequency_predictions.csv` |
| **Model 2** | Grid-Only Logistic Regression (5 features) | `1.594207` | `0.683382` | `0.496644` | `1.541942` | `artifacts/reports/EXP-0002/model2_logistic_predictions.csv` |
| **Model 3** | Grid + Form Logistic Regression (16 features) | `1.355201` | `0.612698` | `0.516779` | **`1.419383`** | `artifacts/reports/EXP-0002/model3_driver_constructor_predictions.csv` |
| **Model 4** | LightGBM GBDT (16 features) | `1.409149` | `0.628561` | `0.530201` | `1.522650` | `artifacts/reports/EXP-0002/model4_lightgbm_predictions.csv` |
| **Model 5** | Plackett-Luce / Conditional Logit (16 features) | **`1.351747`** | **`0.596564`** | **`0.543624`** | `1.440419` | `artifacts/reports/EXP-0004/model5_predictions.csv` |

### Post-Hoc Calibration Benchmark (`EXP-0003`, Primary Cohort: 2018–2024, 149 Races)

| Model & Calibration Variant | Primary Log Loss | Primary Brier Score | Fract. Top-1 | Fixed-Bin ECE | Status / Finding |
|---|---:|---:|---:|---:|---|
| **Model 3 (Logistic) — Raw** | **`1.355201`** | **`0.612698`** | 0.516779 | 0.009618 | Baseline reference; naturally calibrated |
| Model 3 (Logistic) — Platt | 1.357407 | 0.613388 | 0.516779 | 0.009385 | Negligible change ($\Delta \text{LogLoss} = +0.0022$) |
| Model 3 (Logistic) — Isotonic | 1.403784 | 0.613623 | **0.533557** | **0.005006** | Degrades log loss via step-function tail penalty |
| Model 3 (Logistic) — Temperature ($T \approx 1.007$) | 1.357764 | 0.613515 | 0.516779 | 0.009560 | Neutral ($T \approx 1.0$) |
| **Model 4 (LightGBM) — Raw** | 1.409149 | 0.628561 | 0.530201 | 0.013875 | Uncalibrated overconfident GBDT baseline |
| Model 4 (LightGBM) — Platt | 1.388663 | **0.622523** | 0.530201 | **0.007314** | Substantial gain ($\Delta \text{LogLoss} = -0.0205$, $\Delta \text{Brier} = -0.0060$) |
| Model 4 (LightGBM) — Isotonic | 1.450040 | 0.623208 | 0.528523 | 0.007846 | Severely degrades log loss |
| Model 4 (LightGBM) — Temperature ($T \approx 1.360$) | **`1.387587`** | 0.623285 | 0.530201 | 0.007818 | Best calibrated GBDT ($\Delta \text{LogLoss} = -0.0216$) |

---

## 4. Completed Tasks

- [x] Environment inspection and directory validation (`apex-f1` path verified without invalid nesting).
- [x] Git local initialization targeting `https://github.com/Dhruv-vm/apex-f1-intelligence.git`.
- [x] Repository hygiene: comprehensive `.gitignore` and `.env.example` template.
- [x] Persistent AI instructions established in [AGENTS.md](../AGENTS.md), including Notebook-First Collaboration Workflow.
- [x] Empirical provider audit scripts executed across Jolpica, OpenF1, and FastF1 (`artifacts/reports/data_availability_audit_summary.json`).
- [x] Multi-season coverage matrix published in [docs/research/DATA_AVAILABILITY_AUDIT.md](research/DATA_AVAILABILITY_AUDIT.md).
- [x] [ADR-0002](decisions/ADR-0002-data-provider-selection-and-telemetry-strategy.md) approved.
- [x] Collaborative research notebook environment established in `notebooks/`.
- [x] `EXP-0001-R3`: Walk-forward outcome-independent Elo baseline executed (`artifacts/reports/EXP-0001-R3/`).
- [x] `EXP-0001-CAL-001`: Candidate probability calibration audit completed (ECE: `0.030667`, CITL: `0.000000`).
- [x] Pre-race candidate-field audit published in [docs/research/CANDIDATE_FIELD_AUDIT.md](research/CANDIDATE_FIELD_AUDIT.md).
- [x] `EXP-0002`: Models 0, 1, 2, 3, and 4 implemented, executed, and validated in [notebooks/05_static_grid_benchmark.ipynb](../notebooks/05_static_grid_benchmark.ipynb).
- [x] `EXP-0003`: Walk-forward probability calibration benchmark implemented and executed in [notebooks/06_probability_calibration.ipynb](../notebooks/06_probability_calibration.ipynb); artifacts serialized to `artifacts/reports/EXP-0003/`.
- [x] `EXP-0004`: Direct race-level winner probability model (Model 5 Plackett-Luce / Conditional Logit) implemented in [notebooks/07_plackett_luce_ranking.ipynb](../notebooks/07_plackett_luce_ranking.ipynb); artifacts serialized to `artifacts/reports/EXP-0004/`.
- [x] Permanent Research Documentation Workflow established:
  - [docs/RESEARCH_LOG.md](RESEARCH_LOG.md)
  - [docs/EXPERIMENT_REGISTRY.md](EXPERIMENT_REGISTRY.md)
  - [docs/PAPER_TRACEABILITY.md](PAPER_TRACEABILITY.md)
  - [docs/DECISION_LOG.md](DECISION_LOG.md)
  - [docs/DATA_DICTIONARY.md](DATA_DICTIONARY.md)
  - [docs/KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md)
- [x] Phase 1 Backend Foundation implemented and validated:
  - FastAPI modular monolith (`backend/main.py`, `backend/config.py`, `backend/exceptions.py`, `backend/logging_config.py`).
  - Canonical PostgreSQL schema (`seasons`, `circuits`, `events`, `sessions`, `drivers`, `constructors`, `race_results`, `ingestion_logs`) managed via Alembic (`alembic/versions/4f3f929d8b0e_create_canonical_f1_entities.py`).
  - Provider adapters for Jolpica, OpenF1, and FastF1 with local disk caching, exponential backoff retries, and client throttling.
  - Idempotent historical ingestion pipeline validated against the 2024 Abu Dhabi Grand Prix (20 classified results, 5 sessions, deterministic payload hashing).
  - REST API v1 (`/health`, `/ready`, `/seasons`, `/events`, `/events/{id}`, `/events/{id}/sessions`, `/sessions/{id}`, `/events/{id}/results`, `/admin/ingestion/events/{event_id}`).
  - Admin ingestion protection via `X-Admin-Key` header verification.
  - Minimal Next.js frontend integration with typed API client (`frontend/src/lib/api-client.ts`) displaying live health status, event selector, sessions breakdown, and classification table.
  - Multi-Circuit Replay & Geometry Engine (`backend/geometry/`, `backend/replay/`) with Parquet partitions and 60fps HTML5 Canvas track map. Empirical audit confirmed cached datasets represent opening-lap replay windows (1.35% / 0.85% of full race).
  - 2026 Regulation Intelligence Registry (`backend/regulations/`) audited against official FIA Category 2182 (Issue 21, 19 Oct 2026) with dual-dated 16:1 compression ratio timeline and Miami GP energy amendments.
  - Practice Feature Pipelines ($T_1 \dots T_3$) (`backend/features/practice.py`) with strict anti-leakage guards and fuel-confounding caveats.
  - Multi-Checkpoint Forecasting Engine ($T_0 \dots T_5$) (`backend/forecasting/`) with exact Plackett-Luce rank marginals for Win, Podium, Top 5, and Expected Position.
  - Phase 6.1 Historical Walk-Forward Forecast Validation (`backend/forecasting/backtest.py`, `EXP-0005`):
    - Audited historical session availability across the 149-race primary benchmark cohort (2018–2024).
    - Executed strict chronological walk-forward backtest comparing $T_0$, $T_4$, and $T_5$ with zero future leakage.
    - Evaluated separated conventional top-1 accuracy (0/1 binary hit rate) vs fractional winner credit.
    - Statistically confirmed HYP-0001 (Sequential Information Superiority) via paired Wilcoxon signed-rank test ($p = 1.22 \times 10^{-12}$) and 2,000-replicate race-clustered paired bootstrap 95% CIs.
    - Subgroup breakdowns published across Ground Effect era (2022–2024, 68 races) vs Turbo-Hybrid era (2018–2021, 81 races) and season-by-season.
  - Phase 6.3 Practice Feature Validation, Prediction Sensitivity & Model Provenance (`backend/features/practice_audit.py`, `backend/forecasting/practice_subset_ablation.py`, `grid_penalty_audit.py`, `model_objective_comparison.py`, `replay_ledger.py`):
    - Audited FP1, FP2, and FP3 across all 34 standard weekends in 2023–2024 (102 sessions total); established that 99 sessions exist on OpenF1 but only 3 sessions (2.9%) are locally cached (`practice_coverage_audit_34_weekends.csv`).
    - Traced end-to-end T0–T3 feature flow: revealed that neutral 0.0 imputation across uncached sessions produces zero variance, zero standardized features, and L2 regularization shrinking fitted practice weights to exactly $\beta = 0.000000$, resulting in identical probabilities.
    - Evaluated genuine observed practice subset (Abu Dhabi 2024 without imputation): proved practice features improve log loss ($T_0$: 1.3341 $\rightarrow T_1$: 1.2536 $\rightarrow T_2$: 0.7547 $\rightarrow T_3$: 0.7256) while capturing Friday fuel-confounded non-monotonicity.
    - Conducted 2024 season audit of T4 vs T5: identified grid changes in 15 of 24 races (62.5%), shifting candidate probabilities across all 15 races, while non-penalty races are bitwise identical.
    - Extended prediction ledger v2 (`prediction_ledger_v2.jsonl`, 447 rows) with full provenance, exact coefficients, and deterministic replay verification reproducing probabilities within $2.24 \times 10^{-7}$ ($\le 10^{-5}$ tolerance).
    - Compared candidate-level binary logistic + softmax vs race-level conditional logit MLE solver on identical chronological walk-forward splits.
    - Reassessed HYP-0001: maintained `PARTIALLY SUPPORTED` (qualifying grid strongly supported; practice pace/deg demonstrated on verified subset but unverified across multi-season cohorts pending full practice ingestion).
  - Phase 6.3.1 Critical Practice Data & Metric Reconciliation (`backend/features/practice.py`, `backend/forecasting/practice_subset_ablation.py`, `grid_penalty_audit.py`, `replay_ledger.py`):
    - Reconciled Abu Dhabi 2024 session identity: confirmed FP1 is OpenF1 session 9461 (resolving the 9641 transcription typo), FP2 is 9656, FP3 is 9657.
    - Implemented rigorous driver substitution handling: car 37 was piloted by rookie Isack Hadjar in FP1; Max Verstappen did not drive FP1. Verstappen's FP1 telemetry is strictly marked missing (missing=1.0, pace_delta=None), eliminating fabricated defaults or Hadjar pace leakage.
    - Reconciled practice lap pace and stint degradation metrics from raw observations: Leclerc 84.321s, Norris 84.542s (+0.221s), Hamilton 84.806s (+0.485s).
    - Mathematically verified race-level multiclass log loss strictly equals $-\ln(p_{\text{winner}})$ on both 20-driver full entrant simplex and 4-driver restricted contender study. Candidate-level BCE is preserved under its true name (`candidate_level_bce`).
    - Reconciled Phase 6.2 vs Phase 6.3 T4/T5 grid change findings: Phase 6.2 evaluated identical inputs by construction, while Phase 6.3 separated provisional qualifying from confirmed starting grid (shifting probabilities in 15 of 24 rounds in 2024).
    - Verified deterministic replay across all 447 records in `prediction_ledger_v2.jsonl` (447/447 matches, maximum absolute probability difference $3.298 \times 10^{-7} \le 10^{-5}$).
    - Demonstrated that with nested chronological regularization tuning, Conditional Logit MLE achieves Log Loss 1.3526, matching Binary Logistic + Softmax (1.3551).
  - Phase 7 Monte Carlo Race & Strategy Dynamics Simulator (`backend/simulation/`, `artifacts/reports/EXP-0006/`):
    - Implemented stochastic discrete-lap race simulator modeling non-linear tyre wear, pit transit/service losses, FIA Art 30.5 compliance, safety car deployments with restart field compression, and traffic overtaking.
    - Initial counterfactual strategy analysis evaluated on 2024 Abu Dhabi GP (Norris P1) supporting HYP-STRAT-001 under simulation conditions.
    - Initial 3-race backtest smoke test (Abu Dhabi, Silverstone, Bahrain) achieving Log Loss 1.2446, Brier 0.7191, MAE 3.26 positions.
  - Phase 7.1 & 7.2 Monte Carlo Simulator Calibration, CRN Validation & Strategy Robustness (`backend/simulation/scenario.py`, `evaluator.py`, `pit_stop.py`, `traffic.py`, `tyre.py`, `safety_car.py`, `counterfactual.py`, `monte_carlo.py`, `backend/api/v1/simulation.py`):
    - Formulated and verified decoupled exogenous scenario generation for Common Random Numbers (CRN): independent random streams indexed by Run ID, Lap, Driver, and Event Category eliminate event-stream desynchronization.
    - Multi-Seed CRN Validation: Across 5 independent master seeds (`[42, 101, 777, 1337, 2024]`), achieved mean race-time difference variance reduction of **99.996%** (95% CI: $[99.996\%, 99.997\%]$, $\rho = 0.99996$) and mean position difference variance reduction of **90.57%** (95% CI: $[89.58\%, 91.57\%]$). Rigorously explained variance cancellation mechanism: exogenous weather and neutralisation shifts dominate total race variance ($\text{Var}(\Delta_{\text{exog}}) > 1.1 \times 10^6\text{s}^2$), which cancels completely under CRN to isolate pure tactical variance ($\approx 60\text{s}^2$).
    - Full 10,000 Paired Draws Strategy Comparison (Abu Dhabi 2024): Evaluated all 5 strategies across convergence checkpoints ($N=1000, 2500, 5000, 10000$). At $N=10,000$, `SafetyCar_Reactive` achieved Expected Position P3.743 (SE 0.0429), Win Prob 33.29%, beating `Reference_1Stop` (Exp Pos P3.812, Win Prob 17.50%) with paired $\Delta_{\text{pos}} = -0.069$ (Holm-Bonferroni adjusted $p = 9 \times 10^{-5}$). Replaced misleading `scaled_strategy_robustness_10000.json` with the genuine 10,000-draw evaluation.
    - Holdout Strategy Selection Protocol: Disjoint Set A ($N=2,500$, seed 42) for selection and Set B ($N=2,500$, seed 99991) for evaluation. `SafetyCar_Reactive` selected on Set A ($E[\text{pos}] = 3.748$) and verified on Set B ($E[\text{pos}] = 3.541$, win prob 35.3%, beating 1-stop with $\Delta_{\text{pos}} = -0.121$, adjusted $p = 0.00045$). Ex-Post Oracle achieved $E[\text{pos}] = 2.838$, win prob 44.4%, leaving an online position regret of $+0.703$ positions.
    - Pit Stop Provenance & Decomposition: Audited transit loss into circuit entry deceleration ($9.5\text{s}$) and exit acceleration ($11.0\text{s}$) totaling $20.5\text{s}$ transit loss excluding stationary service. Stationary service modeled as $\mathcal{N}(2.45\text{s}, 0.35\text{s})$ with stuck wheel probability $p=0.035$ ($+4.2\text{s}$).
    - Tyre Degradation Calibration: Stint-clustered bootstrap resampling with 95% CIs, fuel burn-off detrending ($-0.0578\text{ s/lap}$ based on $1.75\text{ kg/lap}$ burn-off and $0.033\text{ s/kg}$ sensitivity), compound pace deltas, and quadratic cliff wear.
    - Safety Car & VSC Hazard Decomposition: Separated SC ($\lambda=0.0150$) and VSC ($\lambda=0.0120$) hazard engines based on exposure audit across 346 races (20,722 laps). Enforced chronological cutoff ($VSC \equiv 0$ prior to 2015 season). Lap 1 collision multiplier updated to 2.5 and lap 2 to 1.5.
    - FIA 2024 Sporting Regulations Compliance:
      - Art 22.1 DRS: Strict gap $< 1.000\text{s}$ at detection (boundary 1.0000s strictly ineligible); modeled designated activation zones and zone fractions; added Race Director discretionary disablement (poor visibility, yellow flags).
      - Art 30.5 Tyre Rules: Added mandatory dry compound check; disqualification for completed dry races without $\ge 2$ dry specs or missing designated mandatory dry compounds; 30-second penalty applied strictly if suspended race is not restarted; intermediate/wet exemption.
    - Historical Validation Scope: Explicitly labeled 3-race cohort as a preliminary smoke test (Abu Dhabi, Silverstone, Bahrain).
    - Strategy Sensitivity Sweeps: Confirmed `SafetyCar_Reactive` advantage disappears at zero safety cars ($\text{SC}=0.0\times$), while `Aggressive_2Stop` win rate surges to 27% at $1.5\times$ tyre degradation. Maintained `HYP-STRAT-001` as `SUPPORTED_UNDER_SIMULATION_CONDITIONS`.
    - API & Frontend Enhancements: Async background jobs with polling, 5-modality parameter endpoints, Holm-Bonferroni adjusted $p$-value table, and modality badges.
  - Phase 7.2.1 & EXP-0006 Final Closeout (`backend/simulation/`, `artifacts/reports/EXP-0006/`):
    - Reconciled simulated race-time provenance on 10,000 paired runs:
      - Unconditional all-runs mean (includes 887 DNFs): Reference_1Stop 4,907.93s, SafetyCar_Reactive 4,906.56s, paired difference $-1.361\text{s}$ (SE 0.0882s).
      - Conditional completed-runs mean (9,113 matched finishes): Reference_1Stop 5,190.26s, SafetyCar_Reactive 5,188.73s, paired difference $-1.539\text{s}$ (SE 0.0935s, 95% CI: $[-1.722, -1.355]$). Error vs official winner Norris (5,193.291s) is $< 0.1\%$.
      - DNF counts and rates: Reference_1Stop 887 (8.87%), SafetyCar_Reactive 887 (8.87%). Matched both finished: 9,113 (91.13%). Zero asymmetric DNF runs. Fully resolved prior text citation discrepancy of $-16.36\text{s}$.
    - Historical 3-race backtest smoke test reconciled with exact full-field probability vectors: Abu Dhabi Norris 0.1600 ($-\ln(0.1600) = 1.8326$, Brier 1.0689), British GP Hamilton 0.1200 ($-\ln(0.1200) = 2.1203$, Brier 1.2719), Bahrain GP Verstappen 0.8267 ($-\ln(0.8267) = 0.1903$, Brier 0.0504). Cohort Mean Log Loss: 1.3811, Brier: 0.7971, Top-1 Accuracy: 33.33%, MAE: 3.45.
    - Multi-Objective Strategy Rankings: Evaluated 10,000 paired simulations across 5 objectives (`SafetyCar_Reactive` wins on Win % [33.3%] and Expected Pos [P3.74]; `Reference_1Stop` wins on Podium % [72.9%], Top-5 % [88.8%], and outcome variance [$\sigma=2.81$]). Head-to-head win rate on decisive runs shows `SafetyCar_Reactive` beats 1-stop in 59.07% of non-tied finishes (31.34% vs 21.72% on all runs, 46.94% tied).
    - CRN Marginal Equivalence Audit: Verified via two-sample Kolmogorov-Smirnov tests across all 5 master seeds ($D \le 0.052, p \ge 0.498$), strictly framed as 'no statistically detectable marginal distribution difference in the tested samples', satisfying practical equivalence tolerance $\Delta_{\text{equiv}} \le 0.060$.
    - Circuit-specific DRS configurations (Yas Marina 2 zones / 0.22 fraction, Silverstone 2 / 0.18, Bahrain 3 / 0.25) and Pirelli nominated compounds (C1–C5) established.
    - Disqualified (DSQ) entrants strictly isolated from classified finishers (`is_classified = False`, `current_position = None`, `classification_display = "DSQ"`).
    - Fuel detrending sensitivity grid ($1.4\text{--}2.0\text{ kg/lap}$, $0.025\text{--}0.040\text{ s/kg}$) published in `fuel_tyre_sensitivity_qualification.json` showing adjusted tyre degradation slopes range from $0.0263$ to $0.0713\text{ s/lap}$.
    - Safety Car and VSC counts rebuilt and decoupled: SC (310 distinct phases / 311 total deployments including Spa 2021) and VSC (128 standalone / 180 total activations including 52 compound escalations), with explicit total-lap ($L_{\text{total}}$) and green-flag ($L_{\text{green}}$) denominators, and chronological pre-2015 zero cutoff.
    - Frozen closeout artifact published: `artifacts/reports/EXP-0006/exp_0006_final_closeout.json`.
  - Comprehensive automated test suite: 117 unit and integration tests passing (`pytest tests/ -v`).
  - Next.js frontend production build verified (`npm run build` succeeds cleanly with 6/6 static pages).

---

## 5. Critical Unknowns & Known Limitations

1. **Provisional Result-Record Proxy:** Candidate entrant pools originate from retrospective race-result records. Independently timestamped pre-race entry lists from official FIA manifests have not been reconstructed.
2. **Grid-Zero Interpretation:** In the Ergast/Jolpica dataset, `grid == 0` is an API indicator (audited as 49 pit-lane starts, 7 requiring verification). These records are provisionally encoded as `max(grid) + 1` with an `is_grid_zero` flag.
3. **Probability Simplex vs. Normalized Binary Scores:** Models 2, 3, and 4 normalize binary classifier probabilities across each Grand Prix entrant pool. They guarantee $\sum p_i = 1$, but uncalibrated binary scores can distort probability tails, as demonstrated by LightGBM's inferior log loss relative to regularized logistic regression.

---

## 6. Next Recommended Research Actions

1. **LambdaMART / Direct Ranking Objective Evaluation:** Test pairwise/listwise ranking objectives (`lambdarank` grouped by `race_id`) on LightGBM to address probability tail distortion directly during tree boosting.
2. **Sequential Practice Lap Integration (Milestone 4):** Engineer fuel-corrected practice degradation features from FP2 stint data at forecast checkpoint $T_2$ to test whether practice telemetry beats static grid + form baselines.
3. **Core ML Module Extraction:** Refactor verified feature generation, calibration, and walk-forward evaluation routines into `ml/` library with unit tests in `tests/`.
