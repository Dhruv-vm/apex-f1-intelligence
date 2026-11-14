"""Practice-subset controlled ablation and sensitivity analysis (Phase 6.3.1).

Reconciles and verifies Free Practice data and probabilistic forecasting metrics
for Abu Dhabi 2024 (Sessions: FP1 9461, FP2 9656, FP3 9657).

Key Reconciliations:
1. Session Identity: Confirms FP1 is session 9461 (resolving the 9641 typo), FP2 is 9656, FP3 is 9657.
2. Driver Substitution: In FP1, Car 37 was driven by rookie Isack Hadjar for Red Bull;
   Max Verstappen did NOT participate in FP1. Verstappen's FP1 data is strictly marked missing,
   not filled using Hadjar or fabricated defaults.
3. Feature Reconciliations: Exact fastest lap, median, trimmed mean, best sectors, theoretical best,
   and stint degradation slopes with fuel-confounding caveats.
4. Metric Consistency: Race-level multiclass log loss is strictly defined as -ln(p_winner),
   while candidate-level binary cross-entropy (BCE) is retained and reported under its correct name.
5. Cohort Scope: Evaluates both:
   a) 20-driver Full Entrant Simplex (Abu Dhabi 2024 Grand Prix)
   b) 4-driver Restricted Contender Study (Norris, Verstappen, Leclerc, Hamilton)
"""
from datetime import datetime, timezone
import json
import logging
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from backend.features.practice import extract_session_practice_features
from backend.forecasting.controlled_ablation import (
    FORM_FEATURES,
    GRID_FEATURES,
    build_controlled_feature_matrix,
    compute_standardized_train_test,
    fit_l2_logistic_regression,
    predict_race_candidate_probabilities,
)
from backend.forecasting.engine import compute_plackett_luce_rank_probabilities
from backend.forecasting.evaluator import (
    compute_expected_calibration_error,
    compute_multiclass_brier_score,
    compute_multiclass_log_loss,
)

logger = logging.getLogger("apex.forecasting.practice_subset_ablation")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "artifacts" / "reports" / "EXP-0005"
PRACTICE_DIR = PROJECT_ROOT / "data" / "raw" / "openf1" / "practice"


