# Current Milestone: Milestone 1 — Data Availability, Research Specification & Notebook-Based Source Validation

- **Milestone Code:** `M1`
- **Milestone Title:** Data Availability, Research Specification & Notebook-Based Source Validation
- **Start Date:** 2026-10-18
- **Current Lifecycle Status:** `IN PROGRESS` (Notebook Scaffold Established; Awaiting Collaborative Notebook Validation)

---

## 1. Milestone Objective

Empirically audit historical and modern Formula 1 data availability across candidate providers (Jolpica, OpenF1, FastF1), establish verified coverage through the current 2026 season, formalize feasible forecast checkpoints, and establish the **Notebook-First Research Workflow** where the Project Owner and ChatGPT collaboratively perform data science and source validation in Jupyter notebooks prior to dataset construction and modeling.

---

## 2. Acceptance Criteria Checklist

- [x] **Reproducible Command-Line Audit Scripts:**
  - [x] [scripts/audit/audit_jolpica.py](../../scripts/audit/audit_jolpica.py) auditing schedules, results, qualifying, pitstops, and standings across 1950–2026.
  - [x] [scripts/audit/audit_openf1.py](../../scripts/audit/audit_openf1.py) auditing sessions, sub-second telemetry, laps, stints, weather, intervals, and rate limits.
  - [x] [scripts/audit/audit_fastf1.py](../../scripts/audit/audit_fastf1.py) documenting upstream live timing HTTP 401 authentication gates.
  - [x] [scripts/audit/run_audit_summary.py](../../scripts/audit/run_audit_summary.py) producing consolidated JSON summary.
- [x] **Multi-Season Coverage Matrix & Recommendations:**
  - [x] Coverage matrix published in [docs/research/DATA_AVAILABILITY_AUDIT.md](../research/DATA_AVAILABILITY_AUDIT.md) separating complete seasons (1950–2025) from 2026 Year-to-Date.
- [x] **Architectural Decision Record (ADR):**
  - [x] Published [ADR-0002](../decisions/ADR-0002-data-provider-selection-and-telemetry-strategy.md) adopting the two-tier hybrid data architecture (Jolpica for broad historical sporting records, OpenF1 for open modern telemetry).
- [x] **Notebook-First Workflow & Scaffold:**
  - [x] [notebooks/README.md](../../notebooks/README.md) defining division of responsibilities, directory structure, and 8 core rules.
  - [x] [notebooks/00_environment_and_source_checks.ipynb](../../notebooks/00_environment_and_source_checks.ipynb) validating Python environment, dependencies, and project paths.
  - [x] [notebooks/01_data_source_validation.ipynb](../../notebooks/01_data_source_validation.ipynb) providing the collaborative framework to independently reproduce and verify the audit across Jolpica, OpenF1, and FastF1.
  - [x] [notebooks/03_elo_baseline.ipynb](../../notebooks/03_elo_baseline.ipynb) patched with candidate-level probability distributions, tie-aware top-1 metrics, and non-starter rating exclusion (`EXP-0001-R2` / `EXP-0001-R3`).
  - [x] [notebooks/04_probability_calibration.ipynb](../../notebooks/04_probability_calibration.ipynb) scaffolded and verified for candidate-level one-vs-rest reliability diagrams, ECE, race-clustered bootstrapping, and era drift (`EXP-0001-CAL-001`).
  - [x] [docs/research/CANDIDATE_FIELD_AUDIT.md](../research/CANDIDATE_FIELD_AUDIT.md) authoring pre-race candidate-field reconstruction audit (provisional proxy caveats, race-specific grid-zero encoding with `is_grid_zero`, 149/156 cohort counts).
  - [x] [notebooks/05_static_grid_benchmark.ipynb](../../notebooks/05_static_grid_benchmark.ipynb) scaffolded for EXP-0002 static pre-race starting grid baselines and benchmark.
- [ ] **Collaborative Notebook Execution (Project Owner + ChatGPT):**
  - [ ] Execute `00_environment_and_source_checks.ipynb` to verify the working environment.
  - [ ] Execute `01_data_source_validation.ipynb` to independently verify provider coverage, rate limits, and formulate the confirmed research dataset recommendation.
  - [x] Execute `03_elo_baseline.ipynb` (`EXP-0001-R2` / `EXP-0001-R3`) generating baseline walk-forward distributions and proper scoring metrics.
  - [x] Execute `04_probability_calibration.ipynb` evaluating candidate-level calibration error (ECE = 0.030667, MCE = 0.185189, CITL = 0.000000).
  - [ ] Execute `05_static_grid_benchmark.ipynb` evaluating pre-race starting grid baselines against Elo baseline.

---

## 3. Transition Criteria to Milestone 2

Milestone 1 will conclude and transition to **Milestone 2 (Data Pipeline, Ingestion & Temporal Alignment Store)** when:
1. `notebooks/00_environment_and_source_checks.ipynb` has been executed by the Project Owner and ChatGPT.
2. `notebooks/01_data_source_validation.ipynb` has been executed and confirmed without discrepancies.
3. The confirmed research dataset recommendation is finalized to guide local caching in `data/raw/` and Parquet serialization in `data/processed/`.
