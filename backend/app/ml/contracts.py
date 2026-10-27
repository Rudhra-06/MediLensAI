"""Data contracts, feature definitions, and quality report models for MediLens AI."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class FeatureMetadata(BaseModel):
    """Metadata describing a single engineered provider feature."""

    name: str
    domain: str
    data_type: str
    description: str
    formula: str
    leakage_safety_note: str
    imputation_strategy: str


class DataQualityReport(BaseModel):
    """Structured report documenting ingestion and integrity audit findings."""

    status: str = Field(default="passed", description="'passed', 'warning', or 'failed'")
    timestamp: str
    raw_dataset_counts: Dict[str, int]
    unique_identifiers: Dict[str, int]
    duplicate_records: Dict[str, int]
    missing_value_summary: Dict[str, Dict[str, int]]
    referential_integrity_checks: Dict[str, bool]
    target_distribution: Dict[str, Any]
    warnings: List[str] = Field(default_factory=list)


class FeatureDatasetSummary(BaseModel):
    """Summary of the engineered provider feature dataset."""

    total_providers: int
    total_features: int
    positive_fraud_count: int
    negative_fraud_count: int
    positive_class_ratio: float
    feature_names: List[str]
    target_column_name: str
    target_is_isolated: bool
    deterministic_ordering: bool


FEATURE_DEFINITIONS: Dict[str, FeatureMetadata] = {
    # Volume Features
    "inpatient_claim_count": FeatureMetadata(
        name="inpatient_claim_count",
        domain="Volume",
        data_type="int64",
        description="Total number of inpatient hospital claims billed under the provider.",
        formula="Count(Inpatient ClaimIDs for Provider)",
        leakage_safety_note="Historical claim count; does not use target label.",
        imputation_strategy="0 if provider billed 0 inpatient claims.",
    ),
    "outpatient_claim_count": FeatureMetadata(
        name="outpatient_claim_count",
        domain="Volume",
        data_type="int64",
        description="Total number of outpatient clinic claims billed under the provider.",
        formula="Count(Outpatient ClaimIDs for Provider)",
        leakage_safety_note="Historical claim count; does not use target label.",
        imputation_strategy="0 if provider billed 0 outpatient claims.",
    ),
    "total_claim_count": FeatureMetadata(
        name="total_claim_count",
        domain="Volume",
        data_type="int64",
        description="Total number of combined inpatient and outpatient claims.",
        formula="inpatient_claim_count + outpatient_claim_count",
        leakage_safety_note="Purely count-based aggregation.",
        imputation_strategy="Integer count >= 1.",
    ),
    "inpatient_claim_ratio": FeatureMetadata(
        name="inpatient_claim_ratio",
        domain="Volume",
        data_type="float64",
        description="Proportion of provider claims that were inpatient hospitalizations.",
        formula="inpatient_claim_count / total_claim_count",
        leakage_safety_note="Bounded ratio [0.0, 1.0]. Zero-division guarded.",
        imputation_strategy="0.0 if total_claim_count == 0.",
    ),

    # Financial Reimbursement Features
    "inpatient_reimbursed_sum": FeatureMetadata(
        name="inpatient_reimbursed_sum",
        domain="Financial",
        data_type="float64",
        description="Total insurance reimbursement dollars received for inpatient claims.",
        formula="Sum(InscClaimAmtReimbursed on Inpatient claims)",
        leakage_safety_note="Claim transaction reimbursement amounts only.",
        imputation_strategy="0.0 if no inpatient claims.",
    ),
    "inpatient_reimbursed_mean": FeatureMetadata(
        name="inpatient_reimbursed_mean",
        domain="Financial",
        data_type="float64",
        description="Average insurance reimbursement per inpatient claim.",
        formula="inpatient_reimbursed_sum / inpatient_claim_count",
        leakage_safety_note="Guarded against zero division.",
        imputation_strategy="0.0 if inpatient_claim_count == 0.",
    ),
    "inpatient_reimbursed_max": FeatureMetadata(
        name="inpatient_reimbursed_max",
        domain="Financial",
        data_type="float64",
        description="Maximum single reimbursement amount among inpatient claims.",
        formula="Max(InscClaimAmtReimbursed on Inpatient claims)",
        leakage_safety_note="Non-negative scalar.",
        imputation_strategy="0.0 if no inpatient claims.",
    ),
    "outpatient_reimbursed_sum": FeatureMetadata(
        name="outpatient_reimbursed_sum",
        domain="Financial",
        data_type="float64",
        description="Total insurance reimbursement dollars received for outpatient claims.",
        formula="Sum(InscClaimAmtReimbursed on Outpatient claims)",
        leakage_safety_note="Transaction reimbursement amounts only.",
        imputation_strategy="0.0 if no outpatient claims.",
    ),
    "outpatient_reimbursed_mean": FeatureMetadata(
        name="outpatient_reimbursed_mean",
        domain="Financial",
        data_type="float64",
        description="Average insurance reimbursement per outpatient claim.",
        formula="outpatient_reimbursed_sum / outpatient_claim_count",
        leakage_safety_note="Guarded against zero division.",
        imputation_strategy="0.0 if outpatient_claim_count == 0.",
    ),
    "outpatient_reimbursed_max": FeatureMetadata(
        name="outpatient_reimbursed_max",
        domain="Financial",
        data_type="float64",
        description="Maximum single reimbursement amount among outpatient claims.",
        formula="Max(InscClaimAmtReimbursed on Outpatient claims)",
        leakage_safety_note="Non-negative scalar.",
        imputation_strategy="0.0 if no outpatient claims.",
    ),
    "total_reimbursed_sum": FeatureMetadata(
        name="total_reimbursed_sum",
        domain="Financial",
        data_type="float64",
        description="Grand total insurance reimbursement dollars across all claims.",
        formula="inpatient_reimbursed_sum + outpatient_reimbursed_sum",
        leakage_safety_note="Pure financial summation.",
        imputation_strategy="0.0 default.",
    ),
    "total_reimbursed_mean": FeatureMetadata(
        name="total_reimbursed_mean",
        domain="Financial",
        data_type="float64",
        description="Average reimbursement across all claims billed by the provider.",
        formula="total_reimbursed_sum / total_claim_count",
        leakage_safety_note="Guarded against zero division.",
        imputation_strategy="0.0 if total_claim_count == 0.",
    ),
    "inpatient_reimbursement_ratio": FeatureMetadata(
        name="inpatient_reimbursement_ratio",
        domain="Financial",
        data_type="float64",
        description="Fraction of total provider dollars derived from inpatient hospitalizations.",
        formula="inpatient_reimbursed_sum / total_reimbursed_sum",
        leakage_safety_note="Guarded against zero division.",
        imputation_strategy="0.0 if total_reimbursed_sum == 0.",
    ),

    # Deductible Features
    "inpatient_deductible_sum": FeatureMetadata(
        name="inpatient_deductible_sum",
        domain="Financial",
        data_type="float64",
        description="Total patient deductible paid for inpatient claims.",
        formula="Sum(DeductibleAmtPaid on Inpatient claims)",
        leakage_safety_note="Claim deductible paid.",
        imputation_strategy="0.0 if no inpatient claims or nulls filled with 0.",
    ),
    "outpatient_deductible_sum": FeatureMetadata(
        name="outpatient_deductible_sum",
        domain="Financial",
        data_type="float64",
        description="Total patient deductible paid for outpatient claims.",
        formula="Sum(DeductibleAmtPaid on Outpatient claims)",
        leakage_safety_note="Claim deductible paid.",
        imputation_strategy="0.0 if no outpatient claims.",
    ),
    "total_deductible_sum": FeatureMetadata(
        name="total_deductible_sum",
        domain="Financial",
        data_type="float64",
        description="Total patient deductibles paid across all claims.",
        formula="inpatient_deductible_sum + outpatient_deductible_sum",
        leakage_safety_note="Pure financial summation.",
        imputation_strategy="0.0 default.",
    ),

    # Beneficiary Cohort Features
    "distinct_beneficiaries_count": FeatureMetadata(
        name="distinct_beneficiaries_count",
        domain="Beneficiary",
        data_type="int64",
        description="Number of distinct Medicare beneficiaries treated by the provider.",
        formula="Count(Distinct BeneIDs for Provider)",
        leakage_safety_note="Cardinally aggregated; raw BeneIDs are discarded.",
        imputation_strategy="Integer count >= 1.",
    ),
    "claims_per_beneficiary_mean": FeatureMetadata(
        name="claims_per_beneficiary_mean",
        domain="Beneficiary",
        data_type="float64",
        description="Average number of claims billed per unique beneficiary (service intensity).",
        formula="total_claim_count / distinct_beneficiaries_count",
        leakage_safety_note="Guarded against zero division.",
        imputation_strategy="0.0 if distinct_beneficiaries_count == 0.",
    ),
    "patient_age_mean": FeatureMetadata(
        name="patient_age_mean",
        domain="Beneficiary",
        data_type="float64",
        description="Average age of treated beneficiaries (approximated from DOB to 2009 service year).",
        formula="Mean(2009 - BirthYear(DOB) for distinct treated beneficiaries)",
        leakage_safety_note="Uses only historical demographic birth date; excludes future lookahead.",
        imputation_strategy="Mean of cohort or 65.0 (standard Medicare age) if unavailable.",
    ),
    "patient_renal_disease_ratio": FeatureMetadata(
        name="patient_renal_disease_ratio",
        domain="Beneficiary",
        data_type="float64",
        description="Fraction of treated beneficiaries with End-Stage Renal Disease (ESRD).",
        formula="Count(Bene with RenalDiseaseIndicator=='Y') / distinct_beneficiaries_count",
        leakage_safety_note="Bounded ratio [0.0, 1.0].",
        imputation_strategy="0.0 if distinct_beneficiaries_count == 0.",
    ),
    "patient_chronic_condition_mean": FeatureMetadata(
        name="patient_chronic_condition_mean",
        domain="Beneficiary",
        data_type="float64",
        description="Average number of diagnosed chronic conditions (0-11) per treated beneficiary.",
        formula="Mean(Sum(11 Chronic Condition flags == 1) per treated beneficiary)",
        leakage_safety_note="Clinical risk index of treated cohort without annual future spend leakage.",
        imputation_strategy="0.0 if no beneficiaries.",
    ),

    # Physician Concentration Features
    "distinct_attending_physicians_count": FeatureMetadata(
        name="distinct_attending_physicians_count",
        domain="Physician",
        data_type="int64",
        description="Number of distinct attending physicians submitting claims under provider.",
        formula="Count(Distinct AttendingPhysician IDs excluding null)",
        leakage_safety_note="Cardinality metric only; raw IDs are discarded.",
        imputation_strategy="0 if no attending physicians recorded.",
    ),
    "distinct_operating_physicians_count": FeatureMetadata(
        name="distinct_operating_physicians_count",
        domain="Physician",
        data_type="int64",
        description="Number of distinct operating surgeons submitting claims under provider.",
        formula="Count(Distinct OperatingPhysician IDs excluding null)",
        leakage_safety_note="Cardinality metric only; raw IDs are discarded.",
        imputation_strategy="0 if no operating physicians recorded.",
    ),
    "claims_per_attending_mean": FeatureMetadata(
        name="claims_per_attending_mean",
        domain="Physician",
        data_type="float64",
        description="Average number of claims billed per attending physician.",
        formula="total_claim_count / distinct_attending_physicians_count",
        leakage_safety_note="Guarded against zero division.",
        imputation_strategy="0.0 if distinct_attending_physicians_count == 0.",
    ),

    # Temporal & Duration Features
    "claim_duration_days_mean": FeatureMetadata(
        name="claim_duration_days_mean",
        domain="Temporal",
        data_type="float64",
        description="Average claim duration in days (ClaimEndDt - ClaimStartDt + 1).",
        formula="Mean((ClaimEndDt - ClaimStartDt) in days across claims)",
        leakage_safety_note="Service duration bounded by claim period.",
        imputation_strategy="1.0 default (same-day service).",
    ),
    "claim_duration_days_max": FeatureMetadata(
        name="claim_duration_days_max",
        domain="Temporal",
        data_type="float64",
        description="Maximum single claim duration in days across provider's claims.",
        formula="Max((ClaimEndDt - ClaimStartDt) in days)",
        leakage_safety_note="Transaction-level duration metric.",
        imputation_strategy="1.0 default.",
    ),
    "inpatient_length_of_stay_mean": FeatureMetadata(
        name="inpatient_length_of_stay_mean",
        domain="Temporal",
        data_type="float64",
        description="Average inpatient length of stay (DischargeDt - AdmissionDt) in days.",
        formula="Mean(DischargeDt - AdmissionDt on Inpatient claims)",
        leakage_safety_note="Inpatient hospitalization duration only.",
        imputation_strategy="0.0 if no inpatient claims.",
    ),

    # Clinical Complexity & Coding Features
    "distinct_primary_diagnoses_count": FeatureMetadata(
        name="distinct_primary_diagnoses_count",
        domain="Clinical",
        data_type="int64",
        description="Number of distinct primary diagnosis codes (ClmDiagnosisCode_1) billed.",
        formula="Count(Distinct ClmDiagnosisCode_1 excluding null)",
        leakage_safety_note="Cardinality metric only; raw codes discarded.",
        imputation_strategy="0 if no primary diagnosis codes recorded.",
    ),
    "distinct_admit_diagnoses_count": FeatureMetadata(
        name="distinct_admit_diagnoses_count",
        domain="Clinical",
        data_type="int64",
        description="Number of distinct admitting diagnosis codes billed.",
        formula="Count(Distinct ClmAdmitDiagnosisCode excluding null)",
        leakage_safety_note="Cardinality metric only.",
        imputation_strategy="0 if no admit diagnosis codes recorded.",
    ),
    "diagnosis_diversity_ratio": FeatureMetadata(
        name="diagnosis_diversity_ratio",
        domain="Clinical",
        data_type="float64",
        description="Ratio of distinct primary diagnoses to total claims (measures code concentration).",
        formula="distinct_primary_diagnoses_count / total_claim_count",
        leakage_safety_note="Guarded against zero division. Bounded in (0.0, 1.0].",
        imputation_strategy="0.0 if total_claim_count == 0.",
    ),
    "inpatient_procedure_claim_count": FeatureMetadata(
        name="inpatient_procedure_claim_count",
        domain="Clinical",
        data_type="int64",
        description="Number of inpatient claims having at least one procedure code recorded.",
        formula="Count(Inpatient claims where ClmProcedureCode_1 is not null)",
        leakage_safety_note="Count metric; raw procedure codes discarded.",
        imputation_strategy="0 if no procedures.",
    ),
    "inpatient_procedure_ratio": FeatureMetadata(
        name="inpatient_procedure_ratio",
        domain="Clinical",
        data_type="float64",
        description="Proportion of inpatient claims involving surgical or medical procedures.",
        formula="inpatient_procedure_claim_count / inpatient_claim_count",
        leakage_safety_note="Guarded against zero division.",
        imputation_strategy="0.0 if inpatient_claim_count == 0.",
    ),
}
