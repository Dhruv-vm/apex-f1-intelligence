# APEX — Implementation Roadmap

## 1. Roadmap Architecture

The APEX implementation roadmap divides platform development into nine sequential, gated milestones. Progression to any milestone requires 100% completion of preceding acceptance criteria.

---

## 2. Milestone Breakdown

### Milestone 0: Project Initialization & Documentation Foundation (Current)
- **Focus:** Directory layout, Markdown documentation system, AI instructions, repository readiness.
- **Dependencies:** None.
- **Key Deliverables:** Full documentation suite in `docs/`, `.gitignore`, `.env.example`, initialized local Git repository.
- **Acceptance Criteria:** Validated folder structure, zero dead links, clear agent instructions, no premature code/data files.

### Milestone 1: Data Availability Audit & Provider Verification
- **Focus:** Empirical verification of candidate providers (Jolpica/Ergast, FastF1, OpenF1).
- **Dependencies:** Milestone 0.
- **Key Deliverables:** Audit test scripts in `scripts/audit/`, fully populated [DATA_AVAILABILITY_AUDIT.md](../research/DATA_AVAILABILITY_AUDIT.md).
- **Acceptance Criteria:** Historical season coverage verified for 2018–2024; missingness quantified; API rate limits confirmed.

### Milestone 2: Data Engineering, Local Storage & Temporal Alignment Pipeline
- **Focus:** Ingestion pipelines, local caching, schema validation, and anti-leakage temporal cutoffs.
- **Dependencies:** Milestone 1.
- **Key Deliverables:** Ingestion scripts, SQLite/DuckDB/Parquet schema, automated temporal cutoff test suite.
- **Acceptance Criteria:** Ingestion of target seasons completed locally with 100% reproducible schemas and verified zero leakage.

### Milestone 3: Static Baseline Forecasting & Proper Scoring Benchmarks
- **Focus:** Implementation of non-temporal pre-weekend and pre-race baselines.
- **Dependencies:** Milestone 2.
- **Key Deliverables:** Rolling Elo/TrueSkill ratings, Bradley-Terry constructor models, pre-race LightGBM classifier.
- **Acceptance Criteria:** Baseline models evaluated on rolling-origin splits using multi-class Log Loss and Brier score.

### Milestone 4: Sequential Multi-Checkpoint Feature Pipeline
- **Focus:** Engineering features across discrete weekend checkpoints ($T_0$ through $T_5$).
- **Dependencies:** Milestone 3.
- **Key Deliverables:** Feature extractor modules (FP long-run degradation slopes, qualifying pole deltas), ablation test suite.
- **Acceptance Criteria:** Execution of `EXP-0003` and `EXP-0004`; empirical verification of [HYP-0001](../research/HYPOTHESES.md#hyp-0001-sequential-information-superiority).

### Milestone 5: In-Race Live Updating & Strategy Counterfactual Simulator
- **Focus:** Dynamic lap-by-lap probability updates and counterfactual pit strategy models.
- **Dependencies:** Milestone 4.
- **Key Deliverables:** Lap $K$ checkpoint forecaster, Monte Carlo pit loss simulator, safety car hazard model.
- **Acceptance Criteria:** Backtested live prediction snapshots demonstrating calibrated win/podium probabilities across laps.

### Milestone 6: Core Analytical Backend Services & API Gateway
- **Focus:** High-performance REST and WebSocket API serving predictions and telemetry.
- **Dependencies:** Milestone 5.
- **Key Deliverables:** FastAPI service, OpenAPI documentation, WebSocket telemetry streamer, test suite.
- **Acceptance Criteria:** Sub-100ms response latency on query endpoints; streaming replay integration.

### Milestone 7: Frontend Platform & 11 Analytical Modules
- **Focus:** Cinematic landing portal and the 11-module analytical workspace.
- **Dependencies:** Milestone 6.
- **Key Deliverables:** Next.js application, dark motorsport UI, Model Lab dashboard, telemetry visualizer.
- **Acceptance Criteria:** End-to-end user navigation across all 11 modules; responsive rendering of charts and predictions.

### Milestone 8: End-to-End Validation, Packaging & Documentation Release
- **Focus:** Full system integration, comprehensive backtesting, Docker packaging, research report publication.
- **Dependencies:** Milestone 7.
- **Key Deliverables:** Docker compose deployment, automated integration test suite, research summary in `artifacts/reports/`.
- **Acceptance Criteria:** Complete clean-clone reproducibility, CI passing, formal research paper writeup finalized.
