"""Health check endpoints for MediLens AI."""
from datetime import datetime, timezone
from fastapi import APIRouter
from backend.app.core.config import settings
from backend.app.schemas.health import HealthResponse, ModelReadiness, SubsystemStatus

router = APIRouter(tags=["Health & Diagnostics"])


@router.get("/health", response_model=HealthResponse, summary="System Health & Model Readiness")
def get_health() -> HealthResponse:
    """Return API operational status, version, and ML model readiness.

    Accurately distinguishes between operational API availability and ML model
    availability (which is not ready in this initial phase).
    """
    return HealthResponse(
        status="healthy",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.MEDILENS_ENV,
        timestamp=datetime.now(timezone.utc).isoformat(),
        model_readiness=ModelReadiness(
            ready=False,
            status="not_ready",
            reason="ML model pipeline (XGBoost/scikit-learn/SHAP) is not yet trained or loaded. Risk scoring and SHAP explanations are unavailable in this initial phase.",
            loaded_model_version=None,
        ),
        subsystems=SubsystemStatus(
            database="not_configured",
            claims_pipeline="not_started",
        ),
    )
