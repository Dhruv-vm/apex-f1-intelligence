"""Canonical model registry for APEX Machine Learning (ml.registry).

Tracks:
- Canonical model identities and metadata (EXP-0001 through EXP-0005).
- Model implementation classes and factory bindings.
- Scheduled extraction stages.

Preserves the established research nomenclature:
- ELO_R3: Outcome-Independent Dynamic Elo Rating Baseline
- M0: Uniform Pre-Race Baseline
- M1: Empirical Starting-Grid Win Frequency Baseline
- M2: Grid-Only Univariate Logistic Regression
- M3: Grid + Driver and Constructor Form Logistic Regression
- M4: LightGBM Gradient Boosted Decision Tree Benchmark
- M5: Conditional Logit / Plackett-Luce Choice Model
"""

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Type, Union

from ml.base import BasePredictiveModel, BaseRankingModel


class ModelRegistryError(Exception):
    """Base exception for model registry errors."""
    pass


class UnknownModelError(ModelRegistryError):
    """Raised when an unrecognized model_id is requested."""
    pass


class ModelFactoryUnavailableError(ModelRegistryError):
    """Raised when a canonical model is requested before its factory is registered."""
    pass


@dataclass(frozen=True)
class ModelMetadata:
    """Canonical metadata and research provenance for an APEX model."""
    model_id: str
    name: str
    family: str
    target_checkpoint: str
    literature_reference: str
    scheduled_stage: str
    description: str


# Canonical registry of all validated APEX research models
CANONICAL_MODELS: Dict[str, ModelMetadata] = {
    "ELO_R3": ModelMetadata(
        model_id="ELO_R3",
        name="Outcome-Independent Dynamic Elo Baseline",
        family="Dynamic Rating System",
        target_checkpoint="T0",
        literature_reference="van Kesteren & Bergkamp (2023), Bell et al. (2016)",
        scheduled_stage="Stage 8.4",
        description="Chronological rolling Elo rating with dynamic k-factors and outcome-independent candidate ordering.",
    ),
    "M0": ModelMetadata(
        model_id="M0",
        name="Uniform Pre-Race Baseline",
        family="Heuristic Baseline",
        target_checkpoint="T5",
        literature_reference="Henderson et al. (2016)",
        scheduled_stage="Stage 8.4",
        description="Equal probability assignment (1 / N_r) over all pre-race entrants.",
    ),
    "M1": ModelMetadata(
        model_id="M1",
        name="Empirical Grid Win Frequency",
        family="Empirical Frequency",
        target_checkpoint="T5",
        literature_reference="Urdhwareshe (2025) [audit]",
        scheduled_stage="Stage 8.4",
        description="Historical win frequency conditioned on starting grid position with Laplace smoothing (alpha=10).",
    ),
    "M2": ModelMetadata(
        model_id="M2",
        name="Grid-Only Logistic Regression",
        family="Generalized Linear Model",
        target_checkpoint="T5",
        literature_reference="Henderson et al. (2016)",
        scheduled_stage="Stage 8.4",
        description="Univariate logistic regression on 5 starting grid representation features.",
    ),
    "M3": ModelMetadata(
        model_id="M3",
        name="Grid + Driver/Constructor Form Logistic Regression",
        family="Generalized Linear Model",
        target_checkpoint="T5",
        literature_reference="Henderson et al. (2016), Bell et al. (2016)",
        scheduled_stage="Stage 8.4",
        description="Multivariate logistic regression combining grid geometry with rolling historical driver and constructor form.",
    ),
    "M4": ModelMetadata(
        model_id="M4",
        name="LightGBM GBDT Pre-Race Benchmark",
        family="Gradient Boosted Decision Trees",
        target_checkpoint="T5",
        literature_reference="Niculescu-Mizil & Caruana (2005), Guo et al. (2017)",
        scheduled_stage="Stage 8.4",
        description="Tree-based gradient boosted classifier evaluated under walk-forward protocol on 16 pre-race features.",
    ),
    "M5": ModelMetadata(
        model_id="M5",
        name="Plackett-Luce Ranking / Conditional Logit",
        family="Choice Axiom Ranking Model",
        target_checkpoint="T5",
        literature_reference="Plackett (1975), Luce (1959), Hunter (2004)",
        scheduled_stage="Stage 8.4",
        description="Grouped conditional logit maximum likelihood estimation with joint podium/top-5/expected position marginals.",
    ),
}

# Active factory registry mapping model_id -> callable factory
_FACTORIES: Dict[str, Callable[..., Union[BasePredictiveModel, BaseRankingModel]]] = {}


class ModelRegistry:
    """Central registry and factory interface for APEX models."""

    @classmethod
    def list_canonical_models(cls) -> List[str]:
        """Return list of all canonical model identifiers."""
        return list(CANONICAL_MODELS.keys())

    @classmethod
    def get_metadata(cls, model_id: str) -> ModelMetadata:
        """Retrieve canonical metadata for a model ID."""
        canonical_id = model_id.strip().upper()
        if canonical_id not in CANONICAL_MODELS:
            raise UnknownModelError(
                f"Unknown model_id '{model_id}'. Canonical models are: {cls.list_canonical_models()}."
            )
        return CANONICAL_MODELS[canonical_id]

    @classmethod
    def is_canonical(cls, model_id: str) -> bool:
        """Check if a model ID is part of the canonical research registry."""
        return model_id.strip().upper() in CANONICAL_MODELS

    @classmethod
    def is_available(cls, model_id: str) -> bool:
        """Check if an executable factory has been registered for this model."""
        return model_id.strip().upper() in _FACTORIES

    @classmethod
    def list_available_models(cls) -> List[str]:
        """List model IDs that currently have executable factories registered."""
        return list(_FACTORIES.keys())

    @classmethod
    def register_factory(
        cls,
        model_id: str,
        factory: Callable[..., Union[BasePredictiveModel, BaseRankingModel]],
        overwrite: bool = False,
    ) -> None:
        """
        Register a factory function or class for a canonical model ID.
        """
        canonical_id = model_id.strip().upper()
        if canonical_id not in CANONICAL_MODELS:
            raise UnknownModelError(
                f"Cannot register factory for non-canonical model_id '{model_id}'. "
                f"Canonical models are: {cls.list_canonical_models()}."
            )
        if canonical_id in _FACTORIES and not overwrite:
            raise ModelRegistryError(
                f"Factory for '{canonical_id}' is already registered. Set overwrite=True to replace."
            )
        _FACTORIES[canonical_id] = factory

    @classmethod
    def create_model(cls, model_id: str, **kwargs: Any) -> Union[BasePredictiveModel, BaseRankingModel]:
        """
        Instantiate an executable model by its canonical ID.

        Raises:
            UnknownModelError: If model_id is not in the canonical registry.
            ModelFactoryUnavailableError: If model_id is canonical but not yet extracted/registered.
        """
        canonical_id = model_id.strip().upper()
        if canonical_id not in CANONICAL_MODELS:
            raise UnknownModelError(
                f"Unknown model_id '{model_id}'. Canonical models are: {cls.list_canonical_models()}."
            )
        if canonical_id not in _FACTORIES:
            meta = CANONICAL_MODELS[canonical_id]
            raise ModelFactoryUnavailableError(
                f"Model '{canonical_id}' ({meta.name}) is a canonical APEX research model, "
                f"but its production factory is not yet registered. "
                f"Scheduled extraction: {meta.scheduled_stage}."
            )
        return _FACTORIES[canonical_id](**kwargs)

    @classmethod
    def clear_factories_for_testing(cls) -> None:
        """Internal helper to reset registered factories during test runs."""
        _FACTORIES.clear()
