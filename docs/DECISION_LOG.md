# APEX — Architecture & Methodology Decision Log

This document records the key architectural, methodology, and experimental decisions governing the **APEX — F1 Intelligence** repository. Formal Architecture Decision Records (ADRs) are maintained in `docs/decisions/`.

---

## 1. Decision Registry

| Decision ID | Date | Status | Title & Scope | Rationale & Outcome | Linked ADR |
|---|---|---|---|---|---|
| `DEC-0001` | 2026-10-18 | `APPROVED` | **Folder Structure & Modality Separation** | Strict separation between observed data, historical replay, model forecasts, and scenario simulations. | [ARCHITECTURE.md](ARCHITECTURE.md) |
| `DEC-0002` | 2026-10-18 | `APPROVED` | **Data Provider Strategy & Rate Limiting** | Jolpica selected for 1950–2026 historical results; OpenF1 selected for modern 2023+ telemetry; FastF1 restricted to local parser. | [ADR-0002](decisions/ADR-0002-data-provider-selection-and-telemetry-strategy.md) |
| `DEC-0003` | 2026-10-19 | `APPROVED` | **Notebook-First Research Workflow** | Research and exploratory modeling owned collaboratively by Project Owner + ChatGPT in `notebooks/`; engineering and testing owned by Antigravity. | [AGENTS.md](../AGENTS.md) |
| `DEC-0004` | 2026-10-19 | `APPROVED` | **Outcome-Independent Candidate Ordering** | Prevent tie-break leakage by sorting candidate pools strictly by `driver_id` prior to scoring. | Audited in `EXP-0001-R3` |
| `DEC-0005` | 2026-10-19 | `APPROVED` | **Race-Specific Grid-Zero Encoding** | Replaced arbitrary `effective_grid = 21` with race-specific $\max(\text{grid}_{>0}) + 1$ and explicit `is_grid_zero` flag. Not treated as definitive pit-lane proof. | [CANDIDATE_FIELD_AUDIT.md](research/CANDIDATE_FIELD_AUDIT.md) |
| `DEC-0006` | 2026-10-19 | `APPROVED` | **Standardized Evaluation Cohorts** | Modern era defined as 2018–2024 (149 rounds, 20-car consistency); 2010–2017 defined as 156-round warm-up / sensitivity cohort. | [CANDIDATE_FIELD_AUDIT.md](research/CANDIDATE_FIELD_AUDIT.md) |
| `DEC-0007` | 2026-11-04 | `APPROVED` | **Model 4 LightGBM Implementation Protocol** | Fixed reproducible hyperparameters (`num_leaves=15`, `lr=0.03`, `n_est=250`); 16 features identical to Model 3; strict walk-forward evaluation. | [05_static_grid_benchmark.ipynb](../notebooks/05_static_grid_benchmark.ipynb) |
| `DEC-0008` | 2026-11-04 | `APPROVED` | **Proper Scoring Rules over Top-1 Selection** | Proper scoring rules (Log Loss, Brier score) take precedence over raw argmax Top-1 accuracy when selecting models. Model 3 retained as primary baseline. | [RESEARCH_LOG.md](RESEARCH_LOG.md) |
