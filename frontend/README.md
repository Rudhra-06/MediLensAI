# MediLens AI - Frontend

React 19 + TypeScript + Vite healthcare analytics interface for MediLens AI.

- **Styling:** Tailwind CSS
- **Icons:** Lucide React
- **Charts:** Recharts
- **API Integration:** Connects to FastAPI system health and provider risk endpoints.

## Local API configuration

Copy `.env.example` to `.env.local` and set `VITE_API_BASE_URL` to the FastAPI
origin (for example, `http://localhost:8000`). Restart Vite after changing it.
The default origin is `http://localhost:8000`.

The Provider Risk Assessment screen supports manual feature entry and, only
when `LOCAL_PROVIDER_DEMO_ENABLED=true` in a development backend, a loopback-only
selector of anonymous temporary references backed by a small sample of the
saved validation split. The demo withholds provider IDs, labels and feature
vectors. The validation split was used for model selection, so the demo is not
an independent evaluation. Scores are uncalibrated outputs for the provider
`PotentialFraud` dataset label, not verified fraud. See the root README for the
privacy safeguards and limitations.

See the root [README.md](../README.md) for complete project architecture, installation, and execution instructions.
