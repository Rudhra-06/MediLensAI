# MediLens AI

> **Explainable AI-Powered Healthcare Insurance Claim Fraud Screening and Investigation-Support Platform**
>
> *Predictions indicate potential fraud risk and suspicious patterns to support human review, never proof of fraud.*

---

## 1. Project Overview

**MediLens AI** is an explainable AI healthcare insurance claim screening and audit-support platform. It helps health plans, special investigation units (SIUs), and clinical auditors screen incoming claims, estimate statistical fraud risk, and understand the driving factors behind high-risk scores through interpretable SHAP explanations.

### Clinical & Legal Disclaimer
> **Important:** MediLens AI provides statistical risk estimation and explainability indicators solely to prioritize human auditor review. Predictions **do not constitute proof of fraud**, and the platform strictly forbids automated claims denial or adverse determinations without certified human adjudication.

---

## 2. Architecture & Tech Stack

```
MediLensAI/
├── backend/                  # FastAPI (Python 3.13)
│   ├── app/
│   │   ├── api/routes/       # Endpoints: /api/health
│   │   ├── core/             # Settings & CORS configuration
│   │   ├── schemas/          # Pydantic data schemas
│   │   └── main.py           # Application entry point
│   ├── tests/                # Pytest unit tests
│   └── requirements.txt      # Backend dependencies
├── frontend/                 # React 19 + TypeScript + Vite
│   ├── src/
│   │   ├── components/       # Enterprise UI components & 6 main pages
│   │   ├── services/         # API integration client
│   │   └── types/            # TypeScript interfaces
│   ├── package.json          # Frontend dependencies (Tailwind CSS, Lucide, Recharts)
│   └── vite.config.ts        # Vite configuration
├── pytest.ini                # Pytest configuration
├── .env.example              # Environment variable template
└── .gitignore                # Git ignore rules protecting data, secrets, and artifacts
```

### Detected & Deployed Stack Versions
- **Runtime:** Python 3.13.1, Node.js v24.11.1, npm 11.6.2
- **Backend:** FastAPI `0.162.0`, Uvicorn `0.54.0`, Pydantic `2.14.1`, Pydantic-Settings `2.16.1`, Pytest `9.1.1`, HTTPX `0.28.1`
- **Frontend:** React `19.3.1`, TypeScript `7.0.2`, Vite `8.3.5`, Tailwind CSS `v4`, Lucide React `1.16.0`, Recharts `3.8.0`
- **Future ML Engine (Planned):** scikit-learn, XGBoost, and SHAP (TreeExplainer)
- **Future Storage (Planned):** PostgreSQL

---

## 3. Prerequisites

- **Python:** 3.11+ (verified with Python 3.13.1)
- **Node.js:** v18+ (verified with Node.js v24.11.1)
- **npm:** 9+ (verified with npm 11.6.2)
- **Git:** Version control installed

---

## 4. Installation & Setup

### A. Clone & Configure Environment
```bash
# Clone or navigate to the repository
cd D:\Projects\MediLensAI

# Create your local environment configuration
copy .env.example .env
```

### B. Backend Virtual Environment Setup
```bash
# Create local virtual environment
python -m venv backend/.venv

# Activate the virtual environment
# Windows (PowerShell):
backend\.venv\Scripts\Activate.ps1
# Windows (CMD):
backend\.venv\Scripts\activate.bat
# Linux / macOS:
source backend/.venv/bin/activate

# Install backend dependencies
pip install -r backend/requirements.txt
```

### C. Frontend Dependencies Setup
```bash
# Navigate to frontend directory and install dependencies
cd frontend
npm install
cd ..
```

---

## 5. Running the Application

Both services should run concurrently for full end-to-end integration:

### Terminal 1: Backend API Service
```bash
# From workspace root (D:\Projects\MediLensAI)
backend\.venv\Scripts\python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
- **API Base:** `http://127.0.0.1:8000`
- **Health Check Endpoint:** `http://127.0.0.1:8000/api/health`
- **Interactive Swagger Docs:** `http://127.0.0.1:8000/docs`

### Terminal 2: Frontend Web Application
```bash
# From workspace root (D:\Projects\MediLensAI)
cd frontend
npm run dev
```
- **Vite Dev Server:** `http://localhost:5173`
- Connected automatically to backend API at `http://localhost:8000`

---

## 6. Testing & Validation

### Backend Tests
```bash
# Run pytest test suite from workspace root
backend\.venv\Scripts\pytest -v
```
*Current test suite verifies the root endpoint metadata, CORS headers, and the health check endpoint distinguishing API connectivity from model readiness.*

### Frontend Checks & Production Build
```bash
cd frontend
# Run linter
npm run lint

# Run TypeScript type check and Vite production build
npm run build
```

---

## 7. Current Implementation Status (Part 01, Step 1)

| Area | Status | Notes |
| :--- | :---: | :--- |
| **Repository Foundation** | Completed | Clean Git setup, `.gitignore`, `.env.example`, `pytest.ini` |
| **FastAPI Backend Core** | Completed | Entry point, configuration management, `/api/health`, CORS |
| **API Health Distinctions**| Completed | Distinguishes API status (`healthy`), version (`0.1.0`), and ML readiness (`not_ready`) |
| **Frontend Enterprise Shell** | Completed | Deep navy `#0B192C` + restrained teal `#0D9488` design tokens, responsive sidebar |
| **Frontend/Backend Integration** | Completed | Real-time health polling, status badges (`Connected` / `Disconnected` / `Checking`) |
| **Platform Overview** | Completed | Infrastructure status, honest empty baseline metrics, illustrative distribution chart |
| **Claims Intelligence** | Completed | Single and batch screening architecture blueprints; clear coming-soon states |
| **Investigation Queue** | Completed | Honest empty queue state, triage filter preview, planned schema layout |
| **Model Insights & SHAP**| Completed | Architecture blueprint, global feature importance specifications, local waterfall format |
| **Data Management** | Completed | Data governance principles, synthetic data exclusivity notice, validation matrix |
| **System Settings** | Completed | Read-only runtime parameter inspector, risk threshold calibration defaults |

---

## 8. Development Roadmap

- **Phase 02: Claim Ingestion & Validation Engine**
  - Parsing CMS-1500 / UB-04 and synthetic EDI-837 claim files.
  - Ingestion invariant validator (NPI registry check, diagnosis-procedure pairing).
  - PostgreSQL database models and claim repository.
- **Phase 03: Explainable ML Risk Estimation Pipeline**
  - Supervised training pipeline (scikit-learn + XGBoost classifier).
  - Calibrated probability outputs `[0.0, 1.0]`.
  - Offline cross-validation and bias audit.
- **Phase 04: SHAP Explainability Engine**
  - TreeExplainer calculation for batch and ad-hoc single claims.
  - Interactive waterfall diagrams and force plots.
- **Phase 05: Human-in-the-Loop Investigation Station**
  - Live queue triage, auditor notes, document requests, and resolution logging.
