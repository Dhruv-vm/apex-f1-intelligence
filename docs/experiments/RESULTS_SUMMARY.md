# APEX — Scientific Results & Benchmark Summary

This document synthesizes all verified empirical results across discrete weekend checkpoints.

---

## 1. Benchmark Performance Overview

### Primary Benchmark Cohort: 2018–2024 Modern Hybrid Era (149 Rounds, 2,979 Candidate Records)

| Checkpoint | Model Identifier | Model Family | Multi-Class Log Loss | Multi-Class Brier Score | Fractional Top-1 | Tie-Aware Top-1 | Statistically Superior to Baseline? |
|---|---|---|---:|---:|---:|---:|---|
| **$T_0$: Pre-Weekend** | `EXP-0001-R3` | Driver Pairwise Elo | 2.278177* | 0.845726* | 0.332490* | 0.335260* | Yes (vs Uniform: Log Loss 3.044556, Brier 0.952264) |
| **$T_5$: Pre-Race** | `EXP-0002-M0` | Uniform Baseline ($1/N_r$) | 2.995388 | 0.949982 | 0.050018 | 1.000000 | Baseline |
| **$T_5$: Pre-Race** | `EXP-0002-M1` | Empirical Grid Table ($\alpha=10$) | 1.583766 | 0.682312 | 0.496644 | 0.496644 | Yes (vs Uniform: $\Delta \text{LL} = -1.4116$, $p < 10^{-15}$) |
| **$T_5$: Pre-Race** | `EXP-0002-M2` | Grid-Only Logistic (5 feat.) | 1.594207 | 0.683382 | 0.496644 | 0.496644 | Yes (vs Uniform: $\Delta \text{LL} = -1.4012$, $p < 10^{-15}$) |
| **$T_5$: Pre-Race** | `EXP-0002-M3` | Grid + Form Logistic (16 feat.) | **1.355201** | **0.612698** | 0.516779 | 0.516779 | **Best Overall Probabilistic Performance** ($\Delta \text{LL} = -0.2390$ vs M2) |
| **$T_5$: Pre-Race** | `EXP-0002-M4` | LightGBM GBDT (16 feat.) | 1.409149 | 0.628561 | **0.530201** | **0.530201** | **Best Argmax Accuracy**, but inferior on proper scoring rules |
| **$T_1$: Post-FP1** | *Pending Sequential M4* | Single-Lap Pace GBDT | `[PLANNED]` | `[PLANNED]` | `[PLANNED]` | `[PLANNED]` | — |
| **$T_2$: Post-FP2** | *Pending Sequential M4* | FP2 Stint Pace Degradation | `[PLANNED]` | `[PLANNED]` | `[PLANNED]` | `[PLANNED]` | — |
| **$T_3$: Post-FP3** | *Pending Sequential M4* | Qualifying Sim Delta | `[PLANNED]` | `[PLANNED]` | `[PLANNED]` | `[PLANNED]` | — |
| **$T_4$: Post-Qualifying** | *Pending Baseline M4* | Official Qualifying Classification | `[PLANNED]` | `[PLANNED]` | `[PLANNED]` | `[PLANNED]` | — |

*\*Note: EXP-0001-R3 metrics reflect the full 346-race series (2010–2026).*

---

## 2. Full Historical Series Overview (2010–2026, 346 Rounds, 7,285 Candidate Records)

| Model | Model Family | Multi-Class Log Loss | Multi-Class Brier Score | Fractional Top-1 | Tie-Aware Top-1 |
|---|---|---:|---:|---:|---:|
| **Model 0** | Uniform Baseline ($1/N_r$) | 3.044556 | 0.952264 | 0.047736 | 1.000000 |
| **Model 1** | Empirical Grid Frequency | 1.519516 | 0.657880 | 0.523242 | 0.531792 |
| **Model 2** | Grid-Only Logistic Regression | 1.541942 | 0.662375 | 0.508200 | 0.563584 |
| **Model 3** | Grid + Form Logistic Regression | **1.419383** | **0.624583** | **0.525541** | **0.580925** |
| **Model 4** | LightGBM Gradient Boosted Trees | 1.522650 | 0.650861 | 0.516870 | 0.572254 |

---

## 3. Scientific Hypothesis Outcomes

| Hypothesis ID | Scientific Question | Current Evidence Status | Verified Empirical Evidence |
|---|---|---|---|
| [HYP-0001](../research/HYPOTHESES.md#hyp-0001-sequential-information-superiority) | Sequential Information Superiority | **PARTIALLY SUPPORTED** | Qualifying/grid arrival demonstrates significant information gain ($T_4$ vs $T_0$ $\Delta \text{LogLoss} = -0.2095$, raw Wilcoxon $p = 0.000812 < 0.001$, Holm-Bonferroni adjusted $p = 0.00244$), but multi-season practice superiority ($T_1 \dots T_3$) remains unproven at scale due to historical archive sparsity. |
| [HYP-GRID-001](../research/HYPOTHESES.md#hyp-grid-001-pre-race-grid-position-dominance) | Pre-Race Grid Position Dominance | **SUPPORTED** | Starting grid alone outperforms dynamic ratings by $\Delta \text{LL} = -0.6944$ ($p < 10^{-15}$). |
| [HYP-GRID-002](../research/HYPOTHESES.md#hyp-grid-002-nonlinear-grid-representation-superiority) | Nonlinear Grid + Form Superiority | **SUPPORTED** | Adding form features to grid cuts log loss from `1.5942` to `1.3552` (paired Wilcoxon $p < 10^{-6}$). |
| **HYP-GBDT-001** | GBDT Superiority under Proper Scoring | **NOT SUPPORTED** | LightGBM gains `+1.34%` in raw Top-1 accuracy, but **degrades Log Loss by +0.0539** and **Brier Score by +0.0159** due to tail probability overconfidence. |
