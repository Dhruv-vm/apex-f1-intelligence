"""Core model and prediction contracts for APEX Machine Learning (ml.base).

Defines:
- ForecastResult: Validated point-in-time race forecast container.
- BasePredictiveModel: Shared interface for models producing race-level winner probabilities.
- BaseRankingModel: Dedicated ranking interface for order/score outputs (independent of classification).
"""

from abc import ABC, abstractmethod
import math
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from pydantic import BaseModel, Field, model_validator


class ForecastResult(BaseModel):
    """
    Validated representation of a point-in-time probabilistic Grand Prix forecast.

    Guarantees:
    - Exactly one prediction per unique driver in the entrant candidate set.
    - Full probability simplex normalization: sum(p_win) == 1.0 within 1e-9.
    - Plackett-Luce consistent marginals (if provided):
      - sum(p_podium) == min(3.0, N)
      - sum(p_top5) == min(5.0, N)
      - p_win[i] <= p_podium[i] <= p_top5[i] <= 1.0 for all i
      - sum(expected_rank) == N * (N + 1) / 2 within 1e-6
      - 1.0 <= expected_rank[i] <= N
    - Fully serializable to native Python dict and JSON via Pydantic v2.
    """
    race_id: int
    model_id: str
    driver_ids: List[int]
    p_win: List[float] = Field(..., description="Probabilities of winning the Grand Prix (P1)")
    p_podium: Optional[List[float]] = Field(default=None, description="Probabilities of podium finish (P1-P3)")
    p_top5: Optional[List[float]] = Field(default=None, description="Probabilities of top-5 finish (P1-P5)")
    expected_rank: Optional[List[float]] = Field(default=None, description="Expected finishing positions E[rank]")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Model provenance and inference metadata")

    @model_validator(mode="after")
    def validate_forecast_integrity(self) -> "ForecastResult":
        n = len(self.driver_ids)
        if n == 0:
            raise ValueError("Forecast candidate set cannot be empty.")

        # 1. Driver IDs must be unique
        if len(set(self.driver_ids)) != n:
            raise ValueError("Duplicate driver IDs found in forecast candidate set.")

        # 2. Winner probabilities length and range
        if len(self.p_win) != n:
            raise ValueError(f"p_win length ({len(self.p_win)}) does not match driver_ids length ({n}).")

        for i, p in enumerate(self.p_win):
            if p < -1e-9 or p > 1.0 + 1e-9:
                raise ValueError(f"p_win[{i}]={p} is outside valid probability interval [0, 1].")

        # 3. Simplex normalization
        sum_p_win = sum(self.p_win)
        if not math.isclose(sum_p_win, 1.0, abs_tol=1e-9, rel_tol=1e-7):
            raise ValueError(f"p_win does not sum to 1.0 (sum={sum_p_win:.12f}, residual={abs(sum_p_win - 1.0):.3e}).")

        # 4. Podium marginals validation (optional)
        if self.p_podium is not None:
            if len(self.p_podium) != n:
                raise ValueError(f"p_podium length ({len(self.p_podium)}) does not match candidate length ({n}).")
            expected_podium_sum = min(3.0, float(n))
            sum_podium = sum(self.p_podium)
            if not math.isclose(sum_podium, expected_podium_sum, abs_tol=1e-9, rel_tol=1e-7):
                raise ValueError(
                    f"p_podium sum ({sum_podium:.9f}) does not match expected {expected_podium_sum}."
                )
            for i in range(n):
                if self.p_podium[i] < -1e-9 or self.p_podium[i] > 1.0 + 1e-9:
                    raise ValueError(f"p_podium[{i}]={self.p_podium[i]} is outside [0, 1].")
                if self.p_win[i] > self.p_podium[i] + 1e-9:
                    raise ValueError(
                        f"Inconsistent marginals at index {i}: p_win ({self.p_win[i]}) > p_podium ({self.p_podium[i]})."
                    )

        # 5. Top-5 marginals validation (optional)
        if self.p_top5 is not None:
            if len(self.p_top5) != n:
                raise ValueError(f"p_top5 length ({len(self.p_top5)}) does not match candidate length ({n}).")
            expected_top5_sum = min(5.0, float(n))
            sum_top5 = sum(self.p_top5)
            if not math.isclose(sum_top5, expected_top5_sum, abs_tol=1e-9, rel_tol=1e-7):
                raise ValueError(
                    f"p_top5 sum ({sum_top5:.9f}) does not match expected {expected_top5_sum}."
                )
            for i in range(n):
                if self.p_top5[i] < -1e-9 or self.p_top5[i] > 1.0 + 1e-9:
                    raise ValueError(f"p_top5[{i}]={self.p_top5[i]} is outside [0, 1].")
                lower_bound = self.p_podium[i] if self.p_podium is not None else self.p_win[i]
                bound_name = "p_podium" if self.p_podium is not None else "p_win"
                if lower_bound > self.p_top5[i] + 1e-9:
                    raise ValueError(
                        f"Inconsistent marginals at index {i}: {bound_name} ({lower_bound}) > p_top5 ({self.p_top5[i]})."
                    )

        # 6. Expected finishing rank validation (optional)
        if self.expected_rank is not None:
            if len(self.expected_rank) != n:
                raise ValueError(f"expected_rank length ({len(self.expected_rank)}) does not match candidate length ({n}).")
            expected_rank_sum = n * (n + 1) / 2.0
            sum_rank = sum(self.expected_rank)
            if not math.isclose(sum_rank, expected_rank_sum, abs_tol=1e-6):
                raise ValueError(
                    f"expected_rank sum ({sum_rank:.6f}) does not match expected N(N+1)/2={expected_rank_sum:.6f}."
                )
            for i, r in enumerate(self.expected_rank):
                if r < 1.0 - 1e-9 or r > float(n) + 1e-9:
                    raise ValueError(f"expected_rank[{i}]={r} is outside valid rank span [1, {n}].")

        return self


