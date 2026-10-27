"""Health check response models."""
from typing import Optional
from pydantic import BaseModel, Field


class ModelReadiness(BaseModel):
    """Reflects the operational state of the ML fraud risk estimation pipeline."""

    ready: bool = Field(
        default=False,
        description="Whether the ML risk estimation model is loaded and ready for inference",
    )
    status: str = Field(
        default="not_ready",
        description="Machine learning model readiness status",
    )
    reason: str = Field(
        default="ML model pipeline is not yet trained or loaded. Inference and SHAP explanations are unavailable in this initial foundation stage.",
        description="Human-readable explanation of model state",
    )
    loaded_model_version: Optional[str] = Field(
        default=None,
        description="Identifier of the active model checkpoint if loaded",
    )


class SubsystemStatus(BaseModel):
    """Honest status of auxiliary services."""

    database: str = Field(
        default="not_configured",
        description="Database status (PostgreSQL planned for subsequent phase)",
    )
    claims_pipeline: str = Field(
        default="not_started",
        description="Claims ingestion and validation pipeline state",
    )


class HealthResponse(BaseModel):
    """Health check payload distinguishing API health from ML model readiness."""

    status: str = Field(
        default="healthy",
        description="FastAPI service operational status",
    )
    app_name: str = Field(
        default="MediLens AI",
        description="Application name",
    )
    version: str = Field(
        default="0.1.0",
        description="API version",
    )
    environment: str = Field(
        default="development",
        description="Deployment environment",
    )
    timestamp: str = Field(
        description="ISO-8601 UTC timestamp of the health check request",
    )
    model_readiness: ModelReadiness = Field(
        description="Explainable ML fraud estimation model readiness details",
    )
    subsystems: SubsystemStatus = Field(
        description="Auxiliary subsystem statuses",
    )
