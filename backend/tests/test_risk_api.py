import json
import math

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from backend.app.api.routes.risk import MODEL_VERSION, get_risk_service
from backend.app.main import app
from backend.app.ml.contracts import FEATURE_DEFINITIONS
from backend.app.api.routes.risk import RiskArtifactError, ProviderRiskService


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def valid_features(value=0.0):
    return {name: value for name in FEATURE_DEFINITIONS}


def test_model_health_features_and_openapi(client):
    health = client.get("/api/v1/risk/health")
    assert health.status_code == 200
    data = health.json()
    assert data["ready"] is True
    assert data["model_version"] == MODEL_VERSION
    assert all(data["artifact_status"].values())

    features = client.get("/api/v1/risk/features")
    assert features.status_code == 200
    assert features.json()["count"] == 32
    assert [row["name"] for row in features.json()["features"]] == list(FEATURE_DEFINITIONS)

    schema = client.get("/openapi.json").json()
    assert "/api/v1/risk/assess" in schema["paths"]
    assert "/api/v1/risk/insights" in schema["paths"]
    feature_schema = schema["components"]["schemas"]["ProviderRiskFeatures"]
    assert set(feature_schema["properties"]) == set(FEATURE_DEFINITIONS)
    assert feature_schema["additionalProperties"] is False


def test_model_insights_returns_only_saved_aggregate_metrics_and_global_shap(client):
    response = client.get("/api/v1/risk/insights")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["model_name"] == data["selected_model"] == "random_forest"
    assert data["train_provider_count"] == 4328
    assert data["validation_provider_count"] == 1082
    assert set(data["validation_metrics"]) == {"dummy_prior", "logistic_regression", "random_forest"}
    assert data["validation_metrics"]["random_forest"]["average_precision"] == pytest.approx(0.7868229)
    assert data["explainability_status"] == "available"
    assert data["global_shap"]["output_scale"] == "positive-class probability"
    assert data["global_shap"]["max_absolute_additivity_error"] < 1e-4
    assert len(data["global_shap"]["features"]) == 32
    assert "explanations" not in data
    assert "PRIVATE-" not in response.text
    assert "provider_case_" not in response.text
    assert "target_binary" not in response.text


def test_model_insights_keeps_metrics_when_global_shap_is_missing(client, monkeypatch, tmp_path):
    import shutil
    import backend.app.api.routes.risk as risk_routes

    model_dir = tmp_path / "models"
    model_dir.mkdir()
    shutil.copyfile("models/provider_risk_metrics.json", model_dir / "provider_risk_metrics.json")
    monkeypatch.setattr(risk_routes, "PROJECT_ROOT", tmp_path)
    response = client.get("/api/v1/risk/insights")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["validation_metrics"]
    assert body["explainability_status"] == "unavailable"
    assert body["global_shap"] is None
    assert "unavailable" in body["explainability_note"]


def test_assess_response_and_score_match_saved_pipeline(client):
    values = valid_features(0.5)
    response = client.post("/api/v1/risk/assess", json={"features": values})
    assert response.status_code == 200, response.text
    result = response.json()
    assert 0 <= result["risk_score"] <= 1
    assert result["score_type"] == "uncalibrated_model_score"
    assert result["model_version"] == MODEL_VERSION
    assert "PotentialFraud" in result["disclaimer"]
    service = client.app.state.risk_service
    direct = service.model.predict_proba(pd.DataFrame([[values[k] for k in service.feature_names]], columns=service.feature_names))[0, service.positive_class_index]
    assert math.isclose(result["risk_score"], direct, rel_tol=0.0, abs_tol=1e-12)


@pytest.mark.parametrize("mutate", ["missing", "extra", "string", "infinite", "boolean", "provider_id"])
def test_invalid_feature_requests_are_rejected_without_echoing_values(client, mutate):
    values = valid_features()
    if mutate == "missing":
        values.pop(next(iter(values)))
    elif mutate == "extra":
        values["unexpected"] = 1.0
    elif mutate == "string":
        values[next(iter(values))] = "sensitive-value"
    elif mutate == "infinite":
        values[next(iter(values))] = float("inf")
    elif mutate == "boolean":
        values[next(iter(values))] = True
    elif mutate == "provider_id":
        values["Provider"] = "PRIVATE-PROVIDER"
    if mutate == "infinite":
        response = client.post(
            "/api/v1/risk/assess",
            content=json.dumps({"features": values}, allow_nan=True),
            headers={"content-type": "application/json"},
        )
    else:
        response = client.post("/api/v1/risk/assess", json={"features": values})
    assert response.status_code == 422
    assert "sensitive-value" not in response.text
    assert "PRIVATE-PROVIDER" not in response.text


def test_batch_assessment_and_maximum_size(client):
    response = client.post("/api/v1/risk/assess/batch", json={"providers": [{"features": valid_features(0.1)}, {"features": valid_features(0.2)}]})
    assert response.status_code == 200
    assert response.json()["count"] == 2
    assert all(0 <= item["risk_score"] <= 1 for item in response.json()["assessments"])

    oversized = {"providers": [{"features": valid_features()}] * 101}
    rejected = client.post("/api/v1/risk/assess/batch", json=oversized)
    assert rejected.status_code == 422


def test_unavailable_model_health_and_inference(client):
    app.dependency_overrides[get_risk_service] = lambda: None
    try:
        health = client.get("/api/v1/risk/health")
        assert health.status_code == 200
        assert health.json()["ready"] is False
        assert health.json()["status"] == "unavailable"
        assert client.post("/api/v1/risk/assess", json={"features": valid_features()}).status_code == 503
        assert client.post("/api/v1/risk/assess/batch", json={"providers": [{"features": valid_features()}]}).status_code == 503
        assert client.get("/api/v1/risk/features").status_code == 503
        assert client.get("/api/v1/risk/insights").status_code == 503
    finally:
        app.dependency_overrides.pop(get_risk_service, None)


def test_missing_artifacts_fail_with_clear_startup_error(tmp_path):
    with pytest.raises(RiskArtifactError, match="artifacts are missing"):
        ProviderRiskService.load(tmp_path)
