# APEX — Empirical Data Availability Audit & Provider Verification

> **Audit Status:** VERIFIED EMPIRICALLY  
> **Audit Date:** 2026-10-18  
> **Audit Scripts Executed:** [scripts/audit/audit_jolpica.py](../../scripts/audit/audit_jolpica.py), [scripts/audit/audit_openf1.py](../../scripts/audit/audit_openf1.py), [scripts/audit/audit_fastf1.py](../../scripts/audit/audit_fastf1.py), [scripts/audit/run_audit_summary.py](../../scripts/audit/run_audit_summary.py)  
> **Consolidated Audit JSON:** [artifacts/reports/data_availability_audit_summary.json](../../artifacts/reports/data_availability_audit_summary.json)

---

## 1. Executive Summary & Critical Findings

An empirical audit was conducted on October 18, 2026 across candidate Formula 1 data providers to establish verifiable coverage, timestamp granularity, missingness rates, rate limiting, and authentication gates.

### Critical Empirical Findings:
1. **Jolpica F1 API (Verified Drop-in Ergast Replacement):**
   - Correct base URL is `https://api.jolpi.ca/ergast/f1` (not `.com`).
   - Completely open, unauthenticated REST API covering **1950 through 2025 (76 complete championship seasons)** and **2026 Year-to-Date** (5 completed rounds with results posted as of October 18, 2026).
   - High fidelity for race results, qualifying classifications, constructor/driver standings, and pit stop durations (from 2011 onward). Average query latency: 700ms–1600ms.
