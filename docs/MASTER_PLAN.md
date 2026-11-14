# APEX — F1 Intelligence: Master Implementation Plan

## 1. Plan Overview & Engineering Lifecycle

The master implementation plan defines the complete progression of the **APEX — F1 Intelligence** platform. To maintain scientific integrity and prevent architectural rework, development proceeds strictly through gated phases: from empirical source audits to baseline models, sequential pipelines, backend services, and interactive visualization.

```text
Phase 0: Master Architecture & Data-Readiness Audit (Completed)
   │
   ▼
Phase 1: Backend Domain & Data Foundation (FastAPI, Canonical Schemas, Storage)
   │
   ▼
Phase 2: Historical Telemetry, Circuit Geometry & Session Replay Engine
   │
   ▼
Phase 3: Live Ingestion, Streaming Fan-Out & Real-Time Track Map
   │
   ▼
Phase 4: News, Upgrades & 2026 Effective-Dated Regulation Registry
   │
   ▼
Phase 5: Practice Feature Pipelines & Sequential Performance Models (T1–T3)
   │
   ▼
Phase 6: Multi-Checkpoint Forecasting Engine (T0–T7, Sprint Support)
   │
   ▼
Phase 7: Monte Carlo Race & Strategy Dynamics Simulator
   │
   ▼
Phase 8: Research Model Benchmarks, Ablations & Paper Traceability
   │
   ▼
Phase 9: Integrated APEX Web Terminal & Production Packaging
```

---

## 2. Phase-by-Phase Roadmap

### Phase 0: Master Architecture & Data-Readiness Audit — *COMPLETED*
- **Objective:** Establish canonical architecture, provider licensing audit, 2026 regulation timeline, track map/replay geometry strategy, checkpoint lifecycle, and leakage threat model.
- **Key Deliverables:** Comprehensive Phase 0 report, updated core documentation (`ARCHITECTURE.md`, `MASTER_PLAN.md`, `DATA_SOURCES.md`, `KNOWN_LIMITATIONS.md`, `PROJECT_STATUS.md`).
- **Exit Criteria:** Architecture blueprint approved; zero package installations or uncontrolled scaffold generation.

### Phase 1: Backend Domain & Data Foundation — *COMPLETED*
- **Objective:** Build minimal working FastAPI backend, canonical domain entities, provider adapters (Jolpica, OpenF1), and point-in-time relational storage.
- **Key Deliverables:** `backend/` modular monolith, canonical SQLAlchemy models, Alembic migrations, PostgreSQL relational storage, `backend/providers/` (Jolpica, OpenF1, FastF1), idempotent ingestion service, REST API v1 (`/api/v1/`), minimal Next.js frontend integration, and 19 unit/integration tests.
- **Exit Criteria:** Historical event (2024 Abu Dhabi Grand Prix) ingested through providers into canonical storage and served via REST endpoints with full provenance and verified idempotency. [VERIFIED & COMPLETED]

### Phase 2: Historical Telemetry, Circuit Geometry & Session Replay
- **Objective:** Implement telemetry ingestion, circuit coordinate transformation, spline projection, and full historical session replay.
- **Key Deliverables:** Reusable track-map component with replay mode, 2024 Abu Dhabi GP POC, synchronized telemetry/timing player, multi-circuit validation (Silverstone, Melbourne).
- **Exit Criteria:** User seeks timestamp/lap and views synchronized car markers and telemetry with data quality flags. [VERIFIED & COMPLETED: Multi-circuit geometry registry (Yas Marina & Silverstone), coordinate transformer, time-partitioned Parquet storage, causal replay engine, REST endpoints, and interactive 60fps HTML5 Canvas replay UI with dynamic event switching, driver following, and zoom controls.]

### Phase 3: Live Ingestion, Streaming Fan-Out & Real-Time Track Map
- **Objective:** Build backend single-pipe live ingestion, state aggregator, and WebSocket broadcaster.
- **Key Deliverables:** WebSocket contracts, live track map mode, timing tower, tyre/stint indicators, stale-feed handling.
- **Exit Criteria:** In-session streaming updates markers at 60fps; stale feed surfaces offline indicator within 2.5s.

### Phase 4: News, Upgrades & 2026 Effective-Dated Regulation Registry
- **Objective:** Deploy permitted RSS ingestion, NLP event extraction, Team Upgrade Tracker, and effective-dated rule engine.
- **Key Deliverables:** `backend/regulations/`, structured upgrade timeline, point-in-time rule retrieval.
- **Exit Criteria:** Upgrade timeline displays source evidence and confirmation state; models query rule versions by cutoff timestamp. [REGULATION REGISTRY COMPLETED: Effective-dated 2026 technical rules engine, REST endpoints `/api/v1/regulations`, temporal point-in-time query support for Feb 2026 compression ratio amendment and May 2026 Miami GP amendment.]

