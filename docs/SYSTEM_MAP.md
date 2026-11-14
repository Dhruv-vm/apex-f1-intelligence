# APEX — F1 Intelligence: System Map & Pipeline Flow

> **Status:** ARCHITECTURAL SPECIFICATION — Represents the end-to-end operational pipeline planned for APEX. Solid nodes indicate core pipeline components; dashed subgraphs designate candidate external feeds and prospective live integration.

---

## 1. End-to-End System Pipeline

```mermaid
flowchart TD
    %% External Data Sources
    subgraph ExternalSources["Candidate External Sources"]
        SRC_JOLPICA["Jolpica / Ergast API (Historical Results & Standings)"]
        SRC_FASTF1["FastF1 Library (Telemetry, Lap Times, Weather)"]
        SRC_OPENF1["OpenF1 Community API (Granular Timing & Intervals)"]
        SRC_WEATHER["Meteorological Feeds (Ambient & Track Temp, Rain)"]
    end

    %% Ingestion Subsystem
    subgraph IngestionSubsystem["Data Ingestion & Local Cache"]
        ING_CLIENT["Ingestion Orchestrator & Rate Limiter"]
        RAW_CACHE[("Local Raw Cache /data/raw")]
    end

    %% Validation & Temporal Alignment
    subgraph AlignmentSubsystem["Validation & Temporal Alignment"]
        VAL_CHECK["Schema Validation & Dropped-Lap Detector"]
        TIME_GUARD["Information Cutoff Guard (Anti-Leakage Filter)"]
        HIST_STORE[("Normalized Session Store /data/processed Parquet & SQLite")]
    end

    %% Feature Generation
    subgraph FeatureSubsystem["Feature Engineering Engine"]
        FEAT_HIST["Historical Driver/Car Ratings (Elo & TrueSkill)"]
        FEAT_PACE["Session Long-Run Degradation & Fuel Correction"]
        FEAT_QUALI["Qualifying Sector Deltas & Grid Position"]
        FEAT_INSPECT["Feature Store / Matrices Stamped with Cutoff T"]
    end

    %% Modeling & Forecasting
    subgraph ModelingSubsystem["Probabilistic Modeling Core"]
        MODEL_BASE["Static Baselines (Elo / Bradley-Terry / LightGBM)"]
        MODEL_SEQ["Sequential Multimodal Forecaster (Checkpoint Router)"]
        CALIBRATION["Probability Calibration (Platt / Isotonic / Conformal)"]
    end

    %% Snapshot & Evaluation
    subgraph SnapshotSubsystem["Prediction Snapshots & Observability"]
        SNAP_STORE[("Prediction Snapshots Store")]
        EVAL_ENGINE["Proper Scoring Evaluator (Brier Score & Log Loss)"]
        METRICS_LOG["Experiment Logs & Model Lab Metrics"]
    end

    %% Serving & Presentation
    subgraph ServingSubsystem["Application Services & Interfaces"]
        API_GW["FastAPI Service (REST & WebSockets)"]
        UI_PORTAL["Public Cinematic Landing Experience"]
        UI_WORKSPACE["11 Analytical Modules (Predictions, Telemetry, Strategy, etc.)"]
    end

    %% Flow Connections
    SRC_JOLPICA --> ING_CLIENT
    SRC_FASTF1 --> ING_CLIENT
    SRC_OPENF1 --> ING_CLIENT
    SRC_WEATHER --> ING_CLIENT

    ING_CLIENT --> RAW_CACHE
    RAW_CACHE --> VAL_CHECK
    VAL_CHECK --> TIME_GUARD
    TIME_GUARD --> HIST_STORE

    HIST_STORE --> FEAT_HIST
    HIST_STORE --> FEAT_PACE
    HIST_STORE --> FEAT_QUALI

    FEAT_HIST --> FEAT_INSPECT
    FEAT_PACE --> FEAT_INSPECT
    FEAT_QUALI --> FEAT_INSPECT

    FEAT_INSPECT --> MODEL_BASE
    FEAT_INSPECT --> MODEL_SEQ

    MODEL_BASE --> CALIBRATION
    MODEL_SEQ --> CALIBRATION

    CALIBRATION --> SNAP_STORE
    SNAP_STORE --> EVAL_ENGINE
    EVAL_ENGINE --> METRICS_LOG

    SNAP_STORE --> API_GW
    METRICS_LOG --> API_GW

    API_GW --> UI_PORTAL
    API_GW --> UI_WORKSPACE
```

---

## 2. Checkpoint-Driven Information Flow

The pipeline enforces sequential progression across Grand Prix weekend checkpoints. At each cutoff point $T$, features are locked and a new prediction snapshot is produced:

```mermaid
sequenceDiagram
    autonumber
    participant Track as Track & Timing Feeds
    participant Store as Temporal Store
    participant Feature as Feature Engine
    participant Model as Probabilistic Model
    participant Snapshot as Snapshot Registry

    Note over Track,Snapshot: Checkpoint 0: Pre-Weekend (T_0)
    Track->>Store: Historical season records & calendar metadata
    Store->>Feature: Extract prior driver/team Elo & track characteristics
    Feature->>Model: Features restricted to T_0
    Model->>Snapshot: Generate Pre-Weekend Forecast Snapshot (P_0)

    Note over Track,Snapshot: Checkpoint 1 to 3: Free Practice (FP1, FP2, FP3)
    Track->>Store: Lap times, stint lengths, tire age, track temperature
    Store->>Feature: Compute fuel-corrected pace & degradation slopes
    Feature->>Model: Features updated with FP evidence
    Model->>Snapshot: Generate Post-Practice Forecast Snapshot (P_practice)

    Note over Track,Snapshot: Checkpoint 4: Post-Qualifying
    Track->>Store: Official Q1/Q2/Q3 times, sector speeds, grid penalties
    Store->>Feature: Compute pole delta, grid positions, sector dominance
    Feature->>Model: Features updated with official starting grid
    Model->>Snapshot: Generate Post-Qualifying Forecast Snapshot (P_quali)

    Note over Track,Snapshot: Checkpoint 5: Live Race Checkpoints (Lap K)
    Track->>Store: Live intervals, pit stop durations, tire change records
    Store->>Feature: Dynamic gap delta, virtual pit window, safety car state
    Feature->>Model: Features updated to Lap K
    Model->>Snapshot: Generate Live Race Forecast Snapshot (P_lapK)
```

---

## 3. Implementation Status of Diagram Components

| Component | Architecture Role | Current Status in M0 | Next Action |
|---|---|---|---|
| Ingestion Orchestrator | Connects to external APIs | Provisional Design | Audit in Milestone 1 ([DATA_AVAILABILITY_AUDIT.md](research/DATA_AVAILABILITY_AUDIT.md)) |
| Normalized Session Store | Parquet/SQLite storage | Provisional Schema | Implement in Milestone 2 |
| Information Cutoff Guard | Prevents temporal leakage | Specification defined | Build unit tests in Milestone 2 |
| Feature Engine | Checkpoint matrix generator | Mathematical model planned | Milestone 4 |
| Baseline Models | Elo, Bradley-Terry, GBDT | Formulated in methodology | Milestone 3 |
| Calibration Core | Isotonic / Conformal scaling | Evaluation protocol drafted | Milestone 3 |
| API Gateway | FastAPI endpoints | Empty skeleton | Milestone 6 |
| Frontend Workspace | Next.js visual suite | Empty skeleton | Milestone 7 |
