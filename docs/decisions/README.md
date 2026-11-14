# Architecture Decision Records (ADRs)

## 1. Purpose and Philosophy

Architecture Decision Records (ADRs) capture significant architectural, technological, and methodological decisions made throughout the lifecycle of the **APEX — F1 Intelligence** platform.

Every ADR documents:
- The context and forces motivating a decision.
- The alternatives considered.
- The chosen solution and its explicit technical rationale.
- The positive and negative consequences.
- The review conditions under which the decision must be revisited.

---

## 2. Decision Status Lifecycle

Decisions must be labeled using one of four official statuses:
- `PROPOSED`: Under discussion and review; not yet binding.
- `APPROVED`: Formally agreed upon and currently active in implementation.
- `DEPRECATED`: Superceded by a newer decision or rendered obsolete.
- `REJECTED`: Formally considered and rejected, with documented reasons.

Once written, an ADR is an immutable record. If a decision changes, create a new ADR that references and supersedes the previous record rather than rewriting past history.

---

## 3. ADR Index

| ADR ID | Title | Date | Status | Summary |
|---|---|---|---|---|
| [ADR-0001](ADR_TEMPLATE.md) | Standard Architecture Decision Record Template | 2026-10-18 | `APPROVED` | Baseline template definition for all subsequent ADRs. |
| [ADR-0002](ADR-0002-data-provider-selection-and-telemetry-strategy.md) | Data Provider Selection and Telemetry Ingestion Strategy | 2026-10-18 | `APPROVED` | Hybrid architecture: Jolpica for historical sporting records, OpenF1 for open modern telemetry. |

---

## 4. How to Create an ADR

1. Copy [ADR_TEMPLATE.md](ADR_TEMPLATE.md) to a new file named `ADR-XXXX-title-in-kebab-case.md` (e.g., `ADR-0002-temporal-storage-format.md`).
2. Fill out all sections completely.
3. Update the index table above.
4. Record cross-references in [docs/ARCHITECTURE.md](../ARCHITECTURE.md) and [docs/PROJECT_STATUS.md](../PROJECT_STATUS.md).
