import React, { useEffect, useMemo, useState } from 'react';
import { AlertCircle, RotateCcw, Send, ShieldAlert } from 'lucide-react';
import { assessLocalDemoProvider, assessProvider, fetchLocalDemoProviders, fetchRiskFeatures } from '../../services/api';
import type { LocalDemoProvider, RiskAssessmentResponse, RiskFeatureDescription } from '../../types/risk';

function featureLabel(name: string): string {
  return name.split('_').map((part) => part.charAt(0).toUpperCase() + part.slice(1)).join(' ');
}

function featureUnit(name: string): string {
  if (name.endsWith('_ratio')) return 'fraction · 0 to 1';
  if (name.includes('reimbursed') || name.includes('deductible')) return 'USD';
  if (name.includes('duration') || name.includes('length_of_stay')) return 'days';
  if (name === 'patient_age_mean') return 'years · approximate 2009 cohort age';
  if (name === 'patient_chronic_condition_mean') return 'conditions per beneficiary · 0 to 11';
  if (name.includes('per_beneficiary') || name.includes('per_attending')) return 'claims per person';
  if (name.endsWith('_count')) return 'count · whole number';
  return 'numeric feature value';
}

function featureBounds(name: string): { min?: number; max?: number; step: number | 'any' } {
  if (name.endsWith('_ratio')) return { min: 0, max: 1, step: 'any' };
  if (name === 'patient_age_mean') return { min: 0, max: 120, step: 'any' };
  if (name === 'patient_chronic_condition_mean') return { min: 0, max: 11, step: 'any' };
  return { min: 0, step: name.endsWith('_count') ? 1 : 'any' };
}

function validate(values: Record<string, string>, features: RiskFeatureDescription[]): Record<string, string> {
  const errors: Record<string, string> = {};
  for (const feature of features) {
    const raw = values[feature.name]?.trim();
    if (!raw) {
      errors[feature.name] = 'Enter a value for this required feature.';
      continue;
    }
    const value = Number(raw);
    const bounds = featureBounds(feature.name);
    if (!Number.isFinite(value)) errors[feature.name] = 'Enter a finite number.';
    else if (bounds.min !== undefined && value < bounds.min) errors[feature.name] = `Value must be at least ${bounds.min}.`;
    else if (bounds.max !== undefined && value > bounds.max) errors[feature.name] = `Value must be no greater than ${bounds.max}.`;
    else if (bounds.step === 1 && !Number.isInteger(value)) errors[feature.name] = 'Enter a whole number.';
  }
  return errors;
}

function FeatureField({
  feature,
  value,
  error,
  onChange,
}: {
  feature: RiskFeatureDescription;
  value: string;
  error?: string;
  onChange: (name: string, value: string) => void;
}) {
  const id = `feature-${feature.name}`;
  const bounds = featureBounds(feature.name);
  return (
    <div className="min-w-0">
      <label htmlFor={id} className="block text-sm font-medium text-slate-800">{featureLabel(feature.name)}</label>
      <p id={`${id}-description`} className="mt-1 min-h-10 text-xs leading-relaxed text-slate-500">{feature.description}</p>
      <p className="mb-1.5 text-[11px] font-medium text-teal-700">{featureUnit(feature.name)}</p>
      <input
        id={id}
        type="number"
        inputMode="decimal"
        min={bounds.min}
        max={bounds.max}
        step={bounds.step}
        value={value ?? ''}
        onChange={(event) => onChange(feature.name, event.target.value)}
        aria-invalid={Boolean(error)}
        aria-describedby={error ? `${id}-description ${id}-error` : `${id}-description`}
        className={`w-full rounded-lg border bg-white px-3 py-2.5 text-sm text-slate-900 outline-none transition focus:ring-2 focus:ring-teal-500 ${error ? 'border-rose-400' : 'border-slate-300 focus:border-teal-500'}`}
      />
      {error && <p id={`${id}-error`} className="mt-1 text-xs text-rose-700">{error}</p>}
    </div>
  );
}

