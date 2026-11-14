"""Canonical candidate-pool schema, validation, and ordering rules (ml.data.candidate_schema).

Enforces:
- One candidate row per driver per Grand Prix event.
- Strict outcome-independent candidate ordering (sorted by driver_id, never finishing position).
- Race-level grouping preservation.
- Race-specific effective starting-grid encoding for pit-lane, missing, and grid-zero records.
- Explicit indicators separating verified pit-lane starts, ambiguous zero-grid entries, missing, and invalid grids.
- Strict anti-leakage guards forbidding post-race classification fields from establishing pre-race verification.
- Empirical audit notation regarding grid-zero ambiguity.
"""

from typing import Any, Dict, List, Optional, Union
import numpy as np
import pandas as pd


GRID_ZERO_AUDIT_NOTE: str = (
    "GRID_ZERO_AMBIGUITY: Starting grid position 0 is an API timing indicator "
    "(49 of 56 audited historical instances represent verified pit-lane starts, "
    "while 7 represent ambiguous non-starts / withdrawals recorded with position_text 'W'). "
    "In pre-race feature processing, zero-grid entries remain strictly ambiguous unless "
    "supported by independent pre-race evidence (such as official FIA steward bulletins or "
    "pre-session transponder manifests). Post-race classification fields must never be used "
    "to manufacture pre-race verification."
)

POST_RACE_RESULT_COLUMNS: List[str] = [
    "finish_position",
    "finish_position_int",
    "position_order",
    "positionOrder",
    "position",
    "position_text",
    "positionText",
    "y",
    "status",
    "points",
    "laps",
    "laps_completed",
    "time",
    "official_time",
    "time_millis",
    "fastest_lap",
    "fastest_lap_number",
    "fastest_lap_time",
    "fastest_lap_rank",
    "fastest_lap_avg_speed",
]

FORBIDDEN_SORT_COLUMNS: List[str] = POST_RACE_RESULT_COLUMNS


def validate_candidate_pool(
    df: pd.DataFrame,
    require_target: bool = True,
    target_col: str = "y",
    race_id_col: str = "race_id",
    driver_id_col: str = "driver_id",
) -> pd.DataFrame:
    """
    Validate candidate pool integrity for modeling and evaluation.

    Checks:
    1. Required identifier columns exist.
    2. No duplicate candidates exist for any (race_id, driver_id) pair.
    3. If target is required, y is binary in {0, 1} and exactly one winner exists per race.
    """
    if df.empty:
        raise ValueError("Candidate DataFrame cannot be empty.")

    required_cols = [race_id_col, driver_id_col]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required identifier columns: {missing}.")

    # Duplicate check within race
    duplicates = df.duplicated(subset=[race_id_col, driver_id_col], keep=False)
    if duplicates.any():
        n_dups = int(duplicates.sum())
        sample = df.loc[duplicates, [race_id_col, driver_id_col]].head(4).to_dict(orient="records")
        raise ValueError(
            f"Found {n_dups} duplicate candidate rows for ({race_id_col}, {driver_id_col}). Sample: {sample}."
        )

    if require_target:
        if target_col not in df.columns:
            raise ValueError(f"Required target column '{target_col}' not found in candidate pool.")

        y_vals = df[target_col].to_numpy()
        if not np.all(np.isin(y_vals, [0, 1])):
            raise ValueError(f"Target column '{target_col}' must contain binary values in {{0, 1}}.")

        winner_counts = df.groupby(race_id_col)[target_col].sum()
        invalid_races = winner_counts[winner_counts != 1]
        if not invalid_races.empty:
            sample_invalid = invalid_races.head(3).to_dict()
            raise ValueError(
                f"Evaluation requires exactly one winner per race. Found invalid winner counts in {len(invalid_races)} races. Sample: {sample_invalid}."
            )

    return df


