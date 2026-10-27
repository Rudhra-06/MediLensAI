import json

import joblib
import numpy as np
import pandas as pd
import pytest
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline

from backend.app.ml.explainability import (
    ExplainabilityError,
    _positive_class_values,
    generate_provider_explanations,
)


def test_shap_class_axis_formats_are_normalized_and_validated():
    n, f, c = 3, 4, 2
    canonical = np.arange(n * f * c, dtype=float).reshape(n, f, c)
    expected = canonical[:, :, 1]
    np.testing.assert_array_equal(_positive_class_values(canonical, n, f, 1), expected)
    np.testing.assert_array_equal(_positive_class_values([canonical[:, :, 0], expected], n, f, 1), expected)
    np.testing.assert_array_equal(_positive_class_values(canonical.transpose(2, 0, 1), n, f, 1), expected)
    np.testing.assert_array_equal(_positive_class_values(canonical.transpose(0, 2, 1), n, f, 1), expected)
    with pytest.raises(ExplainabilityError, match="does not match"):
        _positive_class_values(np.zeros((n, f + 1, c)), n, f, 1)


def test_provider_explanations_align_features_and_write_anonymous_artifacts(tmp_path):
    rng = np.random.default_rng(9)
    y = np.array([0] * 40 + [1] * 20)
    x = pd.DataFrame({"feature_a": rng.normal(size=60) + y, "feature_b": rng.normal(size=60)})
    labels = pd.DataFrame({"Provider": [f"PRIVATE_PROVIDER_{i:03}" for i in range(60)], "target_binary": y})
    pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("classifier", RandomForestClassifier(n_estimators=20, random_state=4, n_jobs=1)),
    ]).fit(x, y)
    model_path = tmp_path / "saved_model.joblib"
    joblib.dump({"model": pipeline, "model_name": "random_forest", "feature_names": list(x.columns), "configuration": {}}, model_path)

    output = generate_provider_explanations(
        x, labels, model_path, tmp_path / "out", random_state=5,
        background_size=10, explain_size=12, local_size=3,
    )
    global_data, local_data = output["global"], output["local"]
    assert global_data["feature_count"] == len(x.columns)
    assert len(global_data["features"]) == len(x.columns)
    assert len(local_data["explanations"]) == 3
    assert global_data["output_class"].startswith("PotentialFraud=1")
    assert global_data["output_scale"] == "positive-class probability"
    assert global_data["output_scale_verification"]["max_absolute_additivity_error"] < 1e-4
    assert all(np.isfinite(row["mean_absolute_contribution"]) for row in global_data["features"])
    assert all(len(row["contributions"]) == len(x.columns) for row in local_data["explanations"])
    assert all(np.isfinite(item["contribution"]) for row in local_data["explanations"] for item in row["contributions"])
    assert output["artifacts"]["global"].is_file() and output["artifacts"]["local"].is_file()
    saved_local = json.loads(output["artifacts"]["local"].read_text())
    assert "PRIVATE_PROVIDER_" not in json.dumps(saved_local)
    assert "feature values omitted" in saved_local["identifier_policy"]


def test_saved_model_feature_mismatch_is_rejected(tmp_path):
    x = pd.DataFrame({"feature_a": [0., 1., 2., 3.], "feature_b": [1., 0., 1., 0.]})
    y = np.array([0, 0, 1, 1])
    labels = pd.DataFrame({"Provider": ["P1", "P2", "P3", "P4"], "target_binary": y})
    pipe = Pipeline([("imputer", SimpleImputer()), ("classifier", RandomForestClassifier(n_estimators=2, random_state=1))]).fit(x, y)
    path = tmp_path / "model.joblib"
    joblib.dump({"model": pipe, "model_name": "random_forest", "feature_names": ["feature_b", "feature_a"], "configuration": {}}, path)
    with pytest.raises(ExplainabilityError, match="do not match"):
        generate_provider_explanations(x, labels, path, tmp_path / "out", background_size=2, explain_size=2, local_size=1)
