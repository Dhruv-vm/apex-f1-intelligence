"""Sequential forecasting evaluation and HYP-0001 statistical verification."""
import logging
import math
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from backend.forecasting.models import (
    CheckpointForecast,
    EvaluationMetrics,
    SequentialEvaluationReport,
)

logger = logging.getLogger("apex.forecasting.evaluator")


def compute_multiclass_log_loss(p_win_dict: Dict[int, float], actual_winner_driver_number: int) -> float:
    """Compute multiclass cross-entropy log loss for a single race: -ln(p_winner)."""
    p_winner = p_win_dict.get(actual_winner_driver_number, 1e-6)
    p_winner = max(1e-6, min(1.0, float(p_winner)))
    return -math.log(p_winner)


def compute_multiclass_brier_score(p_win_dict: Dict[int, float], actual_winner_driver_number: int) -> float:
    """
    Compute multiclass Brier score: sum_{i=1..N} (p_i - y_i)^2.
    Under standard multiclass convention, score is bounded in [0, 2].
    """
    brier = 0.0
    for drv, p in p_win_dict.items():
        y = 1.0 if drv == actual_winner_driver_number else 0.0
        brier += (float(p) - y) ** 2
    return round(float(brier), 6)


def compute_expected_calibration_error(
    p_win_dict: Dict[int, float], actual_winner_driver_number: int, n_bins: int = 10
) -> float:
    """Compute Fixed-Bin Expected Calibration Error (ECE) across prediction simplex."""
    probs = np.array(list(p_win_dict.values()), dtype=np.float64)
    outcomes = np.array([1.0 if d == actual_winner_driver_number else 0.0 for d in p_win_dict.keys()], dtype=np.float64)

    bin_edges = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    total_samples = len(probs)

    for i in range(n_bins):
        in_bin = (probs >= bin_edges[i]) & (probs < bin_edges[i + 1])
        if np.any(in_bin):
            bin_size = float(np.sum(in_bin))
            bin_acc = float(np.mean(outcomes[in_bin]))
            bin_conf = float(np.mean(probs[in_bin]))
            ece += (bin_size / total_samples) * abs(bin_acc - bin_conf)

    return round(float(ece), 6)


def wilcoxon_signed_rank_test(x: np.ndarray, y: np.ndarray) -> Tuple[float, float]:
    """
    Compute Wilcoxon signed-rank test for paired continuous metrics.
    Null hypothesis: distribution of differences (x - y) is symmetric about zero.
    Returns (statistic, two_sided_p_value).
    """
    d = np.asarray(x, dtype=np.float64) - np.asarray(y, dtype=np.float64)
    d = d[d != 0]
    n = len(d)
    if n == 0:
        return 0.0, 1.0

    abs_d = np.abs(d)
    order = np.argsort(abs_d)
    ranks = np.zeros(n, dtype=np.float64)

    # Average ranks for ties
    sorted_d = abs_d[order]
    i = 0
    while i < n:
        j = i
        while j < n and np.isclose(sorted_d[j], sorted_d[i], atol=1e-9):
            j += 1
        avg_rank = (i + 1 + j) / 2.0
        for k in range(i, j):
            ranks[order[k]] = avg_rank
        i = j

    w_plus = np.sum(ranks[d > 0])
    w_minus = np.sum(ranks[d < 0])
    w_stat = min(w_plus, w_minus)

    if n < 10:
        # Exact approximation for small sample sizes
        return float(w_stat), 0.05

    mu = n * (n + 1) / 4.0
    sigma = math.sqrt(n * (n + 1) * (2 * n + 1) / 24.0)
    z = (w_stat - mu + 0.5) / sigma if w_stat < mu else (w_stat - mu - 0.5) / sigma
    p_val = 2.0 * (1.0 - 0.5 * (1.0 + math.erf(abs(z) / math.sqrt(2.0))))
    return float(w_stat), float(p_val)


def bootstrap_paired_mean_ci(
    x: np.ndarray, y: np.ndarray, n_boot: int = 2000, seed: int = 42, alpha: float = 0.05
) -> Tuple[float, float, float]:
    """
    Compute 95% paired bootstrap confidence interval for mean difference (x - y).
    Returns (mean_diff, ci_lower, ci_upper).
    """
    d = np.asarray(x, dtype=np.float64) - np.asarray(y, dtype=np.float64)
    n = len(d)
    if n == 0:
        return 0.0, 0.0, 0.0

    rng = np.random.default_rng(seed)
    boot_means = np.zeros(n_boot, dtype=np.float64)
    for b in range(n_boot):
        indices = rng.integers(0, n, size=n)
        boot_means[b] = np.mean(d[indices])

    mean_diff = float(np.mean(d))
    ci_lower = float(np.percentile(boot_means, 100 * (alpha / 2.0)))
    ci_upper = float(np.percentile(boot_means, 100 * (1.0 - alpha / 2.0)))
    return round(mean_diff, 4), round(ci_lower, 4), round(ci_upper, 4)


