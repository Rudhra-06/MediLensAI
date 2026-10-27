import pandas as pd
import pytest
import json
import shutil

from backend.app.ml.contracts import DataQualityReport, FEATURE_DEFINITIONS
from backend.app.ml.features import ProviderFeatureEngineer
from backend.app.ml.ingestion import DataIngestionPipeline, DataIntegrityError, MalformedSchemaError
from backend.app.ml.integrity import ArtifactIntegrityError, MANIFEST_FILENAME
from backend.app.ml.model import ProviderRiskModelError, load_processed_provider_data


def _claim(claim_id, provider, bene, inpatient, amount, diagnosis="D1"):
    return {
        "BeneID": bene, "ClaimID": claim_id, "Provider": provider,
        "InscClaimAmtReimbursed": amount, "DeductibleAmtPaid": 10,
        "AttendingPhysician": "DOC1", "OperatingPhysician": None,
        "ClmDiagnosisCode_1": diagnosis, "ClmAdmitDiagnosisCode": None,
        "ClmProcedureCode_1": None, "claim_duration_days": 2,
        "length_of_stay_days": 1 if inpatient else 0,
        "is_inpatient": int(inpatient),
    }


@pytest.fixture
def tables():
    target = pd.DataFrame({"Provider": ["P1", "P2"], "target_binary": [1, 0]})
    beneficiary = pd.DataFrame({
        "BeneID": ["B1", "B2"], "patient_age": [70.0, 80.0],
        "is_renal_disease": [1, 0], "chronic_conditions_count": [2, 4],
    })
    inpatient = pd.DataFrame([_claim("I1", "P1", "B1", True, 100), _claim("I2", "P1", "B1", True, 200)])
    outpatient = pd.DataFrame([_claim("O1", "P1", "B2", False, 50), _claim("O2", "P2", "B2", False, 25)])
    return target, beneficiary, inpatient, outpatient


def test_provider_aggregation_is_unique_leakage_free_and_cohort_weighted(tables):
    features, labels, summary = ProviderFeatureEngineer().compute_features(*tables)
    assert len(features) == len(labels) == 2
    assert not labels["Provider"].duplicated().any()
    assert list(features.columns) == list(FEATURE_DEFINITIONS)
    assert not {"Provider", "BeneID", "ClaimID", "PotentialFraud", "target_binary"}.intersection(features.columns)
    assert labels["Provider"].tolist() == ["P1", "P2"]
    assert features.loc[0, "inpatient_claim_count"] == 2
    assert features.loc[0, "outpatient_claim_count"] == 1
    assert features.loc[0, "distinct_beneficiaries_count"] == 2
    assert features.loc[0, "patient_age_mean"] == 75
    assert features.loc[0, "patient_renal_disease_ratio"] == 0.5
    assert summary.total_features == len(FEATURE_DEFINITIONS)
    assert summary.positive_fraud_count == 1


def test_duplicate_claims_are_rejected_before_aggregation(tables):
    target, beneficiary, inpatient, outpatient = tables
    inpatient.loc[1, "ClaimID"] = inpatient.loc[0, "ClaimID"]
    with pytest.raises(ValueError, match="ClaimID keys must be unique"):
        ProviderFeatureEngineer().compute_features(target, beneficiary, inpatient, outpatient)


def test_schema_and_invalid_numeric_values_fail_explicitly():
    with pytest.raises(MalformedSchemaError, match="missing required columns"):
        DataIngestionPipeline._validate_schema(pd.DataFrame({"x": [1]}), {"Provider"}, "Target")
    with pytest.raises(MalformedSchemaError, match="invalid values"):
        DataIngestionPipeline._numeric_column(pd.DataFrame({"amount": ["bad"]}), "amount", "Claims")


def test_beneficiary_join_key_uniqueness_is_enforced(tables):
    target, beneficiary, inpatient, outpatient = tables
    beneficiary = pd.concat([beneficiary, beneficiary.iloc[[0]]], ignore_index=True)
    with pytest.raises(ValueError, match="BeneID keys must be present and unique"):
        ProviderFeatureEngineer().compute_features(target, beneficiary, inpatient, outpatient)


def _export_pair(directory, tables):
    engineer = ProviderFeatureEngineer()
    features, labels, summary = engineer.compute_features(*tables)
    report = DataQualityReport(
        timestamp="2026-01-01T00:00:00+00:00",
        raw_dataset_counts={}, unique_identifiers={}, duplicate_records={},
        missing_value_summary={}, referential_integrity_checks={}, target_distribution={},
    )
    from backend.app.ml.config import DatasetPaths
    engineer.paths = DatasetPaths(processed_dir=directory)
    engineer.export_processed_datasets(features, labels, report, summary)
    return features, labels


def test_manifest_loader_accepts_export_and_attaches_generation_contract(tmp_path, tables):
    _export_pair(tmp_path, tables)
    features, labels = load_processed_provider_data(tmp_path)
    assert len(features) == len(labels) == 2
    assert features.attrs["medilens_pair_contract"]["generation_id"] == labels.attrs["medilens_pair_contract"]["generation_id"]
    assert (tmp_path / MANIFEST_FILENAME).is_file()


def test_mixed_generation_and_reordered_rows_are_rejected(tmp_path, tables):
    first, second = tmp_path / "first", tmp_path / "second"
    _export_pair(first, tables)
    altered_tables = list(tables)
    altered_tables[0] = tables[0].copy()
    altered_tables[0].loc[0, "target_binary"] = 0
    _export_pair(second, tuple(altered_tables))
    shutil.copyfile(second / "target_labels.parquet", first / "target_labels.parquet")
    with pytest.raises(ProviderRiskModelError, match="checksum mismatch"):
        load_processed_provider_data(first)

    _export_pair(first, tables)
    reordered = pd.read_parquet(first / "provider_features.parquet").iloc[::-1].reset_index(drop=True)
    reordered.to_parquet(first / "provider_features.parquet", index=False)
    with pytest.raises(ProviderRiskModelError, match="checksum mismatch"):
        load_processed_provider_data(first)


def test_corrupt_or_missing_manifest_fails_closed(tmp_path, tables):
    _export_pair(tmp_path, tables)
    manifest_path = tmp_path / MANIFEST_FILENAME
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["schema_version"] = 999
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ProviderRiskModelError, match="schema version"):
        load_processed_provider_data(tmp_path)
    manifest_path.unlink()
    with pytest.raises(ProviderRiskModelError, match="manifest is missing"):
        load_processed_provider_data(tmp_path)
