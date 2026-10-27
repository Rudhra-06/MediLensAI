"""Provider-level feature engineering pipeline for MediLens AI."""
import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from backend.app.ml.config import DatasetPaths
from backend.app.ml.contracts import (
    FEATURE_DEFINITIONS,
    DataQualityReport,
    FeatureDatasetSummary,
)
from backend.app.ml.integrity import (
    PAIR_METADATA_ATTR,
    attach_pair_contract,
    build_manifest,
    validate_pair_frames,
    write_manifest_atomic,
)

logger = logging.getLogger("medilens.features")


class ProviderFeatureEngineer:
    """Computes reproducible, leakage-free provider-level aggregated features."""

    def __init__(self, paths: Optional[DatasetPaths] = None):
        self.paths = paths or DatasetPaths()
        self.feature_columns: List[str] = list(FEATURE_DEFINITIONS.keys())

    def compute_features(
        self,
        df_target: pd.DataFrame,
        df_beneficiary: pd.DataFrame,
        df_inpatient: pd.DataFrame,
        df_outpatient: pd.DataFrame,
    ) -> Tuple[pd.DataFrame, pd.DataFrame, FeatureDatasetSummary]:
        """Generate provider-level feature table and separate target table.

        Args:
            df_target: Provider target DataFrame with 'Provider' and 'target_binary'
            df_beneficiary: Beneficiary DataFrame with demographics and conditions
            df_inpatient: Inpatient claims DataFrame
            df_outpatient: Outpatient claims DataFrame

        Returns:
            Tuple of:
                - df_features: Exactly one row per provider, containing only feature columns
                - df_labels: Exactly one row per provider, containing 'Provider' and 'target_binary'
                - summary: FeatureDatasetSummary metadata
        """
        required_target = {"Provider", "target_binary"}
        if not required_target.issubset(df_target.columns):
            raise ValueError("Target data is missing required Provider/target_binary columns.")
        for name, frame, keys in (
            ("beneficiary", df_beneficiary, {"BeneID", "patient_age", "is_renal_disease", "chronic_conditions_count"}),
            ("inpatient", df_inpatient, {"BeneID", "ClaimID", "Provider", "is_inpatient"}),
            ("outpatient", df_outpatient, {"BeneID", "ClaimID", "Provider", "is_inpatient"}),
        ):
            missing = keys - set(frame.columns)
            if missing:
                raise ValueError(f"{name.title()} data is missing required columns: {sorted(missing)}")
        if df_target["Provider"].isna().any() or df_target["Provider"].duplicated().any():
            raise ValueError("Target Provider keys must be present and unique.")
        if df_target["target_binary"].isna().any() or not df_target["target_binary"].isin([0, 1]).all():
            raise ValueError("Target labels must contain only non-null binary values.")
        if df_beneficiary["BeneID"].isna().any() or df_beneficiary["BeneID"].duplicated().any():
            raise ValueError("Beneficiary BeneID keys must be present and unique.")
        for name, frame in (("inpatient", df_inpatient), ("outpatient", df_outpatient)):
            if frame[["ClaimID", "Provider", "BeneID"]].isna().any().any():
                raise ValueError(f"{name.title()} claim join keys cannot be null.")
            if frame["ClaimID"].duplicated().any():
                raise ValueError(f"{name.title()} ClaimID keys must be unique.")
            expected_flag = 1 if name == "inpatient" else 0
            if not frame["is_inpatient"].eq(expected_flag).all():
                raise ValueError(f"{name.title()} is_inpatient values do not match the table type.")
        if set(df_inpatient["ClaimID"]).intersection(df_outpatient["ClaimID"]):
            raise ValueError("ClaimID keys overlap between inpatient and outpatient data.")

        # Align beneficiary attributes for joining
        bene_cols = ["BeneID", "patient_age", "is_renal_disease", "chronic_conditions_count"]
        bene_lookup = df_beneficiary[bene_cols].drop_duplicates(subset=["BeneID"])

        # 1. Prepare unified claims with claim-level features
        inp_subset = df_inpatient[
            [
                "BeneID",
                "ClaimID",
                "Provider",
                "InscClaimAmtReimbursed",
                "DeductibleAmtPaid",
                "AttendingPhysician",
                "OperatingPhysician",
                "ClmDiagnosisCode_1",
                "ClmAdmitDiagnosisCode",
                "ClmProcedureCode_1",
                "claim_duration_days",
                "length_of_stay_days",
                "is_inpatient",
            ]
        ].copy()

        out_subset = df_outpatient[
            [
                "BeneID",
                "ClaimID",
                "Provider",
                "InscClaimAmtReimbursed",
                "DeductibleAmtPaid",
                "AttendingPhysician",
                "OperatingPhysician",
                "ClmDiagnosisCode_1",
                "ClmAdmitDiagnosisCode",
                "ClmProcedureCode_1",
                "claim_duration_days",
                "length_of_stay_days",
                "is_inpatient",
            ]
        ].copy()

        # Concatenate inpatient and outpatient claims (mutually exclusive ClaimIDs)
        all_claims = pd.concat([inp_subset, out_subset], ignore_index=True)

        # Merge beneficiary characteristics
        all_claims = all_claims.merge(bene_lookup, on="BeneID", how="left", validate="many_to_one")
        all_claims["patient_age"] = all_claims["patient_age"].fillna(65.0)
        all_claims["is_renal_disease"] = all_claims["is_renal_disease"].fillna(0)
        all_claims["chronic_conditions_count"] = all_claims["chronic_conditions_count"].fillna(0)

        # 2. Compute Inpatient-Specific Provider Aggregations
        inp_claims = all_claims[all_claims["is_inpatient"] == 1]
        inp_grp = inp_claims.groupby("Provider")

        inp_agg = inp_grp.agg(
            inpatient_claim_count=("ClaimID", "count"),
            inpatient_reimbursed_sum=("InscClaimAmtReimbursed", "sum"),
            inpatient_reimbursed_mean=("InscClaimAmtReimbursed", "mean"),
            inpatient_reimbursed_max=("InscClaimAmtReimbursed", "max"),
            inpatient_deductible_sum=("DeductibleAmtPaid", "sum"),
            inpatient_length_of_stay_mean=("length_of_stay_days", "mean"),
            inpatient_procedure_claim_count=(
                "ClmProcedureCode_1",
                lambda s: s.notna().sum(),
            ),
        ).reset_index()

        # 3. Compute Outpatient-Specific Provider Aggregations
        out_claims = all_claims[all_claims["is_inpatient"] == 0]
        out_grp = out_claims.groupby("Provider")

        out_agg = out_grp.agg(
            outpatient_claim_count=("ClaimID", "count"),
            outpatient_reimbursed_sum=("InscClaimAmtReimbursed", "sum"),
            outpatient_reimbursed_mean=("InscClaimAmtReimbursed", "mean"),
            outpatient_reimbursed_max=("InscClaimAmtReimbursed", "max"),
            outpatient_deductible_sum=("DeductibleAmtPaid", "sum"),
        ).reset_index()

        # 4. Compute All-Claims Combined Provider Aggregations
        all_grp = all_claims.groupby("Provider")

        comb_agg = all_grp.agg(
            total_claim_count=("ClaimID", "count"),
            total_reimbursed_sum=("InscClaimAmtReimbursed", "sum"),
            total_reimbursed_mean=("InscClaimAmtReimbursed", "mean"),
            total_deductible_sum=("DeductibleAmtPaid", "sum"),
            distinct_beneficiaries_count=("BeneID", lambda s: s.nunique()),
            distinct_attending_physicians_count=(
                "AttendingPhysician",
                lambda s: s.dropna().nunique(),
            ),
            distinct_operating_physicians_count=(
                "OperatingPhysician",
                lambda s: s.dropna().nunique(),
            ),
            claim_duration_days_mean=("claim_duration_days", "mean"),
            claim_duration_days_max=("claim_duration_days", "max"),
            distinct_primary_diagnoses_count=(
                "ClmDiagnosisCode_1",
                lambda s: s.dropna().nunique(),
            ),
            distinct_admit_diagnoses_count=(
                "ClmAdmitDiagnosisCode",
                lambda s: s.dropna().nunique(),
            ),
        ).reset_index()

        # Beneficiary cohort measures use one observation per provider/person,
        # regardless of how many claims that person generated.
        provider_beneficiaries = all_claims.drop_duplicates(["Provider", "BeneID"])
        cohort_agg = provider_beneficiaries.groupby("Provider", sort=True).agg(
            patient_age_mean=("patient_age", "mean"),
            patient_renal_disease_ratio=("is_renal_disease", "mean"),
            patient_chronic_condition_mean=("chronic_conditions_count", "mean"),
        ).reset_index()
        comb_agg = comb_agg.merge(cohort_agg, on="Provider", how="left", validate="one_to_one")

        # 5. Join to the Master Target Provider Spine (preserving exact provider universe)
        spine = df_target[["Provider"]].drop_duplicates().sort_values("Provider").reset_index(drop=True)
        merged = spine.merge(inp_agg, on="Provider", how="left", validate="one_to_one")
        merged = merged.merge(out_agg, on="Provider", how="left", validate="one_to_one")
        merged = merged.merge(comb_agg, on="Provider", how="left", validate="one_to_one")

        # 6. Fill zeros and derive ratios safely
        # Count & Sum defaults
        count_and_sum_cols = [
            "inpatient_claim_count",
            "outpatient_claim_count",
            "total_claim_count",
            "inpatient_reimbursed_sum",
            "inpatient_reimbursed_mean",
            "inpatient_reimbursed_max",
            "outpatient_reimbursed_sum",
            "outpatient_reimbursed_mean",
            "outpatient_reimbursed_max",
            "total_reimbursed_sum",
            "total_reimbursed_mean",
            "inpatient_deductible_sum",
            "outpatient_deductible_sum",
            "total_deductible_sum",
            "distinct_beneficiaries_count",
            "distinct_attending_physicians_count",
            "distinct_operating_physicians_count",
            "distinct_primary_diagnoses_count",
            "distinct_admit_diagnoses_count",
            "inpatient_procedure_claim_count",
            "inpatient_length_of_stay_mean",
        ]
        for c in count_and_sum_cols:
            if c in merged.columns:
                merged[c] = merged[c].fillna(0.0)

        # Baseline defaults for duration & age if provider had zero claims
        merged["claim_duration_days_mean"] = merged["claim_duration_days_mean"].fillna(1.0)
        merged["claim_duration_days_max"] = merged["claim_duration_days_max"].fillna(1.0)
        merged["patient_age_mean"] = merged["patient_age_mean"].fillna(65.0)
        merged["patient_renal_disease_ratio"] = merged["patient_renal_disease_ratio"].fillna(0.0)
        merged["patient_chronic_condition_mean"] = merged["patient_chronic_condition_mean"].fillna(0.0)

        # Derive ratios with zero-division safety
        total_claims = merged["total_claim_count"]
        inp_claims_cnt = merged["inpatient_claim_count"]
        tot_reimb = merged["total_reimbursed_sum"]
        bene_cnt = merged["distinct_beneficiaries_count"]
        att_cnt = merged["distinct_attending_physicians_count"]

        merged["inpatient_claim_ratio"] = np.where(total_claims > 0, inp_claims_cnt / total_claims, 0.0)
        merged["inpatient_reimbursement_ratio"] = np.where(
            tot_reimb > 0, merged["inpatient_reimbursed_sum"] / tot_reimb, 0.0
        )
        merged["claims_per_beneficiary_mean"] = np.where(bene_cnt > 0, total_claims / bene_cnt, 0.0)
        merged["claims_per_attending_mean"] = np.where(att_cnt > 0, total_claims / att_cnt, 0.0)
        merged["diagnosis_diversity_ratio"] = np.where(
            total_claims > 0, merged["distinct_primary_diagnoses_count"] / total_claims, 0.0
        )
        merged["inpatient_procedure_ratio"] = np.where(
            inp_claims_cnt > 0, merged["inpatient_procedure_claim_count"] / inp_claims_cnt, 0.0
        )

        # 7. Isolate Features from Target Labels
        # Features Table: Keep 'Provider' as index for deterministic alignment, exclude from model columns
        ordered_feature_cols = [c for c in self.feature_columns if c in merged.columns]
        df_features = merged[ordered_feature_cols].copy()
        df_features = df_features.reset_index(drop=True)

        # Target Table: strictly separated
        target_lookup = df_target[["Provider", "target_binary"]].drop_duplicates()
        df_labels = spine.merge(target_lookup, on="Provider", how="left", validate="one_to_one")
        df_labels = df_labels.sort_values("Provider").reset_index(drop=True)
        if len(df_features) != len(df_labels) or df_labels["target_binary"].isna().any():
            raise ValueError("Feature and label rows do not align with the target provider spine.")
        attach_pair_contract(df_features, df_labels)

        # Summary Metrics
        pos_count = int(df_labels["target_binary"].sum())
        total_prov = len(df_labels)
        neg_count = total_prov - pos_count
        ratio = pos_count / total_prov if total_prov > 0 else 0.0

        summary = FeatureDatasetSummary(
            total_providers=total_prov,
            total_features=len(ordered_feature_cols),
            positive_fraud_count=pos_count,
            negative_fraud_count=neg_count,
            positive_class_ratio=round(ratio, 4),
            feature_names=ordered_feature_cols,
            target_column_name="target_binary",
            target_is_isolated=True,
            deterministic_ordering=True,
        )

        return df_features, df_labels, summary

    def export_processed_datasets(
        self,
        df_features: pd.DataFrame,
        df_labels: pd.DataFrame,
        quality_report: DataQualityReport,
        summary: FeatureDatasetSummary,
    ) -> Dict[str, Path]:
        """Save the engineered features, isolated labels, quality report, and dictionary to disk.

        Outputs are placed strictly inside `data/processed/`, which is ignored by Git.
        """
        output_dir = self.paths.processed_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        paths = {
            "features_parquet": self.paths.output_features_path,
            "features_csv": self.paths.output_features_csv_path,
            "targets_parquet": self.paths.output_targets_path,
            "targets_csv": self.paths.output_targets_csv_path,
            "report_json": self.paths.output_report_path,
            "dictionary_json": self.paths.output_dictionary_path,
            "manifest_json": self.paths.output_manifest_path,
        }
        # Verify the in-memory pair still matches the contract assigned during feature generation.
        feature_attached = df_features.attrs.get(PAIR_METADATA_ATTR)
        label_attached = df_labels.attrs.get(PAIR_METADATA_ATTR)
        if feature_attached is not None and label_attached is not None and feature_attached != label_attached:
            raise ValueError("Feature and label generation contracts do not match.")
        contract = validate_pair_frames(df_features, df_labels, feature_attached)
        for frame in (df_features, df_labels):
            attached = frame.attrs.get(PAIR_METADATA_ATTR)
            if attached is not None and any(attached.get(key) != value for key, value in contract.items()):
                raise ValueError("Feature or label rows changed after pair generation.")

        # Stage complete file set on the same filesystem, then publish manifest last as commit marker.
        with tempfile.TemporaryDirectory(prefix=".provider-export-", dir=output_dir) as temporary:
            stage = Path(temporary)
            staged = {key: stage / path.name for key, path in paths.items() if key != "manifest_json"}
            df_features.to_parquet(staged["features_parquet"], index=False)
            df_features.to_csv(staged["features_csv"], index=False)
            df_labels.to_parquet(staged["targets_parquet"], index=False)
            df_labels.to_csv(staged["targets_csv"], index=False)
            staged["report_json"].write_text(json.dumps(quality_report.model_dump(), indent=2), encoding="utf-8")
            dict_payload = {
                "summary": summary.model_dump(),
                "features": {k: v.model_dump() for k, v in FEATURE_DEFINITIONS.items()},
            }
            staged["dictionary_json"].write_text(json.dumps(dict_payload, indent=2), encoding="utf-8")
            manifest = build_manifest(stage, df_features, df_labels, contract["generation_id"])
            for key, staged_path in staged.items():
                os.replace(staged_path, paths[key])
            write_manifest_atomic(paths["manifest_json"], manifest)
        return paths
