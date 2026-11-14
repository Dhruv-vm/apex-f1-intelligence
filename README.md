# APEX — F1 Intelligence

> **Every lap. Every variable. Every possibility.**

[![Milestone](https://img.shields.io/badge/Milestone-0%3A%20Initialization%20%26%20Documentation-00E5FF.svg)](docs/implementation/CURRENT_MILESTONE.md)
[![Status](https://img.shields.io/badge/Status-Scaffold%20Validated-brightgreen.svg)](docs/PROJECT_STATUS.md)
[![License](https://img.shields.io/badge/License-Proprietary%20%2F%20Research-red.svg)](#)

---

## 1. Executive Overview

**APEX — F1 Intelligence** is a long-term, research-driven Formula 1 intelligence platform designed to integrate probabilistic race forecasting, weekend progression analysis, high-frequency telemetry, strategy simulation, and analytical research tools into a cohesive system.

Formula 1 race outcomes are governed by dynamic, non-stationary processes across varying temporal scales: multi-year regulation cycles, circuit evolutionary dynamics, tire degradation physics, changing meteorological conditions, and chaotic in-race interventions such as Safety Cars. Rather than relying on static pre-race predictions or deterministic approximations, APEX investigates a sequential, multimodal probabilistic forecasting framework that updates its predictive distributions as evidence unfolds from free practice through qualifying and into live race checkpoints.

---

## 2. Product Vision & Architecture Scope

APEX is structured into two complementary layers:
1. **Public Presentation & Narrative Engine:** A cinematic, high-performance landing experience reflecting the dark, precise, technical aesthetics of modern motorsport engineering (near-black backgrounds, crisp typography, restrained racing-red accents, and data-dense interactive graphics).
2. **Deep Intelligence Workspace:** A modular analytical suite encompassing 11 dedicated capability modules:

| # | Product Module | Description & Scope |
|---|---|---|
| 1 | **Overview** | Executive dashboard of the ongoing or upcoming Grand Prix weekend. |
| 2 | **Predictions** | Calibrated probabilistic race outcome distributions across sequential checkpoints. |
| 3 | **Live Race** | Real-time race tracking, dynamic gap delta modeling, and probability evolution. |
| 4 | **Telemetry** | Synchronized trace comparisons (speed, throttle, brake, RPM, gear, DRS, tire wear). |
| 5 | **Strategy** | Pit window analysis, undercut/overcut probabilities, and tire degradation curves. |
| 6 | **Analytics** | Longitudinal team/driver pace metrics, qualifying pace deficits, and sector dominances. |
| 7 | **Race Weekend** | Progressive session breakdowns (FP1, FP2, FP3, Qualifying, Sprint, Race). |
| 8 | **Paddock** | Technical upgrades, aerodynamic package trackers, power unit penalty ledgers. |
| 9 | **Probability Markets** | Market implied odds comparison against calibrated model probabilities. |
| 10 | **Model Lab** | Feature importance, ablation comparisons, calibration curves, and Brier score tracking. |
| 11 | **F1 AI** | Natural language reasoning engine grounded in historical timing and telemetry store. |

> *Note: The product scope outlines architectural goals. In Milestone 0, no frontend, backend services, or models have been deployed.*

---

## 3. Working Research Direction

- **Working Title:** *Sequential Multimodal Probabilistic Forecasting of Formula One Race Outcomes Across the Race Weekend and Live Race.*
- **Primary Research Question:** Can sequentially integrating time-aligned Formula One data improve predictive performance and probability calibration of race-outcome forecasts throughout a race weekend and live race, compared with static and single-modality baselines?
- **Candidate Contribution:** A leakage-safe sequential probabilistic forecasting framework updating forecasts dynamically at explicit information cutoffs (pre-weekend, practice sessions, qualifying, pre-race, and live race checkpoints), validated via rolling-origin evaluation on proper scoring rules.

For complete research documentation, consult the [Research Master Index](docs/research/RESEARCH_MASTER.md).

---

## 4. Directory Structure

```text
apex f1/
├── README.md                           # Main repository introduction and orientation
├── AGENTS.md                           # Persistent instructions for AI collaborators
├── .gitignore                          # Repository hygiene for Python, Node, data, and models
├── .env.example                        # Template for environment and configuration keys
│
├── docs/                               # Canonical system documentation
│   ├── PROJECT_CHARTER.md              # Vision, objectives, stakeholders, and governance
│   ├── PROJECT_STATUS.md               # Live project state, milestone tracking, and blockers
│   ├── MASTER_PLAN.md                  # Comprehensive end-to-end development phases
│   ├── ARCHITECTURE.md                 # System components, information boundaries, and pipelines
│   ├── SYSTEM_MAP.md                   # Mermaid diagrams of end-to-end data and modeling flow
│   ├── DATA_DICTIONARY.md              # Provisional data entities, fields, and time semantics
│   ├── DATA_SOURCES.md                 # Inventory of candidate and verified data feeds
│   ├── GLOSSARY.md                     # Domain and statistical terminology reference
│   ├── decisions/                      # Architecture Decision Records (ADRs)
│   ├── research/                       # Formal research protocols, questions, and hypotheses
│   ├── experiments/                    # Experiment tracking logs, ablation plans, and templates
│   └── implementation/                 # Milestones, task backlogs, testing, and issue registers
│
├── notebooks/                          # Collaborative research notebooks (EDA, validation, models)
│   ├── README.md                       # Notebook-first workflow protocol & conventions
│   ├── 00_environment_and_source_checks.ipynb
│   ├── 01_data_source_validation.ipynb
│   └── templates/
│       └── experiment_notebook_template.ipynb
│
├── frontend/                           # Future web application workspace (.gitkeep)
├── backend/                            # Future API and ingestion microservices (.gitkeep)
├── ml/                                 # Future machine learning and probabilistic pipelines (.gitkeep)
├── data/                               # Data storage tiers (raw, interim, processed, external)
├── models/                             # Serialized model artifacts and checkpoints (.gitkeep)
├── scripts/                            # Operational and reproducibility scripts (.gitkeep)
├── tests/                              # Automated test suites (.gitkeep)
└── artifacts/                          # Generated figures, research reports, and exports
```

---

## 5. Canonical Documentation Quick Links

- **Current Status:** [docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md)
- **Active Milestone:** [docs/implementation/CURRENT_MILESTONE.md](docs/implementation/CURRENT_MILESTONE.md)
- **Task Backlog:** [docs/implementation/TASK_BACKLOG.md](docs/implementation/TASK_BACKLOG.md)
- **Architecture Specification:** [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **Research Methodology:** [docs/research/METHODOLOGY.md](docs/research/METHODOLOGY.md)
- **Evaluation Protocol:** [docs/research/EVALUATION_PROTOCOL.md](docs/research/EVALUATION_PROTOCOL.md)
- **Data Availability Audit:** [docs/research/DATA_AVAILABILITY_AUDIT.md](docs/research/DATA_AVAILABILITY_AUDIT.md)
- **Research Notebooks:** [notebooks/README.md](notebooks/README.md)
- **Experiment Index:** [docs/experiments/EXPERIMENT_INDEX.md](docs/experiments/EXPERIMENT_INDEX.md)

---

## 6. Current Status & Future Setup

- **Current State:** Milestone 0 (Project Initialization and Documentation Foundation) is actively in progress and being validated.
- **Dependencies & Packages:** Intentionally not installed during Milestone 0. Package managers, virtual environments, Docker containers, and framework dependencies will be established in subsequent implementation milestones following thorough data availability audits.
- **GitHub Repository:** [https://github.com/Dhruv-vm/apex-f1-intelligence](https://github.com/Dhruv-vm/apex-f1-intelligence)
