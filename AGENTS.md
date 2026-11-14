# AGENTS.md — Persistent Instructions for AI Collaborators

## 1. Purpose and Operating Philosophy

This document contains canonical, non-negotiable guidelines for any AI coding assistant, autonomous agent, or paired developer working on the **APEX — F1 Intelligence** codebase.

APEX is a long-term, rigorous, research-driven Formula 1 intelligence platform combining probabilistic race forecasting, race-weekend analysis, telemetry, strategy simulation, analytics, and research tools. Because empirical honesty, temporal integrity, and reproducibility are paramount, all agents must operate under disciplined software engineering and scientific standards.

### Notebook-First Collaboration Workflow
- **Research & Data Science Ownership (Project Owner + ChatGPT):** The project owner and ChatGPT collaboratively explore data, engineer features, formulate models, and evaluate research experiments within Jupyter notebooks in `notebooks/`.
- **Engineering & Infrastructure Ownership (Antigravity):** Antigravity owns the supporting engineering, repository organization, documentation integrity, automated testing, reproducible pipelines, and eventual application integration. Antigravity does **not** independently pre-fill or fabricate experimental findings.

### Core Workflow Rules:
1. **Notebooks are the primary collaborative environment** for exploratory data analysis, dataset construction, model development, and research experiments.
2. **Antigravity must not independently fabricate or pre-fill experimental findings.** Notebooks must contain executable code, explicit assertions, and actual measured metrics.
3. **Existing audit scripts and results are preliminary** working references until independently reproduced and verified in notebooks (starting with `notebooks/01_data_source_validation.ipynb`).
4. **Every substantive experiment must link** to its hypothesis ID, dataset version/hash, prediction target, information cutoff, code version, results, and limitations.
5. **Reusable, validated logic should eventually move into `ml/` and `backend/` modules** accompanied by automated unit tests in `tests/`.
6. **Actual measured results must be strictly distinguished** from proposals, assumptions, and planned experiments.
7. **Never leak information** from after a forecast cutoff into features, validation folds, or model selection.
8. **Never download the complete historical dataset, install new packages, or access paid services automatically** during environment setup or notebook creation.

---

## 2. Mandatory Reading Before Substantial Work

Before proposing architecture modifications, introducing dependencies, creating models, or writing production code, you **must** read and cross-reference the following canonical documents:

