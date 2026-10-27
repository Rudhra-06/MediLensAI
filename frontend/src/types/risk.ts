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

export interface ValidationMetricSet {
  precision: number;
  recall: number;
  f1: number;
  average_precision: number;
  roc_auc: number;
  confusion_matrix_labels_0_1: number[][];
}

export interface GlobalShapFeature {
  feature: string;
  mean_absolute_contribution: number;
  mean_signed_contribution: number;
  direction: string;
}

export interface GlobalShapSummary {
  shap_version: string;
  output_class: string;
  output_scale: 'positive-class probability';
  feature_count: number;
  background_sample_count: number;
  explanation_sample_count: number;
  importance_method: string;
  interpretation_limit: string;
  max_absolute_additivity_error: number;
  features: GlobalShapFeature[];
}

export interface ProviderRiskInsightsResponse {
  model_version: string;
  model_name: string;
  selected_model: string;
  selection_metric: string;
  split_strategy: string;
  train_provider_count: number;
  validation_provider_count: number;
  validation_metrics: Record<string, ValidationMetricSet>;
  limitations: string[];
  explainability_status: 'available' | 'unavailable';
  explainability_note: string | null;
  global_shap: GlobalShapSummary | null;
}