def enforce_outcome_independent_ordering(
    df: pd.DataFrame,
    race_id_col: str = "race_id",
    driver_id_col: str = "driver_id",
    additional_sort_cols: Optional[List[str]] = None,
) -> pd.DataFrame:
    """
    Enforces strictly outcome-independent candidate ordering.

    Sorts candidates deterministically by race identifier and driver ID.
    Explicitly refuses to sort by finishing position or any post-race outcome field.
    """
    sort_cols = [race_id_col]
    if additional_sort_cols:
        for col in additional_sort_cols:
            if col in FORBIDDEN_SORT_COLUMNS:
                raise ValueError(
                    f"Refusing to sort candidates by outcome column '{col}'. "
                    f"Candidate ordering must be strictly outcome-independent to prevent tie-breaking leakage."
                )
            if col in df.columns and col not in sort_cols:
                sort_cols.append(col)

    if driver_id_col in df.columns and driver_id_col not in sort_cols:
        sort_cols.append(driver_id_col)

    ordered_df = df.sort_values(by=sort_cols).reset_index(drop=True).copy()
    return ordered_df


def encode_effective_grid(
    df: pd.DataFrame,
    grid_col: str = "grid",
    race_id_col: str = "race_id",
    effective_grid_col: str = "effective_grid",
    is_grid_zero_col: str = "is_grid_zero",
    is_grid_missing_col: str = "is_grid_missing",
    is_grid_invalid_col: str = "is_grid_invalid",
    is_grid_ambiguous_col: str = "is_grid_ambiguous",
    is_pit_lane_verified_col: str = "is_pit_lane_verified",
    pre_race_verification_col: Optional[str] = None,
) -> pd.DataFrame:
    """
    Compute race-specific effective starting-grid position, grid-zero indicators,
    and missingness/ambiguity flags with strict temporal integrity.

    Distinguishes:
    - Positive starting grid values (grid > 0).
    - Verified pit-lane starts (grid == 0 with independent pre-race evidence).
    - Ambiguous zero-grid entries (grid == 0 without confirmed pre-race pit-lane verification).
    - Missing grid values (NaN / null / empty).
    - Invalid or negative grid values (grid < 0 or corrupted non-numeric string).

    Strict Temporal Integrity Guard:
        Post-race result columns (finish position, position text, status, laps, points)
        must NEVER be passed as pre_race_verification_col. Passing a post-race result field
        raises ValueError to prevent outcome leakage into pre-race feature matrices.

    Formula for effective_grid:
        For candidate i with valid grid_i > 0:
            effective_grid_i = grid_i
        For candidate i with grid_i <= 0, missing, or invalid:
            effective_grid_i = max_{j: grid_j > 0}(grid_j) + 1.0

    Parameters:
        df: Candidate DataFrame.
        grid_col: Column containing raw starting grid numbers.
        race_id_col: Grouping column for Grand Prix events.
        effective_grid_col: Output column name for effective grid.
        is_grid_zero_col: Output column indicating raw grid == 0.
        is_grid_missing_col: Output column indicating unrecorded/null grid.
        is_grid_invalid_col: Output column indicating negative or corrupted grid.
        is_grid_ambiguous_col: Output column indicating ambiguous zero-grid status.
        is_pit_lane_verified_col: Output column indicating confirmed pit-lane start.
        pre_race_verification_col: Optional column providing independent pre-race verification
                                   (e.g., 'pre_race_pit_lane_start' from official FIA bulletin).
                                   Must not be a post-race result field.

    Returns:
        DataFrame with transformed effective_grid and all diagnostic indicator flags.
    """
    if df.empty:
        return df.copy()

    if grid_col not in df.columns:
        raise ValueError(f"Grid column '{grid_col}' not found in DataFrame.")

    # Guard: Pre-race verification must NOT use post-race result fields
    if pre_race_verification_col is not None:
        if pre_race_verification_col.lower() in [c.lower() for c in POST_RACE_RESULT_COLUMNS]:
            raise ValueError(
                f"Temporal leakage violation: Column '{pre_race_verification_col}' is a post-race result field "
                f"and must not be used to establish pre-race pit-lane verification. "
                f"Pre-race verification must rely exclusively on pre-race manifests (such as official "
                f"stewards bulletins or pre-session transponder telemetry)."
            )

    res = df.copy()
    raw_col = res[grid_col]
    raw_grid = pd.to_numeric(raw_col, errors="coerce")

    # 1. Missing vs Invalid indicators
    # Missing if NaN, None, or null originally
    is_missing = raw_col.isna().to_numpy()
    # Invalid if not originally missing, but conversion failed or negative numeric
    is_invalid = (~is_missing) & (raw_grid.isna() | (raw_grid < 0)).to_numpy()

    # 2. Grid zero indicator
    is_zero = ((~is_missing) & (~is_invalid) & (raw_grid == 0)).to_numpy()

    # 3. Pit-lane verification vs ambiguity (strictly pre-race)
    is_verified = np.zeros(len(res), dtype=int)
    is_ambiguous = np.zeros(len(res), dtype=int)

    if pre_race_verification_col is not None and pre_race_verification_col in res.columns:
        v_col = res[pre_race_verification_col]
        for idx in range(len(res)):
            if is_zero[idx]:
                val = v_col.iloc[idx]
                if isinstance(val, (bool, np.bool_)):
                    if val:
                        is_verified[idx] = 1
                    else:
                        is_ambiguous[idx] = 1
                elif pd.notna(val) and val in {1, "1", "true", "True", "VERIFIED"}:
                    is_verified[idx] = 1
                else:
                    is_ambiguous[idx] = 1
    else:
        # Without independent pre-race verification evidence, all zero-grid entries
        # are explicitly retained as ambiguous rather than manufacturing verification.
        for idx in range(len(res)):
            if is_zero[idx]:
                is_ambiguous[idx] = 1

    res[is_grid_zero_col] = is_zero.astype(int)
    res[is_grid_missing_col] = is_missing.astype(int)
    res[is_grid_invalid_col] = is_invalid.astype(int)
    res[is_grid_ambiguous_col] = is_ambiguous
    res[is_pit_lane_verified_col] = is_verified

    # 4. Compute maximum positive grid per race
    positive_mask = (~is_missing) & (~is_invalid) & (raw_grid > 0)
    pos_grid_df = res.loc[positive_mask].copy()
    pos_grid_df["_pos_val"] = raw_grid[positive_mask]

    max_pos = pos_grid_df.groupby(race_id_col)["_pos_val"].max()

    effective_positions = []
    for idx, row in res.iterrows():
        r_id = row[race_id_col]
        pos_entry = positive_mask.loc[idx] if idx in positive_mask.index else False
        if pos_entry:
            effective_positions.append(float(raw_grid.loc[idx]))
        else:
            # Fallback to race max positive grid + 1.0, or 21.0 if no positive grid exists
            max_g = max_pos.get(r_id, 20.0)
            effective_positions.append(float(max_g) + 1.0)

    res[effective_grid_col] = effective_positions
    return res


def audit_historical_grid_zero_retrospective(
    df: pd.DataFrame,
    grid_col: str = "grid",
    position_text_col: str = "position_text",
) -> Dict[str, Any]:
    """
    Retrospective research audit function for analyzing historical grid-zero entries.

    IMPORTANT: This function is for retrospective dataset auditing and provenance reporting ONLY.
    Its outputs must NEVER be used as inputs for pre-race modeling.
    """
    if grid_col not in df.columns or position_text_col not in df.columns:
        raise ValueError("Audit requires both grid_col and position_text_col.")

    g0 = df[df[grid_col] == 0].copy()
    total_g0 = len(g0)
    if total_g0 == 0:
        return {"total_zero_grid": 0, "active_starters": 0, "withdrawn_dns": 0}

    withdrawn_dns = int(g0[position_text_col].astype(str).str.strip().str.upper().isin(["W", "D", "DNS"]).sum())
    active_starters = total_g0 - withdrawn_dns

    return {
        "total_zero_grid": total_g0,
        "active_starters": active_starters,
        "withdrawn_dns": withdrawn_dns,
        "active_starter_proportion": float(active_starters / total_g0),
        "audit_note": GRID_ZERO_AUDIT_NOTE,
    }
