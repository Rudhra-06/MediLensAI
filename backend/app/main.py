"""MediLens AI - FastAPI Application Entry Point.

Explainable AI-Powered Healthcare Insurance Claim Fraud Screening Platform.
Predictions indicate potential fraud risk for human investigation, not proof of fraud.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.api.routes.health import router as health_router
from backend.app.core.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Explainable AI-powered healthcare insurance claim fraud screening "
        "and investigation-support platform API. Provides claim validation, "
        "ML risk estimation, SHAP explanations, and screening workflows."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS safely for configured frontend origins (avoiding wildcard with credentials)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Register API routes under /api
app.include_router(health_router, prefix=settings.API_PREFIX)


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
            "MediLens AI estimates potential fraud risk to support human review. "
            "Predictions indicate risk tier and suspicious patterns, not proof of fraud."
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
