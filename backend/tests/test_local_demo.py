import pandas as pd
import pytest
from fastapi.testclient import TestClient

from fastapi import FastAPI

from backend.app.api.routes.risk import ProviderRiskService, router as risk_router
from backend.app.core.config import settings
from backend.app.ml.contracts import FEATURE_DEFINITIONS
from backend.app.ml.local_demo import LocalProviderDemo


def _fixture_data():
    columns = list(FEATURE_DEFINITIONS)
    features = pd.DataFrame([[float(i + j) for j in range(len(columns))] for i in range(4)], columns=columns)
    labels = pd.DataFrame({"Provider": ["PRIVATE-A", "PRIVATE-B", "PRIVATE-C", "PRIVATE-D"], "target_binary": [0, 0, 1, 1]})
    config = {
        "random_state": 3,
        "validation_size": 0.5,
        "validation_provider_count": 2,
        "train_target_counts": {"0": 1, "1": 1},
        "validation_target_counts": {"0": 1, "1": 1},
    }
    return features, labels, config


def test_demo_keeps_only_sampled_features_and_ephemeral_aliases():
    features, labels, config = _fixture_data()
    demo = LocalProviderDemo(features, labels, list(FEATURE_DEFINITIONS), config)
    refs = demo.references()
    assert len(refs) == 2
    assert len({item["reference_id"] for item in refs}) == 2
    assert all(set(item) == {"reference_id"} for item in refs)
    assert not hasattr(demo, "labels")
    assert not hasattr(demo, "providers")
    vector = demo.features_for(refs[0]["reference_id"])
    assert vector is not None and list(vector) == list(FEATURE_DEFINITIONS)
    assert "Provider" not in vector and "target_binary" not in vector
    assert demo.features_for("demo-expired-reference") is None
    repeated = LocalProviderDemo(features, labels, list(FEATURE_DEFINITIONS), config)
    first_sample = sorted(tuple(row.values()) for row in demo._feature_vectors.values())
    repeated_sample = sorted(tuple(row.values()) for row in repeated._feature_vectors.values())
    assert first_sample == repeated_sample


def test_demo_rejects_duplicate_provider_labels():
    features, labels, config = _fixture_data()
    labels.loc[1, "Provider"] = labels.loc[0, "Provider"]
    with pytest.raises(ValueError, match="present and unique"):
        LocalProviderDemo(features, labels, list(FEATURE_DEFINITIONS), config)


def test_local_demo_routes_are_loopback_only_opt_in_and_hide_source_rows(monkeypatch):
    features, labels, config = _fixture_data()
    demo = LocalProviderDemo(features, labels, list(FEATURE_DEFINITIONS), config)
    test_app = FastAPI()
    test_app.include_router(risk_router, prefix="/api/v1")
    test_app.state.local_provider_demo = demo
    test_app.state.risk_service = ProviderRiskService.load()
    monkeypatch.setattr(settings, "LOCAL_PROVIDER_DEMO_ENABLED", True)
    monkeypatch.setattr(settings, "MEDILENS_ENV", "development")
    local_headers = {"host": "localhost:8000", "origin": "http://localhost:5173"}
    with TestClient(test_app, client=("127.0.0.1", 50000)) as client:
            listed = client.get("/api/v1/risk/demo/providers", headers=local_headers)
            assert listed.status_code == 200
            body = listed.json()
            assert body["count"] == 2
            assert "validation split" in body["split_disclosure"]
            assert "PRIVATE-" not in listed.text
            assert "target_binary" not in listed.text
            assert "features" not in listed.text
            reference = body["providers"][0]["reference_id"]
            assessed = client.post("/api/v1/risk/demo/assess", json={"reference_id": reference}, headers=local_headers)
            assert assessed.status_code == 200
            result = assessed.json()
            assert result["assessment_mode"] == "retrospective_validation_demo"
            assert 0 <= result["risk_score"] <= 1
            assert "PRIVATE-" not in assessed.text
            assert "target_binary" not in assessed.text
    with TestClient(test_app, client=("192.0.2.10", 50000)) as remote_client:
        assert remote_client.get("/api/v1/risk/demo/providers", headers=local_headers).status_code == 404
    with TestClient(test_app, client=("127.0.0.1", 50000)) as local_client:
        assert local_client.get("/api/v1/risk/demo/providers", headers={"host": "public.example"}).status_code == 404
        assert local_client.get(
            "/api/v1/risk/demo/providers",
            headers={**local_headers, "origin": "https://public.example"},
        ).status_code == 404
        assert local_client.get(
            "/api/v1/risk/demo/providers",
            headers={**local_headers, "x-forwarded-for": "203.0.113.25"},
        ).status_code == 404
    monkeypatch.setattr(settings, "LOCAL_PROVIDER_DEMO_ENABLED", False)
    with TestClient(test_app, client=("127.0.0.1", 50000)) as disabled_client:
        assert disabled_client.get("/api/v1/risk/demo/providers", headers=local_headers).status_code == 404