class BasePredictiveModel(ABC):
    """
    Abstract Base Class for APEX Grand Prix race-winner models.

    All implementing classes produce race-level winner probability distributions
    constrained to sum to 1.0 across the eligible candidate set.
    """

    @property
    @abstractmethod
    def model_id(self) -> str:
        """Canonical model ID (e.g., 'ELO_R3', 'M0', 'M1', 'M2', 'M3', 'M4', 'M5')."""
        pass

    @property
    @abstractmethod
    def feature_names(self) -> List[str]:
        """Ordered list of feature column names expected by this model."""
        pass

    @property
    def model_metadata(self) -> Dict[str, Any]:
        """Model provenance, hyperparameters, and operational constraints."""
        return {
            "model_id": self.model_id,
            "feature_names": self.feature_names,
            "class_name": self.__class__.__name__,
        }

    @abstractmethod
    def fit(
        self,
        X: pd.DataFrame,
        y: np.ndarray,
        race_ids: Optional[np.ndarray] = None,
    ) -> "BasePredictiveModel":
        """
        Fit model parameters on historical training observations.

        Parameters:
            X: Candidate feature matrix.
            y: Binary indicator of race victory (1 if winner, 0 otherwise).
            race_ids: Optional array of race identifiers for grouped models.

        Returns:
            self
        """
        pass

    @abstractmethod
    def predict_proba(
        self,
        X: pd.DataFrame,
        race_ids: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """
        Predict probability of victory for each candidate.

        Guaranteed to sum to 1.0 within each race candidate group.

        Parameters:
            X: Candidate feature matrix.
            race_ids: Array of race identifiers aligning candidates to races.

        Returns:
            1D float array of winner probabilities matching len(X).
        """
        pass

    def predict_race_forecast(
        self,
        race_id: int,
        X_race: pd.DataFrame,
        driver_ids: List[int],
    ) -> ForecastResult:
        """
        Generate a validated ForecastResult for a single Grand Prix event.
        """
        race_ids = np.full(len(X_race), race_id, dtype=int)
        p_win = self.predict_proba(X_race, race_ids=race_ids)
        return ForecastResult(
            race_id=race_id,
            model_id=self.model_id,
            driver_ids=driver_ids,
            p_win=p_win.tolist(),
            metadata=self.model_metadata,
        )


class BaseRankingModel(ABC):
    """
    Dedicated Abstract Base Class for candidate ranking models (e.g., LambdaMART, Bradley-Terry).

    Operates on utility/relevance scores and candidate orderings.
    Raw ranking scores are arbitrary real values and must NOT be interpreted as winner probabilities.
    """

    @property
    @abstractmethod
    def model_id(self) -> str:
        """Canonical model ID (e.g., 'LAMBDAMART_LGBM', 'BRADLEY_TERRY')."""
        pass

    @property
    @abstractmethod
    def feature_names(self) -> List[str]:
        """Ordered list of feature column names expected by this ranking model."""
        pass

    @property
    def model_metadata(self) -> Dict[str, Any]:
        """Ranking model provenance and configuration."""
        return {
            "model_id": self.model_id,
            "feature_names": self.feature_names,
            "class_name": self.__class__.__name__,
            "is_ranking_model": True,
        }

    @abstractmethod
    def fit(
        self,
        X: pd.DataFrame,
        y_ranks: np.ndarray,
        race_ids: np.ndarray,
    ) -> "BaseRankingModel":
        """
        Fit ranking model using grouped listwise or pairwise objectives.

        Parameters:
            X: Candidate feature matrix.
            y_ranks: Finishing rank positions or relevance scores.
            race_ids: Race grouping array.
        """
        pass

    @abstractmethod
    def predict_scores(
        self,
        X: pd.DataFrame,
        race_ids: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """
        Predict real-valued candidate ranking scores.
        Higher score indicates higher predicted finishing position (or lower rank integer).
        """
        pass

    @abstractmethod
    def predict_order(
        self,
        X: pd.DataFrame,
        race_ids: np.ndarray,
        driver_ids: List[int],
    ) -> Dict[int, List[int]]:
        """
        Predict ordered sequence of driver IDs from 1st to last for each race.

        Returns:
            Dict mapping race_id -> list of driver_ids in predicted finishing order.
        """
        pass
