export interface RiskHealthResponse {
  ready: boolean;
  status: 'ready' | 'unavailable';
  model_version: string;
  model_name: string | null;
  artifact_status: Record<string, boolean>;
  reason: string | null;
  disclaimer: string;
  local_demo_enabled?: boolean;
}

export interface RiskFeatureDescription {
  name: string;
  domain: string;
  data_type: string;
  description: string;
}

export type ProviderFeatureValues = Record<string, number>;

export interface RiskAssessmentResponse {
  risk_score: number;
  score_type: 'uncalibrated_model_score';
  model_version: string;
  disclaimer: string;
  assessment_mode?: 'retrospective_validation_demo';
  reference_id?: string;
  split_disclosure?: string;
}

export interface LocalDemoProvider {
  reference_id: string;
}

export interface LocalDemoProvidersResponse {
  enabled: boolean;
  split_disclosure: string;
  providers: LocalDemoProvider[];
  count: number;
}
