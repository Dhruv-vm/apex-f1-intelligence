# APEX — F1 Intelligence

> **Every lap. Every variable. Every possibility.**

[![Milestone](https://img.shields.io/badge/Milestone-Phase%207%20Complete%20%2F%20Phase%208%20Authorized-00E5FF.svg)](docs/implementation/CURRENT_MILESTONE.md)
[![Status](https://img.shields.io/badge/Status-Verified%20%26%20Authorized-brightgreen.svg)](docs/PROJECT_STATUS.md)
[![Backend Tests](https://img.shields.io/badge/Pytest-126%20Passing-success.svg)](tests/)
[![Frontend](https://img.shields.io/badge/Next.js-14.2.35-black.svg)](frontend/)
[![License](https://img.shields.io/badge/License-Proprietary%20%2F%20Research-red.svg)](#)

---

## 1. Executive Overview

**APEX — F1 Intelligence** is a long-term, research-driven Formula 1 intelligence platform designed to integrate probabilistic race forecasting, weekend progression analysis, high-frequency telemetry, strategy simulation, and analytical research tools into a cohesive system.

Formula 1 race outcomes are governed by dynamic, non-stationary processes across varying temporal scales: multi-year regulation cycles, circuit evolutionary dynamics, tyre degradation physics, changing meteorological conditions, and chaotic in-race interventions such as Safety Cars. Rather than relying on static pre-race predictions or deterministic approximations, APEX investigates a sequential, multimodal probabilistic forecasting framework that updates its predictive distributions as evidence unfolds from free practice through qualifying and into live race checkpoints.

---

## 2. Platform Architecture & Current Implementation

APEX is structured into a modular analytical platform combining backend engineering, research forecasting, physics-informed stochastic simulation, and interactive web visualization:

| Subsystem | Component | Technology & Implementation Status |
|---|---|---|
| **Backend API** | Modular Monolith | FastAPI with SQLAlchemy 2.0 ORM, Alembic migrations, Pydantic v2 schemas, and REST endpoints under `/api/v1` for circuits, drivers, constructors, events, sessions, results, regulations, replay, and simulation. |
| **Circuit Geometry & Replay** | Track Map Engine | Multi-circuit geometry registry (`backend/geometry/`) with centerline spline models for Yas Marina and Silverstone; streaming Parquet telemetry storage; causal replay engine with zero lookahead; 60fps HTML5 Canvas track map with driver-following mode and telemetry HUD. |
| **Regulation Intelligence** | Rule Engine | Effective-dated technical and sporting rules engine (`backend/regulations/`) audited against official FIA Category 2182 specifications for 2026 regulations. |
| **Forecasting Engine** | Multi-Checkpoint Pipeline | Sequential point-in-time probabilistic forecasting (`backend/forecasting/`) across $T_0$ (Pre-Weekend), $T_1$ (Post-FP1), $T_2$ (Post-FP2), $T_3$ (Post-FP3), $T_4$ (Post-Qualifying), and $T_5$ (Pre-Race with grid penalties). Plackett-Luce forward choice ranking enforces exact multi-output probability sums ($\sum p_{\text{podium}} = 3.0$, $\sum p_{\text{top5}} = 5.0$, $\sum E[\text{pos}] = N(N+1)/2$). |
| **Race Strategy Simulator** | Monte Carlo Engine | Discrete-lap stochastic race simulator (`backend/simulation/`) with non-linear tyre thermal and wear degradation, fuel load lap-time sensitivity, pit transit losses, aerodynamic wake dirty air, DRS overtaking dynamics, mechanical reliability hazards, and 5 counterfactual strategic policies evaluated with Common Random Numbers (CRN). |
| **Web Client** | Strategy Terminal | Next.js 14 (`^14.2.0`, resolved `14.2.35`) client with React 18, TypeScript, Tailwind CSS, dark technical styling, interactive circuit canvas, and strategy simulation terminal. |

---

## 3. Canonical Research Models & Benchmarks

Research experiments adhere strictly to the **Notebook-First Collaboration Workflow** and are documented in [docs/experiments/EXPERIMENT_INDEX.md](docs/experiments/EXPERIMENT_INDEX.md):

- **EXP-0001 (Dynamic Elo Rating Baseline):** Evaluates non-sequential pre-weekend baselines ($T_0$) using pairwise Bradley-Terry / Elo ratings across 2010–2026 (`EXP-0001-R3` Elo Log Loss: `2.278177`, Brier: `0.845726` vs Uniform: `3.044556`).
- **EXP-0002 (Static Pre-Race Grid Benchmark at $T_5$):**
  - **Model 0 (Uniform Baseline):** $P_i = 1/N_r$ (Primary Log Loss: `2.995388`, Brier: `0.949982`).
  - **Model 1 (Empirical Grid Frequency Baseline):** Laplacian-smoothed historical grid win frequency ($P(\text{Win} \mid \text{Grid})$, $\alpha=10$; Primary Log Loss: `1.583766`, Brier: `0.682312`).
  - **Model 2 (Grid-Only Logistic Regression):** Univariate logistic regression on 5 grid features (Primary Log Loss: `1.594207`, Brier: `0.683382`).
  - **Model 3 (Grid + Driver/Constructor Form Logistic Regression):** Multivariate logistic regression on 16 grid and rolling form features (**Best Overall Probabilistic Performance**: Primary Log Loss `1.355201`, Brier `0.612698`).
  - **Model 4 (LightGBM GBDT Benchmark):** Gradient boosted trees on 16 features (**Best Argmax Top-1 Accuracy**: `53.02%`, but inferior under proper scoring rules due to overconfident probability tails: Log Loss `1.409149`, Brier `0.628561`).
- **EXP-0003 (Post-Hoc Probability Calibration Benchmark):** Evaluates Platt scaling, Isotonic regression, and Temperature scaling. Temperature scaling ($T \approx 1.360$) and Platt scaling significantly improve LightGBM (Log Loss `1.387587`, ECE `0.007818`), while Model 3 Logistic is naturally well-calibrated ($T \approx 1.007$, ECE `0.009618`).
- **EXP-0004 (Direct Race-Level Winner Model — Model 5 Plackett-Luce):** Direct list-wise permutation model optimizing grouped conditional logit log-likelihood (Primary Log Loss: `1.351747`, Brier: `0.596564`, Fract. Top-1: `0.543624`).
- **EXP-0005 (Multi-Checkpoint Walk-Forward Validation & Practice Feature Audit):** Evaluates sequential checkpoints $T_0 \dots T_5$ across the 149-race primary cohort (2018–2024). Confirms significant predictive gain from qualifying grid arrival ($T_4$ vs $T_0$ $\Delta \text{LL} = -0.2095$, $p < 0.001$). Maintains **HYP-0001 as PARTIALLY SUPPORTED** because multi-season practice information superiority ($T_1 \dots T_3$) remains unproven at scale due to historical archive sparsity (only 3 of 102 practice sessions cached locally; 99 provider-available).
- **EXP-0006 (Monte Carlo Strategy Dynamics Simulator):** Evaluates counterfactual strategy optimization for the 2024 Abu Dhabi GP across 10,000 paired simulations with Common Random Numbers, demonstrating >99.9% race-time variance reduction and supporting **HYP-STRAT-001 under simulation conditions**. Includes out-of-sample holdout strategy selection and evaluation across Set A ($N=2,500$) and Set B ($N=2,500$).

---

## 4. Historical Datasets & Boundary Clarifications

1. **2010–2024 Completed Historical Seasons:** Strictly **305 completed Grand Prix races** with **6,432 driver-race records** in `data/interim/driver_race_results_2010_2026_v2_regulation_metadata.csv`, divided into:
   - **Historical Sensitivity / Warm-Up Cohort (2010–2017):** 156 rounds, 3,453 candidate records.
   - **Primary Benchmark Cohort (2018–2024):** 149 rounds, 2,979 candidate records.
2. **2010–2026 Full Series Dataset:** **346 Grand Prix races** with **7,285 candidate records** (including 41 scheduled/candidate rounds from the 2025–2026 calendar).
3. **Clarification on the Number 310:** The number 310 refers strictly to the **310 physical Safety Car phases** audited across 20,722 laps in the 2010–2024 safety car study, **not** to the number of completed Grand Prix races or rounds.
4. **Provisional Result-Record Proxy Caveat:** The historical dataset consists of retrospective race-result records from Ergast/Jolpica. It serves as a provisional result-record proxy until independently timestamped pre-session entry manifests are ingested; zero post-race leakage cannot be formally claimed as proven until genuine pre-race manifests are ingested.
5. **Simulation Evaluation vs Smoke Testing:** The primary strategy findings in EXP-0006 derive from 10,000 paired Monte Carlo simulations with CRN variance reduction. The 3-race historical backtest (`historical_simulation_backtest.json`) represents an exploratory pipeline smoke test, strictly distinguished from full multi-season simulation calibration.

---

## 5. Directory Structure

```text
apex-f1/
├── README.md                           # Main repository introduction and orientation
├── AGENTS.md                           # Persistent instructions for AI collaborators
├── .gitignore                          # Repository hygiene for Python, Node, data, and models
├── .env.example                        # Template for environment and configuration keys
├── alembic.ini                         # Database migration configuration
├── requirements.txt                    # Python environment specifications
│
├── alembic/                            # SQLAlchemy migration revisions
├── backend/                            # FastAPI modular monolith application
│   ├── api/v1/                         # REST routers (circuits, events, predictions, replay, simulation)
│   ├── features/                       # Point-in-time practice intelligence pipelines
│   ├── forecasting/                    # Checkpoint forecasting engine & Plackett-Luce models
│   ├── geometry/                       # Circuit coordinate registry & spline centerlines
│   ├── models/                         # SQLAlchemy 2.0 ORM database entities
│   ├── providers/                      # Jolpica, OpenF1, and FastF1 client adapters
│   ├── regulations/                    # Effective-dated 2026 technical rule engine
│   ├── replay/                         # Causal temporal filter & streaming Parquet replay
│   ├── schemas/                        # Pydantic v2 validation contracts
│   └── simulation/                     # Discrete-lap Monte Carlo strategy simulator
│
├── frontend/                           # Next.js 14 client application (React 18, Tailwind CSS)
│   ├── src/app/                        # Next.js app router pages (/, /replay, /simulation)
│   ├── src/components/replay/          # 60fps Canvas track map, Telemetry HUD, Timing Tower
│   └── src/types/                      # TypeScript API and simulation domain definitions
│
├── data/                               # Tiered data storage
│   ├── interim/                        # Cleaned 2010–2026 historical datasets & manifests
│   ├── processed/replay/               # Opening-lap Parquet partitions (Abu Dhabi, Silverstone)
│   └── raw/                            # Local provider cache (.gitkeep, ignored in git)
│
├── docs/                               # Canonical system and research documentation
│   ├── decisions/                      # Architecture Decision Records (ADRs)
│   ├── experiments/                    # EXPERIMENT_INDEX.md, RESULTS_SUMMARY.md
│   ├── implementation/                 # CURRENT_MILESTONE.md, MASTER_PLAN.md, TASK_BACKLOG.md
│   └── research/                       # RESEARCH_MASTER.md, METHODOLOGY.md, HYPOTHESES.md
│
├── notebooks/                          # Collaborative Jupyter research notebooks (00 through 07)
├── scripts/audit/                      # Reproducible data availability audit scripts
├── tests/                              # Automated test suites (126 backend tests passing)
└── artifacts/reports/                  # Serialized research manifests & metrics (EXP-0001 to EXP-0006)
```

---

## 6. Canonical Documentation Quick Links

- **Current Status:** [docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md)
- **Active Milestone:** [docs/implementation/CURRENT_MILESTONE.md](docs/implementation/CURRENT_MILESTONE.md)
- **Master Plan:** [docs/MASTER_PLAN.md](docs/MASTER_PLAN.md)
- **Architecture Specification:** [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **Experiment Index:** [docs/experiments/EXPERIMENT_INDEX.md](docs/experiments/EXPERIMENT_INDEX.md)
- **Research Methodology:** [docs/research/METHODOLOGY.md](docs/research/METHODOLOGY.md)
- **Hypotheses Registry:** [docs/research/HYPOTHESES.md](docs/research/HYPOTHESES.md)
- **Candidate Field Audit:** [docs/research/CANDIDATE_FIELD_AUDIT.md](docs/research/CANDIDATE_FIELD_AUDIT.md)

---

## 7. Verification & Testing

Execute the backend test suite:
```bash
.venv/bin/pytest tests/
```

Build the frontend client:
```bash
npm --prefix frontend run build
```

- **GitHub Repository:** [https://github.com/Dhruv-vm/apex-f1-intelligence](https://github.com/Dhruv-vm/apex-f1-intelligence)
- **Target Branch:** `main`