export const ProviderRiskPage: React.FC = () => {
  const [features, setFeatures] = useState<RiskFeatureDescription[]>([]);
  const [featureState, setFeatureState] = useState<'loading' | 'ready' | 'error'>('loading');
  const [featureError, setFeatureError] = useState('');
  const [values, setValues] = useState<Record<string, string>>({});
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [requestError, setRequestError] = useState('');
  const [result, setResult] = useState<RiskAssessmentResponse | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [demoProviders, setDemoProviders] = useState<LocalDemoProvider[]>([]);
  const [demoDisclosure, setDemoDisclosure] = useState('');
  const [demoReference, setDemoReference] = useState('');
  const [assessmentMode, setAssessmentMode] = useState<'manual' | 'demo'>('manual');

  useEffect(() => {
    let active = true;
    fetchRiskFeatures()
      .then((data) => {
        if (active) {
          setFeatures(data);
          setFeatureState(data.length ? 'ready' : 'error');
          if (!data.length) setFeatureError('The API returned no feature definitions.');
        }
      })
      .catch((error: unknown) => {
        if (active) {
          setFeatureError(error instanceof Error ? error.message : 'Could not load feature definitions.');
          setFeatureState('error');
        }
      });
    fetchLocalDemoProviders()
      .then((data) => {
        if (active && data.enabled) {
          setDemoProviders(data.providers);
          setDemoDisclosure(data.split_disclosure);
        }
      })
      .catch(() => { /* Demo is optional and disabled by default. */ });
    return () => { active = false; };
  }, []);

  const groupedFeatures = useMemo(() => {
    const groups = new Map<string, RiskFeatureDescription[]>();
    for (const feature of features) {
      const group = groups.get(feature.domain) ?? [];
      group.push(feature);
      groups.set(feature.domain, group);
    }
    return [...groups.entries()];
  }, [features]);

  const handleChange = (name: string, value: string) => {
    setValues((current) => ({ ...current, [name]: value }));
    setErrors((current) => { const next = { ...current }; delete next[name]; return next; });
    setRequestError('');
    setResult(null);
  };

  const reset = () => {
    setValues({});
    setErrors({});
    setRequestError('');
    setResult(null);
    setDemoReference('');
  };

  const assessDemo = async () => {
    setRequestError('');
    setResult(null);
    if (!demoReference) {
      setRequestError('Select an anonymous local demo reference first.');
      return;
    }
    setSubmitting(true);
    try {
      setResult(await assessLocalDemoProvider(demoReference));
    } catch (error: unknown) {
      setRequestError(error instanceof Error ? error.message : 'Demo assessment failed.');
    } finally {
      setSubmitting(false);
    }
  };

  const submit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const nextErrors = validate(values, features);
    setErrors(nextErrors);
    setRequestError('');
    setResult(null);
    if (Object.keys(nextErrors).length) {
      document.getElementById(`feature-${Object.keys(nextErrors)[0]}`)?.focus();
      return;
    }
    setSubmitting(true);
    try {
      const numericValues = Object.fromEntries(features.map((feature) => [feature.name, Number(values[feature.name])])) as Record<string, number>;
      setResult(await assessProvider(numericValues));
    } catch (error: unknown) {
      setRequestError(error instanceof Error ? error.message : 'Assessment request failed.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-5">
      <section className="rounded-xl border border-amber-300 bg-amber-50 p-4 text-amber-950 sm:p-5" role="note">
        <div className="flex items-start gap-3">
          <ShieldAlert className="mt-0.5 h-5 w-5 shrink-0 text-amber-700" aria-hidden="true" />
          <div className="text-sm leading-relaxed">
            <h2 className="font-semibold">Provider-level PotentialFraud model score</h2>
            <p className="mt-1">
              Manual values are not linked to an identified provider. The optional local demo uses retrospective validation-split feature vectors and anonymous, temporary references; it is not a live claims investigation.
            </p>
            <p className="mt-2 font-medium">
              The result is an uncalibrated model score for the provider-level PotentialFraud dataset label. That label is not verified fraud; the score is not proof of wrongdoing, causation, or validated real-world performance.
            </p>
          </div>
        </div>
      </section>

      {featureState === 'loading' && (
        <div className="rounded-xl border border-slate-200 bg-white p-6 text-sm text-slate-600" role="status">Loading feature definitions from FastAPI…</div>
      )}
      {featureState === 'error' && (
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-900" role="alert">
          <strong>Feature definitions unavailable.</strong> <span>{featureError}</span>
        </div>
      )}

      {featureState === 'ready' && (
        <>
        {demoProviders.length > 0 && (
          <section className="rounded-xl border border-slate-200 bg-white p-4 sm:p-5">
            <h2 className="font-semibold text-slate-900">Choose an assessment workflow</h2>
            <div className="mt-3 flex flex-wrap gap-2">
              <button type="button" onClick={() => { setAssessmentMode('manual'); setResult(null); }} className={`rounded-lg px-3 py-2 text-sm font-medium ${assessmentMode === 'manual' ? 'bg-[#0B192C] text-white' : 'border border-slate-300 text-slate-700'}`}>Manual feature entry</button>
              <button type="button" onClick={() => { setAssessmentMode('demo'); setResult(null); }} className={`rounded-lg px-3 py-2 text-sm font-medium ${assessmentMode === 'demo' ? 'bg-[#0B192C] text-white' : 'border border-slate-300 text-slate-700'}`}>Local retrospective demo</button>
            </div>
            {assessmentMode === 'demo' && (
              <div className="mt-4 space-y-3 rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-950">
                <p className="font-medium">Retrospective dataset demonstration · validation split</p>
                <p>{demoDisclosure}</p>
                <label htmlFor="local-demo-reference" className="block text-xs font-semibold">Anonymous temporary reference</label>
                <select id="local-demo-reference" value={demoReference} onChange={(event) => { setDemoReference(event.target.value); setResult(null); }} className="w-full rounded-lg border border-amber-300 bg-white px-3 py-2 text-sm text-slate-900">
                  <option value="">Choose a demo reference</option>
                  {demoProviders.map((provider) => <option key={provider.reference_id} value={provider.reference_id}>{provider.reference_id}</option>)}
                </select>
                <button type="button" disabled={submitting || !demoReference} onClick={assessDemo} className="rounded-lg bg-[#0B192C] px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-50">{submitting ? 'Scoring…' : 'Assess selected demo record'}</button>
              </div>
            )}
          </section>
        )}
        {assessmentMode === 'manual' && (
        <form onSubmit={submit} noValidate className="space-y-5">
          <div className="flex flex-col justify-between gap-3 rounded-xl border border-slate-200 bg-white p-4 sm:flex-row sm:items-center sm:p-5">
            <div>
              <h2 className="font-semibold text-slate-900">Provider-level feature inputs</h2>
              <p className="mt-1 text-xs text-slate-500">All {features.length} values are required. Feature descriptions come from the API dictionary. No provider ID is requested or sent.</p>
            </div>
            <button type="button" onClick={reset} className="inline-flex items-center justify-center gap-2 rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 focus:outline-hidden focus:ring-2 focus:ring-teal-500">
              <RotateCcw className="h-4 w-4" /> Reset form
            </button>
          </div>

          {groupedFeatures.map(([domain, group]) => (
            <fieldset key={domain} className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs sm:p-5">
              <legend className="px-2 text-sm font-bold text-[#0B192C]">{domain}</legend>
              <div className="grid gap-x-5 gap-y-5 md:grid-cols-2 xl:grid-cols-3">
                {group.map((feature) => (
                  <FeatureField key={feature.name} feature={feature} value={values[feature.name] ?? ''} error={errors[feature.name]} onChange={handleChange} />
                ))}
              </div>
            </fieldset>
          ))}

          {requestError && (
            <div role="alert" className="flex items-start gap-2 rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-900">
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" /> {requestError}
            </div>
          )}

          <div className="flex flex-col-reverse justify-between gap-3 sm:flex-row sm:items-center">
            <p className="max-w-2xl text-xs leading-relaxed text-slate-500">Review the feature definitions and verify the source and units of every value before submitting.</p>
            <button type="submit" disabled={submitting} className="inline-flex items-center justify-center gap-2 rounded-lg bg-[#0B192C] px-5 py-3 text-sm font-semibold text-white transition-colors hover:bg-[#1E3E62] focus:outline-hidden focus:ring-2 focus:ring-teal-500 disabled:cursor-wait disabled:opacity-60">
              <Send className="h-4 w-4" /> {submitting ? 'Scoring…' : 'Calculate model score'}
            </button>
          </div>
        </form>
        )}
        </>
      )}

      {result && (
        <section className="rounded-xl border border-teal-300 bg-white p-5 shadow-xs sm:p-6" aria-live="polite">
          <p className="text-xs font-semibold uppercase tracking-wider text-teal-700">{result.assessment_mode === 'retrospective_validation_demo' ? 'Retrospective validation demo · not a live claims investigation' : 'Provider-level model output'}</p>
          <h2 className="mt-1 text-lg font-bold text-slate-900">PotentialFraud=1 uncalibrated model score</h2>
          <p className="mt-3 font-mono text-4xl font-bold tabular-nums text-[#0B192C]">{result.risk_score.toFixed(4)}</p>
          <p className="mt-1 text-xs text-slate-500">Score scale: 0 to 1 · Model version: {result.model_version}</p>
          <p className="mt-4 rounded-lg bg-amber-50 p-3 text-xs leading-relaxed text-amber-950">{result.disclaimer} {result.assessment_mode === 'retrospective_validation_demo' ? result.split_disclosure : 'This result reflects only the manually entered feature vector and is not linked to an identified provider.'}</p>
        </section>
      )}
    </div>
  );
};
