"""Fail-closed integrity contract for paired provider feature and label artifacts."""
from __future__ import annotations

import hashlib
import json
import math
import os
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


MANIFEST_FILENAME = "artifact_manifest.json"
MANIFEST_SCHEMA_VERSION = 1
FEATURE_FILE = "provider_features.parquet"
LABEL_FILE = "target_labels.parquet"
PAIR_METADATA_ATTR = "medilens_pair_contract"
ARTIFACT_NAMES = (
    FEATURE_FILE,
    "provider_features.csv",
    LABEL_FILE,
    "target_labels.csv",
    "data_quality_report.json",
    "feature_dictionary.json",
)


class ArtifactIntegrityError(ValueError):
    """Raised when provider features and labels cannot be proven to be paired."""


def _canonical_hash(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _key_fingerprint(keys: pd.Series) -> str:
    digest = hashlib.sha256()
    for key in keys:
        if pd.isna(key):
            raise ArtifactIntegrityError("Provider keys must not be null.")
        raw = str(key).encode("utf-8")
        digest.update(len(raw).to_bytes(8, "big"))
        digest.update(raw)
    return digest.hexdigest()


def _feature_matrix_fingerprint(features: pd.DataFrame) -> str:
    digest = hashlib.sha256()
    for row in features.itertuples(index=False, name=None):
        for value in row:
            number = float(value)
            if math.isinf(number):
                raise ArtifactIntegrityError("Features contain infinite values.")
            raw = ("null" if math.isnan(number) else number.hex()).encode("ascii")
            digest.update(len(raw).to_bytes(4, "big"))
            digest.update(raw)
    return digest.hexdigest()


def _target_fingerprint(labels: pd.DataFrame) -> str:
    digest = hashlib.sha256()
    for key, label in labels[["Provider", "target_binary"]].itertuples(index=False, name=None):
        raw = str(key).encode("utf-8")
        digest.update(len(raw).to_bytes(8, "big"))
        digest.update(raw)
        digest.update(bytes([int(label)]))
    return digest.hexdigest()


def pair_contract(features: pd.DataFrame, labels: pd.DataFrame, generation_id: str | None = None) -> dict[str, Any]:
    if len(features) == 0 or len(features) != len(labels):
        raise ArtifactIntegrityError("Feature and label row counts must be equal and non-zero.")
    if labels.columns.tolist() != ["Provider", "target_binary"]:
        raise ArtifactIntegrityError("Label schema must be exactly Provider and target_binary.")
    if labels["Provider"].isna().any() or labels["Provider"].duplicated().any():
        raise ArtifactIntegrityError("Provider keys must be present and unique in labels.")
    if not labels["Provider"].astype(str).is_monotonic_increasing:
        raise ArtifactIntegrityError("Provider labels must be in deterministic sorted order.")
    if labels["target_binary"].isna().any() or not labels["target_binary"].isin([0, 1]).all():
        raise ArtifactIntegrityError("Target values must be non-null binary labels.")
    if features.columns.has_duplicates or any(not pd.api.types.is_numeric_dtype(dtype) for dtype in features.dtypes):
        raise ArtifactIntegrityError("Feature schema must contain unique numeric columns.")
    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "generation_id": generation_id or str(uuid.uuid4()),
        "row_count": len(features),
        "provider_key_fingerprint": _key_fingerprint(labels["Provider"]),
        "feature_names": [str(name) for name in features.columns],
        "feature_schema_fingerprint": _canonical_hash([
            {"name": str(name), "dtype": str(dtype)} for name, dtype in features.dtypes.items()
        ]),
        "feature_matrix_fingerprint": _feature_matrix_fingerprint(features),
        "target_rows_fingerprint": _target_fingerprint(labels),
        "target_metadata": {
            "column": "target_binary",
            "source": "PotentialFraud",
            "unit": "provider",
            "encoding": {"0": "No", "1": "Yes"},
            "class_counts": {str(int(k)): int(v) for k, v in labels["target_binary"].value_counts().sort_index().items()},
        },
    }


