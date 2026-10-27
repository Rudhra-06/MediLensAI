"""Versioned provider-level risk inference endpoints."""
from __future__ import annotations

import json
import ipaddress
import math
from pathlib import Path
from typing import Any, Literal, Optional
from urllib.parse import urlsplit

import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, FiniteFloat, model_validator, create_model
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline

from backend.app.ml.model import load_provider_risk_model
from backend.app.ml.local_demo import DEMO_DISCLOSURE, LocalProviderDemo


MODEL_VERSION = "provider-risk-rf-v1"
DISCLAIMER = (
    "Provider-level uncalibrated model score for the PotentialFraud dataset label. "
    "PotentialFraud is not verified fraud; this score is not proof of wrongdoing "
    "or validated real-world performance."
)
MAX_BATCH_SIZE = 100
PROJECT_ROOT = Path(__file__).resolve().parents[4]


class RiskArtifactError(RuntimeError):
    """Saved risk artifacts are missing or incompatible with this API."""


class _StrictFeatureBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="before")
    @classmethod
    def validate_numeric_json_values(cls, values: Any) -> Any:
        if not isinstance(values, dict):
            raise ValueError("features must be an object of numeric feature values")
        expected = set(cls.model_fields)
        provided = set(values)
        missing, extra = expected - provided, provided - expected
        if missing or extra:
            raise ValueError("features must contain exactly the documented model feature fields")
        for value in values.values():
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError("feature values must be JSON numbers")
            if not math.isfinite(float(value)):
                raise ValueError("feature values must be finite numbers")
        return values


def _create_feature_values_model() -> type[BaseModel]:
    from backend.app.ml.contracts import FEATURE_DEFINITIONS

    fields = {
        name: (FiniteFloat, Field(description=definition.description))
        for name, definition in FEATURE_DEFINITIONS.items()
    }
    return create_model(
        "ProviderRiskFeatures",
        __base__=_StrictFeatureBase,
        **fields,
    )


ProviderRiskFeatures = _create_feature_values_model()


class ProviderRiskRequest(BaseModel):
    """A single provider's model features. Raw provider IDs are not accepted."""

    model_config = ConfigDict(extra="forbid")
    features: ProviderRiskFeatures = Field(description="Exactly the 32 documented numeric provider features.")


class ProviderRiskBatchRequest(BaseModel):
    """A bounded batch of provider feature records without provider identifiers."""

    model_config = ConfigDict(extra="forbid")
    providers: list[ProviderRiskRequest] = Field(min_length=1, max_length=MAX_BATCH_SIZE)


class RiskAssessmentResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    risk_score: float = Field(ge=0.0, le=1.0, description="Uncalibrated model score for PotentialFraud=1.")
    score_type: Literal["uncalibrated_model_score"]
    model_version: str
    disclaimer: str


class BatchRiskAssessmentResponse(BaseModel):
    assessments: list[RiskAssessmentResponse]
    count: int


class RiskHealthResponse(BaseModel):
    ready: bool
    status: Literal["ready", "unavailable"]
    model_version: str
    model_name: Optional[str] = None
    artifact_status: dict[str, bool]
    reason: Optional[str] = None
    local_demo_enabled: bool = False
    disclaimer: str = DISCLAIMER


class FeatureDescription(BaseModel):
    name: str
    domain: str
    data_type: str
    description: str


class FeatureListResponse(BaseModel):
    features: list[FeatureDescription]
    count: int
    model_version: str


class ValidationMetricSet(BaseModel):
    precision: FiniteFloat = Field(ge=0.0, le=1.0)
    recall: FiniteFloat = Field(ge=0.0, le=1.0)
    f1: FiniteFloat = Field(ge=0.0, le=1.0)
    average_precision: FiniteFloat = Field(ge=0.0, le=1.0)
    roc_auc: FiniteFloat = Field(ge=0.0, le=1.0)
    confusion_matrix_labels_0_1: list[list[int]]


class GlobalShapFeature(BaseModel):
    feature: str
    mean_absolute_contribution: FiniteFloat = Field(ge=0.0)
    mean_signed_contribution: FiniteFloat
    direction: Literal[
        "increases model output on average",
        "decreases model output on average",
        "zero average signed contribution",
    ]


class GlobalShapSummary(BaseModel):
    shap_version: str
    output_class: str
    output_scale: Literal["positive-class probability"]
    feature_count: int
    background_sample_count: int
    explanation_sample_count: int
    importance_method: str
    interpretation_limit: str
    max_absolute_additivity_error: FiniteFloat = Field(ge=0.0)
    features: list[GlobalShapFeature]


