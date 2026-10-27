import React from 'react';
import { Activity, ArrowRight, Database, Server, ShieldCheck } from 'lucide-react';
import type { HealthResponse, ApiConnectionState } from '../../types/health';
import type { RiskHealthResponse } from '../../types/risk';
import type { PageId } from '../../types/navigation';
import { DisclaimerBanner } from '../common/DisclaimerBanner';

interface OverviewPageProps {
  healthData: HealthResponse | null;
  riskHealth: RiskHealthResponse | null;
  apiState: ApiConnectionState;
  onNavigate: (page: PageId) => void;
}

function ReadinessCard({
  icon: Icon,
  title,
  status,
  detail,
  ready,
}: {
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  status: string;
  detail: string;
  ready: boolean | null;
}) {
  return (
    <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs">
      <div className="flex items-start gap-3">
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-teal-200 bg-teal-50 text-teal-700">
          <Icon className="h-5 w-5" aria-hidden="true" />
        </span>
        <div className="min-w-0">
          <h2 className="font-semibold text-slate-900">{title}</h2>
          <p className={`mt-1 text-sm font-medium ${ready === true ? 'text-teal-700' : ready === false ? 'text-rose-700' : 'text-slate-500'}`}>
            {status}
          </p>
          <p className="mt-2 text-xs leading-relaxed text-slate-500">{detail}</p>
        </div>
      </div>
    </section>
  );
}

export const OverviewPage: React.FC<OverviewPageProps> = ({ healthData, riskHealth, apiState, onNavigate }) => {
  const artifactCount = riskHealth ? Object.values(riskHealth.artifact_status).filter(Boolean).length : 0;
  const totalArtifacts = riskHealth ? Object.keys(riskHealth.artifact_status).length : 0;

  return (
    <div className="space-y-6">
      <DisclaimerBanner />

      <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs sm:p-6">
        <div className="flex flex-col justify-between gap-3 border-b border-slate-100 pb-4 sm:flex-row sm:items-center">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-teal-700">Live service status</p>
            <h2 className="mt-1 text-xl font-bold text-slate-900">Provider risk inference</h2>
            <p className="mt-1 text-sm text-slate-500">Status is read from FastAPI. No claim counts, risk totals, or performance metrics are shown here.</p>
          </div>
          <span className="rounded-md border border-slate-200 bg-slate-50 px-3 py-1.5 font-mono text-xs text-slate-600">
            API {healthData?.version ?? '—'}
          </span>
        </div>

        <div className="grid gap-4 pt-4 md:grid-cols-2 xl:grid-cols-3">
          <ReadinessCard
            icon={Server}
            title="FastAPI service"
            status={apiState === 'checking' ? 'Checking…' : apiState === 'connected' ? healthData?.status ?? 'Connected' : 'Unavailable'}
            detail="Connectivity is checked through the existing system health endpoint."
            ready={apiState === 'checking' ? null : apiState === 'connected'}
          />
          <ReadinessCard
            icon={Activity}
            title="Provider risk model"
            status={riskHealth ? riskHealth.ready ? `${riskHealth.model_name ?? 'Model'} ready` : 'Model unavailable' : apiState === 'checking' ? 'Checking…' : 'Status unavailable'}
            detail={riskHealth?.ready ? `Version ${riskHealth.model_version}; uncalibrated provider-level PotentialFraud score.` : riskHealth?.reason ?? 'The versioned model health endpoint has not responded.'}
            ready={riskHealth?.ready ?? (apiState === 'checking' ? null : false)}
          />
          <ReadinessCard
            icon={ShieldCheck}
            title="Required artifacts"
            status={riskHealth ? `${artifactCount} of ${totalArtifacts} available` : 'Status unavailable'}
            detail={riskHealth ? Object.entries(riskHealth.artifact_status).map(([name, present]) => `${name}: ${present ? 'available' : 'missing'}`).join(' · ') : 'Artifact status comes from the risk health endpoint.'}
            ready={riskHealth ? riskHealth.ready && artifactCount === totalArtifacts : null}
          />
        </div>
      </section>

      <section className="flex flex-col justify-between gap-4 rounded-xl border border-[#1E3E62] bg-[#0B192C] p-5 text-white sm:flex-row sm:items-center sm:p-6">
        <div className="flex items-start gap-3">
          <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-teal-400/30 bg-teal-500/10 text-teal-300">
            <Database className="h-5 w-5" aria-hidden="true" />
          </span>
          <div>
            <h2 className="font-semibold">No provider lookup or stored assessment is connected</h2>
            <p className="mt-1 max-w-2xl text-sm leading-relaxed text-slate-300">
              The assessment form accepts a manually supplied feature vector only. It does not load a provider record, and its result must not be presented as an assessment of an identified provider.
            </p>
          </div>
        </div>
        <button
          type="button"
          onClick={() => onNavigate('provider-risk')}
          className="inline-flex shrink-0 items-center justify-center gap-2 rounded-lg bg-teal-500 px-4 py-2.5 text-sm font-semibold text-[#071820] transition-colors hover:bg-teal-400 focus:outline-hidden focus:ring-2 focus:ring-teal-300"
        >
          Open manual assessment <ArrowRight className="h-4 w-4" />
        </button>
      </section>

      <p className="px-1 text-xs leading-relaxed text-slate-500">
        Model scores describe the model output for the PotentialFraud dataset label. They are uncalibrated and are not proof of fraud, causation, or validated real-world performance.
      </p>
    </div>
  );
};
