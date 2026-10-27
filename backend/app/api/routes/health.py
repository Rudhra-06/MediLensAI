"""Health check endpoints for MediLens AI."""
from datetime import datetime, timezone
from fastapi import APIRouter, Request
from backend.app.core.config import settings
from backend.app.schemas.health import HealthResponse, ModelReadiness, SubsystemStatus

router = APIRouter(tags=["Health & Diagnostics"])


@router.get("/health", response_model=HealthResponse, summary="System Health & Model Readiness")
def get_health(request: Request) -> HealthResponse:
    """Return API operational status, version, and ML model readiness.

    Accurately distinguishes between operational API availability and ML model
    availability of the startup-loaded provider risk model.
    """
    model_service = getattr(request.app.state, "risk_service", None)
    model_ready = model_service is not None
    return HealthResponse(
        status="healthy",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.MEDILENS_ENV,
        timestamp=datetime.now(timezone.utc).isoformat(),
        model_readiness=ModelReadiness(
            ready=model_ready,
            status="ready" if model_ready else "not_ready",
            reason=("Provider risk model loaded." if model_ready else "Provider risk model artifacts are missing or incompatible; risk scoring is unavailable."),
            loaded_model_version=("provider-risk-rf-v1" if model_ready else None),
        ),
        subsystems=SubsystemStatus(
            database="not_configured",
            claims_pipeline="not_started",
        ),
    )
