import type { HealthResponse } from '../types/health';

export const API_BASE_URL: string =
  (import.meta.env.VITE_API_BASE_URL as string) || 'http://localhost:8000';

/**
 * Fetches system health and model readiness from the backend API.
 * Uses a 5-second timeout to promptly report connectivity issues.
 */
export async function fetchHealthStatus(): Promise<HealthResponse> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 5000);

  try {
    const response = await fetch(`${API_BASE_URL}/api/health`, {
      method: 'GET',
      headers: {
        Accept: 'application/json',
      },
      signal: controller.signal,
    });

    if (!response.ok) {
      throw new Error(`Health check failed with status: ${response.status} ${response.statusText}`);
    }

    const data: HealthResponse = await response.json();
    return data;
  } finally {
    clearTimeout(timeoutId);
  }
}