1. [README.md](README.md) — High-level project identity, repository map, and setup principles.
2. [docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md) — The single source of truth for current project progress, completed milestones, blockers, and next actions.
3. [docs/MASTER_PLAN.md](docs/MASTER_PLAN.md) — Complete multi-stage implementation roadmap.
4. [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — Structural design, component boundaries, and provisional system models.
5. [docs/implementation/CURRENT_MILESTONE.md](docs/implementation/CURRENT_MILESTONE.md) — Specific acceptance criteria and task checklist for the current milestone.

If your task touches forecasting methodology, data modeling, or experiments, you must also read:
- [docs/research/RESEARCH_MASTER.md](docs/research/RESEARCH_MASTER.md)
- [docs/research/METHODOLOGY.md](docs/research/METHODOLOGY.md)
- [docs/research/EVALUATION_PROTOCOL.md](docs/research/EVALUATION_PROTOCOL.md)
- [docs/research/DATA_AVAILABILITY_AUDIT.md](docs/research/DATA_AVAILABILITY_AUDIT.md)
- [docs/experiments/EXPERIMENT_INDEX.md](docs/experiments/EXPERIMENT_INDEX.md)

---

## 3. Core Operating Rules

### Rule 1: Markdown Documentation is Canonical Memory
Context windows reset, but repository files persist. Any architectural choice, hypothesis change, dataset audit outcome, or experiment result must be recorded in its respective Markdown document immediately. Do not rely on chat history.

### Rule 2: Strict Temporal Integrity and Leakage Prevention
Formula 1 outcomes are strictly chronological. Any modeling or feature generation pipeline must enforce explicit **information cutoffs** (prediction checkpoints: e.g., Pre-Weekend, Post-FP1, Post-FP2, Post-FP3, Post-Qualifying, Pre-Race, Live Lap $K$). Never use future knowledge (e.g., qualifying outcomes used during practice forecasts, or post-race penalties leaked into pre-race inputs). All evaluations must use rolling-origin or chronological train/validation/test splits.

### Rule 3: Distinguish Reality, Replay, Forecast, and Simulation
You must maintain clear entity and conceptual separation across the four core data modalities:
- **Observed / Ground Truth:** Actual historical records and timing feeds.
- **Historical Replay:** Deterministic re-enactments of observed data constrained to past checkpoints.
- **Model Forecast:** Probabilistic distributions generated at a specific information cutoff.
- **Scenario Simulation:** Synthetic counterfactual "what-if" rollouts (e.g., alternate safety car timing or pit strategies).

### Rule 4: Absolute Empirical Honesty — Never Fabricate
- Never fabricate benchmark results, accuracy numbers, Brier scores, or metric improvements.
- Never invent academic papers, author names, DOIs, or publication citations.
- Never claim a dataset, API, or data field is available without an empirical verification recorded in [docs/research/DATA_AVAILABILITY_AUDIT.md](docs/research/DATA_AVAILABILITY_AUDIT.md).
- Never claim tasks, tests, or milestones are completed unless actually implemented and verified.
- In templates and examples, use clearly marked placeholders (e.g., `[NOT RUN YET]`, `TBD`, `N/A`) rather than plausible fake numbers that could be mistaken for real findings.

### Rule 5: Preserve Working Code & Avoid Speculative Additions
- Respect existing implementations and working tests. Never refactor or delete established modules without an agreed Architecture Decision Record (ADR).
- Do not implement speculative features or third-party dependencies before their prerequisites and data audits are completed and approved.
- Always check that files exist before editing or linking them.

### Rule 6: Rigorous Decision and State Labeling
Use standardized status labels consistently across all documents:

**Decision Statuses (ADRs):**
`PROPOSED` | `APPROVED` | `DEPRECATED` | `REJECTED`

**Hypothesis & Research Statuses:**
`PROPOSED` | `UNDER REVIEW` | `SUPPORTED` | `NOT SUPPORTED` | `REJECTED` | `BLOCKED`

**Experiment Statuses:**
`PLANNED` | `RUNNING` | `COMPLETED` | `FAILED` | `INVALIDATED`

**Task & Milestone Statuses:**
`NOT STARTED` | `IN PROGRESS` | `BLOCKED` | `COMPLETED`

### Rule 7: No AI Slop & Minimal Documentation (Core Engineering Principle)
- **Minimum Necessary Documentation, Maximum Technical Clarity:** Do not create a new Markdown file for every task, experiment, or small implementation. Before creating a file, inspect existing documentation and update the appropriate existing file if covered. Create new files only for genuinely distinct purposes.
- **No AI Filler:** Eliminate generic introductions, conversational filler, repetitive summaries, inflated language, and unsupported claims. Write concisely and technically like a competent engineer/researcher.
- **Evidence-Based Standards:** All documented results must be accurate, verified, reproducible from recorded artifacts, and explicit about limitations. Use compact tables for experimental metrics.
- **Preserve Existing Structure:** Do not retroactively rewrite, delete, or rename working documentation merely to satisfy style preferences. Apply these standards strictly to all new and modified content.

---

## 4. Documentation Consistency Protocols

1. **Relative Hyperlinking:** Always link to referenced documents via relative paths (e.g., `[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)`). Verify that every link resolves.
2. **Concise yet Reproducible:** Keep explanations technically dense and concise. Prioritize reproduction commands, parameter sets, schema definitions, and explicit equations over conversational filler.
3. **Change Logging:** When modifying an existing system or introducing a major research change:
   - Log the rationale in an ADR under [docs/decisions/](docs/decisions/).
   - Update [docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md) and [docs/implementation/CURRENT_MILESTONE.md](docs/implementation/CURRENT_MILESTONE.md).
   - If research methodology changes, update [docs/research/METHODOLOGY.md](docs/research/METHODOLOGY.md) and [docs/research/HYPOTHESES.md](docs/research/HYPOTHESES.md).

---

## 5. End-of-Session Handover Checklist

When concluding any session or milestone, the agent must output a structured handover summary covering:
1. **What changed:** Exactly which files were created, modified, or validated.
2. **What was verified:** Concrete execution commands run and actual outputs observed (e.g., linters, link checks, test suites).
3. **What remains incomplete:** Pending tasks, open questions, or known blockers.
4. **Next recommended action:** The specific next task from [docs/implementation/TASK_BACKLOG.md](docs/implementation/TASK_BACKLOG.md) to execute, its prerequisites, and acceptance criteria.
