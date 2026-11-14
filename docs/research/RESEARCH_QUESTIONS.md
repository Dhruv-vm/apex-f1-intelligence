# APEX — Research Questions

## 1. Primary Research Question

> **Can sequentially integrating time-aligned Formula One data improve predictive performance and probability calibration of race-outcome forecasts throughout a race weekend and live race, compared with static and single-modality baselines?**

---

## 2. Testable Secondary Research Questions

### RQ1: Sequential Information Progression
*To what extent does updating probabilistic forecasts across discrete weekend checkpoints (Pre-Weekend $\rightarrow$ FP1 $\rightarrow$ FP2 $\rightarrow$ FP3 $\rightarrow$ Qualifying $\rightarrow$ Pre-Race) yield monotonic reductions in proper scoring metrics (multi-class Brier score and log loss)?*
- **Focus:** Measuring the exact information gain contributed at each transition.
- **Benchmark:** Static pre-weekend baseline (historical driver/constructor Elo rating).

### RQ2: Modality Contribution and Noise
*Does the inclusion of high-frequency car telemetry (throttle/brake traces, apex speeds) and tire degradation estimates provide statistically significant marginal predictive value over aggregated timing metrics (lap times, sector splits, qualifying classifications), or does high-frequency telemetry introduce overfitting and noise given small sample sizes?*
- **Focus:** Multimodal ablation and feature parsimony.
- **Benchmark:** Timing-only feature matrices vs. telemetry-augmented feature matrices.

### RQ3: Probability Calibration Across Checkpoints
*How does probability calibration (measured via Expected Calibration Error and reliability diagrams) evolve from early uncertain checkpoints (Pre-Weekend) to high-information checkpoints (Post-Qualifying, Live Lap 30)? Does increased feature richness cause overconfidence in the absence of explicit post-hoc calibration?*
- **Focus:** Calibration drift, Platt scaling, isotonic regression, and temperature scaling.
- **Target:** Winner probability distribution and top-3 podium probabilities.

### RQ4: Generalization Across Regulation Shifts & Circuit Archetypes
*How robust is the sequential forecasting framework when evaluated across major aerodynamic/power unit regulatory shifts (e.g., transition from 2021 to 2022 ground-effect regulations), and across divergent circuit topologies (high-downforce street circuits like Monaco vs. low-downforce power circuits like Monza)?*
- **Focus:** Distributional robustness, domain adaptation, and historical rating decay rates.
- **Evaluation:** Rolling-origin backtesting split across regulatory era boundaries.

### RQ5: In-Race Live Dynamic Updating
*Can an in-race probabilistic model dynamically capture the stochastic impact of Safety Car deployments, Virtual Safety Cars, and undercut pit sequences to deliver calibrated win/podium probabilities in real-time during a Grand Prix?*
- **Focus:** Live race checkpoint updating (every $K$ laps or post-event triggers).
- **Benchmark:** Fixed pre-race grid position baseline.
