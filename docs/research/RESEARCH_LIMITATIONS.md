# APEX — Research Limitations & Empirical Constraints

## 1. Context & Scientific Boundaries

Formula 1 presents distinct statistical and methodological challenges that separate it from other commercial sports forecasting domains (such as football, basketball, or baseball). Acknowledging these constraints explicitly ensures that the APEX platform maintains high scientific integrity and avoids over-interpreting noisy empirical signals.

---

## 2. Documented Empirical Limitations

### 2.1 Severe Sample Size Sparsity
- **Constraint:** A Formula 1 season comprises only $20–24$ Grand Prix events per calendar year. Across a six-season modern telemetry window (2018–2024), there are approximately 140 races total.
- **Impact:** High-capacity deep neural networks or complex sequence-to-sequence models are highly prone to overfitting when trained on raw telemetry series without strong regularization, domain priors, or low-dimensional feature distillation.

### 2.2 Discrete Non-Stationary Regulation Breaks
- **Constraint:** Formula 1 undergoes sweeping technical and sporting regulation changes at defined multi-year intervals (e.g., 2014 hybrid engine introduction, 2017 wider track/aero overhaul, 2022 ground-effect aerodynamics).
- **Impact:** Features capturing car performance from prior regulatory eras suffer severe distribution shifts. For example, historical data from Mercedes dominance (2014–2020) fails to reflect 2022 ground-effect hierarchy without active decay or domain adaptation.

### 2.3 Right-Censored & Confounded Observations
- **Constraint:** Finishing positions are censored when a car suffers a mechanical failure, lap 1 collision, or terminal power unit failure.
- **Impact:** A driver running in P2 who suffers an engine failure on Lap 50 is officially classified as a DNF (or placed 18th in raw position statistics). Treating this as a failure of driver pace biases model weights. Models must treat mechanical retirements as distinct stochastic failure modes.

### 2.4 Weather Asymmetry and Extreme Volatility
- **Constraint:** Wet races constitute $< 15\%$ of all championship rounds, yet introduce massive variance in lap times, crash probabilities, and strategy outcomes.
- **Impact:** Models trained primarily on dry-weather track data cannot easily generalize to mixed-condition races (e.g., intermediate/wet transitions) using standard linear degradation assumptions.

### 2.5 Exogenous Interventions & Steward Penalties
- **Constraint:** Race outcomes can be substantially altered hours after the checkered flag by post-race steward investigations (e.g., track limits penalties, scrutineering disqualifications due to plank wear).
- **Impact:** Feature pipelines must strictly record the exact timestamp at which penalties become official to avoid retroactive data contamination.

### 2.6 Data Provider Latency & Public Infrastructure Uptime
- **Constraint:** Real-time timing feeds (OpenF1 and live FastF1 streams) depend on external network stability and public community infrastructure.
- **Impact:** Checkpoint T6 (Live Race) predictions must degrade gracefully if a live packet drop occurs, maintaining the previous lap's probability state rather than failing.
