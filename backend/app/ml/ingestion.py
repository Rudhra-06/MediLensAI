"""Data ingestion, validation, and integrity auditing pipeline for MediLens AI."""
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Tuple
import numpy as np
import pandas as pd

from backend.app.ml.config import DatasetConfig, DatasetPaths
from backend.app.ml.contracts import DataQualityReport

logger = logging.getLogger("medilens.ingestion")


class IngestionError(Exception):
    """Base exception for data ingestion failures."""
    pass


class DatasetNotFoundError(IngestionError, FileNotFoundError):
    """Raised when expected dataset file is missing."""
    pass


class MalformedSchemaError(IngestionError, ValueError):
    """Raised when required schema columns are missing or corrupted."""
    pass


class DataIntegrityError(IngestionError, ValueError):
    """Raised when referential integrity or uniqueness invariants fail."""
    pass


class DataIngestionPipeline:
    """Manages secure, memory-conscious loading and validation of training datasets."""

    def __init__(self, paths: Optional[DatasetPaths] = None):
        self.paths = paths or DatasetPaths()
        self.quality_report: Optional[DataQualityReport] = None

    def validate_dataset_presence(self) -> None:
        """Verify that all four required training CSV files exist before reading."""
        required_files = [
            ("Target Labels", self.paths.train_target_path),
            ("Beneficiary Data", self.paths.train_beneficiary_path),
            ("Inpatient Claims", self.paths.train_inpatient_path),
            ("Outpatient Claims", self.paths.train_outpatient_path),
        ]
        missing = [f"{desc} ({path})" for desc, path in required_files if not path.exists()]
        if missing:
            raise DatasetNotFoundError(
                f"Missing required training datasets: {', '.join(missing)}. "
                "Ensure raw datasets are present in configured data/raw directory."
            )

    @staticmethod
    def _validate_schema(df: pd.DataFrame, required_columns: set, table_name: str) -> None:
        """Assert that all required schema columns are present."""
        if df.empty:
            raise MalformedSchemaError(f"Table '{table_name}' contains no data rows.")
        missing = required_columns - set(df.columns)
        if missing:
            raise MalformedSchemaError(
                f"Table '{table_name}' is missing required columns: {sorted(list(missing))}"
            )

    def load_target_data(self) -> pd.DataFrame:
        """Load and validate provider target labels (Train-*.csv)."""
        path = self.paths.train_target_path
        df = self._read_csv(path, dtype={"Provider": str, "PotentialFraud": str})
        self._validate_schema(df, DatasetConfig.REQUIRED_TARGET_COLUMNS, "Target")

        # Invariant: Provider must be unique
        if df["Provider"].duplicated().any():
            dup_count = int(df["Provider"].duplicated().sum())
            raise DataIntegrityError(f"Target table contains {dup_count} duplicate Provider entries.")
        if df["Provider"].isna().any() or df["Provider"].str.strip().eq("").any():
            raise MalformedSchemaError("Target table contains missing or blank Provider identifiers.")

        # Standardize target values: Yes -> 1, No -> 0
        normalized = df["PotentialFraud"].astype(str).str.strip().str.casefold()
        invalid = ~normalized.isin({"yes", "no", "1", "0"})
        if invalid.any():
            raise MalformedSchemaError(
                f"Target table contains {int(invalid.sum())} unexpected values in PotentialFraud."
            )
        df["target_binary"] = normalized.map({"yes": 1, "1": 1, "no": 0, "0": 0}).astype("int8")
        return df

    def load_beneficiary_data(self) -> pd.DataFrame:
        """Load and validate beneficiary demographics and chronic conditions."""
        path = self.paths.train_beneficiary_path
        df = self._read_csv(
            path,
            dtype={"BeneID": str, "State": str, "County": str, "RenalDiseaseIndicator": str},
        )
        self._validate_schema(df, DatasetConfig.REQUIRED_BENEFICIARY_COLUMNS, "Beneficiary")

        if df["BeneID"].duplicated().any():
            dup_count = int(df["BeneID"].duplicated().sum())
            raise DataIntegrityError(f"Beneficiary table contains {dup_count} duplicate BeneID entries.")
        if df["BeneID"].isna().any() or df["BeneID"].str.strip().eq("").any():
            raise MalformedSchemaError("Beneficiary table contains missing or blank BeneID identifiers.")

        # Parse birth date to calculate approximate age in 2009 (service year)
        # Note: CMS SynPUF DOB is YYYY-MM-DD
        birth_year = pd.to_datetime(df["DOB"], errors="coerce").dt.year
        df["patient_age"] = (2009 - birth_year).clip(lower=0, upper=120).fillna(65.0)

        # Binary ESRD indicator
        df["is_renal_disease"] = (
            df["RenalDiseaseIndicator"].astype(str).str.strip().isin({"Y", "1", 1}).astype(int)
        )

        # Count active chronic conditions (1 = condition present, 2 = absent in CMS SynPUF)
        chronic_cols = [c for c in DatasetConfig.CHRONIC_CONDITION_COLUMNS if c in df.columns]
        if chronic_cols:
            df["chronic_conditions_count"] = (df[chronic_cols] == 1).sum(axis=1)
        else:
            df["chronic_conditions_count"] = 0

        return df

    def load_inpatient_claims(self) -> pd.DataFrame:
        """Load and validate inpatient hospital claims."""
        path = self.paths.train_inpatient_path
        df = self._read_csv(
            path,
            dtype={
                "BeneID": str,
                "ClaimID": str,
                "Provider": str,
                "AttendingPhysician": str,
                "OperatingPhysician": str,
                "OtherPhysician": str,
                "ClmAdmitDiagnosisCode": str,
                "ClmDiagnosisCode_1": str,
                "ClmProcedureCode_1": str,
            },
        )
        self._validate_schema(df, DatasetConfig.REQUIRED_INPATIENT_COLUMNS, "Inpatient")

        if df["ClaimID"].duplicated().any():
            dup_count = int(df["ClaimID"].duplicated().sum())
            raise DataIntegrityError(f"Inpatient claims table contains {dup_count} duplicate ClaimIDs.")
        self._validate_claim_keys(df, "Inpatient")

        df["InscClaimAmtReimbursed"] = self._numeric_column(df, "InscClaimAmtReimbursed", "Inpatient")
        df["DeductibleAmtPaid"] = self._numeric_column(df, "DeductibleAmtPaid", "Inpatient", required=False)

        # Calculate claim duration and length of stay
        start_dt = pd.to_datetime(df["ClaimStartDt"], errors="coerce")
        end_dt = pd.to_datetime(df["ClaimEndDt"], errors="coerce")
        df["claim_duration_days"] = ((end_dt - start_dt).dt.days + 1).clip(lower=1).fillna(1.0)

        admit_dt = pd.to_datetime(df["AdmissionDt"], errors="coerce")
        discharge_dt = pd.to_datetime(df["DischargeDt"], errors="coerce")
        df["length_of_stay_days"] = ((discharge_dt - admit_dt).dt.days).clip(lower=0).fillna(0.0)

        df["is_inpatient"] = 1
        return df

    def load_outpatient_claims(self) -> pd.DataFrame:
        """Load and validate outpatient clinic claims."""
        path = self.paths.train_outpatient_path
        df = self._read_csv(
            path,
            dtype={
                "BeneID": str,
                "ClaimID": str,
                "Provider": str,
                "AttendingPhysician": str,
                "OperatingPhysician": str,
                "OtherPhysician": str,
                "ClmAdmitDiagnosisCode": str,
                "ClmDiagnosisCode_1": str,
                "ClmProcedureCode_1": str,
            },
        )
        self._validate_schema(df, DatasetConfig.REQUIRED_OUTPATIENT_COLUMNS, "Outpatient")

        if df["ClaimID"].duplicated().any():
            dup_count = int(df["ClaimID"].duplicated().sum())
            raise DataIntegrityError(f"Outpatient claims table contains {dup_count} duplicate ClaimIDs.")
        self._validate_claim_keys(df, "Outpatient")

        df["InscClaimAmtReimbursed"] = self._numeric_column(df, "InscClaimAmtReimbursed", "Outpatient")
        df["DeductibleAmtPaid"] = self._numeric_column(df, "DeductibleAmtPaid", "Outpatient", required=False)

        start_dt = pd.to_datetime(df["ClaimStartDt"], errors="coerce")
        end_dt = pd.to_datetime(df["ClaimEndDt"], errors="coerce")
        df["claim_duration_days"] = ((end_dt - start_dt).dt.days + 1).clip(lower=1).fillna(1.0)
        df["length_of_stay_days"] = 0.0  # Outpatient claims do not have inpatient stays

        df["is_inpatient"] = 0
        return df

    def execute_ingestion(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, DataQualityReport]:
        """Execute the end-to-end ingestion and integrity audit pipeline.

        Returns:
            Tuple of (df_target, df_beneficiary, df_inpatient, df_outpatient, quality_report)
        """
        self.validate_dataset_presence()

        df_target = self.load_target_data()
        df_beneficiary = self.load_beneficiary_data()
        df_inpatient = self.load_inpatient_claims()
        df_outpatient = self.load_outpatient_claims()

        # Check ClaimID overlap between Inpatient and Outpatient
        inp_claims = set(df_inpatient["ClaimID"])
        out_claims = set(df_outpatient["ClaimID"])
        overlap_claims = inp_claims & out_claims
        if overlap_claims:
            raise DataIntegrityError(
                f"Found {len(overlap_claims)} ClaimIDs present in both Inpatient and Outpatient datasets."
            )

        # Referential integrity: check BeneIDs in claims vs Beneficiary table
        all_bene_ids = set(df_beneficiary["BeneID"])
        inp_missing_bene = int((~df_inpatient["BeneID"].isin(all_bene_ids)).sum())
        out_missing_bene = int((~df_outpatient["BeneID"].isin(all_bene_ids)).sum())

        # Referential integrity: check Providers in target vs claims
        all_claim_providers = set(df_inpatient["Provider"]) | set(df_outpatient["Provider"])
        target_providers = set(df_target["Provider"])
        target_missing_claims = int((~df_target["Provider"].isin(all_claim_providers)).sum())

        warnings = []
        if inp_missing_bene > 0:
            warnings.append(f"{inp_missing_bene} inpatient claims reference unrecorded BeneIDs.")
        if out_missing_bene > 0:
            warnings.append(f"{out_missing_bene} outpatient claims reference unrecorded BeneIDs.")
        if target_missing_claims > 0:
            warnings.append(f"{target_missing_claims} target providers have zero claims recorded.")

        # Class balance metrics
        total_providers = len(df_target)
        positive_count = int(df_target["target_binary"].sum())
        negative_count = total_providers - positive_count
        pos_ratio = positive_count / total_providers if total_providers > 0 else 0.0

        quality_report = DataQualityReport(
            status="passed" if not warnings else "warning",
            timestamp=datetime.now(timezone.utc).isoformat(),
            raw_dataset_counts={
                "target_providers": total_providers,
                "beneficiaries": len(df_beneficiary),
                "inpatient_claims": len(df_inpatient),
                "outpatient_claims": len(df_outpatient),
                "total_claims": len(df_inpatient) + len(df_outpatient),
            },
            unique_identifiers={
                "unique_providers": len(target_providers),
                "unique_beneficiaries": len(all_bene_ids),
                "unique_claims": len(inp_claims) + len(out_claims),
            },
            duplicate_records={
                "duplicate_target_providers": 0,
                "duplicate_beneficiaries": 0,
                "duplicate_inpatient_claims": 0,
                "duplicate_outpatient_claims": 0,
                "inpatient_outpatient_claim_overlap": len(overlap_claims),
            },
            missing_value_summary={
                "inpatient": {
                    "AttendingPhysician": int(df_inpatient["AttendingPhysician"].isna().sum()),
                    "OperatingPhysician": int(df_inpatient["OperatingPhysician"].isna().sum()),
                    "ClmProcedureCode_1": int(df_inpatient["ClmProcedureCode_1"].isna().sum()),
                },
                "outpatient": {
                    "AttendingPhysician": int(df_outpatient["AttendingPhysician"].isna().sum()),
                    "OperatingPhysician": int(df_outpatient["OperatingPhysician"].isna().sum()),
                    "ClmProcedureCode_1": int(df_outpatient["ClmProcedureCode_1"].isna().sum()),
                },
            },
            referential_integrity_checks={
                "inpatient_bene_ids_valid": inp_missing_bene == 0,
                "outpatient_bene_ids_valid": out_missing_bene == 0,
                "target_providers_in_claims": target_missing_claims == 0,
                "claim_ids_mutually_exclusive": len(overlap_claims) == 0,
            },
            target_distribution={
                "total": total_providers,
                "positive_fraud_yes": positive_count,
                "negative_fraud_no": negative_count,
                "positive_class_ratio": round(pos_ratio, 4),
            },
            warnings=warnings,
        )

        self.quality_report = quality_report
        return df_target, df_beneficiary, df_inpatient, df_outpatient, quality_report

    @staticmethod
    def _validate_claim_keys(df: pd.DataFrame, table_name: str) -> None:
        for column in ("ClaimID", "BeneID", "Provider"):
            if df[column].isna().any() or df[column].astype(str).str.strip().eq("").any():
                raise MalformedSchemaError(f"{table_name} claims contain missing or blank {column} identifiers.")

    @staticmethod
    def _read_csv(path: Path, **kwargs) -> pd.DataFrame:
        """Read with bounded parser memory and provide a safe, non-row-level error."""
        try:
            return pd.read_csv(path, encoding=DatasetConfig.DEFAULT_ENCODING, low_memory=False, **kwargs)
        except (pd.errors.EmptyDataError, pd.errors.ParserError, UnicodeDecodeError) as exc:
            raise MalformedSchemaError(f"Could not parse dataset file '{path.name}'.") from exc

    @staticmethod
    def _numeric_column(df: pd.DataFrame, column: str, table_name: str, required: bool = True) -> pd.Series:
        if column not in df:
            if required:
                raise MalformedSchemaError(f"Table '{table_name}' is missing required column '{column}'.")
            return pd.Series(0.0, index=df.index)
        original = df[column]
        converted = pd.to_numeric(original, errors="coerce")
        invalid = original.notna() & converted.isna()
        if invalid.any():
            raise MalformedSchemaError(f"Table '{table_name}' contains {int(invalid.sum())} invalid values in '{column}'.")
        return converted.fillna(0.0).astype("float64")