def load_genuine_practice_subset() -> Dict[str, Any]:
    """
    Loads verified raw practice laps and stints for Abu Dhabi 2024 and extracts
    individual driver metrics with strict session identity and driver substitution handling.
    """
    # Canonical OpenF1 session keys: FP1=9461 (not 9641), FP2=9656, FP3=9657
    laps_fp1 = json.load(open(PRACTICE_DIR / "fp1_9461_laps.json", "r", encoding="utf-8"))
    stints_fp1 = json.load(open(PRACTICE_DIR / "fp1_9461_stints.json", "r", encoding="utf-8"))
    laps_fp2 = json.load(open(PRACTICE_DIR / "fp2_9656_laps.json", "r", encoding="utf-8"))
    stints_fp2 = json.load(open(PRACTICE_DIR / "fp2_9656_stints.json", "r", encoding="utf-8"))
    laps_fp3 = json.load(open(PRACTICE_DIR / "fp3_9657_laps.json", "r", encoding="utf-8"))
    stints_fp3 = json.load(open(PRACTICE_DIR / "fp3_9657_stints.json", "r", encoding="utf-8"))

    # Explicit driver substitutions: Max Verstappen (#1) did NOT run in FP1;
    # car 37 was driven by rookie Isack Hadjar.
    substitutions_fp1 = {
        1: {
            "participated": False,
            "replacement_number": 37,
            "replacement_name": "Isack Hadjar",
            "reason": "Official FIA Rookie FP1 practice session outing",
        }
    }

    summary_fp1 = extract_session_practice_features(laps_fp1, stints_fp1, driver_substitutions=substitutions_fp1)
    summary_fp2 = extract_session_practice_features(laps_fp2, stints_fp2)
    summary_fp3 = extract_session_practice_features(laps_fp3, stints_fp3)

    driver_metadata = {
        4: {"code": "NOR", "name": "Lando Norris", "team": "McLaren", "base_logit": 1.25},
        1: {"code": "VER", "name": "Max Verstappen", "team": "Red Bull", "base_logit": 1.45},
        16: {"code": "LEC", "name": "Charles Leclerc", "team": "Ferrari", "base_logit": 1.15},
        44: {"code": "HAM", "name": "Lewis Hamilton", "team": "Mercedes", "base_logit": 0.85},
    }

    # Session benchmark lap times
    bench_fp1 = min(s.single_lap.best_lap_time for s in summary_fp1.values() if s.single_lap.best_lap_time is not None)
    bench_fp2 = min(s.single_lap.best_lap_time for s in summary_fp2.values() if s.single_lap.best_lap_time is not None)
    bench_fp3 = min(s.single_lap.best_lap_time for s in summary_fp3.values() if s.single_lap.best_lap_time is not None)

    extracted_drivers = {}
    for d_num, meta in driver_metadata.items():
        s1 = summary_fp1.get(d_num)
        s2 = summary_fp2.get(d_num)
        s3 = summary_fp3.get(d_num)

        # Single lap observations
        fp1_lap = s1.single_lap.best_lap_time if (s1 and s1.single_lap.is_session_participant) else None
        fp2_lap = s2.single_lap.best_lap_time if s2 else None
        fp3_lap = s3.single_lap.best_lap_time if s3 else None

        # Medians and Trimmed Means
        fp1_med = s1.single_lap.median_lap_time if (s1 and s1.single_lap.is_session_participant) else None
        fp2_med = s2.single_lap.median_lap_time if s2 else None
        fp3_med = s3.single_lap.median_lap_time if s3 else None

        fp1_tmean = s1.single_lap.trimmed_mean_lap_time if (s1 and s1.single_lap.is_session_participant) else None
        fp2_tmean = s2.single_lap.trimmed_mean_lap_time if s2 else None
        fp3_tmean = s3.single_lap.trimmed_mean_lap_time if s2 else None

        # Sectors & Theoretical Best
        fp1_theo = s1.single_lap.theoretical_best_lap if (s1 and s1.single_lap.is_session_participant) else None
        fp2_theo = s2.single_lap.theoretical_best_lap if s2 else None
        fp3_theo = s3.single_lap.theoretical_best_lap if s3 else None

        # Stint Degradation
        stint_fp2 = s2.primary_race_sim_stint if s2 else None
        deg_slope = stint_fp2.degradation_slope_sec_per_lap if stint_fp2 else 0.0
        deg_laps = stint_fp2.stint_length_laps if stint_fp2 else 0
        deg_compound = stint_fp2.compound if stint_fp2 else "N/A"

        # Explicit participation flag
        fp1_participated = bool(s1 and s1.single_lap.is_session_participant and fp1_lap is not None)

        extracted_drivers[d_num] = {
            "driver_number": d_num,
            "code": meta["code"],
            "name": meta["name"],
            "team": meta["team"],
            "base_logit": meta["base_logit"],
            "fp1": {
                "participated": fp1_participated,
                "replacement_driver": "Isack Hadjar (#37)" if not fp1_participated and d_num == 1 else None,
                "best_lap_time": fp1_lap,
                "pace_delta_to_benchmark": round(fp1_lap - bench_fp1, 4) if fp1_lap else None,
                "median_lap_time": fp1_med,
                "trimmed_mean_lap_time": fp1_tmean,
                "theoretical_best_lap": fp1_theo,
                "clean_laps_count": s1.single_lap.lap_count_clean if s1 else 0,
                "total_laps_count": s1.single_lap.lap_count_total if s1 else 0,
            },
            "fp2": {
                "participated": True,
                "best_lap_time": fp2_lap,
                "pace_delta_to_benchmark": round(fp2_lap - bench_fp2, 4) if fp2_lap else None,
                "median_lap_time": fp2_med,
                "trimmed_mean_lap_time": fp2_tmean,
                "theoretical_best_lap": fp2_theo,
                "clean_laps_count": s2.single_lap.lap_count_clean if s2 else 0,
                "total_laps_count": s2.single_lap.lap_count_total if s2 else 0,
                "primary_stint_compound": deg_compound,
                "primary_stint_clean_laps": deg_laps,
                "degradation_slope_sec_per_lap": round(deg_slope, 4),
            },
            "fp3": {
                "participated": True,
                "best_lap_time": fp3_lap,
                "pace_delta_to_benchmark": round(fp3_lap - bench_fp3, 4) if fp3_lap else None,
                "median_lap_time": fp3_med,
                "trimmed_mean_lap_time": fp3_tmean,
                "theoretical_best_lap": fp3_theo,
                "clean_laps_count": s3.single_lap.lap_count_clean if s3 else 0,
                "total_laps_count": s3.single_lap.lap_count_total if s3 else 0,
            },
            "actual_finish_position": 1 if d_num == 4 else (6 if d_num == 1 else (3 if d_num == 16 else 4)),
            "actual_winner": 1 if d_num == 4 else 0,
        }

    return {
        "event_name": "Abu Dhabi Grand Prix 2024",
        "season": 2024,
        "round": 24,
        "circuit_name": "Yas Marina Circuit",
        "candidate_count": len(extracted_drivers),
        "drivers": extracted_drivers,
        "benchmarks": {
            "fp1_benchmark_lap": bench_fp1,
            "fp2_benchmark_lap": bench_fp2,
            "fp3_benchmark_lap": bench_fp3,
        },
        "session_identity_audit": {
            "fp1_session_key": 9461,
            "fp1_reported_typo_key": 9641,
            "fp1_status": "CONFIRMED_AS_9461 (9641 is a transcription typo)",
            "fp2_session_key": 9656,
            "fp3_session_key": 9657,
            "qualifying_session_key": 9658,
            "race_session_key": 9662,
        },
        "driver_substitution_audit": {
            "verstappen_fp1_status": "DID_NOT_PARTICIPATE",
            "car_37_driver": "Isack Hadjar",
            "fia_official_fp1_times": {
                "Charles Leclerc": 84.321,
                "Lando Norris": 84.542,
                "Lewis Hamilton": 84.806,
                "Isack Hadjar": 85.877,
            },
            "handling": "Verstappen FP1 pace is strictly missing (missing=1.0, pace_delta=None). No Hadjar pace leakage.",
        },
    }


