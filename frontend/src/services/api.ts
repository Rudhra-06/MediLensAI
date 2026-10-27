import type { HealthResponse } from '../types/health';
import type {
  ProviderFeatureValues,
  RiskAssessmentResponse,
  RiskFeatureDescription,
  RiskHealthResponse,
  LocalDemoProvidersResponse,
  ProviderRiskInsightsResponse,
} from '../types/risk';

export const API_BASE_URL: string =
  (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/$/, '');

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 10000);
  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      headers: { Accept: 'application/json', ...init?.headers },
      signal: controller.signal,
    });
    if (!response.ok) {
      let detail = `Request failed (${response.status})`;
      try {
        const body = (await response.json()) as { detail?: unknown };
        if (typeof body.detail === 'string') detail = body.detail;
        else if (Array.isArray(body.detail)) {
          detail = body.detail
            .map((item) => (typeof item?.msg === 'string' ? item.msg : 'Invalid request'))
            .join('; ');
        }
      } catch {
        // Keep the status-based message when the API returns a non-JSON error.
      }
      throw new Error(detail);
    }
    return (await response.json()) as T;
  } finally {
    clearTimeout(timeoutId);
  }
}

export function fetchHealthStatus(): Promise<HealthResponse> {
  return requestJson<HealthResponse>('/api/health');
}

export function fetchRiskHealth(): Promise<RiskHealthResponse> {
  return requestJson<RiskHealthResponse>('/api/v1/risk/health');
}

export function fetchRiskFeatures(): Promise<RiskFeatureDescription[]> {
  return requestJson<{ features: RiskFeatureDescription[] }>('/api/v1/risk/features').then(
    (response) => response.features,
  );
}

export function fetchRiskInsights(): Promise<ProviderRiskInsightsResponse> {
  return requestJson<ProviderRiskInsightsResponse>('/api/v1/risk/insights');
}

export function assessProvider(features: ProviderFeatureValues): Promise<RiskAssessmentResponse> {
  return requestJson<RiskAssessmentResponse>('/api/v1/risk/assess', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ features }),
  });
}

export function fetchLocalDemoProviders(): Promise<LocalDemoProvidersResponse> {
  return requestJson<LocalDemoProvidersResponse>('/api/v1/risk/demo/providers');
}

export function assessLocalDemoProvider(referenceId: string): Promise<RiskAssessmentResponse> {
  return requestJson<RiskAssessmentResponse>('/api/v1/risk/demo/assess', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ reference_id: referenceId }),
  });
}
