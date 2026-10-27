"""Ephemeral, local-only retrospective provider demo using validation rows."""
from __future__ import annotations

import secrets
from typing import Any

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split


DEMO_SAMPLE_SIZE = 20
DEMO_DISCLOSURE = (
    "Retrospective dataset demonstration from the model validation split. "
    "This split was used for model selection and is not an independent test set. "
    "The PotentialFraud label is not verified fraud; this is not a live claims investigation."
)


class LocalProviderDemo:
    """Keep validation feature vectors in memory behind random per-process aliases."""

    def __init__(self, features: pd.DataFrame, labels: pd.DataFrame, feature_names: list[str], config: dict[str, Any]):
        if list(features.columns) != feature_names:
            raise ValueError("Demo feature schema does not match the saved model.")
        if any(not pd.api.types.is_numeric_dtype(dtype) for dtype in features.dtypes):
            raise ValueError("Demo features must be numeric.")
        if np.isinf(features.to_numpy(dtype=np.float64, copy=False)).any():
            raise ValueError("Demo features cannot contain infinite values.")
        if len(features) != len(labels) or not {"Provider", "target_binary"}.issubset(labels.columns):
            raise ValueError("Demo feature and label rows cannot be aligned safely.")
        if labels["Provider"].isna().any() or labels["Provider"].duplicated().any():
            raise ValueError("Demo provider labels must be present and unique.")
        if not labels["Provider"].astype(str).is_monotonic_increasing:
            raise ValueError("Demo rows must preserve the validated provider sort order.")
        y = labels["target_binary"]
        if y.isna().any() or not y.isin([0, 1]).all():
            raise ValueError("Demo labels must contain only binary target values.")
        actual_counts = {str(int(key)): int(value) for key, value in y.value_counts().sort_index().items()}
        train_counts = config.get("train_target_counts", {})
        validation_counts = config.get("validation_target_counts", {})
        expected_counts = {
            str(key): int(train_counts.get(str(key), train_counts.get(key, 0)))
            + int(validation_counts.get(str(key), validation_counts.get(key, 0)))
            for key in {str(value) for value in y.unique()}
        }
        if actual_counts != expected_counts:
            raise ValueError("Processed labels do not match saved split class counts.")

        seed = int(config["random_state"])
        validation_size = float(config["validation_size"])
        indices = np.arange(len(labels))
        _, validation_indices = train_test_split(
            indices,
            test_size=validation_size,
            random_state=seed,
            stratify=y.astype("int8"),
        )
        expected_validation = int(config["validation_provider_count"])
        if len(validation_indices) != expected_validation:
            raise ValueError("Reconstructed validation split does not match saved configuration.")
        expected_validation_counts = {str(key): int(value) for key, value in config.get("validation_target_counts", {}).items()}
        actual_validation_counts = {str(int(key)): int(value) for key, value in y.iloc[validation_indices].value_counts().sort_index().items()}
        if actual_validation_counts != expected_validation_counts:
            raise ValueError("Reconstructed validation class counts do not match saved configuration.")
        sample_size = min(DEMO_SAMPLE_SIZE, len(validation_indices))
        sample_indices = np.random.default_rng(seed + 1).choice(validation_indices, size=sample_size, replace=False)

        # Provider IDs and targets are deliberately not retained by this object.
        selected = features.iloc[sample_indices].loc[:, feature_names]
        self._feature_vectors = {
            f"demo-{secrets.token_urlsafe(12)}": {name: float(value) for name, value in row.items()}
            for row in selected.to_dict(orient="records")
        }

    def references(self) -> list[dict[str, str]]:
        return [{"reference_id": alias} for alias in self._feature_vectors]

    def features_for(self, reference_id: str) -> dict[str, float] | None:
        values = self._feature_vectors.get(reference_id)
        return dict(values) if values is not None else None
