"""APEX — Counterfactual Strategy Dynamics and Tactical Regret (Phase 7.1 / EXP-0006-R2).

Evaluates alternative pit and tyre tactics on identical race seeds using
Common Random Numbers (CRN) with decoupled ExogenousScenario streams.
Measures empirical variance reduction, paired statistical significance, and tactical regret.
"""
import copy
from typing import Any, Callable, Dict, List, Optional, Tuple
import numpy as np
from pydantic import BaseModel, Field

from backend.simulation.engine import RaceSimulationEngine
from backend.simulation.scenario import ExogenousScenario, ScenarioGenerator
from backend.simulation.state import DriverState, DriverStatus, RaceState
from backend.simulation.strategy import BaseStrategyPolicy, FixedReferenceStrategy, OneStopStrategy, TwoStopStrategy


class StrategyMetrics(BaseModel):
    """Aggregate Monte Carlo metrics for a simulated strategy policy."""
    strategy_name: str
    expected_finishing_position: float
    median_finishing_position: float = 0.0
    position_std: float
    expected_pos_standard_error: float = 0.0
    win_probability: float
    win_standard_error: float = 0.0
    win_probability_ci_95: List[float]
    podium_probability: float
    podium_probability_ci_95: List[float]
    top5_probability: float
    top5_probability_ci_95: List[float]
    dnf_probability: float = 0.0
    dsq_probability: float = 0.0
    classified_rate: float = 1.0  # Proportion of runs finishing classified
    mean_race_time_seconds: float  # Mean accumulated race time for completed/classified race runs
    race_time_std_seconds: float  # Standard deviation for completed race runs
    mean_race_time_all_runs_seconds: float = 0.0  # Mean across all runs including early retirements
    race_time_all_runs_std_seconds: float = 0.0  # Std across all runs including early retirements
    mean_pit_stops: float
    mean_pit_transit_loss_seconds: float = 0.0
    mean_final_tyre_age_laps: float = 0.0
    probability_of_gaining_positions: float
    time_regret_vs_best_seconds: float  # In-sample regret relative to best evaluated alternative
    position_regret_vs_best: float  # In-sample position regret relative to best evaluated alternative
    finishing_position_distribution: Dict[int, float] = Field(default_factory=dict)
    tyre_usage: Dict[str, float] = Field(default_factory=dict)


class PairedStrategyComparison(BaseModel):
    """Detailed paired statistical contrast between two strategies under identical CRN scenarios."""
    strategy_a: str
    strategy_b: str
    mean_position_difference: float  # pos(A) - pos(B), negative means A finished higher up
    ci_pos_diff_95: List[float]
    mean_time_difference_seconds: float  # time(A) - time(B) on all runs (unconditional)
    ci_time_diff_95: List[float]
    mean_time_difference_all_runs_seconds: float = 0.0  # Explicit alias for unconditional paired time diff
    mean_time_difference_matched_finished_seconds: float = 0.0  # time(A) - time(B) strictly on matched runs where both finished
    ci_time_diff_matched_finished_95: List[float] = Field(default_factory=list)
    n_both_finished: int = 0
    n_at_least_one_retired: int = 0
    prob_a_finishes_ahead: float  # Total-runs basis: W_A / N
    prob_b_finishes_ahead: float  # Total-runs basis: W_B / N
    prob_tied: float  # Total-runs basis: T / N
    prob_a_beats_b_decisive: float = 0.0  # Decisive-runs basis: W_A / (W_A + W_B) excluding ties
    p_value_paired_test: float
    p_value_adjusted_holm_bonferroni: float = 1.0
    time_correlation: float
    variance_reduction_percent: float
    head_to_head_definition: str = (
        "prob_a_finishes_ahead = W_A / N (total runs); prob_a_beats_b_decisive = W_A / (W_A + W_B) (decisive runs). "
        "Classified finishers always rank ahead of DNFs; DNFs rank ahead of DSQs."
    )


