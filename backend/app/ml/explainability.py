"""SHAP explanations for the saved provider-level Random Forest artifact."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd
import shap
from sklearn.ensemble import RandomForestClassifier

from backend.app.ml.model import (
    load_processed_provider_data,
    load_provider_risk_model,
    validate_model_inputs,
)


class ExplainabilityError(ValueError):
    """Raised when model, SHAP values, or feature dimensions are incompatible."""


def _positive_class_values(raw_values: Any, sample_count: int, feature_count: int, class_index: int) -> np.ndarray:
    """Normalize legacy SHAP list and current class-axis array formats."""
    if isinstance(raw_values, list):
        if class_index >= len(raw_values):
            raise ExplainabilityError("SHAP output does not contain the positive class.")
        result = np.asarray(raw_values[class_index], dtype=np.float64)
    else:
        values = np.asarray(raw_values, dtype=np.float64)
        if values.ndim == 2 and values.shape == (sample_count, feature_count):
            raise ExplainabilityError("SHAP returned a single output without class identity; refusing to guess its class.")
        if values.ndim != 3:
            raise ExplainabilityError("SHAP values must have two sample/feature axes and one class axis.")
        if values.shape[0] == sample_count and values.shape[1] == feature_count and values.shape[2] > class_index:
            result = values[:, :, class_index]  # current SHAP: samples, features, classes
        elif values.shape[0] > class_index and values.shape[1] == sample_count and values.shape[2] == feature_count:
            result = values[class_index, :, :]  # alternate: classes, samples, features
        elif values.shape[0] == sample_count and values.shape[1] > class_index and values.shape[2] == feature_count:
            result = values[:, class_index, :]  # alternate: samples, classes, features
        else:
            raise ExplainabilityError("SHAP output shape does not match samples/features/classes.")
        result = np.asarray(result, dtype=np.float64)
    if result.shape != (sample_count, feature_count):
        raise ExplainabilityError("Positive-class SHAP dimensions do not match sample and feature dimensions.")
    if not np.isfinite(result).all():
        raise ExplainabilityError("SHAP values contain non-finite values.")
    return result


def _positive_class_baseline(expected_value: Any, class_index: int, class_count: int) -> float:
    values = np.asarray(expected_value, dtype=np.float64).reshape(-1)
    if values.size == 1:
        raise ExplainabilityError("SHAP baseline has no explicit class identity; refusing to guess its class.")
    if values.size != class_count or class_index >= values.size:
        raise ExplainabilityError("SHAP baseline dimensions do not match the classifier classes.")
    baseline = float(values[class_index])
    if not np.isfinite(baseline):
        raise ExplainabilityError("SHAP baseline is not finite.")
    return baseline


def generate_provider_explanations(
    features: pd.DataFrame,
    labels: pd.DataFrame,
    artifact_path: Path,
    output_dir: Optional[Path] = None,
    *,
    random_state: int = 42,
    background_size: int = 64,
    explain_size: int = 256,
    local_size: int = 12,
) -> dict[str, Any]:
    """Explain the saved Random Forest in positive-class probability space.

    Only deterministic, anonymous examples and attribution values are written;
    Provider identifiers, labels, and raw feature values are never exported.
    """
    bundle = load_provider_risk_model(Path(artifact_path))
    model = bundle["model"]
    if bundle["model_name"] != "random_forest" or not isinstance(model.named_steps.get("classifier"), RandomForestClassifier):
        raise ExplainabilityError("Saved artifact is not the expected Random Forest pipeline; model behavior was not changed.")
    feature_names = list(bundle["feature_names"])
    input_feature_names = validate_model_inputs(features, labels)
    if input_feature_names != feature_names:
        raise ExplainabilityError("Processed feature names or order do not match the saved model artifact.")
    classifier = model.named_steps["classifier"]
    classes = np.asarray(classifier.classes_)
    positive_matches = np.flatnonzero(classes == 1)
    if len(positive_matches) != 1:
        raise ExplainabilityError("Saved classifier has no unique PotentialFraud=1 class.")
    positive_index = int(positive_matches[0])

    count = len(features)
    if min(background_size, explain_size, local_size) <= 0:
        raise ExplainabilityError("Background and explanation sample sizes must be positive.")
    background_n = min(background_size, count)
    explain_n = min(explain_size, count)
    local_n = min(local_size, explain_n)
    background = features.sample(n=background_n, random_state=random_state).loc[:, feature_names]
    explained = features.sample(n=explain_n, random_state=random_state + 1).loc[:, feature_names]

    preprocessing = model[:-1]
    background_array = np.asarray(preprocessing.transform(background), dtype=np.float64)
    explained_array = np.asarray(preprocessing.transform(explained), dtype=np.float64)
    if background_array.ndim != 2 or explained_array.ndim != 2 or background_array.shape[1] != len(feature_names) or explained_array.shape[1] != len(feature_names):
        raise ExplainabilityError("Preprocessing changed feature dimensions or ordering relative to the saved artifact.")
    if not np.isfinite(background_array).all() or not np.isfinite(explained_array).all():
        raise ExplainabilityError("Preprocessed model inputs contain non-finite values.")

    explainer = shap.TreeExplainer(
        classifier,
        data=background_array,
        feature_perturbation="interventional",
        model_output="probability",
    )
    try:
        raw_values = explainer.shap_values(explained_array, check_additivity=False)
    except TypeError:  # Older SHAP versions do not expose this keyword.
        raw_values = explainer.shap_values(explained_array)
    contributions = _positive_class_values(raw_values, explain_n, len(feature_names), positive_index)
    baseline = _positive_class_baseline(explainer.expected_value, positive_index, len(classes))
    probabilities = np.asarray(classifier.predict_proba(explained_array)[:, positive_index], dtype=np.float64)
    reconstructed = baseline + contributions.sum(axis=1)
    max_error = float(np.max(np.abs(reconstructed - probabilities)))
    if not np.isfinite(probabilities).all() or max_error > 1e-4:
        raise ExplainabilityError(
            "SHAP additivity check failed for positive-class probabilities; output scale could not be verified."
        )

    mean_signed = contributions.mean(axis=0)
    mean_absolute = np.abs(contributions).mean(axis=0)
    order = np.argsort(-mean_absolute, kind="stable")
    global_rows = [
        {
            "feature": feature_names[i],
            "mean_absolute_contribution": float(mean_absolute[i]),
            "mean_signed_contribution": float(mean_signed[i]),
            "direction": "increases model output on average" if mean_signed[i] > 0 else "decreases model output on average" if mean_signed[i] < 0 else "zero average signed contribution",
            "output_scale": "positive-class probability",
        }
        for i in order
    ]

    # Local examples use fixed row positions, not potentially identifying Provider keys.
    local_rows = []
    for row_index in range(local_n):
        local_values = contributions[row_index]
        indices = np.argsort(-np.abs(local_values), kind="stable")
        local_rows.append({
            "example_id": f"provider_case_{row_index + 1:03d}",
            "output_class": "PotentialFraud=1 (provider-level label; not verified fraud)",
            "output_scale": "positive-class probability",
            "base_probability": baseline,
            "predicted_probability": float(probabilities[row_index]),
            "reconstructed_probability": float(reconstructed[row_index]),
            "contributions": [
                {
                    "feature": feature_names[i],
                    "contribution": float(local_values[i]),
                    "direction": "increases" if local_values[i] > 0 else "decreases" if local_values[i] < 0 else "no change",
                }
                for i in indices
            ],
        })

    common = {
        "model": bundle["model_name"],
        "shap_version": shap.__version__,
        "output_class": "PotentialFraud=1 (provider-level label; not verified fraud)",
        "output_scale": "positive-class probability",
        "output_scale_verification": {
            "method": "base probability plus SHAP contributions compared with saved pipeline positive-class predict_proba",
            "max_absolute_additivity_error": max_error,
            "tolerance": 1e-4,
        },
        "feature_count": len(feature_names),
        "background_sample_count": background_n,
        "explanation_sample_count": explain_n,
        "random_state": random_state,
        "interpretation_limit": "Contributions describe this model's output; they are not proof of fraud or causation.",
    }
    global_payload = {**common, "importance_method": "mean absolute SHAP contribution; mean signed contribution indicates average direction", "features": global_rows}
    local_payload = {**common, "identifier_policy": "Anonymous sample labels only; raw Provider IDs, labels, and feature values omitted.", "explanations": local_rows}

    destination = Path(output_dir) if output_dir else Path(artifact_path).resolve().parent
    destination.mkdir(parents=True, exist_ok=True)
    global_path = destination / "shap_global_importance.json"
    local_path = destination / "provider_explanations.json"
    global_path.write_text(json.dumps(global_payload, indent=2, allow_nan=False), encoding="utf-8")
    local_path.write_text(json.dumps(local_payload, indent=2, allow_nan=False), encoding="utf-8")
    return {"global": global_payload, "local": local_payload, "artifacts": {"global": global_path, "local": local_path}}


def generate_explanations_from_saved_data(
    project_root: Optional[Path] = None,
    *,
    random_state: int = 42,
    background_size: int = 64,
    explain_size: int = 256,
    local_size: int = 12,
) -> dict[str, Any]:
    root = Path(project_root) if project_root else Path(__file__).resolve().parents[3]
    features, labels = load_processed_provider_data(root / "data" / "processed")
    return generate_provider_explanations(
        features, labels, root / "models" / "provider_risk_model.joblib", root / "models",
        random_state=random_state, background_size=background_size,
        explain_size=explain_size, local_size=local_size,
    )
