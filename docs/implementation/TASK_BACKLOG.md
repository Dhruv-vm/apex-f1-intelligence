# APEX — Task Backlog

## 1. Backlog Governance

Tasks are uniquely identified, prioritized (`P0` Urgent / Critical Path, `P1` High, `P2` Medium, `P3` Low / Exploratory), and assigned strict dependency relationships.

**Status Schema:**
`NOT STARTED` | `IN PROGRESS` | `BLOCKED` | `COMPLETED`

---

## 2. Categorized Task Register

### Category: Foundation & Governance (FND)

| Task ID | Priority | Title | Target Milestone | Dependencies | Status | Completion Criteria |
|---|---|---|---|---|---|---|
| `TSK-FND-001` | P0 | Initialize project directory & `.gitignore` | M0 | None | `COMPLETED` | Folder structure matches specification; hygiene rules verified. |
| `TSK-FND-002` | P0 | Draft canonical agent instructions (`AGENTS.md`) | M0 | None | `COMPLETED` | Operating rules, anti-leakage rules, and status taxonomy documented. |
| `TSK-FND-003` | P0 | Author foundational master documentation suite | M0 | `TSK-FND-001` | `COMPLETED` | Master plan, charter, architecture, glossary, and system maps drafted. |
| `TSK-FND-004` | P0 | Setup research and experiment tracking registers | M0 | `TSK-FND-003` | `COMPLETED` | Research master, hypotheses, experiment index/log, templates published. |
| `TSK-FND-005` | P0 | Internal Markdown link validation | M0 | `TSK-FND-004` | `COMPLETED` | Automated script confirms 0 broken relative links. |

---

### Category: Data Auditing & Ingestion (DAT)

| Task ID | Priority | Title | Target Milestone | Dependencies | Status | Completion Criteria |
|---|---|---|---|---|---|---|
| `TSK-DAT-001` | P0 | Develop Jolpica/Ergast API audit script | M1 | `TSK-FND-005` | `COMPLETED` | Script tests 2018–2026 results, standings, pit stops; logs rate limits. |
| `TSK-DAT-002` | P0 | Develop FastF1 telemetry & timing audit script | M1 | `TSK-DAT-001` | `COMPLETED` | Script tests upstream live timing auth, records HTTP 401 token requirements. |
| `TSK-DAT-003` | P1 | Develop OpenF1 community feed audit script | M1 | `TSK-DAT-002` | `COMPLETED` | Measures latency, availability, schema conformance, and 429 rate limits. |
| `TSK-DAT-004` | P0 | Complete empirical audit report in `DATA_AVAILABILITY_AUDIT.md` | M1 | `TSK-DAT-001..3` | `COMPLETED` | Document updated with verified missingness rates, coverage matrix, and ADR-0002. |
| `TSK-DAT-004a` | P0 | Scaffold collaborative research notebook environment | M1 | `TSK-DAT-004` | `COMPLETED` | Valid notebooks created: `00_environment...`, `01_data_source...`, and `templates/`. |
| `TSK-DAT-004b` | P0 | Collaborative notebook source validation (Owner + ChatGPT) | M1 | `TSK-DAT-004a` | `NOT STARTED` | Independent execution of `00` and `01` notebooks confirming data coverage. |
| `TSK-DAT-005` | P0 | Build local caching & ingestion orchestrator | M2 | `TSK-DAT-004b` | `NOT STARTED` | Raw data cached in `data/raw/` with automatic serialization to Parquet. |
| `TSK-DAT-006` | P0 | Implement anti-leakage temporal alignment guard | M2 | `TSK-DAT-005` | `NOT STARTED` | Unit test suite verifies zero data from $t > T_{\text{cutoff}}$ enters feature matrix. |

---

### Category: Modeling & Research (MOD)

| Task ID | Priority | Title | Target Milestone | Dependencies | Status | Completion Criteria |
|---|---|---|---|---|---|---|
| `TSK-MOD-001` | P0 | Implement rolling Elo & historical rating baseline (`EXP-0001`) | M3 | `TSK-DAT-006` | `COMPLETED` | `EXP-0001-R1`, `R2`, and `R3` executed across 2010–2026; candidate distributions, tie metrics, and non-starter exclusion audited. |
| `TSK-MOD-002` | P0 | Implement static pre-race starting grid benchmark (`EXP-0002`) | M3 | `TSK-MOD-001` | `IN PROGRESS` | Pre-race candidate field audit complete (`CANDIDATE_FIELD_AUDIT.md`; provisional result-record proxy caveats, race-specific grid encoding with `is_grid_zero`, 149/156 cohort counts); `EXP-0002` scaffolded in `notebooks/05_static_grid_benchmark.ipynb`; awaiting collaborative execution. |
| `TSK-MOD-003` | P1 | Implement FP2 long-run pace feature extractor (`EXP-0003`) | M4 | `TSK-MOD-002` | `NOT STARTED` | Evaluates whether practice stint pace reduces Log Loss over baseline. |
| `TSK-MOD-004` | P1 | Execute telemetry vs aggregated timing ablation (`EXP-0004`) | M4 | `TSK-MOD-003` | `NOT STARTED` | Empirical test of [HYP-0003](../research/HYPOTHESES.md#hyp-0003-modality-parsimony-and-leakage-sensitivity). |
| `TSK-MOD-005` | P0 | Implement post-hoc calibration pipeline (Isotonic / Conformal) | M4 | `TSK-MOD-001` | `COMPLETED` | Calibration audit executed in `notebooks/04_probability_calibration.ipynb` (`EXP-0001-CAL-001`); ECE = 0.030667, CITL = 0.000000, 9 artifacts generated. |

---

### Category: Platform, API & Visualization (INF / UI)

| Task ID | Priority | Title | Target Milestone | Dependencies | Status | Completion Criteria |
|---|---|---|---|---|---|---|
| `TSK-INF-001` | P1 | Scaffold FastAPI application & probability endpoints | M6 | `TSK-MOD-005` | `NOT STARTED` | REST endpoints serve forecast snapshots with sub-100ms latency. |
| `TSK-INF-002` | P2 | Implement WebSocket telemetry replay streamer | M6 | `TSK-INF-001` | `NOT STARTED` | Stream synchronized historical telemetry to local clients. |
| `TSK-UI-001` | P1 | Initialize Next.js project & dark motorsport styling | M7 | `TSK-INF-001` | `NOT STARTED` | Landing experience and UI theme system initialized. |
| `TSK-UI-002` | P1 | Implement Predictions & Model Lab analytical modules | M7 | `TSK-UI-001` | `NOT STARTED` | Interactive reliability diagrams, Brier score evolution, probability distributions. |
