"""APEX — Monte Carlo Simulation Runner and Convergence Diagnostics (Phase 7.1 / EXP-0006-R2).

Executes large-scale stochastic rollouts (100 to 10,000 iterations), checks distributional
convergence, and estimates win, podium, and points confidence bounds with decoupled scenarios.
"""
import copy
from typing import Any, Callable, Dict, List, Optional
import numpy as np
from pydantic import BaseModel, Field

from backend.simulation.engine import RaceSimulationEngine
from backend.simulation.scenario import ExogenousScenario, ScenarioGenerator
from backend.simulation.state import DriverState, RaceState
from backend.simulation.strategy import BaseStrategyPolicy, OneStopStrategy


class CandidateSimulationSummary(BaseModel):
    """Monte Carlo finishing distribution for an individual driver."""
    driver_id: str
    driver_name: str
    constructor_id: str
    starting_grid: int
    expected_finish_position: float
    finish_position_std: float
    expected_pos_standard_error: float = 0.0
    win_probability: float
    win_standard_error: float = 0.0
    win_probability_ci_95: List[float]
    podium_probability: float
    podium_probability_ci_95: List[float]
    top5_probability: float
    top5_probability_ci_95: List[float]
    dnf_probability: float
    position_distribution: Dict[int, float]  # finish position -> probability
    mean_race_time_seconds: float


class ConvergenceCheckpoint(BaseModel):
    """Distribution snapshot at a specific iteration count to evaluate convergence."""
    iteration_count: int
    leader_win_probability: float
    leader_win_standard_error: float = 0.0
    max_position_change: float


class SimulationRunResult(BaseModel):
    """Complete serialized outcome of a Monte Carlo race simulation run."""
    run_id: str
    race_id: str
    circuit_name: str
    season: int
    total_laps: int
    n_iterations: int
    master_seed: int
    candidates: List[CandidateSimulationSummary]
    convergence_history: List[ConvergenceCheckpoint]
    most_likely_winner: str
    winner_win_probability: float
    simulated_race_control_events_summary: Dict[str, int]


