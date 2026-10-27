"""Unit tests for the health check and root endpoints."""
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Verify that the root endpoint returns service metadata."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "MediLens AI"
    assert data["version"] == "0.1.0"
    assert "/api/health" in data["health_check"]
    assert "proof of fraud" in data["notice"]


def test_health_endpoint():
    """Verify health endpoint distinguishes API health from model readiness."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()

    # API status and identity
    assert data["status"] == "healthy"
    assert data["app_name"] == "MediLens AI"
    assert data["version"] == "0.1.0"
    assert "timestamp" in data

    # Model readiness must be explicitly not ready in this initial phase
    assert "model_readiness" in data
    assert data["model_readiness"]["ready"] is False
    assert data["model_readiness"]["status"] == "not_ready"
    assert "not yet trained" in data["model_readiness"]["reason"]

    # Auxiliary subsystems are honestly reported
    assert data["subsystems"]["database"] == "not_configured"
    assert data["subsystems"]["claims_pipeline"] == "not_started"


def test_cors_headers():
    """Verify CORS headers respond correctly for permitted frontend origins."""
    headers = {
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "GET",
    }
    response = client.options("/api/health", headers=headers)
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
