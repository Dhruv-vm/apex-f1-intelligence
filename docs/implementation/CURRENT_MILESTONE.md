# Current Milestone: EXP-0006 Final Closeout & Phase 8 Gate Authorization

- **Milestone Code:** `EXP-0006-GATE` / `Phase 7.2.1`
- **Milestone Title:** Monte Carlo Simulator Final Calibration, SC/VSC Methodology Reconciliation & Phase 8 Gate
- **Start Date:** 2026-11-05
- **Completion Date:** 2026-11-06
- **Current Lifecycle Status:** `COMPLETED & PHASE 8 AUTHORIZED`

---

## 1. Milestone Objective

Execute final numerical integrity audits and methodological reconciliations on the Monte Carlo Race and Strategy Dynamics Simulator (EXP-0006), verify machine-precision conservation identities, establish decoupled SC/VSC raw message vs lifecycle accounting, validate multi-seed CRN variance reduction, and formally authorize progression to **Phase 8 (Research Model Benchmarks, Ablations & Paper Traceability)**.

---

## 2. Acceptance Criteria Checklist

- [x] **Race-Time Weighted-Mean Mathematical Identity:**
  - Machine-verified across all 10,000 paired simulation runs ($|\text{AllRunMean} - \text{WeightedMean}| \le 9.09 \times 10^{-13}$s).
  - DNF span confirmed across laps 1–58 (mean DNF lap 22.87, duration 0.0s to 5,571.66s), refuting the legacy prose note that assumed DNFs only occur on laps 1–15.
- [x] **Safety Car & VSC Methodology Reconciliation:**
  - **Table A (Raw Message Ledger):** Exactly 1,284 mutually exclusive records partitioned into 311 SC deployed, 180 VSC deployed, 310 SC ending, 128 VSC ending, and 355 duplicate/sector status notices.
  - **Table B (Derived Event Lifecycle Ledger):** Exactly 438 green-originating episodes (258 direct green SC, 180 green VSC partitioned into 52 escalations and 128 standalone conclusions).
  - **Calibrated Green Hazard Rates:** Direct green SC $\lambda_{\text{SC}} = 258 / 19,420 = 0.013285\text{ lap}^{-1}$; green VSC $\lambda_{\text{VSC}} = 180 / 13,558 = 0.013276\text{ lap}^{-1}$; conditional escalation $P(\text{SC} \mid \text{VSC}) = 52 / 180 = 0.288889$.
  - Descriptive macro phase ratio $310 / 19,420 = 0.015963\text{ lap}^{-1}$ strictly segregated from conditional initiation hazards.
- [x] **Common Random Numbers (CRN) Variance Reduction:**
  - Multi-seed validation across seeds 42, 101, 777, 1337, 2024: 99.996% race-time difference variance reduction, 90.64% position difference variance reduction, $\rho = 0.99996$.
  - Two-sample Kolmogorov-Smirnov test confirms no statistically detectable marginal distribution difference ($D \le 0.052, p \ge 0.498 \ge 0.05$).
- [x] **Out-of-Sample Holdout Strategy Evaluation:**
  - Selection on Set A ($N=2,500$, seed 42) vs frozen evaluation on Set B ($N=2,500$, seed 99991).
  - `SafetyCar_Reactive` confirmed as winning strategy on Set B ($\Delta_{\text{pos}} = -0.121$, $p = 0.00045$, Holm-Bonferroni adjusted $p = 0.00045$).
- [x] **Implementation Audit & Gate Tests:**
  - Independent orthogonal random stream (`master_seed + 8089`) and single-evaluation guard per VSC episode implemented in `backend/simulation/engine.py`.
  - Versioned closeout artifacts serialized to `artifacts/reports/EXP-0006/` (`exp_0006_final_closeout_v3.json`).
  - 126 automated backend pytest unit, integration, and mathematical regression tests passing in `tests/test_phase7_numerical_gate.py`.
  - Next.js 14 frontend production build verified.

---

## 3. Transition to Phase 8

EXP-0006 is officially frozen. Phase 8 is authorized to proceed:
1. Port validated research models (Models 0 through 5) from `notebooks/` to production library `ml/`.
2. Construct unified cross-model benchmark evaluation harness on the primary historical cohort (2018–2024, 149 rounds).
3. Evaluate LambdaMART listwise ranking and hierarchical Bayesian formulations.
4. Synthesize verified empirical artifacts into the academic paper draft and traceability matrices.