class CounterfactualComparisonReport(BaseModel):
    """Comparative report evaluating multiple tactical options for a driver."""
    experiment_id: str = "EXP-0006-R2"
    hypothesis_id: str = "HYP-STRAT-001"
    race_id: str
    target_driver_id: str
    target_driver_name: str
    starting_grid: int
    n_simulations: int
    master_seed: int
    evaluated_strategies: List[StrategyMetrics]
    paired_comparisons: List[PairedStrategyComparison] = Field(default_factory=list)
    best_strategy_by_expected_position: str
    best_strategy_by_win_probability: str
    best_strategy_by_podium_probability: str = ""
    best_strategy_by_top5_probability: str = ""
    best_strategy_by_race_time: str
    best_strategy_by_lowest_variance: str = ""
    objective_rankings: Dict[str, List[str]] = Field(default_factory=dict)
    measured_mean_variance_reduction_percent: float = 0.0
    out_of_sample_regret_seconds: Dict[str, float] = Field(default_factory=dict)
    scientific_summary: str
    best_strategy_by_race_time: str
    measured_mean_variance_reduction_percent: float = 0.0
    out_of_sample_regret_seconds: Dict[str, float] = Field(default_factory=dict)
    scientific_summary: str


class CounterfactualEngine:
    """Runs paired Monte Carlo rollouts comparing strategy alternatives via Common Random Numbers (CRN)."""

    def __init__(self, engine: Optional[RaceSimulationEngine] = None):
        self.engine = engine or RaceSimulationEngine()

    def compare_strategies(
        self,
        base_race_state: RaceState,
        target_driver_id: str,
        strategies_to_test: Dict[str, BaseStrategyPolicy],
        default_opponent_strategy: Optional[BaseStrategyPolicy] = None,
        n_simulations: int = 100,
        master_seed: int = 42,
        compute_out_of_sample_validation: bool = False,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> CounterfactualComparisonReport:
        """
        Executes paired rollouts across all strategies using decoupled ExogenousScenario streams.
        """
        if default_opponent_strategy is None:
            default_opponent_strategy = OneStopStrategy(target_pit_lap=22)

        strat_names = list(strategies_to_test.keys())
        results_by_strat: Dict[str, List[Dict[str, Any]]] = {name: [] for name in strat_names}

        scenario_gen = ScenarioGenerator(master_seed=master_seed)
        driver_ids = list(base_race_state.drivers.keys())

        # Common Random Numbers loop over independent exogenous scenarios
        for run_idx in range(n_simulations):
            if progress_callback and (run_idx % 250 == 0 or run_idx == n_simulations - 1):
                progress_callback(run_idx + 1, n_simulations)

            scenario = scenario_gen.generate_scenario(
                run_index=run_idx,
                total_laps=base_race_state.total_laps,
                driver_ids=driver_ids,
            )

            for strat_name, strat_policy in strategies_to_test.items():
                race_copy = copy.deepcopy(base_race_state)

                policies: Dict[str, BaseStrategyPolicy] = {
                    d_id: (strat_policy if d_id == target_driver_id else default_opponent_strategy)
                    for d_id in race_copy.drivers.keys()
                }

                completed_race = self.engine.run_race(
                    race_state=race_copy,
                    strategies=policies,
                    scenario=scenario,
                )
                target_drv = completed_race.drivers[target_driver_id]

                mean_pit_loss = (
                    sum(p.total_pit_loss_seconds for p in target_drv.pit_stop_history)
                    if target_drv.pit_stop_history
                    else 0.0
                )

                results_by_strat[strat_name].append({
                    "position": target_drv.current_position if target_drv.current_position is not None else 21,
                    "classified_position": target_drv.classified_position,
                    "race_time": target_drv.accumulated_race_time,
                    "status": target_drv.status.value,
                    "is_finished": bool(target_drv.status == DriverStatus.FINISHED),
                    "pit_stops": target_drv.pit_stop_count,
                    "is_winner": bool(target_drv.status == DriverStatus.FINISHED and target_drv.classified_position == 1),
                    "is_podium": bool(target_drv.status == DriverStatus.FINISHED and target_drv.classified_position is not None and target_drv.classified_position <= 3),
                    "is_top5": bool(target_drv.status == DriverStatus.FINISHED and target_drv.classified_position is not None and target_drv.classified_position <= 5),
                    "is_dnf": bool(target_drv.status == DriverStatus.RETIRED),
                    "is_dsq": bool(target_drv.status == DriverStatus.DISQUALIFIED),
                    "gained_position": bool(target_drv.classified_position is not None and target_drv.classified_position < target_drv.starting_grid),
                    "pit_loss": mean_pit_loss,
                    "tyre_age": target_drv.current_tyre_age,
                    "compounds_used": [c.value for c in target_drv.compounds_used],
                })

        # Calculate summary metrics per strategy
        strat_metrics_list: List[StrategyMetrics] = []
        for name in strat_names:
            runs = results_by_strat[name]
            positions = np.array([r["position"] for r in runs], dtype=float)
            all_times = np.array([r["race_time"] for r in runs], dtype=float)
            finished_runs = [r for r in runs if r["is_finished"]]
            finished_times = np.array([r["race_time"] for r in finished_runs], dtype=float) if finished_runs else all_times

            pits = np.array([r["pit_stops"] for r in runs], dtype=float)
            wins = np.array([1.0 if r["is_winner"] else 0.0 for r in runs], dtype=float)
            podiums = np.array([1.0 if r["is_podium"] else 0.0 for r in runs], dtype=float)
            top5s = np.array([1.0 if r["is_top5"] else 0.0 for r in runs], dtype=float)
            dnfs = np.array([1.0 if r["is_dnf"] else 0.0 for r in runs], dtype=float)
            dsqs = np.array([1.0 if r["is_dsq"] else 0.0 for r in runs], dtype=float)
            gained = np.array([1.0 if r["gained_position"] else 0.0 for r in runs], dtype=float)
            pit_losses = np.array([r["pit_loss"] for r in runs], dtype=float)
            tyre_ages = np.array([r["tyre_age"] for r in runs], dtype=float)

            pos_mean = float(np.mean(positions))
            pos_median = float(np.median(positions))
            pos_std = float(np.std(positions, ddof=1)) if len(positions) > 1 else 0.0
            pos_se = float(pos_std / np.sqrt(len(positions))) if len(positions) > 0 else 0.0

            win_p = float(np.mean(wins))
            win_se = float(np.sqrt(max(0.0, win_p * (1.0 - win_p)) / len(wins))) if len(wins) > 0 else 0.0

            win_ci = self._bootstrap_ci(wins)
            podium_ci = self._bootstrap_ci(podiums)
            top5_ci = self._bootstrap_ci(top5s)

            # Finishing position frequency distribution
            unique_pos, counts = np.unique(positions.astype(int), return_counts=True)
            dist_dict = {int(p): round(float(c / len(positions)), 4) for p, c in zip(unique_pos, counts)}

            # Compound usage frequency
            compounds_flat = [c for r in runs for c in r.get("compounds_used", [])]
            unique_compounds = set(compounds_flat)
            tyre_usage_dict = {
                c: round(float(compounds_flat.count(c) / len(runs)), 3) for c in sorted(unique_compounds)
            }

            # Finished race times (true full-distance completed runs)
            mean_finished_time = float(np.mean(finished_times)) if len(finished_times) > 0 else float(np.mean(all_times))
            std_finished_time = float(np.std(finished_times, ddof=1)) if len(finished_times) > 1 else 0.0
            mean_all_time = float(np.mean(all_times))
            std_all_time = float(np.std(all_times, ddof=1)) if len(all_times) > 1 else 0.0
            classified_rate = float(len(finished_runs) / len(runs)) if len(runs) > 0 else 0.0

            strat_metrics_list.append(
                StrategyMetrics(
                    strategy_name=name,
                    expected_finishing_position=round(pos_mean, 3),
                    median_finishing_position=round(pos_median, 1),
                    position_std=round(pos_std, 3),
                    expected_pos_standard_error=round(pos_se, 4),
                    win_probability=round(win_p, 4),
                    win_standard_error=round(win_se, 4),
                    win_probability_ci_95=win_ci,
                    podium_probability=round(float(np.mean(podiums)), 4),
                    podium_probability_ci_95=podium_ci,
                    top5_probability=round(float(np.mean(top5s)), 4),
                    top5_probability_ci_95=top5_ci,
                    dnf_probability=round(float(np.mean(dnfs)), 4),
                    dsq_probability=round(float(np.mean(dsqs)), 4),
                    classified_rate=round(classified_rate, 4),
                    mean_race_time_seconds=round(mean_finished_time, 3),
                    race_time_std_seconds=round(std_finished_time, 3),
                    mean_race_time_all_runs_seconds=round(mean_all_time, 3),
                    race_time_all_runs_std_seconds=round(std_all_time, 3),
                    mean_pit_stops=round(float(np.mean(pits)), 2),
                    mean_pit_transit_loss_seconds=round(float(np.mean(pit_losses)), 2),
                    mean_final_tyre_age_laps=round(float(np.mean(tyre_ages)), 1),
                    probability_of_gaining_positions=round(float(np.mean(gained)), 4),
                    time_regret_vs_best_seconds=0.0,
                    position_regret_vs_best=0.0,
                    finishing_position_distribution=dist_dict,
                    tyre_usage=tyre_usage_dict,
                )
            )

        # In-sample relative regret calculation
        best_time = min(m.mean_race_time_seconds for m in strat_metrics_list)
        best_pos = min(m.expected_finishing_position for m in strat_metrics_list)
        for m in strat_metrics_list:
            m.time_regret_vs_best_seconds = round(max(0.0, m.mean_race_time_seconds - best_time), 3)
            m.position_regret_vs_best = round(max(0.0, m.expected_finishing_position - best_pos), 3)

        # Compute exhaustive paired comparisons across strategy combinations
        paired_comparisons: List[PairedStrategyComparison] = []
        vr_list: List[float] = []

        for i in range(len(strat_names)):
            for j in range(i + 1, len(strat_names)):
                name_a = strat_names[i]
                name_b = strat_names[j]

                runs_a = results_by_strat[name_a]
                runs_b = results_by_strat[name_b]

                pos_a = np.array([r["position"] for r in runs_a])
                pos_b = np.array([r["position"] for r in runs_b])
                time_a = np.array([r["race_time"] for r in runs_a])
                time_b = np.array([r["race_time"] for r in runs_b])

                diff_pos = pos_a - pos_b
                diff_time = time_a - time_b

                mean_diff_pos = float(np.mean(diff_pos))
                ci_pos = self._bootstrap_ci(diff_pos)

                mean_diff_time = float(np.mean(diff_time))
                ci_time = self._bootstrap_ci(diff_time)

                # Matched completed runs where both policies finish
                matched_idx = [k for k in range(len(runs_a)) if runs_a[k]["is_finished"] and runs_b[k]["is_finished"]]
                n_both_fin = len(matched_idx)
                n_one_retired = len(runs_a) - n_both_fin
                if n_both_fin > 0:
                    time_a_matched = np.array([runs_a[k]["race_time"] for k in matched_idx])
                    time_b_matched = np.array([runs_b[k]["race_time"] for k in matched_idx])
                    diff_time_matched = time_a_matched - time_b_matched
                    mean_diff_time_matched = float(np.mean(diff_time_matched))
                    ci_time_matched = self._bootstrap_ci(diff_time_matched)
                else:
                    mean_diff_time_matched = mean_diff_time
                    ci_time_matched = ci_time

                p_a_ahead = float(np.mean(pos_a < pos_b))
                p_b_ahead = float(np.mean(pos_b < pos_a))
                p_tied = float(np.mean(pos_a == pos_b))
                decisive_sum = p_a_ahead + p_b_ahead
                p_a_decisive = float(p_a_ahead / decisive_sum) if decisive_sum > 1e-6 else 0.50

                # Correlation & Variance reduction
                std_a = np.std(time_a, ddof=1) if len(time_a) > 1 else 1.0
                std_b = np.std(time_b, ddof=1) if len(time_b) > 1 else 1.0
                if std_a > 1e-6 and std_b > 1e-6:
                    corr = float(np.corrcoef(time_a, time_b)[0, 1])
                else:
                    corr = 0.0

                var_crn = float(np.var(diff_time, ddof=1)) if len(diff_time) > 1 else 0.0
                var_indep = float(std_a**2 + std_b**2)
                vr_pct = max(0.0, round((1.0 - (var_crn / var_indep)) * 100.0, 2)) if var_indep > 1e-6 else 0.0
                vr_list.append(vr_pct)

                # Paired Wilcoxon or t-test equivalent p-value
                se_diff = np.std(diff_pos, ddof=1) / np.sqrt(len(diff_pos)) if len(diff_pos) > 1 else 1.0
                z_score = abs(mean_diff_pos) / max(1e-6, se_diff)
                p_val = float(2.0 * (1.0 - self._approx_standard_normal_cdf(z_score)))

                paired_comparisons.append(
                    PairedStrategyComparison(
                        strategy_a=name_a,
                        strategy_b=name_b,
                        mean_position_difference=round(mean_diff_pos, 3),
                        ci_pos_diff_95=ci_pos,
                        mean_time_difference_seconds=round(mean_diff_time, 3),
                        ci_time_diff_95=ci_time,
                        mean_time_difference_all_runs_seconds=round(mean_diff_time, 3),
                        mean_time_difference_matched_finished_seconds=round(mean_diff_time_matched, 3),
                        ci_time_diff_matched_finished_95=ci_time_matched,
                        n_both_finished=n_both_fin,
                        n_at_least_one_retired=n_one_retired,
                        prob_a_finishes_ahead=round(p_a_ahead, 4),
                        prob_b_finishes_ahead=round(p_b_ahead, 4),
                        prob_tied=round(p_tied, 4),
                        prob_a_beats_b_decisive=round(p_a_decisive, 4),
                        p_value_paired_test=round(p_val, 5),
                        p_value_adjusted_holm_bonferroni=1.0,
                        time_correlation=round(corr, 4),
                        variance_reduction_percent=vr_pct,
                    )
                )

        # Multiple-comparison adjustment: Holm-Bonferroni correction across all paired tests
        num_pairs = len(paired_comparisons)
        if num_pairs > 0:
            sorted_indices = sorted(range(num_pairs), key=lambda idx: paired_comparisons[idx].p_value_paired_test)
            cum_max = 0.0
            for rank_i, orig_idx in enumerate(sorted_indices):
                multiplier = num_pairs - rank_i
                raw_p = paired_comparisons[orig_idx].p_value_paired_test
                adj_p = min(1.0, max(cum_max, raw_p * multiplier))
                cum_max = adj_p
                paired_comparisons[orig_idx].p_value_adjusted_holm_bonferroni = round(adj_p, 5)

        mean_vr = round(float(np.mean(vr_list)), 2) if vr_list else 0.0

        best_by_pos = min(strat_metrics_list, key=lambda m: m.expected_finishing_position).strategy_name
        best_by_win = max(strat_metrics_list, key=lambda m: m.win_probability).strategy_name
        best_by_podium = max(strat_metrics_list, key=lambda m: m.podium_probability).strategy_name
        best_by_top5 = max(strat_metrics_list, key=lambda m: m.top5_probability).strategy_name
        best_by_time = min(strat_metrics_list, key=lambda m: m.mean_race_time_seconds).strategy_name
        best_by_variance = min(strat_metrics_list, key=lambda m: m.position_std).strategy_name

        # Objective rankings
        rankings = {
            "maximise_win_probability": [
                m.strategy_name for m in sorted(strat_metrics_list, key=lambda m: -m.win_probability)
            ],
            "maximise_podium_probability": [
                m.strategy_name for m in sorted(strat_metrics_list, key=lambda m: -m.podium_probability)
            ],
            "maximise_top5_probability": [
                m.strategy_name for m in sorted(strat_metrics_list, key=lambda m: -m.top5_probability)
            ],
            "minimise_expected_position": [
                m.strategy_name for m in sorted(strat_metrics_list, key=lambda m: m.expected_finishing_position)
            ],
            "minimise_race_time": [
                m.strategy_name for m in sorted(strat_metrics_list, key=lambda m: m.mean_race_time_seconds)
            ],
            "minimise_outcome_variance": [
                m.strategy_name for m in sorted(strat_metrics_list, key=lambda m: m.position_std)
            ],
        }

        # Out-of-sample evaluation if requested
        oos_regrets: Dict[str, float] = {}
        if compute_out_of_sample_validation:
            oos_gen = ScenarioGenerator(master_seed=master_seed + 99991)
            oos_results = {s: [] for s in strat_names}
            for oos_idx in range(min(50, n_simulations)):
                oos_scen = oos_gen.generate_scenario(oos_idx, base_race_state.total_laps, driver_ids)
                for s_name, s_pol in strategies_to_test.items():
                    r_copy = copy.deepcopy(base_race_state)
                    pols = {d: (s_pol if d == target_driver_id else default_opponent_strategy) for d in r_copy.drivers}
                    done_r = self.engine.run_race(r_copy, pols, scenario=oos_scen)
                    oos_results[s_name].append(done_r.drivers[target_driver_id].accumulated_race_time)
            min_oos_time = min(float(np.mean(t)) for t in oos_results.values())
            oos_regrets = {
                s: round(float(np.mean(t)) - min_oos_time, 3) for s, t in oos_results.items()
            }

        target_name = base_race_state.drivers[target_driver_id].driver_name
        summary_text = (
            f"Evaluated {len(strat_names)} strategies over {n_simulations} paired rollouts with decoupled Common Random Numbers. "
            f"CRN achieved an average measured variance reduction of {mean_vr:.1f}% across paired strategy differences. "
            f"Strategy '{best_by_pos}' achieved the lowest expected finishing position (P{min(m.expected_finishing_position for m in strat_metrics_list):.2f}). "
            f"Under stochastic neutralisations, adaptive policies exploit the ~10s pit transit discount, "
            f"though optimality is contingent on circuit pit loss and tyre degradation cliff parameters."
        )

        return CounterfactualComparisonReport(
            experiment_id="EXP-0006-R2",
            hypothesis_id="HYP-STRAT-001",
            race_id=base_race_state.race_id,
            target_driver_id=target_driver_id,
            target_driver_name=target_name,
            starting_grid=base_race_state.drivers[target_driver_id].starting_grid,
            n_simulations=n_simulations,
            master_seed=master_seed,
            evaluated_strategies=strat_metrics_list,
            paired_comparisons=paired_comparisons,
            best_strategy_by_expected_position=best_by_pos,
            best_strategy_by_win_probability=best_by_win,
            best_strategy_by_podium_probability=best_by_podium,
            best_strategy_by_top5_probability=best_by_top5,
            best_strategy_by_race_time=best_by_time,
            best_strategy_by_lowest_variance=best_by_variance,
            objective_rankings=rankings,
            measured_mean_variance_reduction_percent=mean_vr,
            out_of_sample_regret_seconds=oos_regrets,
            scientific_summary=summary_text,
        )

    @staticmethod
    def _bootstrap_ci(data: np.ndarray, n_boot: int = 500, ci_level: float = 0.95) -> List[float]:
        """Calculates bootstrap percentile confidence interval."""
        if len(data) == 0:
            return [0.0, 0.0]
        if len(data) == 1:
            val = float(data[0])
            return [val, val]
        rng = np.random.default_rng(1337)
        boot_means = np.empty(n_boot)
        n = len(data)
        for i in range(n_boot):
            sample = rng.choice(data, size=n, replace=True)
            boot_means[i] = np.mean(sample)
        alpha = (1.0 - ci_level) / 2.0
        lower = float(np.percentile(boot_means, alpha * 100.0))
        upper = float(np.percentile(boot_means, (1.0 - alpha) * 100.0))
        return [round(lower, 4), round(upper, 4)]

    @staticmethod
    def _approx_standard_normal_cdf(z: float) -> float:
        """Error function approximation for normal CDF."""
        import math
        return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))
