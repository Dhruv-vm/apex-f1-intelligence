# APEX — F1 Intelligence: System Architecture Specification

> **Status:** PROVISIONAL — Architectural blueprint subject to validation during Milestone 1 data audits and Milestone 2 prototyping.

---

## 1. Architectural Principles

1. **Temporal Boundary Isolation:** The architecture strictly enforces prediction-time cutoffs. Modules operating at Checkpoint $T$ must have zero access to data arriving at $T+\Delta$.
2. **Four-State Data Segregation:**
   - **Observed / Ground Truth:** Immutable raw and processed timing/telemetry records from official sessions.
   - **Historical Replay:** Deterministic temporal playback of past sessions for backtesting and user simulation.
   - **Model Forecast:** Probabilistic predictive distributions stamped with model version, feature cutoff timestamp, and parameter signatures.
   - **Scenario Simulation:** Synthetic counterfactual rollouts (e.g., alternative pit stop strategies or hypothetical safety cars).
3. **Decoupled Analytical Engine & Presentation Layer:** The machine learning and feature generation core operates independently from API gateways and UI clients, communicating via structured data contracts.
4. **Reproducibility First:** Every prediction snapshot records the exact model hash, feature matrix signature, and data source version.

---

## 2. High-Level Subsystems

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        Data Ingestion Layer                           │
│  FastF1 Client  │  Jolpica / Ergast API  │  OpenF1 API  │ Weather Feeds│
└────────────────────────────────────┬───────────────────────────────────┘
                                     │
                                     ▼
┌────────────────────────────────────────────────────────────────────────┐
│                  Temporal Alignment & Validation Store                 │
│       Data Integrity Checks │ Timestamp Normalization │ Parquet / SQL  │
└────────────────────────────────────┬───────────────────────────────────┘
                                     │
                                     ▼
┌────────────────────────────────────────────────────────────────────────┐
│                      Feature Engineering Engine                        │
│   Historical Ratings │ Session Degradation │ Qualifying Pace Deltas    │
└────────────────────────────────────┬───────────────────────────────────┘
                                     │
                                     ▼
┌────────────────────────────────────────────────────────────────────────┐
│             Probabilistic Forecasting & Calibration Engine             │
│   Checkpoint Router │ Model Ensemble / GBDT │ Conformal / Calibration  │
└────────────────────────────────────┬───────────────────────────────────┘
                                     │
                                     ▼
┌────────────────────────────────────────────────────────────────────────┐
│                  Prediction Snapshot & Evaluation Store                │
│       Probabilities │ Brier / Log Loss Metrics │ Reliability Curves    │
└────────────────────────────────────┬───────────────────────────────────┘
                                     │
                                     ▼
┌────────────────────────────────────────────────────────────────────────┐
│                           API Gateway Layer                            │
│           RESTful Endpoints (FastAPI) │ WebSocket Streaming            │
└────────────────────────────────────┬───────────────────────────────────┘
                                     │
                                     ▼
┌────────────────────────────────────────────────────────────────────────┐
│                      Frontend Client Presentation                      │
│   Landing Portal │ 11 Analytical Modules │ Model Lab Observability     │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Subsystem Detailed Responsibilities

### 3.1 Data Provider & Ingestion Layer (`backend/providers/`, `backend/services/`)
- Implemented modular data provider adapters adhering to `BaseDataProvider`:
  - `JolpicaProvider`: Season calendars, Grand Prix events, circuits, drivers, constructors, and race results. Caches raw responses in `data/raw/jolpica/` with a 0.25s throttling rate limit and exponential backoff retries.
  - `OpenF1Provider`: Session schedules, session types, and driver numbers. Caches raw responses in `data/raw/openf1/` with a 0.40s throttling rate limit.
  - `FastF1Provider`: Optional auxiliary adapter with graceful degradation when unauthenticated or offline.
- `IngestionService`: Idempotent multi-provider ingestion workflow. Merges Jolpica sporting records with OpenF1 session keys, enforces unique constraints, logs payload hashes for auditability, and updates existing records without duplication.