def attach_pair_contract(features: pd.DataFrame, labels: pd.DataFrame) -> dict[str, Any]:
    contract = pair_contract(features, labels)
    features.attrs[PAIR_METADATA_ATTR] = dict(contract)
    labels.attrs[PAIR_METADATA_ATTR] = dict(contract)
    return contract


def validate_pair_frames(features: pd.DataFrame, labels: pd.DataFrame, expected: dict[str, Any] | None = None) -> dict[str, Any]:
    actual = pair_contract(features, labels, (expected or {}).get("generation_id"))
    if expected is not None:
        for key in actual:
            if actual[key] != expected.get(key):
                raise ArtifactIntegrityError(f"Feature-label integrity mismatch for {key}.")
    return actual


def build_manifest(directory: Path, features: pd.DataFrame, labels: pd.DataFrame, generation_id: str | None = None) -> dict[str, Any]:
    contract = pair_contract(features, labels, generation_id)
    files: dict[str, dict[str, Any]] = {}
    for name in ARTIFACT_NAMES:
        path = directory / name
        if not path.is_file():
            raise ArtifactIntegrityError(f"Required processed artifact is missing: {name}.")
        digest = hashlib.sha256()
        size = 0
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
                size += len(block)
        files[name] = {"sha256": digest.hexdigest(), "size_bytes": size}
    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "generation_id": contract["generation_id"],
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        **{key: value for key, value in contract.items() if key != "schema_version"},
        "artifacts": files,
    }


def write_manifest_atomic(path: Path, manifest: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=".artifact-manifest-", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(manifest, stream, indent=2, sort_keys=True)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_name, path)
    except Exception:
        try:
            os.unlink(temporary_name)
        except OSError:
            pass
        raise


def validate_processed_artifacts(directory: Path, expected_feature_names: list[str] | None = None) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    manifest_path = directory / MANIFEST_FILENAME
    if not manifest_path.is_file():
        raise ArtifactIntegrityError("Processed artifact manifest is missing; regenerate or migrate the paired artifacts.")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ArtifactIntegrityError("Processed artifact manifest is unreadable or corrupted.") from exc
    if not isinstance(manifest, dict) or manifest.get("schema_version") != MANIFEST_SCHEMA_VERSION:
        raise ArtifactIntegrityError("Processed artifact manifest schema version is unsupported.")
    try:
        uuid.UUID(manifest["generation_id"])
    except (KeyError, ValueError, TypeError, AttributeError) as exc:
        raise ArtifactIntegrityError("Processed artifact manifest generation ID is invalid.") from exc
    file_records = manifest.get("artifacts")
    if not isinstance(file_records, dict) or set(file_records) != set(ARTIFACT_NAMES):
        raise ArtifactIntegrityError("Processed artifact manifest file list is incomplete or unexpected.")
    for name in ARTIFACT_NAMES:
        path = directory / name
        record = file_records[name]
        if not path.is_file():
            raise ArtifactIntegrityError(f"Required processed artifact is missing: {name}.")
        digest = hashlib.sha256()
        size = 0
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
                size += len(block)
        if not isinstance(record, dict) or record.get("sha256") != digest.hexdigest() or record.get("size_bytes") != size:
            raise ArtifactIntegrityError(f"Processed artifact checksum mismatch: {name}.")
    try:
        features = pd.read_parquet(directory / FEATURE_FILE)
        labels = pd.read_parquet(directory / LABEL_FILE)
    except Exception as exc:
        raise ArtifactIntegrityError("Processed feature or label artifact cannot be read.") from exc
    actual = validate_pair_frames(features, labels, manifest)
    if expected_feature_names is not None and actual["feature_names"] != expected_feature_names:
        raise ArtifactIntegrityError("Processed feature schema does not match the expected model feature order.")
    return features, labels, manifest
