"""Data models for sequential multi-checkpoint forecasting engine (Phase 6)."""
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class DriverPrediction(BaseModel):
    """Full-field probabilistic forecast outputs for an individual driver."""
    driver_number: int
    driver_code: str
    driver_name: str
    team_name: str
    grid_position: Optional[int] = None
    p_win: float = Field(..., ge=0.0, le=1.0, description="Probability of winning the Grand Prix (P1)")
    p_podium: float = Field(..., ge=0.0, le=1.0, description="Probability of finishing on podium (P1-P3)")
    p_top5: float = Field(..., ge=0.0, le=1.0, description="Probability of finishing in top five (P1-P5)")
    expected_position: float = Field(..., description="Expected finishing position E[rank]")


class CheckpointForecast(BaseModel):
    """
    Immutable point-in-time probabilistic forecast generated at a specific weekend checkpoint.
    Prepares HYP-0001 (Sequential Information Superiority).
    """
    forecast_id: str
    season: int
    event_id: int
    event_name: str
    checkpoint: str  # T0_PRE_WEEKEND, T1_POST_FP1, T2_POST_FP2, T3_POST_FP3, T4_POST_QUALIFYING, T5_FINAL_PRE_RACE
    cutoff_timestamp: str  # Strict ISO 8601 information cutoff
    prediction_timestamp: str = ""
    model_id: str
    model_version: str
    eligible_drivers_count: int
    drivers: List[DriverPrediction]
    feature_names: List[str] = Field(default_factory=list)
    missingness: Dict[str, bool] = Field(default_factory=dict)
    entropy: float = Field(..., description="Normalized prediction Shannon entropy in nats")
    candidate_set_limitation_flag: str = (
        "CANDIDATE_SET_RETROSPECTIVE: Driver candidate set derived from validated session classification "
        "records; independent timestamped pre-race entry list registry pending."
    )
    provenance: str = "APEX Multi-Checkpoint Sequential Forecasting Engine"


class EvaluationMetrics(BaseModel):
    """Proper scoring rules, calibration diagnostics, and separated accuracy metrics."""
    checkpoint: str
    race_count: int
    multiclass_log_loss: float
    multiclass_brier_score: float
    conventional_top1_acc: float = Field(..., description="Proportion of races where argmax predicted winner is actual winner")
    fractional_top1_score: float = Field(..., description="Mean predicted probability assigned to the actual winner")
    fractional_top1_acc: float = Field(..., description="Maintained for backward compatibility; equals fractional_top1_score")
    expected_calibration_error: float
    podium_brier_score: Optional[float] = None
    top5_brier_score: Optional[float] = None
    position_mae: Optional[float] = None
    delta_log_loss_vs_t0: float
    delta_brier_vs_t0: float


class SequentialEvaluationReport(BaseModel):
    """Evaluation summary comparing predictive performance across weekend checkpoints."""
    evaluation_cohort: str
    checkpoints: List[EvaluationMetrics]
    paired_comparisons: Optional[Dict[str, Dict[str, float]]] = None
    wilcoxon_tests: Optional[Dict[str, Dict[str, float]]] = None
    hyp_0001_supported: bool
    summary_interpretation: str
