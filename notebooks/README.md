# APEX — Notebook-First Research & Modeling Workflow

## 1. Operating Philosophy & Collaboration Protocol

APEX adopts a **Notebook-First Research Workflow** for all exploratory data analysis, dataset construction, probabilistic modeling, and experimental evaluation.

### Division of Ownership:
- **Research & Data Science (Project Owner + ChatGPT):** Collaboratively design, implement, explore, and evaluate data science experiments directly within Jupyter notebooks. Formulate features, train models, inspect probability calibrations, and draw scientific conclusions.
- **Supporting Engineering & Governance (Antigravity):** Owns the underlying infrastructure, project organization, canonical Markdown documentation, repository hygiene, data pipelines, automated tests, and eventual application/API integration. Antigravity does **not** independently pre-fill or fabricate experimental findings.

---

## 2. Directory Structure & Numbering Conventions

```text
notebooks/
├── README.md                                  # This workflow, governance, and operating guide
├── 00_environment_and_source_checks.ipynb     # Environment, path, package, and script accessibility checks
├── 01_data_source_validation.ipynb            # Independent verification of Jolpica, OpenF1, and FastF1
├── 02_historical_race_dataset.ipynb           # Historical race dataset extraction and profiling (2010–2026)
├── 03_elo_baseline.ipynb                      # EXP-0001 driver-only pairwise Elo walk-forward baseline
├── 04_probability_calibration.ipynb           # EXP-0005-PRE candidate-level probability calibration audit
├── 05_static_grid_benchmark.ipynb             # EXP-0002 pre-race static starting grid baseline & benchmark
└── templates/
    └── experiment_notebook_template.ipynb     # Standardized skeleton for research experiments (EXP-XXXX)
```

### Numbering & Lifecycle Conventions:
- `00–09`: Environment, source validation, exploratory data analysis (EDA), and data profiling.
- `10–19`: Dataset construction, time-alignment checks, and feature engineering.
- `20–29`: Baseline probabilistic modeling and scoring benchmarks.
- `30–49`: Sequential checkpoint models, multimodal experiments, and live race updating.
- `50+`: Post-hoc probability calibration, ablation studies, and evaluation analyses.
- `templates/`: Canonical notebook templates used when initializing new research experiments.

---

## 3. Core Notebook Operating Rules

1. **Notebooks are the Primary Research Surface:** All exploratory data analysis, feature prototyping, and model experiments occur in notebooks before being extracted into library modules.
2. **No Fabricated Findings:** Notebooks must contain executable code, explicit assertions, and actual measured metrics. Antigravity must never pre-fill synthetic results or fabricate outputs.
3. **Preliminary Status of External Audits:** Existing command-line audit scripts and reports are preliminary working references until independently reproduced and verified within notebooks.
4. **Traceable Experiment Metadata:** Every experiment notebook must specify:
   - Target Research Question ID and Hypothesis ID (e.g., `RQ1`, `HYP-0001`).
   - Data sources, date ranges, and dataset version hashes.
   - Prediction target (e.g., Race Winner, Top-3 Podium) and explicit information cutoff ($T_{cutoff}$).
   - Method, baseline comparison, and random seeds.
   - Strictly proper scoring rules (Brier score, multi-class Log Loss, ECE).
   - Limitations and next decisions.
5. **Graduation to Production Modules:** Reusable, validated logic developed in notebooks will be refactored by Antigravity into modular, tested Python packages in `ml/` and `backend/` accompanied by automated unit tests in `tests/`.
6. **Strict Separation of Modalities:** Always distinguish actual historical observations, historical replay, model forecasts, and counterfactual scenario simulations.
7. **Strict Anti-Leakage Integrity:** Never leak post-cutoff information (such as post-race penalties or future session outcomes) into feature matrices or model training folds.
8. **Resource Discipline:** Never trigger bulk historical downloads or install unverified packages automatically during notebook initialization.
