# APEX — Known Scientific & Technical Limitations

This document maintains a living inventory of known methodological, data, algorithmic, and engineering limitations within the **APEX — F1 Intelligence** codebase.

---

## 1. Data Availability & Temporal Limitations

### 1.1 Provisional Retrospective Result-Record Proxy
- **Description:** Historical candidate pools (346 races across 2010–2026, 7,285 entrant rows) originate from Ergast/Jolpica retrospective race-result records.
- **Risk:** Zero post-race leakage cannot be mathematically proven until candidate pools are verified against timestamped official FIA pre-race entry sheets.
- **Mitigation:**
  - Candidates are never filtered using post-race status codes (e.g. `DNS`, `Hydraulics`).
  - Entrants breaking down before or on the formation lap are preserved in candidate sets.
  - Candidate records are sorted deterministically by `driver_id` prior to scoring to prevent tie-break leakage.

### 1.2 Grid-Zero Interpretation
- **Description:** In Ergast/Jolpica, `grid == 0` is an API indicator, not a definitive pit-lane start flag.
- **Audit Findings:** 49 of 56 audited zero-grid records were confirmed pit-lane starts; 7 represent disqualifications, grid penalties, or anomalies requiring individual verification.
- **Handling:** Encoded as $\max_{i, \text{grid}_i > 0}(\text{grid}_i) + 1$ with an explicit binary `is_grid_zero` flag.

### 1.3 Telemetry Historical Horizon
- **Description:** High-frequency car telemetry (speed, throttle, brake, RPM) is only publicly accessible via OpenF1 for modern seasons (2023–2026).
- **Impact:** Longitudinal studies across 2010–2022 cannot utilize continuous telemetry and must rely on timing feeds, lap times, sector times, and aggregated pit stop metrics.

---

## 2. Modeling & Statistical Limitations

### 2.1 Post-Hoc Normalization vs. True Multinomial Likelihood
- **Description:** Models 2, 3, and 4 train binary classifiers on individual candidate-event pairs and normalize predicted probabilities across entrants in race $r$ ($\sum_{i=1}^{N_r} p_i = 1$).
- **Impact:**
  - While ensuring valid simplex boundaries, independent binary cross-entropy does not optimize the joint multinomial log-likelihood $\prod_{i} p_i^{y_i}$.
  - In tree-based models (Model 4 LightGBM), this leads to probability tail distortion and overconfidence for favorites.
- **Remedy:** Model 5 Plackett-Luce / Conditional Logit (EXP-0004) directly optimizes the multinomial likelihood for winner prediction, achieving superior Brier score (`0.596564`) and top-1 accuracy (`54.36%`). Full finishing-order ranking models (Plackett-Luce multi-choice and LambdaMART) remain planned for downstream phases.

### 2.2 Uncalibrated Tree Probabilities & Post-Hoc Calibration Limits
- **Description:** LightGBM achieves higher Top-1 argmax accuracy (`53.02%` vs `51.68%`), but worse multiclass log loss (`1.409149` vs `1.355201`) compared to regularized logistic regression.
- **Audit Findings (EXP-0003):** Post-hoc Temperature Scaling ($T \approx 1.360$) and Platt Scaling reduce Model 4 log loss to `1.387587` and Brier score to `0.622523`, but still do not match Model 3 (`1.355201`).
- **Remedy:** Post-hoc calibration mitigates but cannot fully compensate for point-wise binary cross-entropy loss during tree construction. Joint ranking or multinomial objectives are required.

### 2.3 Isotonic Regression Tail Degeneracy in Sports Forecasting
- **Description:** Fitting non-parametric monotonic step functions (`IsotonicRegression`) maps low candidate probabilities to extreme zero/near-zero values.
- **Impact:** When an upset winner occurs from lower grid positions, the resulting logarithmic penalty ($-\log(p_w)$) severely degrades multiclass log loss (Model 4 Isotonic log loss worsens to `1.450040`; Model 3 worsens to `1.403784`).
- **Guideline:** Non-parametric step calibration should not be applied to sports forecasting without aggressive probability floor smoothing. Smooth parametric scalers (Temperature Scaling, Platt Scaling) are strictly preferred.

---

## 3. Engineering & Operational Limitations

### 3.1 Rate Limiting on External APIs
- **Description:** OpenF1 enforces strict rate limits (HTTP 429 on unthrottled bursts).
- **Requirement:** Pipeline ingestion in Milestone 2 must enforce client-side polite delays (0.3s–0.5s) and exponential backoff.

### 3.2 Upstream Live Timing Token Barriers
- **Description:** FastF1's direct F1 Live Timing archive parser requires session tokens (`f1auth.json`) requiring an authenticated F1 account.
- **Handling:** FastF1 is treated as an optional local cache parser; Jolpica and OpenF1 remain the primary open sources.

### 3.3 OpenF1 Coordinate Granularity & Lateral Placement Ambiguity
- **Description:** OpenF1 car location telemetry is sampled at ~3.7 Hz with arbitrary circuit-specific coordinate frames $(x, y, z)$. Coordinates lack lateral displacement (left vs. right track boundary positioning).
- **Handling:** Coordinates require 2D affine alignment, smoothing, and projection onto a 1D curvilinear track centerline spline $s \in [0, L_{\text{track}}]$. Lateral placement within track boundaries cannot be fabricated.

### 3.4 Weather Forecast Vintages vs. Observed Session Weather
- **Description:** Standard F1 telemetry APIs record observed on-track weather during the session, but do not provide historical forecast vintages available hours or days prior to the session.
- **Handling:** Point-in-time pre-session forecasts ($T_0 \dots T_5$) must ingest meteorological forecast archives (e.g. Open-Meteo Historical Forecast API) stamped with publication runtime, never leaking observed session weather into pre-session predictions.

### 3.5 Upstream Real-Time Data Terms & Licensing
- **Description:** OpenF1 documentation indicates that historical data is open/free, whereas real-time live data feeds require a subscription. Direct official Formula 1 live timing feeds are proprietary and unauthenticated access is forbidden.
- **Handling:** The backend implements a single-pipe ingestion and local WebSocket fan-out architecture. Live modes must operate with verified subscription credentials or run in local simulation/replay mode. Browser clients are strictly prohibited from directly polling upstream providers.