### 3.2 Canonical Relational Store & Migrations (`backend/models/`, `backend/database.py`, `alembic/`)
- Relational metadata store implemented in PostgreSQL using SQLAlchemy 2.0 and Alembic migrations.
- Canonical entities:
  - `seasons`: Championship seasons and archive URLs.
  - `circuits`: Circuit references, coordinates, country, and locality.
  - `events`: Grand Prix rounds, dates, and circuit foreign keys (unique per season and round).
  - `sessions`: Practice, Qualifying, Sprint, and Race sessions with start/end timestamps and provider session keys.
  - `drivers` & `constructors`: Normalized competitor entities.
  - `race_results`: Classified finish positions, grid slots, laps completed, points, finish status, and fastest lap metrics.
  - `ingestion_logs`: Audit logs tracking provider name, entity type, records ingested, payload SHA-256 hash, and status.
- High-volume telemetry traces remain strictly reserved for the analytical storage layer (Parquet in later phases).

### 3.3 Feature Engineering Engine (`ml/features/`)
- Computes time-gated feature representations across defined forecast checkpoints:
  - *Pre-Weekend:* Driver/Constructor rolling Elo ratings, circuit historical characteristics (pit lane loss time, overtaking difficulty, historical safety car rate).
  - *Free Practice (FP1–FP3):* Long-run representative pace, fuel-corrected lap time estimations, tire wear degradation slopes.
  - *Qualifying:* Pole position gap, qualifying session sector dominances, tire compound deltas.
  - *Live Race:* Current gap to leader, interval to car ahead/behind, tire age, pit window delta.

### 3.4 Probabilistic Forecasting & Calibration Engine (`ml/models/`)
- Generates probability distributions over categorical race outcomes:
  - Race Winner (categorical distribution over $N=20$ drivers).
  - Podium Finish (top-3 binary classification per driver).
  - Top-6 / Top-10 Points Finish.
  - Classified DNF (mechanical, collision, or technical retirement).
- Employs calibration techniques (e.g., Platt scaling, isotonic regression, temperature scaling, conformal prediction) to guarantee empirical reliability.

### 3.5 API Gateway Layer (`backend/api/`)
- Delivers predictions, telemetry comparisons, and weekend analytics via JSON REST endpoints.
- Provides WebSocket channels for live race telemetry streaming and dynamic probability updates.

### 3.6 Replay & Live Track Map Subsystem (`backend/replay/`, `backend/live/`)
- **Historical Replay:** Indexes session telemetry and timing into versioned Parquet bundles; serves time-windowed slices and synchronized telemetry playback. Standardizes continuous telemetry traces onto a uniform 5-meter distance grid ($s = 0, 5, 10, \dots, L_{\text{track}}$) rather than raw timestamps to enable corner-by-corner multi-driver comparisons.
- **Circuit Geometry Engine:** Transforms raw provider coordinate frames into normalized 2D circuit-local SVG/Canvas coordinates using a 2D rotation matrix $[[ \cos\theta, \sin\theta ], [ -\sin\theta, \cos\theta ]]$ parameterized by `circuit_info.rotation`; aligns coordinates along a curvilinear track centerline spline $s \in [0, L_{\text{track}}]$ and handles pit-lane routing.
- **Live Fan-Out Daemon:** Establishes a single persistent upstream subscription, maintains in-memory session state, and fans out updates to frontend clients over WebSockets without client-side upstream polling.

### 3.7 News, Technical Intelligence & Regulation Registry (`backend/intelligence/`, `backend/regulations/`)
- Ingests permitted motorsport RSS feeds and official FIA documents.
- Extracts named entities, topic classifications, and structured technical upgrade events (front wing, floor, power unit) with source credibility scoring.
- Enforces an effective-dated regulation engine tracking technical amendments (PU 50/50 split, energy limits, active aero X/Z modes, compression ratio measurement rules).

