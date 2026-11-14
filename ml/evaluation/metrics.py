"""Strictly proper scoring rules and race evaluation metrics (ml.evaluation.metrics).

Implements canonical metrics matching EXP-0001 through EXP-0005 standards:
- Multi-class Log Loss: -1/R * sum_{r=1}^R log(p_{r, winner})
- Multi-class Brier Score: 1/R * sum_{r=1}^R sum_{i=1}^{N_r} (p_{r, i} - y_{r, i})^2
- Tie-Aware Top-1 Accuracy: Proportion of races where actual winner is among argmax(p)
- Fractional Top-1 Credit: Top-1 credit weighted inversely by argmax set size (1 / |argmax(p)|)
- Probability Simplex Normalization verification

All functions preserve candidate alignment and reject malformed probability vectors.
"""

from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd


def check_probability_simplex(p: np.ndarray, atol: float = 1e-9) -> bool:
    """
    Verify whether a 1D probability vector lies on the probability simplex.

    Conditions:
    1. 1D non-empty array.
    2. All elements >= -atol and <= 1.0 + atol.
    3. sum(p) == 1.0 within atol.
    """
    arr = np.asarray(p, dtype=np.float64)
    if arr.ndim != 1 or len(arr) == 0:
        return False
    if np.any(arr < -atol) or np.any(arr > 1.0 + atol):
        return False
    return bool(abs(float(np.sum(arr)) - 1.0) <= atol)


def compute_single_race_metrics(
    y: np.ndarray,
    p: np.ndarray,
    eps: float = 1e-15,
    atol: float = 1e-9,
) -> Dict[str, float]:
    """
    Compute strictly proper scoring metrics for a single Grand Prix event.

    Parameters:
        y: 1D binary indicator vector (y_i = 1 for race winner, 0 otherwise).
        p: 1D probability distribution over candidates.
        eps: Lower bound for probability clipping in log loss calculation.
        atol: Absolute tolerance for simplex summation.

    Returns:
        Dict with keys: 'log_loss', 'brier_score', 'tie_aware_top1', 'fractional_top1'.

    Raises:
        ValueError: If array lengths mismatch, probabilities violate simplex, or no winner is recorded.
    """
    y_arr = np.asarray(y, dtype=np.int64)
    p_arr = np.asarray(p, dtype=np.float64)

    if len(y_arr) != len(p_arr):
        raise ValueError(f"Length mismatch: len(y)={len(y_arr)} != len(p)={len(p_arr)}.")
    if len(p_arr) == 0:
        raise ValueError("Candidate array cannot be empty.")

    if not check_probability_simplex(p_arr, atol=atol):
        sum_val = float(np.sum(p_arr))
        raise ValueError(
            f"Malformed probability vector: does not sum to 1.0 (sum={sum_val:.12f}) "
            f"or contains out-of-range elements [min={np.min(p_arr):.4f}, max={np.max(p_arr):.4f}]."
        )

    n_winners = int(np.sum(y_arr))
    if n_winners == 0:
        raise ValueError("Evaluation requires at least one recorded winner (sum(y) == 0).")

    # Multiclass Brier score: sum_{i=1..N} (p_i - y_i)^2
    brier_score = float(np.sum((p_arr - y_arr) ** 2))

    # Multiclass Log Loss: -ln(p_winner)
    winner_indices = np.flatnonzero(y_arr == 1)
    if n_winners == 1:
        w_idx = int(winner_indices[0])
        p_winner = float(np.clip(p_arr[w_idx], eps, 1.0))
        log_loss = -float(np.log(p_winner))
    else:
        # Tied winners: average log loss across winners
        log_loss = -float(np.mean([np.log(np.clip(p_arr[idx], eps, 1.0)) for idx in winner_indices]))

    # Argmax tie-breaking and fractional top-1 credit
    max_p = np.max(p_arr)
    top_mask = np.isclose(p_arr, max_p, rtol=1e-9, atol=1e-12)
    n_ties = int(np.sum(top_mask))

    winner_hits_in_top = int(np.sum(top_mask[winner_indices]))
    tie_aware_top1 = 1.0 if winner_hits_in_top > 0 else 0.0
    fractional_top1 = float(winner_hits_in_top / n_ties)

    return {
        "log_loss": log_loss,
        "brier_score": brier_score,
        "tie_aware_top1": tie_aware_top1,
        "fractional_top1": fractional_top1,
    }


def evaluate_race_predictions(
    df: pd.DataFrame,
    prob_col: str = "probability",
    target_col: str = "y",
    race_id_col: str = "race_id",
    eps: float = 1e-15,
    atol: float = 1e-9,
) -> Dict[str, Any]:
    """
    Evaluates multi-race probabilistic predictions with strict simplex and tie handling.

    Averages metric values uniformly across all unique races in the dataset (macro average).

    Returns:
        Dict containing:
        - 'races': total number of races evaluated
        - 'mean_log_loss': macro-averaged multiclass log loss
        - 'mean_brier_score': macro-averaged multiclass Brier score
        - 'tie_aware_top1': proportion of races where winner was in argmax(p)
        - 'fractional_top1': mean fractional credit assigned to winner
    """
    if df.empty:
        raise ValueError("Prediction DataFrame cannot be empty.")

    for col in [race_id_col, target_col, prob_col]:
        if col not in df.columns:
            raise ValueError(f"Required column '{col}' missing from prediction DataFrame.")

    log_losses: List[float] = []
    brier_scores: List[float] = []
    tie_aware_top1s: List[float] = []
    fractional_top1s: List[float] = []

    for race_id, group in df.groupby(race_id_col, sort=False):
        y = group[target_col].to_numpy(dtype=np.int64)
        p = group[prob_col].to_numpy(dtype=np.float64)

        metrics = compute_single_race_metrics(y=y, p=p, eps=eps, atol=atol)
        log_losses.append(metrics["log_loss"])
        brier_scores.append(metrics["brier_score"])
        tie_aware_top1s.append(metrics["tie_aware_top1"])
        fractional_top1s.append(metrics["fractional_top1"])

    races_count = len(log_losses)
    return {
        "races": races_count,
        "mean_log_loss": float(np.mean(log_losses)),
        "mean_brier_score": float(np.mean(brier_scores)),
        "tie_aware_top1": float(np.mean(tie_aware_top1s)),
        "fractional_top1": float(np.mean(fractional_top1s)),
    }