2. **OpenF1 Community API (Verified Telemetry & Real-Time Engine):**
   - Open, unauthenticated REST & WebSocket API at `https://api.openf1.org/v1`.
   - Verified active coverage for **2023, 2024, 2025, and 2026 Year-to-Date** (21 meetings occurred; 19 completed race sessions).
   - **Pre-2023 seasons (2021, 2022) return HTTP 404 (Not Found)**; OpenF1 does not maintain archives prior to 2023.
   - Granular channels verified: sub-second lap timing, sector 1/2/3 durations, car telemetry (speed, throttle, brake, RPM, DRS, gear; sampled at approximately **3.7 Hz** according to official documentation: [https://openf1.org/docs/](https://openf1.org/docs/)), stint tyre compounds & age, pit lane/stop durations, track/air weather, and race control messages.
   - **Rate Limiting:** OpenF1 enforces strict rate limits. Rapid unthrottled bursts return `HTTP 429: Too Many Requests`. Ingestion clients must enforce a 0.3s–0.5s inter-request delay.
3. **FastF1 / Official F1 Live Timing Upstream (Authentication Gated):**
   - Specific tested endpoints on `https://livetiming.formula1.com/static/...` returned `HTTP 401 Unauthorized` for unauthenticated requests.
   - This HTTP 401 response is evidence that direct access to that particular static archive endpoint requires credentials (such as an F1 account token via `f1auth.json`). It is not proof that every FastF1 feature, local cache workflow, or alternative endpoint is inaccessible.
   - FastF1 remains an effective library when provided with an F1 account token or when loading pre-cached session files from `data/raw/fastf1_cache/`.

---

## 2. Multi-Season Provider Coverage Matrix

The table below delineates verified data availability across historical eras and the current 2026 championship (evaluated as of October 18, 2026):

| Data Dimension / Entity | Historical Era (1950–2010) | Hybrid Era I (2011–2022) | Modern Telemetry (2023–2025) | Current Season (2026 Year-to-Date) | Verified Primary Provider |
|---|:---:|:---:|:---:|:---:|---|
| **Championship Calendar & Schedule** | Verified (Jolpica) | Verified (Jolpica) | Verified (Jolpica & OpenF1) | Verified (23 rounds Jolpica, 27 meetings OpenF1) | Jolpica / OpenF1 |
| **Race Results & Classifications** | Verified (Jolpica) | Verified (Jolpica) | Verified (Jolpica & OpenF1) | Verified (Rounds 1–5 Jolpica; 19 rounds OpenF1) | Jolpica / OpenF1 |
| **Qualifying Classifications (Q1/Q2/Q3)** | Partial (from 1996) | Verified (Jolpica) | Verified (Jolpica & OpenF1) | Verified (Jolpica & OpenF1) | Jolpica / OpenF1 |
| **Driver & Constructor Standings** | Verified (Jolpica) | Verified (Jolpica) | Verified (Jolpica) | Verified (Jolpica) | Jolpica |
| **Pit Stop Durations** | Unavailable | Verified (2011–2022 Jolpica) | Verified (Jolpica & OpenF1) | Verified (Jolpica & OpenF1) | Jolpica / OpenF1 |
| **Official Sector Times (S1/S2/S3)** | Unavailable | FastF1 (Auth or local cache required) | Verified (OpenF1) | Verified (OpenF1) | OpenF1 |
| **Car Telemetry (Speed, Throttle, Brake)** | Unavailable | FastF1 (Auth or local cache required) | Verified (OpenF1 @ ~3.7 Hz) | Verified (OpenF1 @ ~3.7 Hz) | OpenF1 |
| **Tyre Compound Allocation & Age** | Unavailable | FastF1 (Auth or local cache required) | Verified (OpenF1 `stints`) | Verified (OpenF1 `stints`) | OpenF1 |
| **Track & Ambient Weather** | Session summaries | Session summaries | Verified (OpenF1 1-min intervals) | Verified (OpenF1 1-min intervals) | OpenF1 |
| **Race Control Flags & SC Messages** | Text notes | Text notes | Verified (OpenF1 `race_control`) | Verified (OpenF1 `race_control`) | OpenF1 |
| **Live Intervals & Gaps** | Unavailable | Unavailable | Verified (OpenF1 `intervals`) | Verified (OpenF1 `intervals`) | OpenF1 |

---

## 3. Current 2026 Season Status (Year-to-Date as of October 18, 2026)

- **Total Scheduled Rounds:** 24 Grand Prix rounds (OpenF1 catalogs 27 meetings including pre-season tests).
- **Completed Events:** 21 meetings completed up to October 18, 2026 (most recently Singapore Grand Prix on October 9–11).
- **Jolpica Ingestion State:** Results for Rounds 1–5 posted (Australia, China, Japan, Miami, Canada). Rounds 6–21 results in community curation.
- **OpenF1 Ingestion State:** Full session metadata available for all 21 completed meetings; detailed lap series verified for early rounds; late-season sessions require throttled ingestion.
- **Upcoming Events (Remaining 2026 Schedule):**
  1. Round 19: United States Grand Prix (Austin) — 2026-10-23 to 2026-10-25
  2. Round 20: Mexico City Grand Prix — 2026-10-30 to 2026-11-01
  3. Round 21: São Paulo Grand Prix (Interlagos) — 2026-11-06 to 2026-11-08
  4. Round 22: Las Vegas Grand Prix — 2026-11-19 to 2026-11-21
  5. Round 23: Qatar Grand Prix (Lusail) — 2026-11-27 to 2026-11-29
  6. Round 24: Abu Dhabi Grand Prix (Yas Marina) — 2026-12-04 to 2026-12-06

---

## 4. Post-Session vs. Real-Time Latency Analysis

| Provider | Access Modality | Latency / Availability Window | Suitable Checkpoints | Unsuitable Checkpoints |
|---|---|---|---|---|
| **Jolpica F1 API** | Historical REST | Typically available 2 to 24 hours post-session | $T_0$ (Pre-Weekend), $T_4$ (Post-Quali backtesting), Historical baselines | $T_6$ (Live Lap $K$), Real-time formation lap updates |
| **OpenF1 REST** | In-Session / Post-Session REST | Near-instant to ~15 min post-session; historical archives instant | $T_1 \dots T_3$ (Practice), $T_4$ (Quali), $T_5$ (Pre-Race), Historical replay | High-frequency HFT execution |
| **OpenF1 Live Stream** | WebSocket Streaming | Sub-second live event push | $T_6$ (Live Race Lap $K$), live telemetry visualizer | Offline historical training |
| **FastF1 (Local Cache)**| Python Object Interface | Offline parsing of cached files | $T_1 \dots T_4$ backtesting (when tokens available) | Zero-token CI automated tests |

---

## 5. Feasible Forecasting Targets & Checkpoint Boundaries

Based strictly on audited data availability, the project's forecast checkpoints are formalized as follows:

```text
[T0: Pre-Weekend] ──▶ [T1: Post-FP1] ──▶ [T2: Post-FP2] ──▶ [T3: Post-FP3] ──▶ [T4: Post-Quali] ──▶ [T5: Pre-Race] ──▶ [T6: Live Lap K]
   (1950–2026)          (2023–2026)       (2023–2026)       (2023–2026)       (1950–2026)       (2023–2026)       (2023–2026)
```

### Checkpoint Specifications & Feasibility:
1. **Checkpoint $T_0$ (Pre-Weekend):**
   - **Feasibility:** Fully feasible from 1950 to 2026.
   - **Data Sources:** Jolpica historical race results, constructor standings, driver Elo ratings, circuit historical safety car rates.
   - **Information Cutoff:** Wednesday 23:59 UTC prior to event.
2. **Checkpoints $T_1, T_2, T_3$ (Free Practice 1, 2, 3):**
   - **Feasibility:** Feasible for **2023–2026 via OpenF1** (and 2018–2022 only if FastF1 cache is supplied).
   - **Data Sources:** OpenF1 `laps` (FP long-run degradation slopes, fuel-adjusted pace deltas), OpenF1 `weather` (track evolution).
   - **Information Cutoff:** Official session checkered flag timestamp.
3. **Checkpoint $T_4$ (Post-Qualifying):**
   - **Feasibility:** Fully feasible from 1996 to 2026 via Jolpica; enhanced sector deltas feasible 2023–2026 via OpenF1.
   - **Data Sources:** Official starting grid, Q1/Q2/Q3 lap times, delta to pole ($\Delta_{\text{pole}}$), sector dominance.
   - **Information Cutoff:** 60 minutes post-Q3 session conclusion (capturing initial grid penalties).
4. **Checkpoint $T_5$ (Pre-Race):**
   - **Feasibility:** Feasible for **2023–2026 via OpenF1**.
   - **Data Sources:** Declared starting tyre compound (`stints`), pit lane starts, formation lap track surface temperature.
   - **Information Cutoff:** 20 minutes prior to race formation lap.
5. **Checkpoint $T_6$ (Live Race Lap $K$):**
   - **Feasibility:** Feasible for **2023–2026 via OpenF1 `intervals`, `pit`, `stints`, and `race_control`**.
   - **Data Sources:** Gap to leader, interval to car ahead/behind, tyre age in laps, safety car / VSC state.
   - **Information Cutoff:** Timestamp when driver crosses start/finish line on Lap $K$.

---

## 6. Data Rights, Licensing & Terms of Use

1. **Jolpica F1 API:**
   - License: MIT License (Community-maintained open API, non-commercial research use).
   - Terms: Requests should be polite and cached locally; bulk scraping should respect reasonable rate limits.
2. **OpenF1 Community API:**
   - License: Open Source (Community project under GPL / Open Data guidelines).
   - Terms: Attribution required. Strict rate limiting enforced by cloud hosting provider. No abuse of public infrastructure.
3. **Formula One Digital Media & FOM Invariants:**
   - Telemetry and timing data are utilized strictly for non-commercial scientific research, probability calibration, and educational demonstration under fair use doctrine.
   - Proprietary live broadcast feeds, video streams, and commercial branding are strictly excluded from repository code and storage.

---

## 7. Recommended Initial Forecasting Dataset & First Baseline

### Initial Recommended Dataset Architecture:
- **Layer 1 (Broad Historical Baseline Dataset):** Seasons **2018–2025 (Complete) + 2026 YTD** ingested via **Jolpica F1 API**.
  - Total volume: ~165 Grand Prix events.
  - Features: Driver rolling Elo ratings, constructor championship standings, starting grid position, qualifying time deltas, historical circuit pit loss.
  - Purpose: Train and validate static historical baselines ($T_0$ and $T_4$).
- **Layer 2 (Granular Multimodal Telemetry Dataset):** Seasons **2023–2025 (Complete) + 2026 YTD** ingested via **OpenF1 API**.
  - Total volume: ~75 Grand Prix events with complete sub-second telemetry, sector times, tyre compound stints, and weather traces.
  - Features: Practice long-run tire degradation slopes, sector-level speed traps, live race interval gaps.
  - Purpose: Train and validate sequential checkpoint updates ($T_1 \dots T_3$, $T_5$, $T_6$) and ablation studies.

### Recommended First Baseline (`EXP-0001`):
- **Model:** Rolling Driver Elo + Constructor Bradley-Terry Model at Checkpoint $T_0$ (Pre-Weekend).
- **Validation Split:** Chronological rolling-origin:
  - Fold 1: Train 2018–2021 $\rightarrow$ Test 2022
  - Fold 2: Train 2018–2022 $\rightarrow$ Test 2023
  - Fold 3: Train 2018–2023 $\rightarrow$ Test 2024
  - Fold 4: Train 2018–2024 $\rightarrow$ Test 2025–2026
- **Primary Proper Scoring Rule:** Multi-class Brier Score and Multi-class Log Loss on Race Winner.

---

## 8. Pre-Race Candidate Field & Temporal Cutoff Audit

A dedicated empirical audit on pre-race candidate-field reconstruction across 2010–2026 (7,285 entrants across 346 races) was conducted in October 2026. The full audit findings, era coverage matrix, and anti-leakage rules are documented in:

👉 **[docs/research/CANDIDATE_FIELD_AUDIT.md](CANDIDATE_FIELD_AUDIT.md)**

### Critical Takeaways for Checkpoint $T_5$ (Pre-Race Cutoff):
1. **Provisional Result-Record Proxy:** Retrospective race-result records serve as a provisional proxy until independently timestamped pre-race entry lists are verified; zero post-race leakage cannot be formally claimed as proven.
2. **Race-Specific Grid-Zero Encoding (`grid == 0`):** 87.5% (49/56) of `grid == 0` records represent active race starters (pit lane), while 7 require verification. Models must retain them in the candidate pool, encoding them with a race-specific effective grid position equal to the maximum positive grid plus one ($\max_{i, \text{grid}_i > 0}(\text{grid}_i) + 1$) and an `is_grid_zero` indicator, without treating grid-zero as definitive proof of a pit-lane start.
3. **No Post-Race Exclusion:** 62 historical entrants broke down on reconnaissance/formation laps. At $T_5$, they held valid grid slots. Drivers must never be excluded using post-race status codes.
4. **Standardized Evaluation Cohorts:** **149 rounds** across 2018–2024 recommended as the primary out-of-sample benchmark cohort; **156 rounds** across 2010–2017 recommended as the historical sensitivity/warm-up cohort.


