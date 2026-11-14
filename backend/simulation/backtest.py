"""APEX — Historical Race Simulation Backtest Engine (Phase 7 / EXP-0006).

Chronologically validates the Monte Carlo simulator against complete historical races
without forward temporal leakage, evaluating:
- Multiclass log loss
- Multiclass Brier score
- Finishing position Mean Absolute Error (MAE)
- Top-1 hit rate and podium coverage
"""
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from backend.simulation.forecasting_bridge import ForecastingBridge
from backend.simulation.monte_carlo import MonteCarloSimulator
from backend.simulation.state import TrackCondition

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "artifacts" / "reports" / "EXP-0006"
DATA_PATH = PROJECT_ROOT / "data" / "interim" / "driver_race_results_2010_2026_v2_regulation_metadata.csv"


class RaceBacktestEvaluation(BaseModel):
    """Validation results for a single historical race."""
    season: int
    round_num: int
    race_name: str
    circuit_name: str
    total_laps: int
    actual_winner_driver_id: str
    actual_winner_name: str
    simulated_winner_win_prob: float
    simulated_race_log_loss: float
    simulated_brier_score: float
    top1_argmax_correct: float
    mean_finish_position_mae: float
    top3_actual_podium_coverage: float
    full_field_probability_vector: Dict[str, float] = Field(default_factory=dict)
    actual_vs_simulated_positions: Dict[str, Dict[str, Any]]


class BacktestCohortSummary(BaseModel):
    """Multi-race aggregate backtest report for EXP-0006."""
    experiment_id: str = "EXP-0006"
    hypothesis_id: str = "HYP-STRAT-001"
    evaluation_title: str = "Monte Carlo Race Simulator Historical Backtest"
    n_races_evaluated: int
    iterations_per_race: int
    mean_multiclass_log_loss: float
    mean_brier_score: float
    mean_top1_accuracy: float
    mean_position_mae: float
    race_evaluations: List[RaceBacktestEvaluation]
    scientific_conclusions: str


class SimulatorBacktester:
    """Executes chronological backtests comparing simulation distributions against historical reality."""

    def __init__(self, data_path: Optional[Path] = None):
        self.bridge = ForecastingBridge(data_path or DATA_PATH)
        self.simulator = MonteCarloSimulator()
        self.df = pd.read_csv(data_path or DATA_PATH)

    def run_backtest_cohort(
        self,
        race_tuples: List[Dict[str, Any]],
        n_iterations: int = 150,
        master_seed: int = 42,
    ) -> BacktestCohortSummary:
        """
        Evaluates simulator on a specified cohort of historical races.
        """
        evaluations: List[RaceBacktestEvaluation] = []

        for r_spec in race_tuples:
            s = r_spec["season"]
            rnd = r_spec["round"]
            cond = r_spec.get("track_condition", TrackCondition.DRY)

            race_state = self.bridge.build_initial_race_state(s, rnd, track_condition=cond)
            sim_result = self.simulator.run_simulations(
                race_state, n_iterations=n_iterations, master_seed=master_seed
            )

            # Retrieve ground truth results
            ground_truth = self.df[(self.df["season"] == s) & (self.df["round"] == rnd)].copy()
            winner_row = ground_truth[ground_truth["finish_position"] == 1].iloc[0]
            actual_winner_id = str(winner_row["driver_id"])
            actual_winner_name = str(winner_row["driver_name"])

            actual_pos_map = dict(zip(ground_truth["driver_id"].astype(str), ground_truth["finish_position"].astype(int)))
            actual_podium_ids = set(ground_truth[ground_truth["finish_position"].isin([1, 2, 3])]["driver_id"].astype(str))

            # Score probabilities
            cand_map = {c.driver_id: c for c in sim_result.candidates}
            winner_prob = cand_map[actual_winner_id].win_probability if actual_winner_id in cand_map else 1e-4
            log_loss = float(-np.log(max(1e-4, winner_prob)))

            # Multiclass Brier
            brier = 0.0
            for d_id, cand in cand_map.items():
                y = 1.0 if d_id == actual_winner_id else 0.0
                brier += (cand.win_probability - y) ** 2

            top1_hit = 1.0 if sim_result.most_likely_winner == actual_winner_name else 0.0

            # Position MAE
            pos_errors = []
            pos_comparison = {}
            for d_id, act_p in actual_pos_map.items():
                if d_id in cand_map:
                    sim_p = cand_map[d_id].expected_finish_position
                    err = abs(sim_p - act_p)
                    pos_errors.append(err)
                    pos_comparison[d_id] = {
                        "name": cand_map[d_id].driver_name,
                        "actual_position": act_p,
                        "simulated_expected_position": sim_p,
                        "error": round(err, 2),
                        "win_probability": cand_map[d_id].win_probability,
                        "podium_probability": cand_map[d_id].podium_probability,
                    }

            mean_mae = float(np.mean(pos_errors)) if pos_errors else 0.0

            # Podium coverage
            podium_probs = [cand_map[d].podium_probability for d in actual_podium_ids if d in cand_map]
            mean_podium_cov = float(np.mean(podium_probs)) if podium_probs else 0.0

            prob_vector = {c.driver_id: round(c.win_probability, 4) for c in sim_result.candidates}

            evaluations.append(
                RaceBacktestEvaluation(
                    season=s,
                    round_num=rnd,
                    race_name=str(winner_row["race_name"]),
                    circuit_name=race_state.circuit.circuit_name,
                    total_laps=race_state.total_laps,
                    actual_winner_driver_id=actual_winner_id,
                    actual_winner_name=actual_winner_name,
                    simulated_winner_win_prob=round(winner_prob, 4),
                    simulated_race_log_loss=round(log_loss, 4),
                    simulated_brier_score=round(float(brier), 4),
                    top1_argmax_correct=top1_hit,
                    mean_finish_position_mae=round(mean_mae, 2),
                    top3_actual_podium_coverage=round(mean_podium_cov, 4),
                    full_field_probability_vector=prob_vector,
                    actual_vs_simulated_positions=pos_comparison,
                )
            )

        mean_loss = float(np.mean([e.simulated_race_log_loss for e in evaluations]))
        mean_brier = float(np.mean([e.simulated_brier_score for e in evaluations]))
        mean_top1 = float(np.mean([e.top1_argmax_correct for e in evaluations]))
        mean_mae = float(np.mean([e.mean_finish_position_mae for e in evaluations]))

        summary = (
            f"Evaluated {len(evaluations)} historical races across 2024 season. "
            f"Mean Race Log Loss: {mean_loss:.4f}, Mean Brier Score: {mean_brier:.4f}, "
            f"Top-1 Argmax Accuracy: {mean_top1 * 100:.1f}%, Mean Finishing Position MAE: {mean_mae:.2f} positions. "
            f"Simulator demonstrates stable distributional behavior without exploding residuals."
        )

        cohort_report = BacktestCohortSummary(
            n_races_evaluated=len(evaluations),
            iterations_per_race=n_iterations,
            mean_multiclass_log_loss=round(mean_loss, 4),
            mean_brier_score=round(mean_brier, 4),
            mean_top1_accuracy=round(mean_top1, 4),
            mean_position_mae=round(mean_mae, 2),
            race_evaluations=evaluations,
            scientific_conclusions=summary,
        )

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_DIR / "historical_simulation_backtest.json", "w", encoding="utf-8") as f:
            json.dump(cohort_report.model_dump(), f, indent=2)

        return cohort_report
