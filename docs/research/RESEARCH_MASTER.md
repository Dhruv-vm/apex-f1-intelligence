# APEX — Research Master Index & Status

## 1. Executive Research Overview

- **Working Title:** *Sequential Multimodal Probabilistic Forecasting of Formula One Race Outcomes Across the Race Weekend and Live Race*
- **Research Lead / Core Investigator:** APEX Core Engineering & AI Collaboration Team
- **Current Status:** Foundation Stage (`PROPOSED` working methodology, zero empirical results established)

The primary goal of APEX research is to formulate, implement, and benchmark a leakage-free sequential forecasting framework for Formula 1 Grands Prix. Modern motorsport presents a distinct temporal machine learning challenge: non-stationary data streams arriving across distinct session checkpoints (FP1, FP2, FP3, Qualifying, Pre-Race, Live Lap $K$), high-stakes tail risks (DNFs, safety cars, weather transitions), and small out-of-sample sample sizes ($20–24$ events per season).

---

## 2. Research Document Directory & Index

Every formal research component is documented in its dedicated document linked below:

| Document | Primary Focus | Status |
|---|---|---|
| [RESEARCH_QUESTIONS.md](RESEARCH_QUESTIONS.md) | Primary and secondary testable scientific questions | `APPROVED` (Questions formulated) |
| [HYPOTHESES.md](HYPOTHESES.md) | Formal hypothesis registry with null/alternative formulations | `PROPOSED` (Awaiting experiments) |
| [LITERATURE_REVIEW.md](LITERATURE_REVIEW.md) | Systematic academic and industry literature tracker | `UNDER REVIEW` (Verification protocol active) |
| [RELATED_WORK.md](RELATED_WORK.md) | Comparative analysis of existing motorsport & sports forecasting models | `UNDER REVIEW` (Taxonomy established) |
| [METHODOLOGY.md](METHODOLOGY.md) | Mathematical specification of sequential probabilistic forecasting | `PROPOSED` (Candidate method) |
| [EVALUATION_PROTOCOL.md](EVALUATION_PROTOCOL.md) | Scoring rules (Brier, Log Loss), calibration curves, rolling-origin backtesting | `APPROVED` (Protocol established) |
| [DATA_AVAILABILITY_AUDIT.md](DATA_AVAILABILITY_AUDIT.md) | Empirical audit of FastF1, Jolpica, OpenF1, and meteorological feeds | `VERIFIED` (Audited in M1) |
| [RESEARCH_LIMITATIONS.md](RESEARCH_LIMITATIONS.md) | Documented constraints, data gaps, censored events, regulation shifts | `ACTIVE` (Living document) |
| [FUTURE_DIRECTIONS.md](FUTURE_DIRECTIONS.md) | Long-range extensions (deep state-space models, computer vision) | `PROPOSED` (Future horizons) |
| [Collaborative Notebooks](../../notebooks/README.md) | Notebook-first collaborative research surface (EDA, models, ablations) | `ACTIVE` (Scaffolded in M1) |

---

## 3. Evidence Status Schema

To prevent confirmation bias and maintain scientific rigor, all hypotheses and experimental claims must adhere to the standardized evidence status taxonomy:

- `PROPOSED`: Formulated logically based on motorsport domain theory; no empirical backtesting completed.
- `UNDER REVIEW`: Active experiment designed or currently executing; data collection underway.
- `SUPPORTED`: Validated by statistically significant improvements on out-of-sample proper scoring rules with zero temporal leakage.
- `NOT SUPPORTED`: Out-of-sample empirical results show no statistically significant improvement over baselines.
- `REJECTED`: Empirical evidence demonstrates degraded predictive skill, severe miscalibration, or unmitigated temporal leakage.
- `BLOCKED`: Experiment cannot proceed due to missing data feeds, provider rate limits, or unresolved data audits.

---

## 4. Current Research Summary

At Milestone 0:
- **Number of Verified Papers:** 0 (Literature review templates initialized; bibliography pending empirical verification).
- **Number of Backtested Seasons:** 0 (Data ingestion pending Milestone 1 & 2).
- **Supported Hypotheses:** 0.
- **Active Hypotheses:** 4 formulated under `PROPOSED` status in [HYPOTHESES.md](HYPOTHESES.md).
