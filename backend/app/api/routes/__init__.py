"""API route modules."""
from backend.app.api.routes.health import router as health_router
from backend.app.api.routes.risk import router as risk_router

__all__ = ["health_router", "risk_router"]
