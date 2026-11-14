# APEX — Experiment System & Protocol

## 1. Purpose & Standards

The APEX experiment tracking system provides an immutable, transparent, and reproducible record of every scientific experiment, baseline benchmark, and ablation study performed across the project lifecycle.

To prevent chat context loss and guarantee full auditability:
1. Every experiment is assigned a permanent, unique identifier (e.g., `EXP-0001`).
2. Every experiment record is committed to this directory or its subdirectories as a standalone Markdown file.
3. No experiment may claim results without specifying random seeds, dataset commit hashes, train/test split dates, and reproduction commands.
4. Experiment templates must never contain fabricated or placeholder numbers that could be mistaken for verified empirical findings.

---

## 2. Experiment Lifecycle & Status Taxonomy

Every experiment record moves through defined lifecycle states:
- `PLANNED`: Formal experiment design documented and reviewed; hypothesis and metrics specified; execution pending.
- `RUNNING`: Experiment executing in development or compute environment.
- `COMPLETED`: Script execution finished; metrics computed, calibration evaluated, and results recorded.
- `FAILED`: Script failed due to technical exceptions, data corruption, or memory limits.
- `INVALIDATED`: Execution completed, but post-hoc audit revealed temporal leakage, incorrect cutoff boundaries, or compromised evaluation folds.

---

## 3. Directory Map

```text
docs/experiments/
├── README.md                           # This overview and operating protocol
├── EXPERIMENT_INDEX.md                 # Complete register of all experiments and their statuses
├── EXPERIMENT_LOG.md                   # Chronological ledger of experiment runs
├── RESULTS_SUMMARY.md                  # Executive synthesis of validated empirical benchmarks
├── ABLATION_PLAN.md                    # Structured plan for feature and modality ablations
└── templates/
    ├── EXPERIMENT_TEMPLATE.md          # Standardized template for new experiment specifications
    └── RESULTS_TEMPLATE.md             # Standardized template for experiment result writeups
```

---

## 4. How to Register a New Experiment

1. Copy [templates/EXPERIMENT_TEMPLATE.md](templates/EXPERIMENT_TEMPLATE.md) to a new file named `EXP-XXXX-short-title.md` (e.g., `EXP-0001-static-elo-baseline.md`).
2. Fill out all pre-execution sections (Hypothesis, Cutoff, Split Strategy, Model Config, Reproduction Command).
3. Register the new experiment in [EXPERIMENT_INDEX.md](EXPERIMENT_INDEX.md) with status `PLANNED`.
4. Execute the experiment script using fixed random seeds and pinned dataset versions.
5. Record measured results, calibration curves, and error analysis in the document.
6. Update [EXPERIMENT_LOG.md](EXPERIMENT_LOG.md) and [RESULTS_SUMMARY.md](RESULTS_SUMMARY.md).
