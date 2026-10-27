"""Reproducible provider-level baseline risk modeling and validation."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from backend.app.ml.integrity import (
    ArtifactIntegrityError,
    PAIR_METADATA_ATTR,
    validate_pair_frames,
    validate_processed_artifacts,
)


DEFAULT_SEED = 42
DEFAULT_VALIDATION_SIZE = 0.2
FORBIDDEN_FEATURE_NAMES = {
    "provider", "providerid", "beneid", "beneficiaryid", "claimid",
    "potentialfraud", "target", "target_binary", "fraud", "fraud_label",
}
LIMITATIONS = [
    "PotentialFraud is a provider-level dataset label, not verified fraud.",
    "Validation is a single stratified holdout and does not establish real-world performance.",
    "Retrospective aggregated features may introduce temporal leakage because their observation window is not separated from the label period.",
    "No test-set evaluation, probability calibration, threshold optimization, or deployment validation was performed.",
]


class ProviderRiskModelError(ValueError):
    """Raised when provider-level modeling inputs violate the training contract."""


def validate_model_inputs(features: pd.DataFrame, labels: pd.DataFrame) -> list[str]:
    """Check deterministic positional alignment and prevent target/ID leakage."""
    if not isinstance(features, pd.DataFrame) or not isinstance(labels, pd.DataFrame):
        raise ProviderRiskModelError("Features and labels must be pandas DataFrames.")
    if features.empty or labels.empty or len(features) != len(labels):
        raise ProviderRiskModelError("Feature and label row counts must match and be non-empty.")
    if not {"Provider", "target_binary"}.issubset(labels.columns):
        raise ProviderRiskModelError("Labels must contain Provider and target_binary columns.")
    providers = labels["Provider"]
    if providers.isna().any() or providers.duplicated().any():
        raise ProviderRiskModelError("Provider labels must be present and unique.")
    if not providers.astype(str).is_monotonic_increasing:
        raise ProviderRiskModelError("Labels must be sorted by Provider to match the feature row order.")
    if labels["target_binary"].isna().any() or not labels["target_binary"].isin([0, 1]).all():
        raise ProviderRiskModelError("target_binary must contain only non-null values 0 and 1.")
    if features.columns.has_duplicates:
        raise ProviderRiskModelError("Feature names must be unique.")
    if len(features.columns) == 0:
        raise ProviderRiskModelError("At least one feature is required.")
    forbidden = [
        name for name in features.columns
        if str(name).casefold() in FORBIDDEN_FEATURE_NAMES
        or any(token in str(name).casefold() for token in ("potentialfraud", "fraud", "target"))
        or any(token in str(name).casefold() for token in ("provider_id", "beneficiary_id", "claim_id", "fraud_label"))
    ]
    if forbidden:
        raise ProviderRiskModelError("Feature columns include identifiers or target-like fields.")
    if any(not pd.api.types.is_numeric_dtype(dtype) for dtype in features.dtypes):
        raise ProviderRiskModelError("All model features must be numeric.")
    values = features.to_numpy(dtype=np.float64, copy=False)
    if np.isinf(values).any():
        raise ProviderRiskModelError("Features cannot contain infinite values.")
    y = labels["target_binary"].astype("int8")
    if y.nunique() != 2 or y.value_counts().min() < 2:
        raise ProviderRiskModelError("Both target classes need at least two providers.")
    return [str(column) for column in features.columns]


def _pipeline(estimator: Any, *, scale: bool = False) -> Pipeline:
    steps: list[tuple[str, Any]] = [("imputer", SimpleImputer(strategy="median"))]
    if scale:
        steps.append(("scaler", StandardScaler()))
    steps.append(("classifier", estimator))
    return Pipeline(steps)


def _metrics(estimator: Pipeline, x_val: pd.DataFrame, y_val: pd.Series) -> Dict[str, Any]:
    prediction = estimator.predict(x_val)
    probability = estimator.predict_proba(x_val)[:, 1]
    precision_curve, recall_curve, thresholds = precision_recall_curve(y_val, probability)
    return {
        "precision": float(precision_score(y_val, prediction, zero_division=0)),
        "recall": float(recall_score(y_val, prediction, zero_division=0)),
        "f1": float(f1_score(y_val, prediction, zero_division=0)),
        "average_precision": float(average_precision_score(y_val, probability)),
        "roc_auc": float(roc_auc_score(y_val, probability)),
        "confusion_matrix_labels_0_1": confusion_matrix(y_val, prediction, labels=[0, 1]).tolist(),
        "precision_recall_curve": {
            "precision": precision_curve.tolist(),
            "recall": recall_curve.tolist(),
            "thresholds": thresholds.tolist(),
        },
    }


def train_provider_risk_model(
    features: pd.DataFrame,
    labels: pd.DataFrame,
    artifact_dir: Optional[Path] = None,
    *,
    random_state: int = DEFAULT_SEED,
    validation_size: float = DEFAULT_VALIDATION_SIZE,
    require_integrity: bool = True,
) -> Dict[str, Any]:
    """Compare dummy, balanced logistic regression, and balanced random forest.

    The split occurs before fitting pipelines, so imputers and scaling learn from
    training providers only. Validation Average Precision selects the artifact.
    """
    feature_names = validate_model_inputs(features, labels)
    feature_contract = features.attrs.get(PAIR_METADATA_ATTR)
    label_contract = labels.attrs.get(PAIR_METADATA_ATTR)
    if require_integrity:
        if feature_contract is None or label_contract is None:
            raise ProviderRiskModelError("Training requires features and labels loaded or generated under a validated artifact contract.")
        if feature_contract != label_contract:
            raise ProviderRiskModelError("Feature and label generation contracts do not match.")
        try:
            validate_pair_frames(features, labels, feature_contract)
        except ArtifactIntegrityError as exc:
            raise ProviderRiskModelError("Feature-label integrity validation failed before training.") from exc
    elif feature_contract is not None or label_contract is not None:
        if feature_contract != label_contract:
            raise ProviderRiskModelError("Feature and label generation contracts do not match.")
        try:
            validate_pair_frames(features, labels, feature_contract)
        except ArtifactIntegrityError as exc:
            raise ProviderRiskModelError("Feature-label integrity validation failed before training.") from exc
    if not 0 < validation_size < 1:
        raise ProviderRiskModelError("validation_size must be between zero and one.")
    x_train, x_val, y_train, y_val = train_test_split(
        features.loc[:, feature_names], labels["target_binary"].astype("int8"),
        test_size=validation_size, random_state=random_state, stratify=labels["target_binary"],
    )
    pipelines = {
        "dummy_prior": _pipeline(DummyClassifier(strategy="prior")),
        "logistic_regression": _pipeline(
            LogisticRegression(class_weight="balanced", max_iter=2000, random_state=random_state),
            scale=True,
        ),
        "random_forest": _pipeline(
            RandomForestClassifier(
                n_estimators=300, class_weight="balanced_subsample", random_state=random_state,
                n_jobs=1, min_samples_leaf=2,
            )
        ),
    }
    results: Dict[str, Dict[str, Any]] = {}
    for name, pipeline in pipelines.items():
        pipeline.fit(x_train, y_train)
        results[name] = _metrics(pipeline, x_val, y_val)
    selected_name = max(results, key=lambda name: results[name]["average_precision"])
    configuration = {
        "target": "provider-level target_binary derived from PotentialFraud; not verified fraud",
        "split": "single stratified train/validation holdout; no test set",
        "validation_size": validation_size,
        "random_state": random_state,
        "train_provider_count": int(len(x_train)),
        "validation_provider_count": int(len(x_val)),
        "train_target_counts": {str(k): int(v) for k, v in y_train.value_counts().sort_index().items()},
        "validation_target_counts": {str(k): int(v) for k, v in y_val.value_counts().sort_index().items()},
        "feature_count": len(feature_names),
        "data_generation_id": feature_contract.get("generation_id") if feature_contract else None,
        "feature_schema_fingerprint": feature_contract.get("feature_schema_fingerprint") if feature_contract else None,
        "feature_preprocessing": "median imputation in sklearn Pipeline; StandardScaler for logistic regression; fit on training split only",
        "model_selection_metric": "validation average_precision",
        "models": {
            "dummy_prior": {"strategy": "prior"},
            "logistic_regression": {"class_weight": "balanced", "max_iter": 2000},
            "random_forest": {"class_weight": "balanced_subsample", "n_estimators": 300, "min_samples_leaf": 2, "n_jobs": 1},
        },
        "limitations": LIMITATIONS,
    }
    output_dir = Path(artifact_dir) if artifact_dir else Path(__file__).resolve().parents[3] / "models"
    output_dir.mkdir(parents=True, exist_ok=True)
    selected_model_path = output_dir / "provider_risk_model.joblib"
    metrics_path = output_dir / "provider_risk_metrics.json"
    config_path = output_dir / "provider_risk_config.json"
    features_path = output_dir / "provider_risk_features.json"
    joblib.dump({"model": pipelines[selected_name], "model_name": selected_name, "feature_names": feature_names, "configuration": configuration}, selected_model_path)
    metrics_payload = {
        "selection_metric": "validation average_precision",
        "selected_model": selected_name,
        "split": {"random_state": random_state, "validation_size": validation_size, "train_providers": len(x_train), "validation_providers": len(x_val)},
        "validation_metrics": results,
        "limitations": LIMITATIONS,
    }
    for path, payload in ((metrics_path, metrics_payload), (config_path, configuration), (features_path, {"feature_names": feature_names})):
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return {
        "model_name": selected_name,
        "metrics": results,
        "selected_metrics": results[selected_name],
        "configuration": configuration,
        "artifacts": {"model": selected_model_path, "metrics": metrics_path, "configuration": config_path, "features": features_path},
    }


def load_provider_risk_model(path: Path) -> Dict[str, Any]:
    """Load a saved bundle and verify its inference feature contract."""
    bundle = joblib.load(path)
    required = {"model", "model_name", "feature_names", "configuration"}
    if not isinstance(bundle, dict) or not required.issubset(bundle):
        raise ProviderRiskModelError("Saved model artifact does not satisfy the provider model contract.")
    return bundle


def load_processed_provider_data(processed_dir: Optional[Path] = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
    root = Path(processed_dir) if processed_dir else Path(__file__).resolve().parents[3] / "data" / "processed"
    try:
        features, labels, manifest = validate_processed_artifacts(root)
    except ArtifactIntegrityError as exc:
        raise ProviderRiskModelError(str(exc)) from exc
    features.attrs[PAIR_METADATA_ATTR] = {
        key: manifest[key] for key in (
            "schema_version", "generation_id", "row_count", "provider_key_fingerprint",
            "feature_names", "feature_schema_fingerprint", "feature_matrix_fingerprint",
            "target_rows_fingerprint", "target_metadata",
        )
    }
    labels.attrs[PAIR_METADATA_ATTR] = dict(features.attrs[PAIR_METADATA_ATTR])
    return features, labels
