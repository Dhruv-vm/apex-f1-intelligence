/**
 * APEX — Simulation & Counterfactual Strategy Types (Phase 7.1 / EXP-0006-R2)
 */

export interface SimulationCircuit {
  circuit_id: string;
  circuit_name: string;
  total_laps: number;
  base_lap_time_seconds: number;
  pit_transit_loss_seconds: number;
  overtaking_difficulty_index: number;
  safety_car_hazard_rate: number;
}

export interface CandidateSimulationSummary {
  driver_id: string;
  driver_name: string;
  constructor_id: string;
  starting_grid: number;
  expected_finish_position: number;
  finish_position_std: number;
  expected_pos_standard_error?: number;
  win_probability: number;
  win_standard_error?: number;
  win_probability_ci_95: [number, number];
  podium_probability: number;
  podium_probability_ci_95: [number, number];
  top5_probability: number;
  top5_probability_ci_95: [number, number];
  dnf_probability: number;
  position_distribution: Record<number, number>;
  mean_race_time_seconds: number;
}

export interface ConvergenceCheckpoint {
  iteration_count: number;
  leader_win_probability: number;
  leader_win_standard_error?: number;
  max_position_change: number;
}

export interface SimulationRunResult {
  run_id: string;
  race_id: string;
  circuit_name: string;
  season: number;
  total_laps: number;
  n_iterations: number;
  master_seed: number;
  candidates: CandidateSimulationSummary[];
  convergence_history: ConvergenceCheckpoint[];
  most_likely_winner: string;
  winner_win_probability: number;
  simulated_race_control_events_summary: Record<string, number>;
}

export interface StrategyMetrics {
  strategy_name: string;
  expected_finishing_position: number;
  median_finishing_position?: number;
  position_std: number;
  expected_pos_standard_error?: number;
  win_probability: number;
  win_standard_error?: number;
  win_probability_ci_95: [number, number];
  podium_probability: number;
  podium_probability_ci_95: [number, number];
  top5_probability: number;
  top5_probability_ci_95: [number, number];
  dnf_probability?: number;
  dsq_probability?: number;
  classified_rate?: number;
  mean_race_time_seconds: number;
  race_time_std_seconds: number;
  mean_race_time_all_runs_seconds?: number;
  race_time_all_runs_std_seconds?: number;
  mean_pit_stops: number;
  mean_pit_transit_loss_seconds?: number;
  mean_final_tyre_age_laps?: number;
  probability_of_gaining_positions: number;
  time_regret_vs_best_seconds: number;
  position_regret_vs_best: number;
  finishing_position_distribution?: Record<number, number>;
  tyre_usage?: Record<string, number>;
}

export interface PairedStrategyComparison {
  strategy_a: string;
  strategy_b: string;
  mean_position_difference: number;
  ci_pos_diff_95: [number, number];
  mean_time_difference_seconds: number;
  ci_time_diff_95: [number, number];
  mean_time_difference_all_runs_seconds?: number;
  mean_time_difference_matched_finished_seconds?: number;
  ci_time_diff_matched_finished_95?: [number, number];
  n_both_finished?: number;
  n_at_least_one_retired?: number;
  prob_a_finishes_ahead: number;
  prob_b_finishes_ahead: number;
  prob_tied: number;
  prob_a_beats_b_decisive?: number;
  p_value_paired_test: number;
  p_value_adjusted_holm_bonferroni?: number;
  time_correlation: number;
  variance_reduction_percent: number;
  head_to_head_definition?: string;
}

export interface CounterfactualComparisonReport {
  experiment_id: string;
  hypothesis_id: string;
  race_id: string;
  target_driver_id: string;
  target_driver_name: string;
  starting_grid: number;
  n_simulations: number;
  master_seed: number;
  evaluated_strategies: StrategyMetrics[];
  paired_comparisons?: PairedStrategyComparison[];
  best_strategy_by_expected_position: string;
  best_strategy_by_win_probability: string;
  best_strategy_by_podium_probability?: string;
  best_strategy_by_top5_probability?: string;
  best_strategy_by_race_time: string;
  best_strategy_by_lowest_variance?: string;
  objective_rankings?: Record<string, string[]>;
  measured_mean_variance_reduction_percent?: number;
  out_of_sample_regret_seconds?: Record<string, number>;
  scientific_summary: string;
}

export interface SimulationJobStatus {
  job_id: string;
  job_type: string;
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED';
  progress_pct: number;
  result?: any;
  error?: string;
}