### 3.8 Monte Carlo Strategy & Race Dynamics Simulator (`backend/simulation/`)
- Executes correlated stochastic race trajectories at discrete lap transitions:
  - `state.py`: Explicit discrete-lap state representations (`DriverState`, `RaceState`, `CircuitProfile`, `TyreCompound`, `SafetyCarState`, `TrackCondition`). Supports circuit-specific DRS activation zones (`drs_activation_zones`, `drs_zone_lap_fraction`, `drs_configuration_mode`), nominated Pirelli compounds (`nominated_compounds` C1–C5), and mandatory dry compound enforcement. Entrants carry explicit classification flags (`is_classified`, `classified_position`, `classification_display`) ensuring DSQ entrants remain strictly unranked without ordinary finishing ranks.
  - `engine.py`: Discrete-lap state machine simulating pit transitions, compound switches, traffic interactions, incident rolls, and standing start physical delay (+4.8s on Lap 1). Strictly separates finished drivers from DNFs and DSQs in final race classification.
  - `scenario.py`: Decoupled exogenous scenario generator for Common Random Numbers (CRN). Explicitly isolates independent random streams indexed by (Run ID, Lap, Driver, Event Category) for weather, incidents, SC compression, driver pace normals, stint degradation normals, pit service delays, mechanical reliability, and traffic overtaking coin flips, preventing event stream desynchronization.
  - `tyre.py`: Compound characteristics (Soft, Medium, Hard, Inter, Wet), thermal warm-up losses, linear degradation slopes calibrated via stint-clustered bootstrap with 95% CIs and fuel detrending (-0.0578 s/lap based on 1.75 kg/lap and 0.033 s/kg), parameter sensitivity bounds ($0.0263\text{--}0.0713\text{ s/lap}$), and non-linear quadratic wear cliffs.
  - `pit_stop.py`: Circuit transit loss decomposed into entry deceleration (9.5s) and exit acceleration (11.0s) totaling 20.5s transit loss, stochastic stationary wheel-change distributions ($\mathcal{N}(2.45\text{s}, 0.35\text{s})$), stuck wheel delay ($p=0.035$, $+4.2\text{s}$), SC (~50%) and VSC (~35%) transit discounts, team double-stack queue penalties, and FIA Art 30.5 compliance validation (mandatory dry compounds, DSQ for dry races with <2 specs, 30s penalty only if suspended without restart).
  - `safety_car.py`: Physical Safety Car and Virtual Safety Car engines with separate historical exposure denominators across 346 races (20,722 laps for SC, $\lambda=0.0150$) vs post-2015 VSC era (247 races, 14,810 laps, $\lambda=0.0120$), enforcing chronological cutoff ($VSC \equiv 0$ pre-2015). Dynamic SC deployment length ($\mathcal{N}(4.2, 1.2)$ laps), stochastic pack compression, and elevated lap 1–2 incident multipliers.
  - `weather.py`: Track and air temperature evolution, rain onset hazard, and drying Markov state transitions.
  - `reliability.py`: Constructor-specific mechanical failure hazards and lap 1 collision hazards.
  - `traffic.py`: Strict DRS detection threshold (<1.000s gap, strictly ineligible at 1.0000s, -0.35s speed advantage), circuit-specific designated activation zones, Race Director discretionary disablement (poor visibility, yellow flags), dirty-air cornering penalty (+0.25s), and sigmoid overtake probability governed by circuit overtaking difficulty.
  - `lap_time.py`: Synthesizes base driver/constructor pace, latent fuel burn-off (1.75 kg/lap, 0.033 s/kg), track evolution rubbers-in (-0.012 s/lap), tyre compound deltas, standing start delay, and driver consistency noise.
  - `strategy.py`: Dynamic pit policies including `OneStopStrategy`, `TwoStopStrategy`, `UndercutStrategy`, `OvercutStrategy`, and `SafetyCarReactiveStrategy`.
  - `counterfactual.py`: Executes paired rollouts with Common Random Numbers (CRN) to mathematically isolate tactical policy effects, compute time/position regret, and report step-down Holm-Bonferroni adjusted $p$-values across all pairwise strategy comparisons. Evaluates race duration on completed runs (`mean_race_time_finished_seconds`) alongside all-runs metrics to prevent DNF dilution. Computes multi-objective rankings and head-to-head metrics on both total-runs and decisive-runs bases.
  - `monte_carlo.py`: Batch rollout manager (100–10,000 iterations) with convergence tracking and 95% bootstrap confidence intervals.
  - `evaluator.py`: Multi-seed CRN variance reduction auditing across independent master seeds, two-sample Kolmogorov-Smirnov test for CRN marginal distribution invariance verification ($p \ge 0.05$), independent holdout strategy selection and evaluation (Set A vs Set B), scaled 10,000-draw comparisons, and parameter sweeps.
  - `forecasting_bridge.py`: Translates historical race records and checkpoint predictions into calibrated starting states with circuit-specific DRS parameters.
  - `backtest.py`: Chronological historical backtester scoring full-field probability vectors with mathematically exact multiclass log loss ($-\ln(p_{\text{winner}})$).
  - Exposed via REST endpoints under `/api/v1/simulation/` and integrated into the Next.js frontend at `/simulation`.

