# APEX — Testing & Verification Strategy

> **Status Notice:** This document establishes the planned testing architecture for future implementation milestones. At Milestone 0, test frameworks and test suites have not been executed, as application code has not yet been implemented.

---

## 1. Testing Philosophy & Verification Tiers

To safeguard mathematical validity, temporal integrity, and system reliability, APEX adopts a six-tiered testing strategy:

```text
┌────────────────────────────────────────────────────────┐
│ 1. Temporal Leakage & Information Boundary Tests       │
├────────────────────────────────────────────────────────┤
│ 2. Data Validation & Schema Integrity Tests            │
├────────────────────────────────────────────────────────┤
│ 3. Mathematical & Model Evaluation Tests               │
├────────────────────────────────────────────────────────┤
│ 4. Unit Tests (Core Algorithms & Transformations)      │
├────────────────────────────────────────────────────────┤
│ 5. Integration Tests (End-to-End Pipeline & Storage)   │
├────────────────────────────────────────────────────────┤
│ 6. Reproducibility & Determinism Tests                 │
└────────────────────────────────────────────────────────┘
```

---

## 2. Testing Specifications by Tier

### Tier 1: Temporal Leakage & Boundary Tests (Highest Priority)
- **Objective:** Mathematically guarantee that features generated for checkpoint $T_{\text{cutoff}}$ contain zero knowledge of future track events ($t > T_{\text{cutoff}}$).
- **Test Implementation Plan:**
  - Automated canary test: inject synthetic future events (e.g., a qualifying penalty or a race lap crash) and assert that feature matrices computed for prior checkpoints remain bitwise identical.
  - Assert that all records in the feature store have `source_timestamp <= checkpoint_cutoff_utc`.

### Tier 2: Data Validation & Schema Tests
- **Objective:** Ensure external timing and telemetry feeds adhere to defined contracts before entering the database.
- **Test Implementation Plan:**
  - Pydantic / Pandera schema validators for `LapRecord`, `TelemetrySample`, `Circuit`, and `Session`.
  - Monotonicity checks: assert elapsed session time and distance are strictly non-decreasing per lap.
  - Boundary checks: speed $\in [0, 380\text{ km/h}]$, throttle $\in [0, 100\%]$, lap times $> 50\text{ s}$.

### Tier 3: Mathematical & Model Evaluation Tests
- **Objective:** Verify proper scoring rule computations, calibration math, and probability axioms.
- **Test Implementation Plan:**
  - Axiom test: assert all predicted probability vectors sum exactly to $1.0000 \pm 10^{-6}$ for categorical race winner targets, and sum to $3.0000 \pm 10^{-6}$ for podium targets.
  - Scoring rule unit tests: test Brier score and Log Loss implementations against reference analytical values.
  - Monotonicity of calibration curves: ensure isotonic calibration produces monotonically increasing mappings.

### Tier 4: Unit Tests
- **Objective:** Test individual helper functions, rolling Elo rating updates, stint pace fuel correction models, and feature encoders.
- **Coverage Target:** $> 85\%$ line coverage across `ml/` and `backend/`.

### Tier 5: Integration Tests
- **Objective:** Test end-to-end data flow: from reading raw cached FastF1 files to generating calibrated prediction snapshots and serving them via the FastAPI test client.

### Tier 6: Reproducibility & Determinism Tests
- **Objective:** Ensure experiments executed with identical seeds and configurations produce identical metrics across independent runs.
- **Test Implementation Plan:** Run baseline `EXP-0001` across two independent runs and assert that resulting Brier scores match to 6 decimal places.

---

## 3. Tooling & Test Automation Stack (Planned for M2+)

- **Test Runner:** `pytest` with `pytest-asyncio` for API testing.
- **Schema Validation:** `pydantic v2` and `pandera`.
- **Linting & Code Quality:** `ruff` (formatting and linting) and `mypy` (strict type checking).
- **CI Automation:** GitHub Actions workflow executing unit, leakage, and schema tests on every pull request.
