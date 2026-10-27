"""MediLens AI - ML Data Ingestion and Feature Engineering Package."""

from backend.app.ml.config import DatasetConfig, DatasetPaths
from backend.app.ml.contracts import (
    DataQualityReport,
    FeatureDatasetSummary,
    FeatureMetadata,
    FEATURE_DEFINITIONS,
)
from backend.app.ml.ingestion import DataIngestionPipeline
from backend.app.ml.features import ProviderFeatureEngineer
from backend.app.ml.model import (
    ProviderRiskModelError,
    load_processed_provider_data,
    load_provider_risk_model,
    train_provider_risk_model,
    validate_model_inputs,
)
from backend.app.ml.explainability import (
    ExplainabilityError,
    generate_explanations_from_saved_data,
    generate_provider_explanations,
)

__all__ = [
    "DatasetConfig",
    "DatasetPaths",
    "DataQualityReport",
    "FeatureDatasetSummary",
    "FeatureMetadata",
    "FEATURE_DEFINITIONS",
    "DataIngestionPipeline",
    "ProviderFeatureEngineer",
    "ProviderRiskModelError",
    "load_processed_provider_data",
    "load_provider_risk_model",
    "train_provider_risk_model",
    "validate_model_inputs",
    "ExplainabilityError",
    "generate_explanations_from_saved_data",
    "generate_provider_explanations",
]
