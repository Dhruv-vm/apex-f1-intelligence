# APEX — Future Research Directions

> **Status:** PROPOSED HORIZONS — Exploratory research tracks to be considered only after the core sequential probabilistic forecasting framework (Milestones 0–8) has been implemented, calibrated, and benchmarked.

---

## 1. Advanced Modeling Horizons

### 1.1 Deep State-Space Models & Neural ODEs
- **Concept:** Continuous-time modeling of tire degradation and fuel burn dynamics using Neural Ordinary Differential Equations (Neural ODEs) or Structured State Space models (S4 / Mamba architectures).
- **Potential Value:** Accommodate variable-length stints and asynchronous sensor observations directly without requiring discrete lap bucketing.

### 1.2 Multi-Agent Game-Theoretic Pit Strategy Optimization
- **Concept:** Formulating the pit stop decision problem as an $N$-player stochastic dynamic game where each team strategist anticipates rival undercut/overcut responses.
- **Potential Value:** Transitions from passive prediction to counterfactual prescriptive strategy optimization under Nash equilibrium conditions.

---

## 2. Multimodal Feed Expansions

### 2.1 Acoustic & Natural Language Team Radio Parsing
- **Concept:** Streaming transcription and sentiment analysis of team radio communications during sessions (e.g., driver complaints regarding graining, brake vibrations, or tactical orders).
- **Potential Value:** Extracts latent mechanical distress and tactical intent signals prior to visible telemetry anomalies.

### 2.2 Computer Vision on Broadcast & Onboard Video Feeds
- **Concept:** Applying visual object detection and tracking to onboard camera feeds to estimate aerodynamic wing deflection, front wing endplate damage, and track rubberization state.
- **Potential Value:** Captures physical damage events (e.g., minor endplate contact) that do not trigger formal race control status flags.

### 2.3 Synthetic Aerodynamic Package Simulation
- **Concept:** Ingesting 3D track elevation profiles, corner camber, and wind tunnel technical upgrade reports to model circuit-specific downforce efficiency.
- **Potential Value:** Enables pre-weekend simulations for newly modified circuits (e.g., track resurfacing or layout alterations) before cars hit the track in FP1.