### 3.9 Research & Exploration Layer (`notebooks/`)
- The primary collaborative workspace where the Project Owner and ChatGPT perform exploratory data analysis, source validation, feature prototyping, and experimental modeling.
- Prototypes algorithms and scoring diagnostics before production graduation.
- Enforces strict anti-leakage cutoffs ($T_{cutoff}$) and connects every experiment directly to the research hypothesis registry.
- Validated notebook pipelines are subsequently refactored into tested `ml/` library modules by Antigravity.

### 3.10 Frontend Client Presentation (`frontend/`)
- Public showcase landing page: cinematic, high-speed aesthetic with dark visual identity (`#0A0A0C` background, `#E10600` racing red accents, technical typography).
- Dedicated Workspace housing the 11 functional modules:
  1. Overview
  2. Predictions
  3. Race Weekend
  4. Live Race
  5. Track Map
  6. Historical Replay
  7. Telemetry Lab
  8. Driver & Constructor Analytics
  9. Strategy Intelligence
  10. Monte Carlo Simulator
  11. News, Technical Upgrades & Regulation Tracker
  12. Model Lab / Research

---

## 4. Primary Data Entities

1. **`Circuit`:** Permanent venue attributes (name, location, length, turn count, historical safety car probability, average pit delta).
2. **`SeasonEvent`:** Specific Grand Prix weekend in a championship calendar (year, round, event format: Standard vs. Sprint).
3. **`Session`:** Individual track session (FP1, FP2, FP3, Qualifying, Sprint Shootout, Sprint, Race).
4. **`Driver` & `Constructor`:** Competitor metadata, historical ratings, and championship point states.
5. **`LapRecord`:** Lap-level timing, driver, tire compound, tire age, lap time (ms), personal best / session best flags, track status (Green, Yellow, VSC, SC, Red).
6. **`TelemetryTrace`:** Synchronized channels (timestamp, distance, speed, throttle, brake, gear, RPM, DRS).
7. **`LocationSample`:** Car position sample $(x, y, z)$ projected onto track distance $s$ with pit status.
8. **`WeatherForecastVintage`:** Point-in-time meteorological forecast stamped with generation runtime and target valid time.
9. **`ExtractedNewsEvent`:** Structured technical upgrade or paddock news event with publication timestamp, component category, and confirmation status.
10. **`RegulationVersion`:** Effective-dated technical/sporting rule parameter set with publication and enforcement dates.
11. **`ForecastSnapshot`:** Output of a model at a specific cutoff: `{snapshot_id, event_id, checkpoint_id, model_version, predicted_probabilities, evaluation_metrics}`.
12. **`StrategyScenario`:** Counterfactual configuration: `{pit_laps, tire_compound_sequence, degradation_multiplier, target_lap}`.
13. **`ReplayManifest`:** Metadata descriptor for full-session replay indexing and chunk offsets.

---

## 5. Security, Secrets & Boundaries

- All API keys, credentials, and configuration reside in `.env` (instantiated from `.env.example`).
- No hardcoded access tokens or external production endpoints allowed in repository code.
- Data ingestion scripts must implement polite rate limiting, retry backoffs, and local caching.