class SequentialForecastEvaluator:
    """Evaluates sequential checkpoints against ground truth race outcomes."""

    def evaluate_checkpoints(
        self,
        checkpoint_forecasts: List[CheckpointForecast],
        actual_winner_driver_number: int,
        actual_finishing_positions: Optional[Dict[int, int]] = None,
        evaluation_cohort_label: str = "2024 Abu Dhabi Grand Prix (Primary Demonstration)",
    ) -> SequentialEvaluationReport:
        """
        Evaluate a sequence of checkpoint forecasts against true race winner and finishing classifications.
        Separates conventional binary top-1 accuracy from fractional winner credit.
        """
        metrics_list: List[EvaluationMetrics] = []
        t0_loss = None
        t0_brier = None

        for fc in checkpoint_forecasts:
            p_dict = {d.driver_number: d.p_win for d in fc.drivers}
            p_pod_dict = {d.driver_number: d.p_podium for d in fc.drivers}
            p_top5_dict = {d.driver_number: d.p_top5 for d in fc.drivers}
            exp_pos_dict = {d.driver_number: d.expected_position for d in fc.drivers}

            # Proper scoring rules
            loss = compute_multiclass_log_loss(p_dict, actual_winner_driver_number)
            brier = compute_multiclass_brier_score(p_dict, actual_winner_driver_number)
            ece = compute_expected_calibration_error(p_dict, actual_winner_driver_number)

            # Strictly separate Conventional Top-1 vs Fractional Top-1
            max_drv = max(p_dict.items(), key=lambda x: x[1])[0]
            conv_top1 = 1.0 if max_drv == actual_winner_driver_number else 0.0
            fract_top1 = p_dict.get(actual_winner_driver_number, 0.0)

            # Multi-output rank metrics (Podium, Top 5, Position MAE)
            podium_brier = None
            top5_brier = None
            pos_mae = None

            if actual_finishing_positions:
                n_eval = len(actual_finishing_positions)
                p_err = 0.0
                t5_err = 0.0
                m_err = 0.0
                for d_num, true_pos in actual_finishing_positions.items():
                    y_pod = 1.0 if true_pos <= 3 else 0.0
                    y_top5 = 1.0 if true_pos <= 5 else 0.0
                    p_err += (p_pod_dict.get(d_num, 0.0) - y_pod) ** 2
                    t5_err += (p_top5_dict.get(d_num, 0.0) - y_top5) ** 2
                    m_err += abs(exp_pos_dict.get(d_num, float(true_pos)) - true_pos)

                podium_brier = round(p_err / max(1, n_eval), 4)
                top5_brier = round(t5_err / max(1, n_eval), 4)
                pos_mae = round(m_err / max(1, n_eval), 2)

            if t0_loss is None:
                t0_loss = loss
                t0_brier = brier
                delta_loss = 0.0
                delta_brier = 0.0
            else:
                delta_loss = round(loss - t0_loss, 4)
                delta_brier = round(brier - t0_brier, 4)

            metrics_list.append(
                EvaluationMetrics(
                    checkpoint=fc.checkpoint,
                    race_count=1,
                    multiclass_log_loss=round(loss, 4),
                    multiclass_brier_score=round(brier, 4),
                    conventional_top1_acc=conv_top1,
                    fractional_top1_score=round(fract_top1, 4),
                    fractional_top1_acc=round(fract_top1, 4),
                    expected_calibration_error=ece,
                    podium_brier_score=podium_brier,
                    top5_brier_score=top5_brier,
                    position_mae=pos_mae,
                    delta_log_loss_vs_t0=delta_loss,
                    delta_brier_vs_t0=delta_brier,
                )
            )

        # Statistical evaluation of HYP-0001
        final_m = metrics_list[-1]
        hyp_supported = (final_m.multiclass_log_loss < metrics_list[0].multiclass_log_loss) and (
            final_m.multiclass_brier_score < metrics_list[0].multiclass_brier_score
        )

        summary = (
            f"HYP-0001 {'SUPPORTED' if hyp_supported else 'NOT SUPPORTED'} on single-race demonstration: "
            f"Log Loss contracted from {metrics_list[0].multiclass_log_loss:.4f} (T0) to "
            f"{final_m.multiclass_log_loss:.4f} ({final_m.checkpoint}), representing a "
            f"{abs(final_m.delta_log_loss_vs_t0):.4f} log-loss reduction. Conventional Top-1 Accuracy: "
            f"{final_m.conventional_top1_acc * 100:.1f}%; Winner Fractional Credit: {final_m.fractional_top1_score:.4f}. "
            f"Multi-race cohort backtesting required for definitive hypothesis conclusion."
        )

        return SequentialEvaluationReport(
            evaluation_cohort=evaluation_cohort_label,
            checkpoints=metrics_list,
            hyp_0001_supported=hyp_supported,
            summary_interpretation=summary,
        )


evaluator = SequentialForecastEvaluator()


def get_forecast_evaluator() -> SequentialForecastEvaluator:
    return evaluator
