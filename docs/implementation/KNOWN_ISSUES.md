# APEX — Known Issues, Technical Debt & Open Questions

## 1. Active Open Questions & Blockers

| Issue ID | Category | Summary | Severity | Impacted Area | Resolution Plan |
|---|---|---|---|---|---|
| `ISSUE-001` | Data / API | Rate limits and response latency of Jolpica and OpenF1 APIs under high concurrency | High | Data Ingestion | Benchmark during Milestone 1 data availability audit. |
| `ISSUE-002` | Research | Handling right-censored race outcomes (crashes, mechanical DNFs) in finish-position models | Medium | Modeling | Formulate DNF as a separate stochastic survival/classification hazard. |
| `ISSUE-003` | Research | Aerodynamic regulation break between 2021 and 2022 causing historical feature decay | High | Feature Engine | Evaluate exponential decay weighting on pre-2022 car pace features. |
| `ISSUE-004` | Data | Incomplete weather radar data for older Grand Prix rounds (2018–2020) | Low | Weather Features | Fall back to ambient session averages when radar feeds are missing. |
| `ISSUE-005` | Architecture| Local storage footprint of uncompressed high-frequency telemetry across 7 seasons | Medium | Storage / Cache | Benchmark Parquet with zstandard compression vs DuckDB in Milestone 2. |

---

## 2. Technical Debt & Design Compromises

1. **Sprint Weekend Format Heterogeneity:** Between 2021 and 2024, the FIA revised the sprint weekend rules three times (changing Friday qualifying meaning, introducing Sprint Shootout, altering parc fermé rules). The checkpoint router must accommodate these evolving format definitions.
2. **Post-Race Steward Penalty Contamination:** Steward investigations frequently conclude hours after the Grand Prix finishes. We must log `provisional_classification_time` and `final_official_classification_time` separately in the database to avoid lookahead contamination during live evaluation.

---

## 3. Licensing & Commercial Invariants

- **Formula 1 Intellectual Property & Trademarks:** APEX is an independent research platform. The system uses official timing feeds for research and academic evaluation under fair use. Commercial branding or official FOM live streaming integration is strictly out of scope.
