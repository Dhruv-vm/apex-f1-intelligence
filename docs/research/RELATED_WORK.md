# APEX — Related Work & Comparative Taxonomy

## 1. Context & Scope

Predictive modeling in motorsport occupies an intersection of vehicle dynamics, sports analytics, and temporal machine learning. This document analyzes established paradigms in motorsport research, identifies their structural limitations, and positions the candidate contributions of **APEX — F1 Intelligence**.

---

## 2. Taxonomy of Related Methodologies

| Research Domain | Dominant Approaches | Typical Output | Key Structural Limitations | How APEX Addresses This |
|---|---|---|---|---|
| **Classical Race Outcome Prediction** | Logistic regression, Random Forests, GBDTs on season-aggregated stats | Deterministic winner / Top-3 classification or finishing rank | Often evaluated with random $k$-fold cross-validation (temporal leakage); ignores weekend progression | Strict chronological rolling-origin splits; evaluation across discrete weekend checkpoints (T0–T5) |
| **Driver Ranking & Skill Attribution** | Bradley-Terry, Elo, TrueSkill, mixed-effects linear regression | Latent driver/car skill scores | Static across seasons; does not ingest within-weekend practice long-run pace | Combines rolling latent ratings with session-specific pace updates |
| **Lap Time & Telemetry Dynamics** | Physics-based tire friction models, polynomial lap regression | Deterministic lap time estimates ($t_{lap}$) | Evaluates vehicle performance in isolation; detached from field-level race probability distributions | Distills telemetry into tire degradation slope features directly informing probability distributions |
| **Strategy & Pit Stop Optimization** | Monte Carlo tree search, Dynamic Programming, Markov Decision Processes | Optimal planned pit stop laps | Assumes deterministic pace curves; often ignores competitor tactical interaction | Integrates stochastic hazard rates (Safety Car) with calibrated win/podium probability surfaces |
| **Sports Betting & Market Models** | Odds-implied probability aggregation | Market consensus probabilities | Black-box commercial odds; subject to public betting biases and favorite-longshot bias | Open, empirical, reproducible benchmark evaluated against strictly proper scoring rules |

---

## 3. Critical Failure Modes in Prior Literature

A systematic survey of prior motorsport prediction literature reveals four recurring methodological pitfalls that APEX explicitly designs against:

### 3.1 Temporal Leakage (Lookahead Bias)
Many studies aggregate season-level or weekend-level statistics (e.g., "average pit stop duration across the Grand Prix" or "fastest lap of the weekend") as input features for pre-race prediction. In a true production setting, this information does not exist prior to race completion. APEX eliminates this by defining immutable temporal cutoffs for every checkpoint.

### 3.2 Reliance on Point Accuracy over Proper Scoring Rules
Evaluating multi-class motorsport outcomes using accuracy (e.g., "Top-1 Accuracy = 65%") is scientifically misleading in dominant eras (e.g., Hamilton 2014–2020 or Verstappen 2022–2023), where predicting the favorite yields high nominal accuracy while providing zero probability calibration. APEX standardizes on **strictly proper scoring rules** (multi-class Brier score and log loss) that reward honesty and penalize overconfidence.

### 3.3 Static Weekend Rigidity
Most academic models operate as a single static inference step (either before the weekend starts or immediately after qualifying). Formula 1 weekends generate significant non-stationary evidence between Thursday setup declarations and Sunday lights-out. APEX explicitly formalizes the **sequential update paradigm**.

### 3.4 Unverified Data Availability & Proprietary Enclosures
Many vehicle dynamics studies rely on proprietary team telemetry or commercial software (e.g., ATLAS) that cannot be audited or reproduced by the broader scientific community. APEX commits to reproducible data pipelines built on auditable public timing feeds (Jolpica, FastF1, OpenF1).
