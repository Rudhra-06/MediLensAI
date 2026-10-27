"""Unit tests for the health check and root endpoints."""
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_root_endpoint(client):
    """Verify that the root endpoint returns service metadata."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "MediLens AI"
    assert data["version"] == "0.1.0"
    assert "/api/health" in data["health_check"]
    assert "proof of fraud" in data["notice"]


def test_health_endpoint(client):
    """Verify health endpoint distinguishes API health from model readiness."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()

    # API status and identity
    assert data["status"] == "healthy"
    assert data["app_name"] == "MediLens AI"
    assert data["version"] == "0.1.0"
    assert "timestamp" in data

    # Model readiness reflects the startup-loaded inference artifact.
    assert "model_readiness" in data
    assert data["model_readiness"]["ready"] is True
    assert data["model_readiness"]["status"] == "ready"
    assert data["model_readiness"]["loaded_model_version"] == "provider-risk-rf-v1"

    # Auxiliary subsystems are honestly reported
    assert data["subsystems"]["database"] == "not_configured"
    assert data["subsystems"]["claims_pipeline"] == "not_started"


def test_cors_headers(client):
    """Verify CORS headers respond correctly for permitted frontend origins."""
    headers = {
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "GET",
    }
    response = client.options("/api/health", headers=headers)
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
