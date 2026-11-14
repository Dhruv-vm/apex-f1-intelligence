# APEX — Data Storage Architecture & Hygiene

## 1. Directory Structure & Tiers

The `data/` directory is partitioned into four distinct operational tiers:

```text
data/
├── README.md                           # This architecture and storage policy document
│
├── raw/                                # Immutable external payloads and provider caches
│   └── .gitkeep
│
├── interim/                            # Intermediate parsed records, uncalibrated tables, sqlite db
│   └── .gitkeep
│
├── processed/                          # Formatted, validated, time-aligned feature matrices (Parquet)
│   └── .gitkeep
│
└── external/                           # Reference external metadata (circuit specs, regulations)
    └── .gitkeep
```

---

## 2. Storage Tier Descriptions

### `data/raw/`
- **Role:** Immutable staging cache for unmodified external API payloads (FastF1 session caches, Jolpica JSON responses, raw weather station dumps).
- **Policy:** Never edited manually. Kept strictly out of Git version control via `.gitignore`. Re-creatable by running ingestion audit scripts.

### `data/interim/`
- **Role:** Cleaned, partially transformed tables, intermediate SQLite databases, and parsed lap tables prior to feature extraction.
- **Policy:** Ephemeral workspace. Can be safely purged and rebuilt from `data/raw/` at any time.

### `data/processed/`
- **Role:** The canonical, versioned, time-aligned feature store. Contains columnar Parquet files with explicit timestamp cutoff tags, driver identifiers, and validated ground-truth labels.
- **Policy:** Used directly by baseline and sequential models in `ml/`. Pinned by dataset release versions (e.g., `apex_dataset_v1.0.0.parquet`).

### `data/external/`
- **Role:** Hand-verified static reference tables (official FIA sporting regulations, circuit GPS coordinates, tire compound stiffness specs).
- **Policy:** Small, verified text/CSV files may be version-controlled if fully audited and permissible under licensing terms.

---

## 3. Git Hygiene & Sensitive Data Safeguards

1. **No Binary or Large File Commits:**
   Telemetry files and Parquet tables easily exceed hundreds of megabytes. All files in `data/raw/`, `data/interim/`, and `data/processed/` are excluded by `.gitignore` (except `.gitkeep`).
2. **Reproducibility Over Storage:**
   Any developer or researcher cloning this repository must be able to recreate the entire dataset from scratch using the deterministic scripts in `scripts/ingestion/` without relying on committed binary data files.
3. **Licensing & Redistribution Compliance:**
   Raw timing feeds and telemetry downloaded from proprietary APIs must never be committed to public repositories. Only open data schemas and reproducible extraction recipes belong in source control.
