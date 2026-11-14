# ADR-0002: Data Provider Selection and Telemetry Ingestion Strategy

- **Status:** APPROVED
- **Date:** 2026-10-18
- **Author(s):** APEX Core Engineering Team
- **Deciders:** APEX Architecture & Research Working Group
- **Supersedes:** N/A
- **Superseded By:** N/A

---

## 1. Context and Problem Statement

To train and evaluate probabilistic race outcome models across the Grand Prix weekend ($T_0$ to $T_6$), APEX requires:
1. Long-term historical sporting records (race results, qualifying times, starting grids, championship standings) spanning decades to construct stable driver and constructor Elo/Bradley-Terry ratings.
2. High-resolution session data (lap times, sector splits, tyre stints, weather, and car telemetry) to build sequential checkpoint updating models ($T_1 \dots T_6$).

During the Milestone 1 empirical audit, we discovered that:
- Specific tested unauthenticated requests to the official live timing static archive (`livetiming.formula1.com/static/...`) return `HTTP 401 Unauthorized`, indicating that direct access to those static archive endpoints requires an F1 account token (`f1auth.json`).
- OpenF1 (`https://api.openf1.org/v1`) offers an open, unauthenticated REST/WebSocket API with car telemetry (sampled at ~3.7 Hz per https://openf1.org/docs/), stints, intervals, weather, and race control, but only archives data from **2023 onward** (returning 404 for 2021 and 2022).
- Jolpica (`https://api.jolpi.ca/ergast/f1`) offers open, unauthenticated Ergast-compatible REST access from **1950 through 2026**, but does not provide continuous telemetry traces or live intervals.

---

## 2. Decision Drivers
- **Zero-Friction Reproducibility:** Anyone cloning the repository must be able to run baseline models and data audits without purchasing proprietary subscriptions or providing private user credentials.
- **Strict Temporal Integrity:** Selected feeds must supply accurate ISO-8601 timestamps to enforce information cutoffs.
- **Separation of Baseline vs. Telemetry Eras:** Ability to evaluate static historical models on extensive datasets (1950–2026) while isolating high-frequency sequential models on the modern telemetry era (2023–2026).
- **API Stability & Rate Limit Compliance:** Avoid hitting recurring HTTP 429 errors during pipeline execution.

---

## 3. Considered Options
- **Option 1: Rely exclusively on FastF1.** Require developers to provide personal F1 account login tokens (`f1auth.json`) for all data ingestion.
- **Option 2: Rely exclusively on Jolpica.** Abandon telemetry features ($T_1 \dots T_3$, $T_6$) and restrict APEX strictly to qualifying grid and historical results.
- **Option 3: Two-Tier Hybrid Architecture (Chosen).**
  - **Tier 1 (Sporting Ground Truth & Baseline Era 1950–2026):** Ingest historical schedules, qualifying grids, race classifications, and pit stops via **Jolpica F1 API**.
  - **Tier 2 (Modern Multimodal Telemetry Era 2023–2026):** Ingest sub-second lap timing, sector deltas, car telemetry (~3.7 Hz), tyre compounds, and live intervals via **OpenF1 Community API** with client-side request pacing (0.3s–0.5s).
  - **Auxiliary FastF1 Adapter:** Maintain an optional FastF1 parser for local development when credentials or pre-cached files are present.

---

## 4. Decision Outcome
**Chosen Option:** **Option 3: Two-Tier Hybrid Architecture.**

### Rationale
Option 3 provides 100% open, credential-free reproducibility for both the broad historical baseline (1950–2026) and the modern multimodal sequential framework (2023–2026). It decouples the project from the fragile upstream F1 Live Timing authentication wall while preserving our scientific research roadmap.

---

## 5. Consequences & Trade-Offs

### Positive Consequences
- Immediate, open reproducibility for CI/CD pipelines and external researchers without API keys.
- Covers ~165 races in the modern hybrid baseline (2018–2026) and ~75 complete race weekends with granular telemetry (2023–2026).
- Direct access to live intervals, pit stop durations, and track status flags via OpenF1 for in-race Checkpoint $T_6$.

### Negative Consequences / Accepted Risks
- Pre-2023 telemetry (2018–2022) cannot be fetched via OpenF1; multi-checkpoint models incorporating practice telemetry must focus their evaluation on the 2023–2026 era unless local FastF1 caches are supplied.
- OpenF1 requires client-side rate limiting to prevent HTTP 429 errors.

---

## 6. Review Conditions
Re-evaluate this decision if:
1. OpenF1 deprecates free access or experiences prolonged server downtime.
2. FastF1 releases an unauthenticated community mirror for historical archives.
3. Jolpica adds high-resolution lap telemetry.
