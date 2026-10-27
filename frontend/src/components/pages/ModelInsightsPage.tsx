import React from 'react';
import {
  BrainCircuit,
  BarChart2,
  Sparkles,
} from 'lucide-react';
import { EmptyState } from '../common/EmptyState';
import { DisclaimerBanner } from '../common/DisclaimerBanner';

export const ModelInsightsPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <DisclaimerBanner />

      {/* Header with Model Readiness Status */}
      <div className="bg-white rounded-xl border border-slate-200/90 p-5 shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base font-bold text-slate-900">
                Model Explainability & SHAP Insights
              </h2>
              <span className="text-[11px] font-semibold bg-amber-50 text-amber-800 border border-amber-200 px-2.5 py-0.5 rounded-full">
                Training Pending
              </span>
            </div>
            <p className="text-xs text-slate-600 mt-1 max-w-2xl">
              Transparent, interpretable fraud risk estimation powered by TreeSHAP. Auditors can inspect global feature contributions and per-claim local waterfalls explaining why a claim scored high risk.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs bg-slate-100 text-slate-700 px-3 py-1.5 rounded-lg border border-slate-200 font-mono">
              Model: None Loaded
            </span>
          </div>
        </div>
      </div>

      {/* Honest Empty State for Model */}
      <EmptyState
        icon={BrainCircuit}
        title="No Trained Model Loaded"
        description="The ML risk pipeline (scikit-learn + XGBoost + SHAP TreeExplainer) has not yet been trained or loaded into the backend runtime. No fabricated accuracy, AUC-ROC, or precision-recall figures are generated."
        badgeText="Model Pipeline Unloaded"
        badgeType="amber"
        secondaryNotice="In Phase 03, the pipeline will ingest synthetic training claims, perform cross-validation, and serialize an XGBoost classifier with its corresponding SHAP explainer."
      />

      {/* Explainability Architecture Blueprint */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Planned Global Feature Importance Blueprint */}
        <div className="bg-white rounded-xl border border-slate-200/90 p-5 shadow-xs">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <BarChart2 className="w-4 h-4 text-teal-600" />
              <h3 className="text-sm font-bold text-slate-900">
                Planned Global SHAP Summary
              </h3>
            </div>
            <span className="text-[10px] bg-slate-100 text-slate-600 px-2 py-0.5 rounded-sm border border-slate-200">
              Architecture Blueprint
            </span>
          </div>

          <p className="text-xs text-slate-500 mb-4">
            Aggregates mean absolute SHAP values across the entire validation cohort to identify the primary systematic fraud signals across healthcare domains:
          </p>

          <div className="space-y-2.5 text-xs">
            {[
              {
                name: 'Procedure Unbundling Indicator (CPT pairing)',
                domain: 'Billing Anomalies',
                expectedRole: 'High positive impact on risk',
              },
              {
                name: 'Provider Billing Velocity (claims/day ratio)',
                domain: 'Behavioral Volume',
                expectedRole: 'High positive impact on risk',
              },
              {
                name: 'Billed-to-Allowed Amount Discrepancy Ratio',
                domain: 'Financial Deviation',
                expectedRole: 'Moderate positive impact',
              },
              {
                name: 'Diagnosis-to-Procedure Clinical Coherence',
                domain: 'Medical Necessity',
                expectedRole: 'Negative impact if standard match',
              },
              {
                name: 'Duplicate Beneficiary Service Frequency',
                domain: 'Beneficiary Overuse',
                expectedRole: 'High positive impact on risk',
              },
            ].map((f, i) => (
              <div
                key={i}
                className="p-2.5 rounded-lg bg-slate-50 border border-slate-200/70 flex items-center justify-between"
              >
                <div>
                  <div className="font-semibold text-slate-800 text-[11px]">{f.name}</div>
                  <div className="text-[10px] text-slate-500 mt-0.5">{f.domain}</div>
                </div>
                <span className="text-[10px] text-teal-800 bg-teal-50 border border-teal-200 px-2 py-0.5 rounded-full font-medium shrink-0">
                  {f.expectedRole}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Planned Local Explanation / Waterfall Blueprint */}
        <div className="bg-white rounded-xl border border-slate-200/90 p-5 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-teal-600" />
                <h3 className="text-sm font-bold text-slate-900">
                  Per-Claim Local Explanation Schema
                </h3>
              </div>
              <span className="text-[10px] bg-slate-100 text-slate-600 px-2 py-0.5 rounded-sm border border-slate-200">
                Auditor View
              </span>
            </div>

            <p className="text-xs text-slate-500 mb-4">
              Every flagged claim presented to an investigator will include an individualized SHAP decomposition answering: <em>"Why did the model assign this risk score?"</em>
            </p>

            <div className="bg-slate-900 text-slate-200 rounded-lg p-4 font-mono text-[11px] leading-relaxed border border-slate-800 overflow-x-auto">
              <div className="text-slate-400 mb-2">// Planned Local SHAP API Response Schema:</div>
              <pre className="text-teal-300">
{`{
  "claim_id": "CLM-SYNTH-XXXX",
  "base_value": 0.12,          // Dataset baseline risk
  "predicted_risk": 0.81,      // Estimated risk score
  "risk_tier": "HIGH_SUSPICION",
  "shap_contributions": [
    { "feature": "billing_velocity", "val": 42.0, "shap": +0.35 },
    { "feature": "unbundling_score", "val": 0.94, "shap": +0.22 },
    { "feature": "provider_tenure",  "val": 8.5,  "shap": -0.06 }
  ]
}`}
              </pre>
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-100 text-[11px] text-slate-400 flex items-center justify-between">
            <span>Library: shap 0.46+ / TreeExplainer</span>
            <span>Target: Phase 04</span>
          </div>
        </div>
      </div>
    </div>
  );
};
