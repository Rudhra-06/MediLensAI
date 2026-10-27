"""MediLens AI FastAPI entry point for provider-level retrospective inference."""
import logging
import ipaddress
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from backend.app.api.routes import health_router, risk_router
from backend.app.api.routes.risk import ProviderRiskService
from backend.app.core.config import settings

logger = logging.getLogger("medilens.api")


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Load the fixed local risk model once per application worker."""
    try:
        application.state.risk_service = ProviderRiskService.load()
        application.state.risk_load_error = None
        application.state.local_provider_demo = None
        application.state.risk_service.local_demo_enabled = False
        try:
            loopback_bind = ipaddress.ip_address(settings.API_HOST).is_loopback
        except ValueError:
            loopback_bind = settings.API_HOST.casefold() == "localhost"
        if settings.LOCAL_PROVIDER_DEMO_ENABLED and settings.MEDILENS_ENV == "development" and loopback_bind:
            try:
                application.state.local_provider_demo = application.state.risk_service.load_local_demo()
                application.state.risk_service.local_demo_enabled = True
            except Exception as exc:
                application.state.local_demo_load_error = type(exc).__name__
                logger.error("Local provider demo unavailable during startup (%s).", type(exc).__name__)
        elif settings.LOCAL_PROVIDER_DEMO_ENABLED:
            logger.error("Local provider demo is disabled because development mode and a loopback bind are required.")
    except Exception as exc:
        application.state.risk_service = None
        application.state.local_provider_demo = None
        application.state.risk_load_error = type(exc).__name__
        logger.error("Provider risk model unavailable during startup (%s).", type(exc).__name__)
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Local development API for provider-level inference against a saved "
        "PotentialFraud-label model. Scores are uncalibrated and do not represent "
        "claim-level predictions, verified fraud, or real-world validation."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


@app.exception_handler(RequestValidationError)
async def sanitized_validation_error(_request: Request, exc: RequestValidationError) -> JSONResponse:
    """Avoid echoing submitted feature values in 422 responses."""
    safe_errors = [
        {key: error[key] for key in ("loc", "msg", "type") if key in error}
        for error in exc.errors()
    ]
    return JSONResponse(status_code=422, content={"detail": safe_errors})

# CORS is restricted to explicit configured origins; API routes do not use cookies.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Register API routes under /api
app.include_router(health_router, prefix=settings.API_PREFIX)
app.include_router(risk_router, prefix=f"{settings.API_PREFIX}/v1")


@app.get("/", tags=["Root"])
def root_status():
    """Root endpoint providing service metadata and discovery links."""
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.MEDILENS_ENV,
        "documentation": "/docs",
        "health_check": f"{settings.API_PREFIX}/health",
        "notice": (
            "This API returns provider-level uncalibrated model scores for the "
            "PotentialFraud dataset label, which is not verified fraud. Scores are "
            "not proof of fraud or validated real-world performance."
        ),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
    )