class MonteCarloSimulator:
    """Manages repeatable batch rollouts of the APEX race engine."""

    def __init__(self, engine: Optional[RaceSimulationEngine] = None):
        self.engine = engine or RaceSimulationEngine()

    def run_simulations(
        self,
        base_race_state: RaceState,
        strategies: Optional[Dict[str, BaseStrategyPolicy]] = None,
        n_iterations: int = 100,
        master_seed: int = 42,
        run_id: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> SimulationRunResult:
        """
        Runs n_iterations stochastic race rollouts and collects empirical distributions.
        Uses decoupled ExogenousScenario generation to ensure environmental consistency.
        """
        if strategies is None:
            strategies = {
                d_id: OneStopStrategy(target_pit_lap=int(base_race_state.total_laps * 0.40))
                for d_id in base_race_state.drivers.keys()
            }

        driver_ids = list(base_race_state.drivers.keys())
        driver_positions: Dict[str, List[int]] = {d: [] for d in driver_ids}
        driver_times: Dict[str, List[float]] = {d: [] for d in driver_ids}
        driver_dnfs: Dict[str, int] = {d: 0 for d in driver_ids}

        event_counts: Dict[str, int] = {"SAFETY_CAR": 0, "VSC": 0, "RETIREMENT": 0, "OVERTAKE": 0}

        convergence_checkpoints: List[ConvergenceCheckpoint] = []
        check_intervals = [50, 100, 250, 500, 1000, 2500, 5000, 10000]
        check_intervals = [k for k in check_intervals if k <= n_iterations]
        if n_iterations not in check_intervals:
            check_intervals.append(n_iterations)

        last_mean_positions: Dict[str, float] = {}
        scenario_gen = ScenarioGenerator(master_seed=master_seed)

        for i in range(1, n_iterations + 1):
            scenario = scenario_gen.generate_scenario(
                run_index=i,
                total_laps=base_race_state.total_laps,
                driver_ids=driver_ids,
            )
            race_copy = copy.deepcopy(base_race_state)

            completed = self.engine.run_race(race_copy, strategies, scenario=scenario)

            # Record event counts
            for ev in completed.events_log:
                if ev.event_type in event_counts:
                    event_counts[ev.event_type] += 1

            for d_id in driver_ids:
                drv = completed.drivers[d_id]
                pos_val = float(drv.current_position) if drv.current_position is not None else float(len(driver_ids) + 1)
                driver_positions[d_id].append(pos_val)
                driver_times[d_id].append(drv.accumulated_race_time)
                if drv.status.value != "FINISHED":
                    driver_dnfs[d_id] += 1

            # Convergence monitoring at checkpoints
            if i in check_intervals:
                current_means = {
                    d: float(np.mean(driver_positions[d][:i])) for d in driver_ids
                }
                max_change = 0.0
                if last_mean_positions:
                    max_change = max(abs(current_means[d] - last_mean_positions[d]) for d in driver_ids)
                last_mean_positions = current_means

                win_rates = {
                    d: float(np.mean([1.0 if p == 1 else 0.0 for p in driver_positions[d][:i]]))
                    for d in driver_ids
                }
                top_d = max(win_rates.items(), key=lambda x: x[1])
                p_win = top_d[1]
                se_win = float(np.sqrt(max(0.0, p_win * (1.0 - p_win)) / i))

                convergence_checkpoints.append(
                    ConvergenceCheckpoint(
                        iteration_count=i,
                        leader_win_probability=round(p_win, 4),
                        leader_win_standard_error=round(se_win, 4),
                        max_position_change=round(max_change, 4),
                    )
                )

            if progress_callback is not None and (i % 25 == 0 or i == n_iterations):
                progress_callback(i, n_iterations)

        # Aggregate candidate summaries
        candidate_summaries: List[CandidateSimulationSummary] = []
        for d_id in driver_ids:
            drv_base = base_race_state.drivers[d_id]
            pos_arr = np.array(driver_positions[d_id], dtype=float)
            time_arr = np.array(driver_times[d_id], dtype=float)

            wins = (pos_arr == 1.0).astype(float)
            podiums = (pos_arr <= 3.0).astype(float)
            top5s = (pos_arr <= 5.0).astype(float)

            pos_mean = float(np.mean(pos_arr))
            pos_std = float(np.std(pos_arr, ddof=1)) if len(pos_arr) > 1 else 0.0
            pos_se = float(pos_std / np.sqrt(len(pos_arr))) if len(pos_arr) > 0 else 0.0

            win_p = float(np.mean(wins))
            win_se = float(np.sqrt(max(0.0, win_p * (1.0 - win_p)) / len(wins))) if len(wins) > 0 else 0.0

            pos_dist: Dict[int, float] = {}
            for p in range(1, len(driver_ids) + 1):
                pos_dist[p] = round(float(np.mean(pos_arr == p)), 4)

            candidate_summaries.append(
                CandidateSimulationSummary(
                    driver_id=d_id,
                    driver_name=drv_base.driver_name,
                    constructor_id=drv_base.constructor_id,
                    starting_grid=drv_base.starting_grid,
                    expected_finish_position=round(pos_mean, 2),
                    finish_position_std=round(pos_std, 2),
                    expected_pos_standard_error=round(pos_se, 4),
                    win_probability=round(win_p, 4),
                    win_standard_error=round(win_se, 4),
                    win_probability_ci_95=self._bootstrap_ci(wins),
                    podium_probability=round(float(np.mean(podiums)), 4),
                    podium_probability_ci_95=self._bootstrap_ci(podiums),
                    top5_probability=round(float(np.mean(top5s)), 4),
                    top5_probability_ci_95=self._bootstrap_ci(top5s),
                    dnf_probability=round(float(driver_dnfs[d_id] / n_iterations), 4),
                    position_distribution=pos_dist,
                    mean_race_time_seconds=round(float(np.mean(time_arr)), 2),
                )
            )

        candidate_summaries.sort(key=lambda c: c.expected_finish_position)
        winner_cand = max(candidate_summaries, key=lambda c: c.win_probability)

        return SimulationRunResult(
            run_id=run_id or f"sim_{base_race_state.race_id}_{n_iterations}iter",
            race_id=base_race_state.race_id,
            circuit_name=base_race_state.circuit.circuit_name,
            season=base_race_state.season,
            total_laps=base_race_state.total_laps,
            n_iterations=n_iterations,
            master_seed=master_seed,
            candidates=candidate_summaries,
            convergence_history=convergence_checkpoints,
            most_likely_winner=winner_cand.driver_name,
            winner_win_probability=winner_cand.win_probability,
            simulated_race_control_events_summary=event_counts,
        )

    @staticmethod
    def _bootstrap_ci(data: np.ndarray, n_boot: int = 500) -> List[float]:
        """Calculates 95% bootstrap confidence interval."""
        if len(data) == 0:
            return [0.0, 0.0]
        n = len(data)
        rng = np.random.default_rng(9999)
        boot_means = [
            float(np.mean(data[rng.integers(0, n, size=n)]))
            for _ in range(n_boot)
        ]
        return [round(float(np.percentile(boot_means, 2.5)), 4), round(float(np.percentile(boot_means, 97.5)), 4)]
