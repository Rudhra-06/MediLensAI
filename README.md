# MediLens AI

MediLens AI is a local development project for **provider-level retrospective risk screening** using an aggregated Medicare claims dataset. It is an educational and engineering prototype, not a claims adjudication or fraud investigation system.

> **Safety notice:** The target is the source dataset's `PotentialFraud` provider label. It is not verified fraud. Model scores are uncalibrated and do not establish wrongdoing, causation, or real-world performance. Do not use them for denial, payment, referral, or other adverse decisions.

## Architecture

- `backend/`: FastAPI, Pydantic schemas, pandas/NumPy data pipeline, saved scikit-learn model and pytest tests.
- `frontend/`: React, TypeScript and Vite dashboard. Provider assessment supports manually supplied feature values and an optional local retrospective demo.
- `data/raw/`: local source CSV files (not committed).
- `data/processed/`: locally generated features, labels, feature dictionary and quality report (not committed).
- `models/`: fitted model and JSON model, metrics and explanation artifacts (not committed).

The offline pipeline ingests claim and beneficiary tables, validates their schemas and keys, creates one provider feature row per labeled provider, and writes the target separately. Its implementation is in `backend/app/ml/ingestion.py` and `backend/app/ml/features.py` (`DataIngestionPipeline` and `ProviderFeatureEngineer`). The training function `train_provider_risk_model` in `backend/app/ml/model.py` compares a prior dummy classifier, class-balanced logistic regression and class-balanced random forest. Preprocessing is fit within the training partition. The selected saved pipeline is loaded once by FastAPI; requests do not retrain it.

Processed feature/label exports are paired by the ignored `data/processed/artifact_manifest.json`. The manifest records a generation UUID, schema and row counts, SHA-256 fingerprints of the ordered provider-key sequence, feature schema and feature values, target metadata, and checksums of the complete processed output set. Training, API startup and local demo loading validate this manifest and fail closed on missing or mismatched artifacts. Re-run feature export to establish a new generation after changing processed outputs; do not copy feature and label files independently.

## Requirements and setup

Prerequisites: Python 3.11 or newer, Node.js 20.19+ (or 22.12+) for the Vite 8 toolchain, and npm. From the repository root on Windows PowerShell:

```powershell
python -m venv backend/.venv
backend\.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements.txt
Copy-Item .env.example .env
cd frontend
npm install
Copy-Item .env.example .env.local
```

Put the locally licensed/source dataset files in the expected `data/raw/` paths described by `backend/app/ml/config.py`. Run the existing ingestion/feature engineering and model training functions from the backend environment to create `data/processed/` and `models/` artifacts. The raw data and generated outputs are intentionally excluded from Git. The API needs the saved model, configuration, feature list and processed feature dictionary to start inference successfully.

Start the backend from the repository root:

```powershell
backend\.venv\Scripts\python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

Start the frontend in a second terminal:

```powershell
cd frontend
npm run dev
```

Set `VITE_API_BASE_URL` in `frontend/.env.local` if the API is not at `http://localhost:8000`; restart Vite after changing it. Interactive API documentation is at `http://127.0.0.1:8000/docs`.

Backend `CORS_ORIGINS` must be a comma-separated list of explicit HTTP(S) origins: plain HTTP is accepted only for loopback development origins; non-loopback origins must use HTTPS. Wildcard origins are rejected, and the API does not enable credentialed CORS.

## Data provenance and limitations

The configured raw table names and schema correspond to the CMS SynPUF-style Medicare data bundle (provider labels, beneficiary data, inpatient claims and outpatient claims). The repository does not record the exact download URL, version, or provenance chain for the supplied provider `PotentialFraud` label file, so that label source cannot be independently verified from this project. Source CSVs are not tracked; a new checkout must obtain authorized files independently. Do not copy raw data or generated row-level artifacts into source control or public storage. Check source dataset terms and permissions before use.