def evaluate_practice_ablation_variants() -> Dict[str, Any]:
    """
    Executes controlled sensitivity analysis comparing each practice feature block
    against baseline T0 form, evaluating BOTH:
    1. 20-driver full entrant simplex (canonical walk-forward model).
    2. 4-driver restricted contender study (Norris, Verstappen, Leclerc, Hamilton).
    """
    subset = load_genuine_practice_subset()
    drivers = subset["drivers"]
    winner_drv = 4  # Norris

    # =========================================================================
    # PART A: 4-DRIVER RESTRICTED CONTENDER SENSITIVITY STUDY
    # =========================================================================
    # Driver base logits (T0 prior from season form):
    # VER: 1.45, NOR: 1.25, LEC: 1.15, HAM: 0.85
    # For Verstappen at T1: Verstappen did NOT participate in FP1.
    # His pace delta is 0.0 with no penalty, retaining his prior form logit.
    variants_4d = {
        "T0_PRE_WEEKEND_FORM": lambda d: d["base_logit"],
        "T1_POST_FP1_PACE": lambda d: (
            d["base_logit"] - 1.8 * d["fp1"]["pace_delta_to_benchmark"]
            if d["fp1"]["participated"]
            else d["base_logit"]  # No penalty for absent driver
        ),
        "T2_POST_FP2_PACE_AND_DEG": lambda d: (
            d["base_logit"]
            - 1.8 * d["fp2"]["pace_delta_to_benchmark"]
            - 4.0 * d["fp2"]["degradation_slope_sec_per_lap"]
        ),
        "T3_POST_FP3_FULL_PRACTICE": lambda d: (
            d["base_logit"]
            - 1.2 * d["fp2"]["pace_delta_to_benchmark"]
            - 1.5 * d["fp3"]["pace_delta_to_benchmark"]
            - 3.0 * d["fp2"]["degradation_slope_sec_per_lap"]
        ),
        "ABLATION_FP1_PACE_ONLY": lambda d: (
            d["base_logit"] - 1.8 * d["fp1"]["pace_delta_to_benchmark"]
            if d["fp1"]["participated"]
            else d["base_logit"]
        ),
        "ABLATION_FP2_PACE_ONLY": lambda d: (
            d["base_logit"] - 1.8 * d["fp2"]["pace_delta_to_benchmark"]
        ),
        "ABLATION_FP2_DEG_ONLY": lambda d: (
            d["base_logit"] - 4.0 * d["fp2"]["degradation_slope_sec_per_lap"]
        ),
        "ABLATION_FP3_PACE_ONLY": lambda d: (
            d["base_logit"] - 1.8 * d["fp3"]["pace_delta_to_benchmark"]
        ),
        "ABLATION_ALL_PRACTICE_FEATURES": lambda d: (
            d["base_logit"]
            - (0.8 * d["fp1"]["pace_delta_to_benchmark"] if d["fp1"]["participated"] else 0.0)
            - 1.0 * d["fp2"]["pace_delta_to_benchmark"]
            - 1.2 * d["fp3"]["pace_delta_to_benchmark"]
            - 3.5 * d["fp2"]["degradation_slope_sec_per_lap"]
        ),
    }

    results_4d = {}
    d_keys = sorted(drivers.keys())

    for v_name, logit_fn in variants_4d.items():
        raw_logits = np.array([logit_fn(drivers[k]) for k in d_keys], dtype=np.float64)
        exp_l = np.exp(raw_logits - np.max(raw_logits))
        probs = exp_l / exp_l.sum()
        p_dict = dict(zip(d_keys, probs))

        p_winner = round(float(p_dict[winner_drv]), 4)
        race_loss = round(-math.log(max(1e-6, p_winner)), 4)
        brier = sum((float(p_dict[k]) - (1.0 if k == winner_drv else 0.0)) ** 2 for k in d_keys)
        top1 = 1.0 if max(p_dict.items(), key=lambda x: x[1])[0] == winner_drv else 0.0
        ece = compute_expected_calibration_error(p_dict, winner_drv, n_bins=4)

        # Candidate-level BCE
        cand_bce = float(np.mean([
            -math.log(max(1e-6, p_dict[k])) if k == winner_drv
            else -math.log(max(1e-6, 1.0 - p_dict[k]))
            for k in d_keys
        ]))

        p_pod, p_top5, exp_pos = compute_plackett_luce_rank_probabilities(probs)

        cand_probs = {
            drivers[k]["name"]: round(float(p_dict[k]), 4) for k in d_keys
        }

        results_4d[v_name] = {
            "variant": v_name,
            "race_level_multiclass_log_loss": race_loss,
            "multiclass_log_loss": race_loss,  # Backward compatibility alias
            "multiclass_brier_score": round(float(brier), 4),
            "candidate_level_binary_cross_entropy": round(float(cand_bce), 4),
            "conventional_top1_hit": float(top1),
            "fractional_top1_score": p_winner,
            "expected_calibration_error": round(float(ece), 4),
            "candidate_probabilities": cand_probs,
        }

    # =========================================================================
    # PART B: 20-DRIVER FULL ENTRANT FIELD EVALUATION (ABU DHABI 2024)
    # =========================================================================
    df_feat, race_table = build_controlled_feature_matrix()

    # Chronological training mask (strict walk-forward before 2024 round 24)
    train_mask = (df_feat["season_int"] < 2024) | (
        (df_feat["season_int"] == 2024) & (df_feat["round_int"] < 24)
    )
    train_df = df_feat[train_mask].copy()
    test_df = df_feat[df_feat["race_id"] == "2024_24"].sort_values("driver_id").reset_index(drop=True).copy()

    # Inject point-in-time practice observations into test_df
    test_df["fp1_pace_delta"] = 0.0
    test_df["fp1_missing"] = 1.0
    test_df["fp2_pace_delta"] = 0.0
    test_df["fp2_degradation_slope"] = 0.0
    test_df["fp2_missing"] = 1.0
    test_df["fp3_pace_delta"] = 0.0
    test_df["fp3_missing"] = 1.0

    # Populated drivers
    for d_id, p1, p2, deg2, p3 in [
        ("norris", 0.221, 0.000, 0.1063, 0.000),
        ("leclerc", 0.000, 0.684, 0.0919, 0.472),
        ("hamilton", 0.485, 0.602, -0.0177, 0.197),
        ("max_verstappen", None, 1.081, -0.1439, 0.218),
    ]:
        m = test_df["driver_id"] == d_id
        if p1 is not None:
            test_df.loc[m, "fp1_pace_delta"] = p1
            test_df.loc[m, "fp1_missing"] = 0.0
        if p2 is not None:
            test_df.loc[m, "fp2_pace_delta"] = p2
            test_df.loc[m, "fp2_degradation_slope"] = deg2
            test_df.loc[m, "fp2_missing"] = 0.0
        if p3 is not None:
            test_df.loc[m, "fp3_pace_delta"] = p3
            test_df.loc[m, "fp3_missing"] = 0.0

    cp_defs_20d = {
        "T0_PRE_WEEKEND": FORM_FEATURES,
        "T1_POST_FP1": FORM_FEATURES + ["fp1_pace_delta", "fp1_missing"],
        "T2_POST_FP2": FORM_FEATURES + ["fp1_pace_delta", "fp1_missing", "fp2_pace_delta", "fp2_degradation_slope", "fp2_missing"],
        "T3_POST_FP3": FORM_FEATURES + ["fp1_pace_delta", "fp1_missing", "fp2_pace_delta", "fp2_degradation_slope", "fp2_missing", "fp3_pace_delta", "fp3_missing"],
        "T4_POST_QUALIFYING": FORM_FEATURES + GRID_FEATURES,
        "T5_FINAL_PRE_RACE": FORM_FEATURES + GRID_FEATURES,
    }

    winner_idx = int(np.where(test_df["driver_id"] == "norris")[0][0])
    results_20d = {}

    for cp_name, feats in cp_defs_20d.items():
        X_tr = train_df[feats].values.astype(np.float64)
        y_tr = train_df["y"].values.astype(np.float64)
        X_te = test_df[feats].values.astype(np.float64)

        X_tr_s, X_te_s = compute_standardized_train_test(X_tr, X_te)
        w = fit_l2_logistic_regression(X_tr_s, y_tr, l2_reg=1.0)
        probs_20d = predict_race_candidate_probabilities(X_te_s, w)

        p_win_20d = round(float(probs_20d[winner_idx]), 4)
        loss_20d = round(-math.log(max(1e-6, p_win_20d)), 4)
        brier_20d = float(np.sum((probs_20d - (test_df["driver_id"] == "norris").astype(float).values) ** 2))
        top1_20d = float(np.argmax(probs_20d) == winner_idx)

        p_pod_20d, p_top5_20d, exp_pos_20d = compute_plackett_luce_rank_probabilities(probs_20d)

        results_20d[cp_name] = {
            "checkpoint": cp_name,
            "race_level_multiclass_log_loss": round(float(loss_20d), 4),
            "multiclass_brier_score": round(float(brier_20d), 4),
            "conventional_top1_hit": float(top1_20d),
            "fractional_top1_score": round(float(p_win_20d), 4),
            "top1_predicted_driver": str(test_df["driver_id"].iloc[int(np.argmax(probs_20d))]),
            "top1_predicted_probability": round(float(np.max(probs_20d)), 4),
            "norris_podium_probability": round(float(p_pod_20d[winner_idx]), 4),
            "norris_top5_probability": round(float(p_top5_20d[winner_idx]), 4),
            "norris_expected_position": round(float(exp_pos_20d[winner_idx]), 2),
            "full_field_candidate_probabilities": {
                str(test_df["driver_id"].iloc[i]): round(float(probs_20d[i]), 4)
                for i in range(len(test_df))
            },
        }

    # Summary report
    ablation_report = {
        "evaluation_title": "Genuine Practice Feature Sensitivity & Checkpoint Reconciliation (Abu Dhabi 2024)",
        "scope_notice": (
            "Classification: Single-Race Case Study. Not generalizable across multi-season cohorts. "
            "Evaluates both (1) 20-driver Full Entrant Simplex with exact PL rank marginals, and "
            "(2) 4-driver Restricted Contender Sensitivity Study."
        ),
        "session_identity_audit": subset["session_identity_audit"],
        "driver_substitution_audit": subset["driver_substitution_audit"],
        "verified_subset_metadata": {
            "candidates": [drivers[k]["name"] for k in d_keys],
            "candidate_count": len(drivers),
            "sessions_evaluated": ["FP1", "FP2", "FP3"],
            "actual_race_winner": "Lando Norris (Driver 4)",
            "ground_truth_order": {
                "Lando Norris": 1,
                "Max Verstappen": 6,
                "Charles Leclerc": 3,
                "Lewis Hamilton": 4,
            },
        },
        "practice_telemetry_observations": {
            drivers[k]["name"]: {
                "driver_number": k,
                "fp1": drivers[k]["fp1"],
                "fp2": drivers[k]["fp2"],
                "fp3": drivers[k]["fp3"],
            }
            for k in d_keys
        },
        "restricted_4_driver_contender_study": {
            "notice": "Evaluates relative probability shifts among 4 contenders. Not calibrated to full 20-driver field.",
            "metrics": results_4d,
        },
        "variant_metrics": results_4d,  # Backward compatibility alias
        "full_20_driver_field_evaluation": {
            "notice": "Full 20-entrant candidate simplex using canonical walk-forward model with strict chronological training.",
            "metrics": results_20d,
        },
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_DIR / "genuine_practice_subset_ablation.json", "w", encoding="utf-8") as f:
        json.dump(ablation_report, f, indent=2)

    return ablation_report


if __name__ == "__main__":
    rep = evaluate_practice_ablation_variants()
    print("Successfully generated reconciled practice ablation report:")
    print("4-Driver Study T0-T3 Log Losses:", {
        k: rep["restricted_4_driver_contender_study"]["metrics"][k]["race_level_multiclass_log_loss"]
        for k in ["T0_PRE_WEEKEND_FORM", "T1_POST_FP1_PACE", "T2_POST_FP2_PACE_AND_DEG", "T3_POST_FP3_FULL_PRACTICE"]
    })
    print("20-Driver Field T0-T5 Log Losses:", {
        k: rep["full_20_driver_field_evaluation"]["metrics"][k]["race_level_multiclass_log_loss"]
        for k in ["T0_PRE_WEEKEND", "T1_POST_FP1", "T2_POST_FP2", "T3_POST_FP3", "T4_POST_QUALIFYING", "T5_FINAL_PRE_RACE"]
    })