### Phase 5: Practice Feature Pipelines & Sequential Performance Models
- **Objective:** Implement point-in-time practice session feature pipelines ($T_1 \dots T_3$).
- **Key Deliverables:** Single-lap pace, long-run tyre degradation slopes, sector dominance, sequential practice snapshots.
- **Exit Criteria:** Feature generator reconstructs qualifying and race inputs at historical practice checkpoints without forward leakage. [PRACTICE PIPELINE COMPLETED: `backend/features/practice.py` extracting single-lap metrics, trimmed means, best sectors, theoretical bests, and stint degradation slopes (sec/lap). Constructs immutable T1 (Post-FP1), T2 (Post-FP2), and T3 (Post-FP3) snapshots with automated `TemporalLeakageError` anti-leakage verification.]

### Phase 6: Multi-Checkpoint Forecasting Engine — *COMPLETED*
- **Objective:** Deploy versioned $T_0 \dots T_7$ forecast snapshot engine supporting standard and Sprint weekend schedules.
- **Key Deliverables:** Checkpoint router, immutable forecast store, probability trajectory tracker.
- **Exit Criteria:** Full historical weekend replay produces identical frozen forecasts at each checkpoint when tested against future data perturbation. [CHECKPOINT ENGINE COMPLETED: Implemented `backend/forecasting/engine.py`, `backend/forecasting/evaluator.py`, and REST endpoints `/api/v1/predictions`. Supports checkpoints $T_0 \dots T_5$. Computes mathematically consistent Plackett-Luce forward choice rankings ensuring $\sum p_{\text{podium}} = 3.0$ and $\sum p_{\text{top5}} = 5.0$. Audits HYP-0001 as PARTIALLY SUPPORTED: qualifying grid arrival is statistically superior ($T_4$ vs $T_0$ $\Delta \text{LL} = -0.2095$, $p = 0.00081$), while multi-season practice transitions ($T_1 \dots T_3$) remain unproven at scale due to archive sparsity.]

### Phase 7: Monte Carlo Race & Strategy Dynamics Simulator — *COMPLETED*
- **Objective:** Build stochastic race trajectory simulator incorporating correlated weather, safety cars, and pit strategy counterfactuals.
- **Key Deliverables:** `backend/simulation/`, 100 to 10,000-draw Monte Carlo engine, counterfactual strategy engine with Common Random Numbers (CRN), undercut/overcut/safety-car-reactive strategy evaluation, REST API endpoints under `/api/v1/simulation`, Next.js simulation page at `/simulation`.
- **Exit Criteria:** Empirical finish-position distributions validated against historical outcomes with calibrated confidence bounds. [COMPLETED & PHASE 8 AUTHORIZED: Implemented discrete-lap simulator with tyre degradation cliffs, pit-lane transit and stationary losses, FIA Art 30.5 tyre compliance, safety car deployments with restart compression, DRS and dirty-air traffic modeling. Registered and evaluated EXP-0006 supporting HYP-STRAT-001 under simulation conditions. Completed 10,000 paired simulations, multi-seed CRN audit across 5 master seeds (99.997% race-time variance reduction, 92.33% position variance reduction, KS-test marginal equivalence p >= 0.498, D <= 0.052 <= 0.060), independent holdout strategy selection and evaluation (Set A vs Set B), race-time calibration reconciliation (5,188.7s finished vs official winner 5,193.291s), standing start delay (+4.8s), mathematically exact 3-race historical backtest (Abu Dhabi 1.8326, Silverstone 2.1203, Bahrain 0.1903, Mean 1.3811). Passed numerical integrity gate: machine-precision weighted-mean identity verified (residual <= 9.09e-13s) with DNF span across laps 1–58; SC/VSC methodology correction separates Table A raw message accounting (1,284 records) from Table B event lifecycles (438 green episodes); direct green initiation hazards calibrated (SC 258/19420, VSC 180/13558, conditional escalation 52/180) with orthogonal escalation stream and neutralisation guard; 126 tests passing; Phase 8 authorized.]

### Phase 8: Research Model Benchmarks, Ablations & Paper Traceability
- **Objective:** Port validated notebook models (Models 0–5) to shared `ml/` library, evaluate LambdaMART and hierarchical Bayesian models, and compile paper artifacts.
- **Key Deliverables:** Standardized model registry, paired cluster bootstrap evaluations, publication-ready figures and tables.
- **Exit Criteria:** All models reproducible via CLI; Paper Traceability Matrix fully verified.

### Phase 9: Integrated APEX Web Terminal & Production Packaging
- **Objective:** Connect the 11 analytical views in a production Next.js terminal, Docker packaging, and CI/CD pipelines.
- **Key Deliverables:** Next.js dark/technical UI, end-to-end integration tests, Docker Compose deployment.
- **Exit Criteria:** Sub-100ms API responses, 60fps track map playback, zero client-side direct upstream requests.