Features are retrospective provider aggregates. Their observation window is not separated from the label period; this may cause temporal leakage. Beneficiary attributes and claim aggregates are sensitive even after direct identifiers are removed. This repository does not establish a production privacy or security boundary.

## Model workflow and recorded validation

The saved baseline uses 32 numeric provider aggregate features and a single stratified split with seed 42: 4,328 providers for training and 1,082 for validation. The labels are 506 positive and 4,904 negative overall. The validation partition contains 101 positives and 981 negatives. The model was selected using validation Average Precision; therefore this partition is **not an independent test set**. No separate test set, calibration, threshold optimization, prospective evaluation, subgroup fairness audit or deployment validation was performed.

The recorded validation Average Precision values are 0.0933 for the prior dummy baseline, 0.7697 for logistic regression, and 0.7868 for the selected random forest. These are retrospective single-split results and must not be interpreted as expected real-world performance. Metrics and limitations are saved locally in `models/provider_risk_metrics.json`.

`PotentialFraud` is kept in a separate label table and never included in the feature matrix or inference request. Provider, beneficiary, claim and physician IDs are not model features. The API accepts only the exact feature schema and rejects extra fields. The model score is an uncalibrated output associated with class `PotentialFraud=1`, not a calibrated probability.

## API

The general API health route is `GET /api/health`. Risk endpoints are under `/api/v1/risk`:

| Method and path | Purpose |
| --- | --- |
| `GET /risk/health` | Risk model and required artifact readiness |
| `GET /risk/features` | Feature names, domains and safe descriptions |
| `POST /risk/assess` | Score one manually supplied 32-feature provider vector |
| `POST /risk/assess/batch` | Score a bounded batch of vectors |
| `GET /risk/demo/providers` | Optional local-only ephemeral demo references |
| `POST /risk/demo/assess` | Score one selected local demo reference |

The manual request has the form `{"features": {"feature_name": 1.0, ...}}` and must contain exactly the documented numeric features. Responses label the score `uncalibrated_model_score` and include a disclaimer. No API provides a general processed dataset download or accepts arbitrary file paths.

## Local retrospective demo

The demo is disabled by default. For a local demonstration only, set the following in backend `.env`:

```dotenv
MEDILENS_ENV=development
LOCAL_PROVIDER_DEMO_ENABLED=true
API_HOST=127.0.0.1
```

Restart FastAPI and open the Provider Risk Assessment page. The selector exposes at most 20 random per-process aliases. Backend code reconstructs the saved stratified validation split, chooses a deterministic small sample from it, and keeps its feature rows in process memory. The source provider IDs and target labels are discarded by the demo registry and never returned. Aliases expire when the process restarts. The API requires loopback peer/Host/Origin values and rejects forwarded/proxy headers. Do not place the local demo behind a reverse proxy or expose the development API to a network; a proxy that strips client metadata can invalidate application-level locality checks. The API does not expose the underlying vectors.

These rows were withheld from fitting but their validation partition was used to compare and select models. The demo therefore illustrates the application workflow; it is not unseen performance evaluation. Disable the demo outside local development. Manual feature entry remains available without asserting that values identify a real provider.

## Privacy and ethical safeguards

- Raw and processed datasets, model artifacts and local environments are Git-ignored.
- Do not log request bodies, provider/beneficiary/physician IDs, claims or row-level data.
- The local demo is opt-in, loopback-only, returns ephemeral aliases, and withholds IDs, labels and feature vectors.
- Feature contributions and scores describe model behavior only. They are not proof of fraud or causal explanations.
- PotentialFraud means the source dataset label, not a verified finding.
- Human review, independent validation, privacy review, temporal evaluation and fairness assessment would be necessary before any operational use.

## Verification

Run the backend suite from the repository root:

```powershell
backend\.venv\Scripts\python -m pytest backend/tests -q
```

Run frontend static checks and production build:

```powershell
cd frontend
npm run lint
npm run build
```
