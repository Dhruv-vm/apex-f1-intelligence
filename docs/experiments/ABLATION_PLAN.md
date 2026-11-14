# APEX — Feature & Modality Ablation Plan

> **Status:** PLANNED PROTOCOL — Ablation experiments are contingent upon successful completion of Milestone 1 data availability audits and Milestone 2 ingestion pipelines.

---

## 1. Motivation & Objective

Formula 1 prediction models frequently suffer from dimensionality bloat: practitioners add raw telemetry channels, weather metrics, and practice lap aggregates without isolating their marginal contribution to forecast accuracy and calibration.

The objective of this ablation plan is to isolate and quantify the exact value of each information modality, determining whether complex features (e.g., 50 Hz throttle traces) deliver statistically significant gains over parsimonious timing baselines.

---

## 2. Planned Modality Tiers

Feature sets are partitioned into five cumulative tiers:

| Modality Tier | Tier Name | Content / Features | Availability Checkpoint |
|---|---|---|---|
| **Tier 0** | **Historical Ratings** | Rolling driver Elo, constructor championship standings, circuit historical safety car frequency. | $T_0$ (Pre-Weekend) |
| **Tier 1** | **Free Practice Aggregates** | FP1–FP3 fastest lap deltas, FP2 long-run degradation slopes, stint lap counts. | $T_1 \dots T_3$ (Post-Practice) |
| **Tier 2** | **Qualifying Order & Speed** | Official starting grid, delta to pole ($\Delta_{\text{pole}}$), speed trap velocities, Q3 sector times. | $T_4$ (Post-Qualifying) |
| **Tier 3** | **High-Frequency Telemetry** | Corner apex minimum speeds, throttle application points, brake event durations, DRS efficiency. | $T_4$ (Post-Qualifying) |
| **Tier 4** | **Environmental & Track State**| Track surface temperature, ambient humidity, rain risk probability, track evolution slope. | $T_5$ (Pre-Race) |

---

## 3. Systematic Ablation Matrix

The following experimental matrix will be executed during Milestone 4:

| Ablation Run | Tier 0 (Historical) | Tier 1 (Practice Pace) | Tier 2 (Quali Order) | Tier 3 (Telemetry) | Tier 4 (Weather) | Scientific Target |
|---|:---:|:---:|:---:|:---:|:---:|---|
| **ABL-BASE** | Included | Excluded | Excluded | Excluded | Excluded | Pure static historical baseline |
| **ABL-FP** | Included | **Included** | Excluded | Excluded | Excluded | Measure marginal value of practice pace |
| **ABL-QUALI** | Included | Included | **Included** | Excluded | Excluded | Benchmark standard weekend progression |
| **ABL-TELEM** | Included | Included | Included | **Included** | Excluded | Test [HYP-0003](../research/HYPOTHESES.md#hyp-0003-modality-parsimony-and-leakage-sensitivity) (Telemetry noise) |
| **ABL-FULL** | Included | Included | Included | Included | **Included** | Complete multimodal pipeline |
| **ABL-NO-FP** | Included | **Excluded** | Included | Excluded | Excluded | Counterfactual: Does Quali alone obsolete FP data? |

---

## 4. Evaluation Criteria for Feature Inclusion

A feature modality will only be retained in the default production pipeline if:
1. It reduces multi-class Log Loss by $\ge 0.015$ or Brier Score by $\ge 0.008$ ($p < 0.05$).
2. It does not degrade Expected Calibration Error ($ECE$).
3. Missingness in the audited provider feed is $< 2.0\%$ across historical test seasons.
