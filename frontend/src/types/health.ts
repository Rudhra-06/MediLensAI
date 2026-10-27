/**
 * API Health and System Status Types
 */

export interface ModelReadiness {
  ready: boolean;
  status: 'ready' | 'not_ready' | 'degraded';
  reason: string;
  loaded_model_version: string | null;
}

export interface SubsystemStatus {
  database: string;
  claims_pipeline: string;
}

export interface HealthResponse {
  status: 'healthy' | 'degraded' | 'unhealthy';
  app_name: string;
  version: string;
  environment: string;
  timestamp: string;
  model_readiness: ModelReadiness;
  subsystems: SubsystemStatus;
}

export type ApiConnectionState = 'checking' | 'connected' | 'disconnected';
