"""Configuration and paths for MediLens AI data ingestion and feature pipelines."""
import os
from pathlib import Path
from typing import Dict, List, Set
from pydantic import BaseModel, Field


class DatasetPaths(BaseModel):
    """Filepaths and directory configurations for datasets."""

    raw_dir: Path = Field(
        default_factory=lambda: Path(
            os.getenv("MEDILENS_DATA_RAW_DIR", Path(__file__).resolve().parents[3] / "data" / "raw")
        )
    )
    processed_dir: Path = Field(
        default_factory=lambda: Path(
            os.getenv("MEDILENS_DATA_PROCESSED_DIR", Path(__file__).resolve().parents[3] / "data" / "processed")
        )
    )

    train_target_filename: str = "Train-1542865627584.csv"
    train_beneficiary_filename: str = "Train_Beneficiarydata-1542865627584.csv"
    train_inpatient_filename: str = "Train_Inpatientdata-1542865627584.csv"
    train_outpatient_filename: str = "Train_Outpatientdata-1542865627584.csv"

    @property
    def train_target_path(self) -> Path:
        return self.raw_dir / self.train_target_filename

    @property
    def train_beneficiary_path(self) -> Path:
        return self.raw_dir / self.train_beneficiary_filename

    @property
    def train_inpatient_path(self) -> Path:
        return self.raw_dir / self.train_inpatient_filename

    @property
    def train_outpatient_path(self) -> Path:
        return self.raw_dir / self.train_outpatient_filename

    @property
    def output_features_path(self) -> Path:
        return self.processed_dir / "provider_features.parquet"

    @property
    def output_features_csv_path(self) -> Path:
        return self.processed_dir / "provider_features.csv"

    @property
    def output_targets_path(self) -> Path:
        return self.processed_dir / "target_labels.parquet"

    @property
    def output_targets_csv_path(self) -> Path:
        return self.processed_dir / "target_labels.csv"

    @property
    def output_report_path(self) -> Path:
        return self.processed_dir / "data_quality_report.json"

    @property
    def output_dictionary_path(self) -> Path:
        return self.processed_dir / "feature_dictionary.json"

    @property
    def output_manifest_path(self) -> Path:
        return self.processed_dir / "artifact_manifest.json"


class DatasetConfig:
    """Schema contracts and required column constraints."""

    # Target table constraints
    REQUIRED_TARGET_COLUMNS: Set[str] = {"Provider", "PotentialFraud"}

    # Beneficiary table constraints
    REQUIRED_BENEFICIARY_COLUMNS: Set[str] = {
        "BeneID",
        "DOB",
        "Gender",
        "Race",
        "RenalDiseaseIndicator",
        "State",
        "County",
    }

    # 11 Chronic conditions tracked in CMS SynPUF
    CHRONIC_CONDITION_COLUMNS: List[str] = [
        "ChronicCond_Alzheimer",
        "ChronicCond_Heartfailure",
        "ChronicCond_KidneyDisease",
        "ChronicCond_Cancer",
        "ChronicCond_ObstrPulmonary",
        "ChronicCond_Depression",
        "ChronicCond_Diabetes",
        "ChronicCond_IschemicHeart",
        "ChronicCond_Osteoporasis",
        "ChronicCond_rheumatoidarthritis",
        "ChronicCond_stroke",
    ]

    # Inpatient claims table constraints
    REQUIRED_INPATIENT_COLUMNS: Set[str] = {
        "BeneID",
        "ClaimID",
        "ClaimStartDt",
        "ClaimEndDt",
        "Provider",
        "InscClaimAmtReimbursed",
        "AdmissionDt",
        "DischargeDt",
    }

    # Outpatient claims table constraints
    REQUIRED_OUTPATIENT_COLUMNS: Set[str] = {
        "BeneID",
        "ClaimID",
        "ClaimStartDt",
        "ClaimEndDt",
        "Provider",
        "InscClaimAmtReimbursed",
    }

    # Encoding
    DEFAULT_ENCODING: str = "utf-8"
