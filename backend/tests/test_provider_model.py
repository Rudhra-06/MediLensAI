import json

import numpy as np
import pandas as pd
import pytest

from backend.app.ml.model import (
    ProviderRiskModelError,
    load_provider_risk_model,
    train_provider_risk_model,
    validate_model_inputs,
)
from backend.app.ml.integrity import attach_pair_contract


@pytest.fixture
def model_data():
    rng = np.random.default_rng(17)
    count = 100
    y = np.array([0] * 80 + [1] * 20)
    features = pd.DataFrame({
        "claim_count": rng.normal(size=count) + y * 1.5,
        "reimbursement_mean": rng.normal(size=count) + y * 0.8,
    })
    labels = pd.DataFrame({"Provider": [f"P{i:03d}" for i in range(count)], "target_binary": y})
    features.loc[[3, 14], "claim_count"] = np.nan
    return features, labels


def test_alignment_and_leakage_contract(model_data):
    x, y = model_data
    assert validate_model_inputs(x, y) == ["claim_count", "reimbursement_mean"]
    bad_labels = y.iloc[::-1].reset_index(drop=True)
    with pytest.raises(ProviderRiskModelError, match="sorted by Provider"):
        validate_model_inputs(x, bad_labels)
    leaking = x.assign(PotentialFraud=0)
    with pytest.raises(ProviderRiskModelError, match="identifiers or target-like"):
        validate_model_inputs(leaking, y)
    leaking = x.assign(fraud_indicator=0)
    with pytest.raises(ProviderRiskModelError, match="identifiers or target-like"):
        validate_model_inputs(leaking, y)


def test_stratified_training_is_reproducible_and_saves_loadable_artifacts(model_data, tmp_path):
    x, y = model_data
    first = train_provider_risk_model(x, y, tmp_path / "first", require_integrity=False)
    second = train_provider_risk_model(x, y, tmp_path / "second", require_integrity=False)
    assert set(first["metrics"]) == {"dummy_prior", "logistic_regression", "random_forest"}
    assert first["model_name"] == second["model_name"]
    assert first["metrics"] == second["metrics"]
    assert first["configuration"]["train_provider_count"] == 80
    assert first["configuration"]["validation_provider_count"] == 20
    assert all(path.is_file() for path in first["artifacts"].values())
    assert json.loads(first["artifacts"]["metrics"].read_text())["selected_model"] == first["model_name"]
    bundle = load_provider_risk_model(first["artifacts"]["model"])
    assert bundle["model_name"] == first["model_name"]
    assert bundle["feature_names"] == list(x.columns)
    assert bundle["model"].predict_proba(x.iloc[:3]).shape == (3, 2)


def test_duplicate_provider_rows_are_rejected(model_data):
    x, y = model_data
    y.loc[1, "Provider"] = y.loc[0, "Provider"]
    with pytest.raises(ProviderRiskModelError, match="present and unique"):
        validate_model_inputs(x, y)


def test_training_requires_matching_unmodified_pair_contract(model_data, tmp_path):
    x, y = model_data
    attach_pair_contract(x, y)
    first = train_provider_risk_model(x, y, tmp_path / "valid", require_integrity=True)
    assert first["configuration"]["data_generation_id"] == x.attrs["medilens_pair_contract"]["generation_id"]

    changed = x.iloc[::-1].reset_index(drop=True)
    changed.attrs = x.attrs.copy()
    with pytest.raises(ProviderRiskModelError, match="integrity validation failed"):
        train_provider_risk_model(changed, y, tmp_path / "changed", require_integrity=True)
