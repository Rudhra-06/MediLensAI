import React, { useEffect, useState } from 'react';
import { BarChart2, BrainCircuit, CircleHelp, LoaderCircle } from 'lucide-react';
import { DisclaimerBanner } from '../common/DisclaimerBanner';
import { EmptyState } from '../common/EmptyState';
import { fetchRiskHealth, fetchRiskInsights } from '../../services/api';
import type { ProviderRiskInsightsResponse, RiskHealthResponse } from '../../types/risk';

const MODEL_LABELS: Record<string, string> = {
  dummy_prior: 'Dummy prior baseline',
  logistic_regression: 'Logistic Regression',
  random_forest: 'Random Forest',
};

function percent(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

function contributionPoints(value: number): string {
  const points = value * 100;
  return `${points > 0 ? '+' : ''}${points.toFixed(2)} pp`;
}

function ModelInsightsData({ data }: { data: ProviderRiskInsightsResponse }) {
  const shap = data.global_shap;
  return (
    <>
      <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs sm:p-6">
        <div className="flex flex-col justify-between gap-3 border-b border-slate-100 pb-4 sm:flex-row sm:items-start">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-teal-700">Saved validation results</p>
            <h2 className="mt-1 text-lg font-bold text-slate-900">Baseline model comparison</h2>
            <p className="mt-1 text-sm text-slate-600">
              {data.split_strategy} ({data.train_provider_count.toLocaleString()} train / {data.validation_provider_count.toLocaleString()} validation providers).
            </p>
          </div>
          <span className="rounded-full border border-teal-200 bg-teal-50 px-3 py-1 text-xs font-semibold text-teal-800">
            Selected: {MODEL_LABELS[data.selected_model] ?? data.selected_model}
          </span>
        </div>

        <div className="mt-4 overflow-x-auto">
          <table className="w-full min-w-[620px] border-collapse text-left text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-xs text-slate-500">
                <th className="px-3 py-2 font-semibold">Validation model</th>
                <th className="px-3 py-2 font-semibold">Precision</th>
                <th className="px-3 py-2 font-semibold">Recall</th>
                <th className="px-3 py-2 font-semibold">F1</th>
                <th className="px-3 py-2 font-semibold">Average precision</th>
                <th className="px-3 py-2 font-semibold">ROC-AUC</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(data.validation_metrics).map(([name, metric]) => (
                <tr key={name} className={`border-b border-slate-100 ${name === data.selected_model ? 'bg-teal-50/70 font-semibold text-slate-900' : 'text-slate-700'}`}>
                  <th scope="row" className="px-3 py-3">{MODEL_LABELS[name] ?? name}</th>
                  <td className="px-3 py-3 tabular-nums">{percent(metric.precision)}</td>
                  <td className="px-3 py-3 tabular-nums">{percent(metric.recall)}</td>
                  <td className="px-3 py-3 tabular-nums">{percent(metric.f1)}</td>
                  <td className="px-3 py-3 tabular-nums">{percent(metric.average_precision)}</td>
                  <td className="px-3 py-3 tabular-nums">{percent(metric.roc_auc)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {data.validation_metrics[data.selected_model] && (
          <p className="mt-3 text-xs text-slate-600">
            Selected-model confusion matrix (actual labels 0/1 by predicted 0/1):{' '}
            <span className="font-mono">
              {data.validation_metrics[data.selected_model].confusion_matrix_labels_0_1.map((row) => `[${row.join(', ')}]`).join(' ')}
            </span>
          </p>
        )}

        <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50 p-4 text-xs leading-relaxed text-amber-950">
          <h3 className="font-semibold">How to interpret these metrics</h3>
          <ul className="mt-2 list-disc space-y-1 pl-5">
            {data.limitations.map((limitation) => <li key={limitation}>{limitation}</li>)}
            <li>Model scores are uncalibrated and are not verified-fraud probabilities.</li>
          </ul>
        </div>
      </section>

      <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs sm:p-6">
        <div className="flex items-start gap-3 border-b border-slate-100 pb-4">
          <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-teal-200 bg-teal-50 text-teal-700">
            <BarChart2 className="h-5 w-5" aria-hidden="true" />
          </span>
          <div>
            <h2 className="font-semibold text-slate-900">Global SHAP feature contributions</h2>
            {shap && <p className="mt-1 text-xs text-slate-500">SHAP {shap.shap_version} · {shap.explanation_sample_count} deterministic explanation rows · {shap.feature_count} features</p>}
          </div>
        </div>

        {!shap ? (
          <EmptyState
            icon={CircleHelp}
            title="Global explanations unavailable"
            description={data.explainability_note ?? 'No compatible saved global SHAP summary is available.'}
            badgeText="No SHAP data"
          />
        ) : (
          <>
            <p className="mt-4 text-sm text-slate-600">
              Contributions explain the Random Forest output for <strong>PotentialFraud=1</strong> on the verified <strong>{shap.output_scale}</strong> scale. Mean absolute contribution shows typical magnitude; mean signed contribution shows average direction. Values below are percentage points of model output.
            </p>
            <p className="mt-2 text-xs text-slate-500">
              Output scale verification: maximum additivity residual {shap.max_absolute_additivity_error.toExponential(2)} (saved tolerance 1.00e-4).
            </p>
            <div className="mt-4 overflow-x-auto">
              <table className="w-full min-w-[520px] border-collapse text-left text-sm">
                <thead>
                  <tr className="border-b border-slate-200 text-xs text-slate-500">
                    <th className="px-3 py-2 font-semibold">Feature</th>
                    <th className="px-3 py-2 font-semibold">Mean absolute contribution</th>
                    <th className="px-3 py-2 font-semibold">Mean signed contribution</th>
                    <th className="px-3 py-2 font-semibold">Average direction</th>
                  </tr>
                </thead>
                <tbody>
                  {shap.features.slice(0, 10).map((item) => (
                    <tr key={item.feature} className="border-b border-slate-100 text-slate-700">
                      <th scope="row" className="px-3 py-3 font-medium text-slate-900">{item.feature.replaceAll('_', ' ')}</th>
                      <td className="px-3 py-3 tabular-nums">{(item.mean_absolute_contribution * 100).toFixed(2)} pp</td>
                      <td className="px-3 py-3 tabular-nums">{contributionPoints(item.mean_signed_contribution)}</td>
                      <td className="px-3 py-3 text-xs">{item.direction}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="mt-3 text-xs leading-relaxed text-slate-500">
              {shap.importance_method}. These global summaries describe model behavior only; they are not evidence of fraud or causation. Local provider-level explanations and sample records are not displayed here.
            </p>
          </>
        )}
      </section>
    </>
  );
}

export const ModelInsightsPage: React.FC = () => {
  const [health, setHealth] = useState<RiskHealthResponse | null>(null);
  const [data, setData] = useState<ProviderRiskInsightsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    Promise.allSettled([fetchRiskHealth(), fetchRiskInsights()]).then(([healthResult, insightsResult]) => {
      if (!active) return;
      if (healthResult.status === 'fulfilled') setHealth(healthResult.value);
      if (insightsResult.status === 'fulfilled') setData(insightsResult.value);
      else setError(insightsResult.reason instanceof Error ? insightsResult.reason.message : 'Saved model insights are unavailable.');
      setLoading(false);
    });
    return () => { active = false; };
  }, []);

  const modelReady = health?.ready === true;
  return (
    <div className="space-y-6">
      <DisclaimerBanner />
      <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs sm:p-6">
        <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-start">
          <div className="flex items-start gap-3">
            <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-teal-200 bg-teal-50 text-teal-700">
              <BrainCircuit className="h-5 w-5" aria-hidden="true" />
            </span>
            <div>
              <h2 className="text-lg font-bold text-slate-900">Model Insights & Explainability</h2>
              <p className="mt-1 text-sm text-slate-600">Provider-level Random Forest readiness, recorded validation results and global SHAP summaries.</p>
            </div>
          </div>
          <span className={`rounded-full border px-3 py-1 text-xs font-semibold ${modelReady ? 'border-teal-200 bg-teal-50 text-teal-800' : 'border-amber-200 bg-amber-50 text-amber-800'}`}>
            {loading ? 'Checking model status…' : modelReady ? `${health?.model_name ?? 'Model'} ready · ${health.model_version}` : 'Model unavailable'}
          </span>
        </div>
        {!modelReady && !loading && <p className="mt-3 text-sm text-slate-600">{health?.reason ?? 'Risk API health could not be verified.'}</p>}
      </section>

      {loading && (
        <div className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white p-5 text-sm text-slate-600" role="status">
          <LoaderCircle className="h-4 w-4 animate-spin" aria-hidden="true" /> Loading saved model insights…
        </div>
      )}

      {!loading && !data && (
        <EmptyState
          icon={CircleHelp}
          title="Saved model insights unavailable"
          description={error || 'The backend did not return compatible validation artifacts.'}
          badgeText="Insights unavailable"
        />
      )}

      {!loading && data && <ModelInsightsData data={data} />}
    </div>
  );
};