class ProviderRiskInsightsResponse(BaseModel):
    model_version: str
    model_name: str
    selected_model: str
    selection_metric: str
    split_strategy: str
    train_provider_count: int
    validation_provider_count: int
    validation_metrics: dict[str, ValidationMetricSet]
    limitations: list[str]
    explainability_status: Literal["available", "unavailable"]
    explainability_note: Optional[str] = None
    global_shap: Optional[GlobalShapSummary] = None


def required_artifact_paths(project_root: Path = PROJECT_ROOT) -> dict[str, Path]:
    """Return only the fixed local files used by this API."""
    return {
        "model": project_root / "models" / "provider_risk_model.joblib",
        "configuration": project_root / "models" / "provider_risk_config.json",
        "feature_list": project_root / "models" / "provider_risk_features.json",
        "feature_dictionary": project_root / "data" / "processed" / "feature_dictionary.json",
        "artifact_manifest": project_root / "data" / "processed" / "artifact_manifest.json",
    }


class ProviderRiskService:
    """Validates fixed artifacts once and reuses their fitted model for scoring."""

    def __init__(self, bundle: dict[str, Any], feature_descriptions: list[dict[str, str]]):
        self.bundle = bundle
        self.feature_names: list[str] = list(bundle["feature_names"])
        self.feature_descriptions = feature_descriptions
        self.model = bundle["model"]
        if not isinstance(self.model, Pipeline) or not self.model.steps or self.model.steps[-1][0] != "classifier":
            raise RiskArtifactError("Saved preprocessing/model pipeline is incompatible.")
        classifier = self.model.named_steps.get("classifier")
        if bundle.get("model_name") != "random_forest" or not isinstance(classifier, RandomForestClassifier):
            raise RiskArtifactError("Saved model is not the expected fitted Random Forest pipeline.")
        if len(self.feature_names) != 32 or len(set(self.feature_names)) != 32:
            raise RiskArtifactError("Saved model feature list must contain 32 unique names.")
        model_feature_names = list(getattr(self.model, "feature_names_in_", self.feature_names))
        if model_feature_names != self.feature_names or classifier.n_features_in_ != len(self.feature_names):
            raise RiskArtifactError("Saved pipeline input features do not match its model feature list.")
        try:
            probe = pd.DataFrame(np.zeros((1, len(self.feature_names))), columns=self.feature_names)
            transformed = self.model[:-1].transform(probe)
            if np.asarray(transformed).shape != (1, len(self.feature_names)):
                raise RiskArtifactError("Saved preprocessing changes the model feature dimensions.")
        except RiskArtifactError:
            raise
        except Exception as exc:
            raise RiskArtifactError("Saved preprocessing pipeline failed its compatibility check.") from exc
        positive_matches = np.flatnonzero(np.asarray(classifier.classes_) == 1)
        if len(positive_matches) != 1:
            raise RiskArtifactError("Saved classifier does not expose a unique PotentialFraud=1 class.")
        self.positive_class_index = int(positive_matches[0])
        self.model_name = bundle["model_name"]
        self.artifact_status = {key: True for key in ("model", "configuration", "feature_list", "feature_dictionary")}

    @classmethod
    def load(cls, project_root: Path = PROJECT_ROOT) -> "ProviderRiskService":
        paths = required_artifact_paths(project_root)
        status = {name: path.is_file() for name, path in paths.items()}
        missing = [name for name, exists in status.items() if not exists]
        if missing:
            raise RiskArtifactError("Required model artifacts are missing: " + ", ".join(missing))
        try:
            bundle = load_provider_risk_model(paths["model"])
            config = json.loads(paths["configuration"].read_text(encoding="utf-8"))
            feature_payload = json.loads(paths["feature_list"].read_text(encoding="utf-8"))
            dictionary = json.loads(paths["feature_dictionary"].read_text(encoding="utf-8"))
            from backend.app.ml.integrity import validate_processed_artifacts
            processed_features, processed_labels, manifest = validate_processed_artifacts(
                paths["feature_dictionary"].parent,
            )
        except Exception as exc:
            raise RiskArtifactError("One or more required model or processed data integrity artifacts could not be loaded.") from exc

        feature_names = list(bundle.get("feature_names", []))
        saved_feature_names = feature_payload.get("feature_names")
        dictionary_features = dictionary.get("features")
        if not isinstance(saved_feature_names, list) or feature_names != saved_feature_names:
            raise RiskArtifactError("Saved model and feature-list artifacts do not match.")
        if not isinstance(config, dict) or config.get("feature_count") != len(feature_names):
            raise RiskArtifactError("Saved model configuration does not match its feature count.")
        if list(processed_features.columns) != feature_names:
            raise RiskArtifactError("Validated processed feature schema does not match the saved model.")
        if "data_generation_id" in config and config.get("data_generation_id") not in (None, manifest["generation_id"]):
            raise RiskArtifactError("Saved model was trained from a different processed artifact generation.")
        configured_class_counts = {
            str(key): int(value)
            for key, value in config.get("train_target_counts", {}).items()
        }
        configured_class_counts.update({
            str(key): configured_class_counts.get(str(key), 0) + int(value)
            for key, value in config.get("validation_target_counts", {}).items()
        })
        if configured_class_counts != manifest["target_metadata"]["class_counts"]:
            raise RiskArtifactError("Saved model target counts do not match validated processed labels.")
        if not isinstance(dictionary_features, dict) or set(dictionary_features) != set(feature_names):
            raise RiskArtifactError("Processed feature dictionary does not match the saved model features.")
        from backend.app.ml.contracts import FEATURE_DEFINITIONS
        if list(FEATURE_DEFINITIONS) != feature_names:
            raise RiskArtifactError("API feature schema does not match the saved model feature order.")
        descriptions = []
        for name in feature_names:
            item = dictionary_features[name]
            if not isinstance(item, dict) or item.get("name") != name:
                raise RiskArtifactError("Feature dictionary contains incompatible metadata.")
            descriptions.append({
                "name": name,
                "domain": str(item.get("domain", "")),
                "data_type": str(item.get("data_type", "")),
                "description": str(item.get("description", "")),
            })
        service = cls(bundle, descriptions)
        service.artifact_status = {"model": True, "configuration": True, "feature_list": True, "feature_dictionary": True, "artifact_manifest": True}
        return service

    def assess(self, features: dict[str, float]) -> dict[str, Any]:
        if set(features) != set(self.feature_names):
            raise ValueError("Feature names do not match the saved model schema.")
        ordered = [features[name] for name in self.feature_names]
        if any(isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)) for value in ordered):
            raise ValueError("Feature values must be finite numbers.")
        frame = pd.DataFrame([[float(value) for value in ordered]], columns=self.feature_names)
        score = float(self.model.predict_proba(frame)[0, self.positive_class_index])
        if not math.isfinite(score) or not 0.0 <= score <= 1.0:
            raise RiskArtifactError("Saved model returned a score outside its probability output range.")
        return {
            "risk_score": score,
            "score_type": "uncalibrated_model_score",
            "model_version": MODEL_VERSION,
            "disclaimer": DISCLAIMER,
        }

    def load_local_demo(self, processed_dir: Path = PROJECT_ROOT / "data" / "processed") -> LocalProviderDemo:
        """Load fixed processed artifacts; demo state retains no IDs or labels."""
        from backend.app.ml.model import load_processed_provider_data

        features, labels = load_processed_provider_data(processed_dir)
        return LocalProviderDemo(features, labels, self.feature_names, self.bundle["configuration"])


