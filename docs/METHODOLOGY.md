# APEX — Consolidated Research Methodology & Pipeline

This document outlines the end-to-end scientific methodology, feature engineering pipeline, walk-forward evaluation protocol, and scoring criteria implemented in **APEX — F1 Intelligence**.

Detailed checkpoint specifications and theoretical formulations are documented in [docs/research/METHODOLOGY.md](research/METHODOLOGY.md).

---

## 1. Information Cutoffs & Forecast Checkpoints

Forecasting Formula 1 races without temporal leakage requires enforcing discrete information cutoffs ($T_0 \dots T_6$):
- **$T_0$ (Pre-Weekend):** Wednesday 23:59 UTC prior to event. Features: historical Elo ratings, championship standings, circuit historical priors.
- **$T_1$ (Post-FP1):** Single-lap pace deltas and ambient conditions.
- **$T_2$ (Post-FP2):** Representative long-run stint pace, tire degradation slopes.
- **$T_3$ (Post-FP3):** Qualifying simulation runs, low-fuel cornering speeds.
- **$T_4$ (Post-Qualifying):** Official qualifying classifications and pole deltas.
- **$T_5$ (Pre-Race):** Official FIA Final Starting Grid (30 minutes prior to formation lap).
- **$T_6$ (Live Lap $K$):** Real-time intervals, tire degradation, pit stops, track status.

---

## 2. Pre-Race Feature Engineering Pipeline ($T_5$)

Models 0–4 in `EXP-0002` utilize a standardized feature pipeline containing 16 validated pre-race signals:

### 2.1 Starting Grid Features (5)
1. `effective_grid`: Official positive grid position ($1 \dots 20/24$), or $\max_{i, \text{grid}_i > 0}(\text{grid}_i) + 1$ for grid-zero records.
2. `log_grid`: Natural log $\ln(\text{effective\_grid})$ to capture the steep nonlinear dropoff in win probability beyond row 1–2.
3. `is_front_row`: Binary indicator ($\text{effective\_grid} \in \{1, 2\}$).
4. `is_pole`: Binary indicator ($\text{effective\_grid} == 1$).
5. `is_grid_zero`: Binary flag indicating API `grid_position == 0` (provisional pit start proxy).

### 2.2 Rolling Form Features (11)
Computed strictly from races occurring prior to the current Grand Prix:
- **Driver Form:** Prior starts count, career win rate, last-5 race win rate, last-5 race mean finish (fallback `20.0`), last-5 finish sample standard deviation (`0.0` if $<2$ finishes), last-5 race mean points.
- **Constructor Form:** Prior weekend count, career win rate, last-5 race win rate, last-5 race mean finish (fallback `20.0`), last-5 race mean points.

---

## 3. Strict Walk-Forward Evaluation Protocol

1. **Chronological Sorting:** The calendar table is sorted deterministically by `race_date, season_int, round_int, race_id`.
2. **Outcome-Independent Candidate Ordering:** Candidates within each race are sorted by `driver_id` prior to scoring, eliminating tie-break selection bias.
3. **Temporal Partitioning:** For each race $r \in \{0 \dots R-1\}$, models are trained strictly on historical candidate rows from races $\{r' \mid r' < r\}$.
4. **Cold-Start Handling:** For the first 20 races ($r < 20$), uniform probabilities $1/N_r$ are assigned as the cold-start baseline.
5. **No Same-Race History Updates:** Driver and constructor histories are updated only after predictions for all candidates in race $r$ have been recorded.
6. **Simplex Verification:** Raw positive-class scores $s_i$ are clipped ($s_i \ge 10^{-12}$) and normalized:
   $$p_i = \frac{s_i}{\sum_{j=1}^{N_r} s_j}, \quad \text{guaranteeing } \sum_{i=1}^{N_r} p_i = 1$$

---

## 4. Strictly Proper Scoring Metrics

Model comparison is governed strictly by proper scoring rules:

1. **Multiclass Log Loss (Cross-Entropy):**
   $$\mathcal{L}_{\text{log}} = -\frac{1}{R} \sum_{r=1}^R \ln(p_{r, \text{winner}})$$
2. **Multiclass Brier Score (Quadratic Score):**
   $$\mathcal{L}_{\text{Brier}} = \frac{1}{R} \sum_{r=1}^R \sum_{i=1}^{N_r} (p_{r,i} - y_{r,i})^2$$
3. **Fractional Top-1 Accuracy:**
   $$\text{Acc}_{\text{fract}} = \frac{1}{R} \sum_{r=1}^R \frac{\mathbb{I}(\text{winner} \in \mathcal{T}_r)}{|\mathcal{T}_r|}$$
   where $\mathcal{T}_r = \{i \mid p_{r,i} = \max_j p_{r,j}\}$ handles ties fairly.
4. **Tie-Aware Top-1 Accuracy:** Credit given if the winner is among the top-ranked candidates.

---

## 5. Model Lineup & Hierarchy

- **Model 0 (Uniform Baseline):** Equal probability $1/N_r$.
- **Model 1 (Empirical Grid Table):** Laplace/Dirichlet smoothed historical grid win rates ($\alpha=10.0$).
- **Model 2 (Grid-Only Logistic Regression):** L2-regularized logit on 5 grid features.
- **Model 3 (Grid + Form Logistic Regression):** L2-regularized logit on 16 grid + rolling form features (Current Best Probabilistic Model).
- **Model 4 (LightGBM GBDT):** Non-linear gradient boosted decision trees (`num_leaves=15`, `lr=0.03`, `n_est=250`) on 16 features.
