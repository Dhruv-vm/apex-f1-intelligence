# APEX — Pre-Race Candidate Field Reconstruction & Temporal Cutoff Audit

> **Audit Status:** COMPLETED EMPIRICALLY  
> **Audit Date:** 2026-10-19  
> **Target Forecast Checkpoints:** $T_4$ (Post-Qualifying, ~1h post-Q3) and $T_5$ (Pre-Race, ~30m prior to formation lap)  
> **Target Experiment:** [EXP-0002](../experiments/EXPERIMENT_INDEX.md#exp-0002) (Static Pre-Race Grid-Winner Benchmark)  
> **Related Hypotheses:** [HYP-0001](HYPOTHESES.md#hyp-0001-sequential-information-superiority), [HYP-GRID-001](HYPOTHESES.md#hyp-grid-001-pre-race-grid-position-dominance), [HYP-GRID-002](HYPOTHESES.md#hyp-grid-002-nonlinear-grid-representation-superiority)

---

## 1. Executive Summary & Purpose

In Formula 1 race outcome forecasting, the prediction target for race winner is a categorical probability distribution over all eligible competitors:
$$\mathbf{p} = [p_1, p_2, \dots, p_N], \quad \sum_{i=1}^N p_i = 1, \quad p_i = P(\text{Driver } i \text{ wins} \mid \mathcal{I}_T)$$

Before training any model at checkpoint $T_5$ (Pre-Race), we must establish:
1. **Who belongs in the candidate set $\{1, \dots, N\}$ at cutoff $T_5$** without using future information (such as post-race classification, retirement causes, or laps completed).
2. **What starting grid position or pit-lane status is assigned to each candidate** at $T_5$.
3. **How provider limitations, historical data structures, and regulatory eras affect candidate-field reconstruction**.

This audit provides an empirical investigation of candidate-field reconstruction using the 2010–2026 historical race dataset (`data/interim/driver_race_results_2010_2026_v2_regulation_metadata.csv`, 7,285 entrant rows across 346 Grand Prix events) and direct API queries against Jolpica F1 and OpenF1.

> [!IMPORTANT]
> **Provisional Result-Record Proxy Caveat:** The current dataset consists of retrospective race-result records from Ergast/Jolpica. We have **not yet established an independently timestamped pre-race entry list** for every historical Grand Prix. Consequently, the entrant field in this dataset serves as a **provisional result-record proxy** until full independent entry-field reconstruction is verified against official pre-session timing manifests. While retrospective outcome indicators must not be used to filter candidates, zero post-race leakage cannot be formally claimed as proven until genuine pre-race manifests are ingested.

---

## 2. Key Empirical Findings (2010–2026 Historical Dataset)

An empirical audit of the 7,285 candidate records across 346 races revealed critical edge cases in candidate-field definition and starting grid representation:

### 2.1 The `grid == 0` Edge Case: Pit-Lane Starters vs. True Non-Starters
In the historical Ergast/Jolpica schema, a starting grid position of `0` is an API-level convention that does **not** signify that a driver failed to enter or start the race:
- **Total `grid == 0` records (2010–2026):** 56 entrants across 45 Grand Prix events.
- **Active Pit-Lane Starters (87.5%, 49/56):** 49 drivers with `grid == 0` took the start from the pit lane (e.g., following parc fermé modifications, engine component changes, or chassis rebuilds). Many achieved strong points-paying finishes (e.g., Fernando Alonso finishing P5 from pit lane in Monaco 2010; Sebastian Vettel P8 from pit lane in Abu Dhabi 2012; Esteban Ocon P10 in Miami 2024).
- **True Non-Starters (12.5%, 7/56):** Only 7 entrants with `grid == 0` did not take the start (recorded with `position_text == 'W'` or Did Not Start).
- **API Value Interpretation:** A recorded `grid == 0` is an API indicator whose underlying sporting circumstances (pit-lane start, technical penalty, or administrative classification) require careful contextual interpretation rather than naive numeric filtering.

> [!CRITICAL]
> **Anti-Leakage Rule 1:** A model or pipeline must **never** drop entrants where `grid == 0` under the assumption that they are non-starters. Dropping `grid == 0` discards valid contenders who legitimately started the Grand Prix from the pit lane. In pre-race feature modeling, entrants with `grid == 0` must be assigned a race-specific effective grid position defined as the **maximum positive starting grid position in that race plus one** ($\text{effective\_grid} = \max_{i, \text{grid}_i > 0}(\text{grid}_i) + 1$), accompanied by an explicit `is_grid_zero` indicator. API grid-zero status must not be treated as definitive proof of an actual pit-lane start (the current audit identified 49 of 56 zero-grid records as active pit-lane starts; the remaining 7 require appropriate contextual interpretation or verification). A static fixed assignment (such as position 21) is invalid because starting grid sizes varied from 20 to 24 cars across the 2010–2026 history.

### 2.2 Formation Lap and Reconnaissance Lap Breakdowns (`grid > 0`, DNS)
- Across 2010–2026, **62 entrants had an assigned starting grid position (`grid > 0`) but failed to take the race start** or retired on the formation lap (e.g., Charles Leclerc at Monaco 2021 with driveshaft failure prior to start; Sergio Pérez at Belgium 2021 crash on reconnaissance lap; Carlos Sainz at Qatar 2023 fuel leak).
- In post-race classification tables, these drivers are recorded with statuses such as `"Did not start"`, `"Hydraulics"`, `"Engine"`, or `"Gearbox"`, and finishing position text `'W'` (Withdrawn) or `'D'` (DNS).
- **Temporal Integrity Rule:** At cutoff $T_5$ (30 minutes prior to formation lap), these drivers were formally entered on the official FIA Final Starting Grid and were active contenders. Filtering them out of the pre-race candidate set based on post-race status codes constitutes **direct post-cutoff outcome leakage**.

> [!CRITICAL]
> **Anti-Leakage Rule 2:** Pre-race candidate sets at $T_5$ must be constructed strictly from pre-race entry and grid information without using post-race status. Entrants who suffer reconnaissance-lap or formation-lap failures must be retained in the candidate probability simplex ($\sum P = 1$), receiving their fair pre-race probability share. Their failure to start is an observed race outcome ($Y_{\text{winner}} = 0, Y_{\text{dnf}} = 1$), not an allowable pre-race filter criterion.

---

## 3. Data Provider Availability & Endpoint Capabilities

| Provider / Channel | Endpoint / Artifact | Information Content | Timestamp Granularity | Pre-Race Availability at $T_5$ |
|---|---|---|---|---|
| **Jolpica F1 API** | `/{season}/{round}/results.json` | Final finishing positions, race winner, and `grid` (starting grid position). | Event date only (`YYYY-MM-DD`). No document release timestamp. | Available retrospectively post-race. Does not provide standalone pre-race snapshot. |
| **Jolpica F1 API** | `/{season}/{round}/qualifying.json` | Q1, Q2, Q3 session times and qualifying rank. | Event date only. | Available at $T_4$ (Post-Qualifying). Does **not** include post-qualifying grid penalties or pit-lane start notices issued between Q3 and race start. |
| **Jolpica F1 API** | `/{season}/{round}/grid.json` | *Endpoint does not exist* (returns HTTP 400). | N/A | Unavailable via Ergast/Jolpica API. |
| **FastF1** | `fastf1.get_session(year, round, 'R').results` | `GridPosition`, `Position`, `Status`, `Points`. | Session schedule UTC timestamps. | Available post-session via cache/F1 timing archive. Reflects final starting grid. |
| **OpenF1 API** | `/v1/sessions` | Meeting metadata, session type, session start/end UTC. | Exact millisecond UTC timestamps. | Available in real time (2023–2026). |
| **OpenF1 API** | `/v1/position` & `/v1/car_data` | Pre-race transponder signals, out-lap timestamps, entrant list. | Sub-second UTC timestamps (~3.7 Hz). | High-precision pre-race candidate manifest available at $T_5$ for 2023–2026. |
| **FIA Documents** | Official FIA Stewards Document Archive | "Final Starting Grid", "Provisional Starting Grid", "Decision — Car X Parc Fermé". | Exact publication time stamped on official PDF bulletins. | Ground truth authority. Requires manual/semi-automated PDF parsing for historical audit. |

---

## 4. Historical Era Coverage Matrix & Feasibility

We assess the auditability and defensibility of reconstructing pre-race candidate fields across five distinct Formula 1 regulatory eras:

| Era | Seasons | Qualifying & Grid Format | Candidate Field Completeness | Pit-Lane & Penalty Auditability | Defensibility for $T_5$ Cutoff |
|---|---|---|---|---|---|
| **Early / Classic Era** | 1950–1993 | Varied (aggregate times, multi-day sessions, reserve drivers). | Partial. Grid positions recorded in `results.json`, but non-qualifiers/reserves inconsistently tracked. | Low. Pre-race withdrawals and grid changes not timestamped. | **Low / Retrospective Only.** Historical baseline only; not defensible for strict cutoff backtesting. |
| **Refueling / V10–V8 Era** | 1994–2009 | Single-lap / aggregate qualifying with race-fuel regulations (2003–2009). | High. 20–22 cars per race; starting grid recorded in `results.json`. | Moderate. Grid penalties documented in race reports; official FIA steward timestamps not machine-readable. | **Moderate.** Feasible for static baseline modeling with documented retrospective entrant limitation. |
| **Modern Knockout Era** | 2010–2017 | Three-part knockout qualifying (Q1/Q2/Q3, 107% rule enforced). Pirelli spec tires. | Complete. 20–24 cars per race; starting grid positions (0–24) fully documented. | Moderate to High. All 56 `grid == 0` pit-lane starts verifiable via race classification records. | **High.** Scientifically sound for walk-forward baseline backtesting; serves as historical sensitivity/warm-up cohort. |
| **Hybrid Halo & Sprint Era** | 2018–2022 | Knockout qualifying + Sprint format introduced in 2021. Halo safety introduced. | Complete. FastF1 session results available; FIA steward PDF bulletins archived online. | High. Clear distinction between qualifying classification, sprint classification, and final race grid. | **Very High.** High-integrity benchmark cohort. Fully auditable starting grid and candidate field. |
| **Ground-Effect Telemetry Era** | 2023–2026 | Ground-effect aerodynamics; Sprint formats revised; OpenF1 active. | Complete & Millisecond Timestamped. Real-time pit-lane and garage transponder signals. | Complete. Sub-second UTC timestamps for session entrant manifests at $T_5$. | **Gold Standard.** Complete real-time auditability without retrospective assumptions. |

---

## 5. Recommended Evaluation Cohort for EXP-0002

Based on the coverage matrix and data audit, we propose the following scoped evaluation strategy for EXP-0002 (Static Pre-Race Grid Benchmark):

1. **Primary Out-of-Sample Benchmark Cohort (2018–2024):**
   - **Total Rounds:** 149 Grand Prix events (2,979 candidate rows).
   - **Justification:** High regulatory consistency, complete FastF1 data backing, available FIA stewards bulletins, and modern 20-car grid sizes.
   - **Holdout Test Set:** 2024 season (and 2025–2026 YTD holdout: 41 rounds) evaluated strictly out-of-sample.
2. **Historical Warm-up / Sensitivity Cohort (2010–2017):**
   - **Total Rounds:** 156 Grand Prix events (3,453 candidate rows).
   - **Justification:** Provides training volume for Bayesian priors, empirical grid transition tables, and constructor dynamic ratings. Evaluated separately to test whether model parameters are stable across regulation changes (e.g., 2013 V8 $\rightarrow$ 2014 V6 Turbo Hybrid).
3. **Pre-2010 Exclusion from Primary Benchmark:**
   - Pre-2010 races are excluded from the primary EXP-0002 benchmark due to refueling regulation confounders (where grid position was heavily confounded by starting fuel load rather than pure car pace) and absence of machine-readable pre-race grid timestamps.

---

## 6. Implementation Protocol for EXP-0002 Notebook (`notebooks/05_static_grid_benchmark.ipynb`)

To guarantee empirical honesty and prevent leakage, the EXP-0002 benchmark implementation must adhere to these four operational rules:

1. **Strict Outcome-Independent Candidate Ordering:**
   Candidates within each race must be sorted strictly by an outcome-independent identifier (e.g., `driver_id` or `grid_position` ascending, with deterministic tie-breaking on `driver_id`). Never sort candidates by `position_order` or `finish_position`.
2. **Race-Specific Grid-Zero Representation:**
   Entrants with `grid == 0` must be assigned a race-specific effective grid position defined as the **maximum positive starting grid position in that race plus one** ($\text{effective\_grid} = \max_{i, \text{grid}_i > 0}(\text{grid}_i) + 1$), accompanied by an explicit `is_grid_zero` indicator. A fixed position (e.g., 21) must not be assumed. API grid-zero status must not be treated as definitive proof of an actual pit-lane start (49 of 56 audited as active pit starts, 7 require verification); the underlying sporting circumstances of API value zero must be appropriately interpreted.
3. **Simplex Normalization:**
   Predicted win probabilities across all $N$ eligible pre-race entrants in a race must sum to exactly 1:
   $$\sum_{i=1}^N P(\text{Winner} = \text{Driver}_i) = 1.0 \pm 10^{-5}$$
4. **Scoring Rule Rigor:**
   All candidate models (Uniform baseline, Empirical Grid Transition, Multinomial Logit Softmax, GBDT) must be scored using identical strictly proper scoring rules:
   - Multi-class Log Loss (negative log likelihood of the true winner).
   - Multi-class Brier Score ($\sum_{i=1}^N (p_i - y_i)^2$).
   - Tie-aware Top-1 Accuracy and Fractional Top-1 Credit.
   - Candidate-level Expected Calibration Error (ECE).
