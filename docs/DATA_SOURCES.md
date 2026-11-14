# APEX — F1 Intelligence: Data Sources Registry

> **Status:** AUDITED & VERIFIED — Provider statuses updated following the empirical audit conducted in Milestone 1 on 2026-10-18. Detailed audit logs and coverage figures are recorded in [docs/research/DATA_AVAILABILITY_AUDIT.md](research/DATA_AVAILABILITY_AUDIT.md).

---

## 1. Provider Tier Classification

Every data source in APEX is classified into one of four verified lifecycle tiers:

1. **CANDIDATE:** Identified as relevant; empirical verification pending.
2. **VERIFIED:** Programmatically audited with test scripts; verified historical coverage, latency, rate limits, and schema contracts.
3. **IMPLEMENTED:** Ingestion pipeline, local caching, and transformation logic implemented in `backend/ingestion/`.
4. **TESTED:** Automated regression tests running in CI validating continuous schema conformance.

---

## 2. Registry of Audited Data Sources

| Provider Name | Role & Domain | Primary Data Fields | Target Era | Tier Status | Access / Auth Model | Audit Link |
|---|---|---|---|---|---|---|
| **Jolpica F1 API (Ergast Replacement)** | Historical Sporting Records | Season calendar, race results, driver/constructor standings, qualifying classifications, pit stop durations | 1950 – 2025 (Complete) + 2026 YTD | **IMPLEMENTED** | Open REST API (`https://api.jolpi.ca/ergast/f1`); No auth required; ~4 req/s; Cached adapter in `backend/providers/jolpica.py` | [Audit Section](research/DATA_AVAILABILITY_AUDIT.md#1-executive-summary--critical-findings) |
| **OpenF1 Community API** | Telemetry, Laps, Weather & Live Race | Lap times, sector 1/2/3, car telemetry (speed, throttle, brake, RPM, DRS @ ~3.7 Hz), stints, weather, race control. *Note: Cached datasets for Abu Dhabi 2024 (Session 9662) and Silverstone 2024 (Session 9558) represent opening lap replay windows (~60–95s, ~1 lap, ~0.85%–1.35% of race distance), explicitly indexed as `OPENING_LAP_REPLAY_WINDOW`.* | 2023 – 2025 (Complete) + 2026 YTD | **IMPLEMENTED** | Open REST & WebSocket (`https://api.openf1.org/v1`); Historical data free; Live data paid/subscription; Rate limit ~3.3 req/s (0.4s pacing); Cached adapter in `backend/providers/openf1.py` | [Audit Section](research/DATA_AVAILABILITY_AUDIT.md#1-executive-summary--critical-findings) |
| **FastF1 Python Library / F1 Live Timing** | Timing, Telemetry & Session Weather | Lap times, tire compounds, car telemetry (10–50 Hz in full archive) | 2018 – Present (Official timing archive) | **IMPLEMENTED (OPTIONAL)** | Tested static archive endpoints return HTTP 401 unauthenticated; functional with F1 token (`f1auth.json`) or local cache; Graceful degradation adapter in `backend/providers/fastf1.py` | [Audit Section](research/DATA_AVAILABILITY_AUDIT.md#1-executive-summary--critical-findings) |
| **FIA Official Documents** | Regulations, Starting Grids & Decisions | Technical/Sporting regulations, official pre-race entry lists, starting grids, steward decisions. Source: [FIA Regulation Index Category 2182](https://www.fia.com/regulation/category/2182), specifically 2026 Technical Regulations Issue 21 (published 19 October 2026). | 1990 – Present | **VERIFIED** | Public web/PDF archive (`fia.com`); unauthenticated | [Audit Section](research/DATA_AVAILABILITY_AUDIT.md#2-multi-season-provider-coverage-matrix) |
| **Open-Meteo Historical Forecasts** | Meteorological Forecast Vintages | Air/track temperature forecasts, rain probability, wind speed/direction stamped by forecast runtime | Modern era | **CANDIDATE** | Open API / Developer tier; non-commercial / commercial tiers available | [Audit Section](research/DATA_AVAILABILITY_AUDIT.md#2-multi-season-provider-coverage-matrix) |
| **Motorsport RSS Feeds** | News & Technical Upgrade Extraction | Public headlines, publication timestamps, articles, technical upgrade announcements | Modern era | **CANDIDATE** | Public RSS feeds (Motorsport.com, Autosport, RaceFans); Metadata and excerpts only | [Audit Section](research/DATA_AVAILABILITY_AUDIT.md#2-multi-season-provider-coverage-matrix) |

---

## 3. Ingestion Rules & Rate Limits

1. **Mandatory Caching (`data/raw/`):** External network requests to Jolpica and OpenF1 must be cached locally to disk on initial fetch. Subsequent model training, validation, and feature generation will read strictly from local cache.
2. **Client-Side Throttling:**
   - Jolpica: Minimum 0.25s delay between requests.
   - OpenF1: Minimum 0.4s delay between requests to prevent HTTP 429 errors.
3. **Telemetry & Coordinate Strategy:**
   - OpenF1 serves as the primary open telemetry source for modern seasons (2023–2026).
   - Telemetry is sampled at approximately 3.7 Hz with arbitrary origin $(x, y, z)$ coordinates lacking lateral track-position offset. Track rendering requires affine transformation and projection onto circuit splines.
   - FastF1 serves as an auxiliary parser for users who supply authenticated tokens or pre-cached timing archives in `data/raw/fastf1_cache/`.
4. **Licensing & Usage Constraints:**
   - OpenF1 is an unofficial community project intended for educational, non-commercial, and research use. Live real-time streams require a paid tier.
   - All third-party upstream requests must be routed through the backend fan-out layer; client browsers must never directly poll upstream APIs.
   - Direct connection to official F1 SignalR Core websockets (`wss://livetiming.formula1.com/signalrcore`) is an unauthenticated, reverse-engineered private endpoint used in some open-source dashboards. This endpoint violates Formula One World Championship Limited (FOWC) Terms of Use and presents high operational and legal risk (IP bans, protocol changes). APEX strictly rejects direct scraping of this endpoint in favor of documented OpenF1 / Jolpica APIs or user-supplied local caches.

---

## 4. Epistemological Modality & Parameter Classification (Phase 7.1)

In compliance with APEX Core Operating Rules (Rule 3 & 4), all simulation parameters and state variables are strictly categorized into five epistemological modalities:

| Parameter / Variable | Modality | Source / Basis | Mathematical / Physical Meaning |
|---|---|---|---|
| Historical Starting Grids & Official Classifications | **OBSERVED** | Jolpica / Ergast API & FIA Classifications | Ground-truth sporting classifications and starting orders |
| Sector Laps & Observed Lap Times | **OBSERVED** | OpenF1 Session Transcripts | Raw recorded timing metrics from official session timing transponders |
| Pit Stop In-Transit Loss | **EMPIRICALLY ESTIMATED** | Calibrated on 346 races (2010–2024) | Circuit-specific entry deceleration (9.5s) and exit acceleration (11.0s) totaling 20.5s transit loss (Yas Marina) excluding stationary service |
| Stationary Wheel Service Time | **EMPIRICALLY ESTIMATED** | Fit from historical pit data | Pit box stationary service distribution $\mathcal{N}(2.45\text{s}, 0.35\text{s})$ with stuck wheel hazard $p=0.035$ (+4.2s penalty) |
| Compound Pace Deltas ($\Delta t_{\text{compound}}$) | **EMPIRICALLY ESTIMATED** | Multi-season practice/race telemetry | Relative offset vs Medium (Soft: -0.65s, Medium: 0.0s, Hard: +0.75s, Inter: +4.5s, Wet: +9.0s) |
| Tyre Degradation Linear Slopes | **EMPIRICALLY ESTIMATED** | Stint-clustered bootstrap with fuel detrending | Base wear rates ($0.038$ to $0.075$ s/lap) with recorded 95% bootstrap confidence intervals and -0.0578 s/lap fuel detrending |
| Safety Car Base Hazard Rate | **EMPIRICALLY ESTIMATED** | Separated exposure denominators across 346 races (20,722 laps for SC) vs 247 races (14,810 laps for VSC era 2015–2024) | Base full Safety Car hazard $\lambda_{\text{SC}} = 310 / 20,722 = 0.0150\text{ lap}^{-1}$; Virtual Safety Car $\lambda_{\text{VSC}} = 180 / 14,810 = 0.0120\text{ lap}^{-1}$ (pre-2015 $\text{VSC} \equiv 0.0000$) |
| Starting Fuel Load & Burn-Off Rate | **ASSUMED (LATENT)** | FIA maximum fuel limit (110 kg); empirical sensitivity bounds | Baseline: $105.0\text{ kg}$ starting mass, $1.75\text{ kg/lap}$ consumption, $0.033\text{ s/kg}$ sensitivity ($-0.0578\text{ s/lap}$). Latent parameter sensitivity grid ($1.4\text{--}2.0\text{ kg/lap}$, $0.025\text{--}0.040\text{ s/kg}$) bounds fuel-corrected degradation slopes between $0.0263$ and $0.0713\text{ s/lap}$ |
| Standing Start Physical Launch Delay | **EMPIRICALLY ESTIMATED** | Telemetry acceleration delta (0 km/h vs 280 km/h flying lap) | $+4.8\text{s}$ added to Lap 1 elapsed time for accelerating from grid standstill |
| Track Rubbers-In Evolution Rate | **ASSUMED** | Racing engineering heuristic | $-0.012\text{ s/lap}$ grip improvement over clean green track |
| Non-Linear Tyre Cliff Exponent | **ASSUMED** | Non-linear thermal degradation heuristic | Quadratic penalty $0.018 \times (\text{lap} - \text{life})^2$ active when tyre life exceeds compound threshold |
| Target Pit Lap & Strategy Selection | **USER CONFIGURED** | User / Scenario Specification | Specified pit stops, target compound sequences, and undercut trigger offsets |
| Deg Multiplier / SC Probability Scale | **USER CONFIGURED** | Sensitivity Scenario Slider | User-specified perturbations (e.g. 0.5x–2.0x) to test tactical robustness |
| Monte Carlo Finishing Simplex & Lap Traces | **SIMULATED** | APEX Monte Carlo Engine (CRN) | Synthetic stochastic realization computed across $N \in [100, 10000]$ decoupled draws |