def get_risk_service(request: Request) -> Optional[ProviderRiskService]:
    return getattr(request.app.state, "risk_service", None)


def _local_demo_for_request(request: Request) -> LocalProviderDemo:
    """Serve demo data only on direct loopback requests with a local Host."""
    from backend.app.core.config import settings

    client = request.client
    try:
        loopback = client is not None and ipaddress.ip_address(client.host).is_loopback
    except ValueError:
        loopback = False
    try:
        host = urlsplit(f"//{request.headers.get('host', '')}").hostname
        local_host = host is not None and host.casefold() in {"localhost", "127.0.0.1", "::1"}
    except ValueError:
        local_host = False
    origin = request.headers.get("origin")
    if origin is None:
        local_origin = True
    else:
        try:
            parsed_origin = urlsplit(origin)
            origin_host = parsed_origin.hostname
            _ = parsed_origin.port
            local_origin = (
                parsed_origin.scheme in {"http", "https"}
                and origin_host is not None
                and origin_host.casefold() in {"localhost", "127.0.0.1", "::1"}
                and parsed_origin.username is None
                and parsed_origin.password is None
                and parsed_origin.path in {"", "/"}
                and not parsed_origin.query
                and not parsed_origin.fragment
            )
        except ValueError:
            local_origin = False
    proxy_headers = any(
        name.casefold() == "forwarded"
        or name.casefold() == "via"
        or name.casefold() == "x-real-ip"
        or name.casefold().startswith("x-forwarded-")
        for name in request.headers.keys()
    )
    demo = getattr(request.app.state, "local_provider_demo", None)
    if (
        not settings.LOCAL_PROVIDER_DEMO_ENABLED
        or settings.MEDILENS_ENV != "development"
        or not loopback
        or not local_host
        or not local_origin
        or proxy_headers
        or demo is None
    ):
        raise HTTPException(status_code=404, detail="Local provider demo is unavailable.")
    return demo


class LocalDemoAssessmentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reference_id: str = Field(min_length=10, max_length=80, pattern=r"^demo-[A-Za-z0-9_-]+$")


class LocalDemoReferencesResponse(BaseModel):
    enabled: bool
    split_disclosure: str
    providers: list[LocalDemoAssessmentRequest]
    count: int


router = APIRouter(prefix="/risk", tags=["Provider Risk Inference"])


@router.get("/health", response_model=RiskHealthResponse, summary="Provider risk model readiness")
def risk_health(
    service: Optional[ProviderRiskService] = Depends(get_risk_service),
) -> RiskHealthResponse:
    paths = required_artifact_paths()
    present = {name: path.is_file() for name, path in paths.items()}
    if service is None:
        return RiskHealthResponse(
            ready=False,
            status="unavailable",
            model_version=MODEL_VERSION,
            artifact_status=present,
            reason="Risk model artifacts are missing or incompatible; inference is unavailable.",
            local_demo_enabled=False,
        )
    return RiskHealthResponse(
        ready=True,
        status="ready",
        model_version=MODEL_VERSION,
        model_name=service.model_name,
        artifact_status=service.artifact_status,
        local_demo_enabled=getattr(service, "local_demo_enabled", False),
    )


def _assess_or_503(service: Optional[ProviderRiskService], request: ProviderRiskRequest) -> dict[str, Any]:
    if service is None:
        raise HTTPException(status_code=503, detail="Provider risk model is unavailable.")
    try:
        return service.assess(request.features.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/assess", response_model=RiskAssessmentResponse, summary="Assess one provider's features")
def assess_provider(
    request: ProviderRiskRequest,
    service: Optional[ProviderRiskService] = Depends(get_risk_service),
) -> dict[str, Any]:
    return _assess_or_503(service, request)


@router.post("/assess/batch", response_model=BatchRiskAssessmentResponse, summary="Assess a bounded provider batch")
def assess_provider_batch(
    request: ProviderRiskBatchRequest,
    service: Optional[ProviderRiskService] = Depends(get_risk_service),
) -> dict[str, Any]:
    if service is None:
        raise HTTPException(status_code=503, detail="Provider risk model is unavailable.")
    results = [_assess_or_503(service, item) for item in request.providers]
    return {"assessments": results, "count": len(results)}


@router.get("/features", response_model=FeatureListResponse, summary="List safe model feature descriptions")
def list_provider_features(
    service: Optional[ProviderRiskService] = Depends(get_risk_service),
) -> FeatureListResponse:
    if service is None:
        raise HTTPException(status_code=503, detail="Provider risk model is unavailable.")
    return FeatureListResponse(
        features=[FeatureDescription(**item) for item in service.feature_descriptions],
        count=len(service.feature_descriptions),
        model_version=MODEL_VERSION,
    )


@router.get(
    "/insights",
    response_model=ProviderRiskInsightsResponse,
    summary="Read aggregate validation metrics and global SHAP importance",
)
def provider_risk_insights(
    service: Optional[ProviderRiskService] = Depends(get_risk_service),
) -> ProviderRiskInsightsResponse:
    """Return only aggregate model metrics and global feature contributions.

    Local explanation samples, provider aliases, labels and raw feature rows are
    deliberately excluded from this public response.
    """
    if service is None:
        raise HTTPException(status_code=503, detail="Provider risk model is unavailable.")
    metrics_path = PROJECT_ROOT / "models" / "provider_risk_metrics.json"
    shap_path = PROJECT_ROOT / "models" / "shap_global_importance.json"
    try:
        metrics_data = json.loads(metrics_path.read_text(encoding="utf-8"))
        selected_model = metrics_data["selected_model"]
        raw_metrics = metrics_data["validation_metrics"]
        split = metrics_data["split"]
        if selected_model != service.model_name or not isinstance(raw_metrics, dict):
            raise ValueError("Saved validation metrics do not match the loaded model.")
        validation_metrics: dict[str, ValidationMetricSet] = {}
        for name in ("dummy_prior", "logistic_regression", "random_forest"):
            metric = raw_metrics[name]
            matrix = metric["confusion_matrix_labels_0_1"]
            if (
                not isinstance(matrix, list)
                or len(matrix) != 2
                or any(not isinstance(row, list) or len(row) != 2 for row in matrix)
            ):
                raise ValueError("Saved confusion matrix has an incompatible shape.")
            validation_metrics[name] = ValidationMetricSet(
                **{key: metric[key] for key in (
                    "precision", "recall", "f1", "average_precision", "roc_auc",
                )},
                confusion_matrix_labels_0_1=matrix,
            )
        train_count = int(split["train_providers"])
        validation_count = int(split["validation_providers"])
        if train_count < 1 or validation_count < 1:
            raise ValueError("Saved validation split counts are invalid.")
        limitations = metrics_data["limitations"]
        if not isinstance(limitations, list) or any(not isinstance(item, str) for item in limitations):
            raise ValueError("Saved validation limitations have an incompatible schema.")
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="Saved validation metric artifact is missing or incompatible.",
        ) from exc

    global_shap: Optional[GlobalShapSummary] = None
    explainability_note: Optional[str] = None
    if not shap_path.is_file():
        explainability_note = "Global SHAP artifact is unavailable."
    else:
        try:
            shap_data = json.loads(shap_path.read_text(encoding="utf-8"))
            shap_rows = shap_data["features"]
            shap_names = [row["feature"] for row in shap_rows]
            verification = shap_data["output_scale_verification"]
            max_additivity_error = float(verification["max_absolute_additivity_error"])
            tolerance = float(verification["tolerance"])
            if (
                shap_data.get("model") != service.model_name
                or shap_data.get("output_class", "").split(" ")[0] != "PotentialFraud=1"
                or shap_data.get("output_scale") != "positive-class probability"
                or shap_data.get("feature_count") != len(service.feature_names)
                or len(shap_rows) != len(service.feature_names)
                or len(set(shap_names)) != len(shap_names)
                or set(shap_names) != set(service.feature_names)
                or not math.isfinite(max_additivity_error)
                or not math.isfinite(tolerance)
                or tolerance <= 0
                or max_additivity_error > tolerance
            ):
                raise ValueError("Saved global SHAP schema does not match the loaded model.")
            global_shap = GlobalShapSummary(
                shap_version=str(shap_data["shap_version"]),
                output_class=str(shap_data["output_class"]),
                output_scale=shap_data["output_scale"],
                feature_count=int(shap_data["feature_count"]),
                background_sample_count=int(shap_data["background_sample_count"]),
                explanation_sample_count=int(shap_data["explanation_sample_count"]),
                importance_method=str(shap_data["importance_method"]),
                interpretation_limit=str(shap_data["interpretation_limit"]),
                max_absolute_additivity_error=max_additivity_error,
                features=[GlobalShapFeature(**row) for row in shap_rows],
            )
        except Exception:
            # Metrics remain useful if SHAP is absent or incompatible; never expose partial data.
            explainability_note = "Global SHAP artifact is unavailable or incompatible with the loaded feature schema."

    return ProviderRiskInsightsResponse(
        model_version=MODEL_VERSION,
        model_name=service.model_name,
        selected_model=selected_model,
        selection_metric=str(metrics_data["selection_metric"]),
        split_strategy="Single stratified train/validation holdout; validation Average Precision selected the model; no independent test set.",
        train_provider_count=train_count,
        validation_provider_count=validation_count,
        validation_metrics=validation_metrics,
        limitations=limitations,
        explainability_status="available" if global_shap is not None else "unavailable",
        explainability_note=explainability_note,
        global_shap=global_shap,
    )


@router.get("/demo/providers", response_model=LocalDemoReferencesResponse, summary="List ephemeral local retrospective demo references")
def list_local_demo_providers(request: Request) -> LocalDemoReferencesResponse:
    demo = _local_demo_for_request(request)
    references = demo.references()
    return LocalDemoReferencesResponse(
        enabled=True,
        split_disclosure=DEMO_DISCLOSURE,
        providers=references,
        count=len(references),
    )


@router.post("/demo/assess", summary="Assess one ephemeral local retrospective demo reference")
def assess_local_demo_provider(
    payload: LocalDemoAssessmentRequest,
    request: Request,
    service: Optional[ProviderRiskService] = Depends(get_risk_service),
) -> dict[str, Any]:
    demo = _local_demo_for_request(request)
    if service is None:
        raise HTTPException(status_code=503, detail="Provider risk model is unavailable.")
    features = demo.features_for(payload.reference_id)
    if features is None:
        raise HTTPException(status_code=404, detail="Local demo reference is unavailable or expired.")
    return {
        **service.assess(features),
        "assessment_mode": "retrospective_validation_demo",
        "reference_id": payload.reference_id,
        "split_disclosure": DEMO_DISCLOSURE,
    }
