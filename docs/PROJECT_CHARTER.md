# APEX — F1 Intelligence: Project Charter

## 1. Project Overview & Identity

- **Project Name:** APEX — F1 Intelligence
- **Tagline:** Every lap. Every variable. Every possibility.
- **Repository:** `https://github.com/Dhruv-vm/apex-f1-intelligence`
- **Working Research Title:** Sequential Multimodal Probabilistic Forecasting of Formula One Race Outcomes Across the Race Weekend and Live Race

---

## 2. Problem Statement

Formula 1 race prediction in commercial and media contexts is frequently characterized by either simplistic heuristic analysis, static pre-race point estimates, or subjective pundit commentary. These approaches suffer from fundamental limitations:
1. **Lack of Probabilistic Calibration:** Point forecasts (e.g., "Verstappen will win") fail to convey the true probability distribution, underestimating tail events, mechanical DNFs, weather volatility, and safety car interventions.
2. **Temporal Rigidity:** Pre-race models do not systematically ingest the non-stationary information stream generated across free practice (FP1, FP2, FP3) and qualifying sessions, nor do they update live as fuel loads burn off and tire degradation curves manifest.
3. **Data Leakage in Research:** Academic motorsport prediction literature frequently exhibits temporal leakage (e.g., using post-qualifying penalties, session-aggregated metrics, or post-race variables to predict in-session states).
4. **Modality Silos:** Timing data (lap times, sector splits), weather metrics, telemetry traces, and historical team/driver ratings are rarely united into an empirical, sequentially updated framework with proper scoring evaluations.

---

## 3. Project Objectives & Core Deliverables

### Scientific & Research Objectives
1. **Develop a Leakage-Safe Forecasting Engine:** Formalize strict prediction-time information cutoffs across the Grand Prix lifecycle.
2. **Quantify Sequential Value of Information:** Empirically evaluate whether updating predictive distributions with session-specific telemetry and timing yields statistically significant improvements in proper scoring rules (Brier score, multi-class log loss) over static historical baselines.
3. **Calibrate Extreme Uncertainty:** Ensure predicted probabilities reflect empirical long-run frequencies, particularly for low-probability events (e.g., midfield podiums, wet-weather upsets, mechanical retirements).

### Product & Platform Objectives
1. **Cinematic Public Experience:** High-end landing interface conveying motorsport engineering precision through dark, restrained, technical UI.
2. **Comprehensive Analytics Workspace:** Eleven integrated product modules: Overview, Predictions, Live Race, Telemetry, Strategy, Analytics, Race Weekend, Paddock, Probability Markets, Model Lab, and F1 AI.
3. **Transparent Model Observability:** A public "Model Lab" exposing reliability diagrams, rolling Brier scores, feature importance, and historical prediction snapshots without fabrication.

---

## 4. Scope Boundaries

### In Scope
- Systematic ingestion, cleaning, and time-alignment of historical and modern Formula 1 timing, telemetry, weather, and sporting records (2018–present for high-frequency telemetry; 1950–present for historical race records where appropriate).
- Baseline probabilistic modeling (Elo, Bradley-Terry, gradient-boosted trees) and advanced sequential/multimodal architectures.
- Rigorous rolling-origin out-of-sample backtesting across multiple full seasons.
- Production-grade web interface and backend API delivering calibrated probabilities and interactive telemetry comparisons.

### Out of Scope (Explicit Anti-Goals)
- Real-time in-car sports betting execution or financial transaction processing.
- Prophetic or deterministic single-point outcome claims.
- High-frequency CFD (Computational Fluid Dynamics) simulations requiring proprietary team CAD models.
- Speculative feature engineering not grounded in verifiable timing, telemetry, or official sporting regulations.

---

## 5. Governance and Verification Standards

1. **Empirical Primacy:** No claim of predictive superiority or model accuracy is valid without an immutable, reproducible experiment record in [docs/experiments/](experiments/).
2. **Documentation As Canonical Record:** All design choices and deviations from this charter must be documented through Architecture Decision Records in [docs/decisions/](decisions/).
3. **Milestone Gating:** Transition between roadmap milestones requires 100% completion of defined acceptance criteria in [docs/implementation/CURRENT_MILESTONE.md](implementation/CURRENT_MILESTONE.md).
