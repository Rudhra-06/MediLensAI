import React from 'react';
import {
  FileText,
  AlertTriangle,
  Clock,
  ArrowRight,
  Server,
  Cpu,
  Layers,
  Info,
} from 'lucide-react';
import type { HealthResponse, ApiConnectionState } from '../../types/health';
import type { PageId } from '../../types/navigation';
import { MetricCard } from '../common/MetricCard';
import { DisclaimerBanner } from '../common/DisclaimerBanner';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

interface OverviewPageProps {
  healthData: HealthResponse | null;
  apiState: ApiConnectionState;
  onNavigate: (page: PageId) => void;
}

// Strictly synthetic illustrative schema preview data for chart layout testing
const ILLUSTRATIVE_TIER_PREVIEW = [
  { tier: 'Low Risk (<30%)', count: 0, description: 'Direct pass / standard processing' },
  { tier: 'Moderate Risk (30-65%)', count: 0, description: 'Secondary automated audit' },
  { tier: 'Elevated Risk (65-85%)', count: 0, description: 'Priority auditor triage' },
  { tier: 'High Suspicion (>85%)', count: 0, description: 'Full investigation support' },
];

export const OverviewPage: React.FC<OverviewPageProps> = ({
  healthData,
  apiState,
  onNavigate,
}) => {
  return (
    <div className="space-y-6">
      {/* Human Investigation Compliance Banner */}
      <DisclaimerBanner />

      {/* Real Infrastructure Readiness Status Card */}
      <div className="bg-white rounded-xl border border-slate-200/90 p-5 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base font-bold text-slate-900">
                System Readiness & Architecture Baseline
              </h2>
              <span className="text-xs bg-slate-100 text-slate-700 px-2 py-0.5 rounded-full font-medium border border-slate-200">
                Phase 01 Foundation
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-1">
              Active verification of connected backend services, runtime configuration, and ML model loading status.
            </p>
          </div>

          <div className="flex items-center gap-2 text-xs">
            <span className="text-slate-500">FastAPI Version:</span>
            <span className="font-mono bg-slate-100 text-slate-800 px-2 py-0.5 rounded-sm border border-slate-200">
              {healthData?.version ?? 'Checking...'}
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4">
          {/* API Backend Subsystem */}
          <div className="p-3.5 rounded-lg bg-slate-50/70 border border-slate-200/80 flex items-start gap-3">
            <div className="w-8 h-8 rounded-md bg-teal-50 text-teal-700 border border-teal-200 flex items-center justify-center shrink-0">
              <Server className="w-4 h-4" />
            </div>
            <div className="text-xs">
              <div className="font-semibold text-slate-900">Backend API (FastAPI)</div>
              <div className="text-slate-500 mt-0.5">
                Status:{' '}
                <span
                  className={
                    apiState === 'connected'
                      ? 'text-teal-700 font-medium'
                      : 'text-rose-700 font-medium'
                  }
                >
                  {apiState === 'connected' ? 'Connected & Healthy' : 'Disconnected'}
                </span>
              </div>
              <div className="text-[11px] text-slate-400 mt-1">
                Port: 8000 | Endpoint: /api/health
              </div>
            </div>
          </div>

          {/* ML Inference Engine */}
          <div className="p-3.5 rounded-lg bg-slate-50/70 border border-slate-200/80 flex items-start gap-3">
            <div className="w-8 h-8 rounded-md bg-amber-50 text-amber-700 border border-amber-200 flex items-center justify-center shrink-0">
              <Cpu className="w-4 h-4" />
            </div>
            <div className="text-xs">
              <div className="font-semibold text-slate-900">ML Risk Engine (XGBoost/SHAP)</div>
              <div className="text-slate-500 mt-0.5">
                Status:{' '}
                <span className="text-amber-700 font-medium">
                  {healthData?.model_readiness.status === 'ready'
                    ? 'Ready'
                    : 'Not Loaded (Planned Step)'}
                </span>
              </div>
              <div className="text-[11px] text-slate-400 mt-1">
                Awaiting trained claim fraud model
              </div>
            </div>
          </div>

          {/* Ingestion & PostgreSQL Subsystem */}
          <div className="p-3.5 rounded-lg bg-slate-50/70 border border-slate-200/80 flex items-start gap-3">
            <div className="w-8 h-8 rounded-md bg-slate-100 text-slate-600 border border-slate-200 flex items-center justify-center shrink-0">
              <Layers className="w-4 h-4" />
            </div>
            <div className="text-xs">
              <div className="font-semibold text-slate-900">Claims Database & Ingestion</div>
              <div className="text-slate-500 mt-0.5">
                Status:{' '}
                <span className="text-slate-600 font-medium">Not Configured (Future Phase)</span>
              </div>
              <div className="text-[11px] text-slate-400 mt-1">
                Zero synthetic or live claims loaded
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Honest Operational Metric Baseline Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Claims Ingested"
          value="0"
          subtitle="No claims ingested yet"
          icon={FileText}
          badgeLabel="Empty State"
          badgeVariant="neutral"
          infoTooltip="Operational claim ingestion pipeline will be established in subsequent steps."
        />
        <MetricCard
          title="Flagged For Review"
          value="0"
          subtitle="Investigation queue is clear"
          icon={AlertTriangle}
          badgeLabel="Queue Empty"
          badgeVariant="neutral"
          infoTooltip="Claims will appear here once automated scoring detects elevated risk patterns."
        />
        <MetricCard
          title="Model Status"
          value="Unloaded"
          subtitle="Pipeline training pending"
          icon={Cpu}
          badgeLabel="Not Trained"
          badgeVariant="amber"
          infoTooltip="ML risk model will be trained and calibrated in the dedicated ML phase."
        />
        <MetricCard
          title="Avg Review Time"
          value="—"
          subtitle="Requires baseline claims"
          icon={Clock}
          badgeLabel="No Data"
          badgeVariant="neutral"
          infoTooltip="Audit duration tracking begins once analysts process investigation cases."
        />
      </div>

      {/* Two-Column Middle Section: Workflow Architecture & Illustrative Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Screening Pipeline Architecture */}
        <div className="lg:col-span-7 bg-white rounded-xl border border-slate-200/90 p-5 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-sm font-bold text-slate-900">
                  MediLens AI Fraud Screening Workflow
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  End-to-end explainable triage lifecycle from claim ingestion to human determination.
                </p>
              </div>
              <span className="text-[11px] font-semibold text-teal-800 bg-teal-50 border border-teal-200 px-2.5 py-0.5 rounded-full">
                Architecture Roadmap
              </span>
            </div>

            <div className="space-y-3 mt-4">
              {[
                {
                  step: '01',
                  name: 'Claim Ingestion & Validation',
                  desc: 'CMS-1500 / UB-04 format ingestion, provider NPI verification, coding consistency.',
                  status: 'Phase 02 (Planned)',
                },
                {
                  step: '02',
                  name: 'Feature Extraction & Engineering',
                  desc: 'Billing velocity, procedure unbundling indicators, peer comparison ratios.',
                  status: 'Phase 03 (Planned)',
                },
                {
                  step: '03',
                  name: 'Explainable ML Risk Scoring',
                  desc: 'Supervised XGBoost risk estimator outputting calibrated probability [0.0 - 1.0].',
                  status: 'Phase 03 (Planned)',
                },
                {
                  step: '04',
                  name: 'SHAP Contribution Breakdown',
                  desc: 'Waterfall and force plots revealing top positive/negative risk contributors per claim.',
                  status: 'Phase 04 (Planned)',
                },
                {
                  step: '05',
                  name: 'Human Auditor Investigation Queue',
                  desc: 'Analyst accepts, requests documentation, or resolves without automated denial.',
                  status: 'Phase 05 (Planned)',
                },
              ].map((item) => (
                <div
                  key={item.step}
                  className="flex items-start gap-3 p-2.5 rounded-lg hover:bg-slate-50 border border-slate-100 transition-colors"
                >
                  <span className="w-6 h-6 rounded-md bg-[#0B192C] text-teal-400 font-mono text-xs font-bold flex items-center justify-center shrink-0 mt-0.5">
                    {item.step}
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-xs font-semibold text-slate-900 truncate">
                        {item.name}
                      </span>
                      <span className="text-[10px] text-slate-500 shrink-0 font-medium">
                        {item.status}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-500 leading-snug mt-0.5">{item.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="pt-4 mt-4 border-t border-slate-100 flex items-center justify-between">
            <span className="text-xs text-slate-500">Ready to explore platform modules?</span>
            <button
              onClick={() => onNavigate('claims-intelligence')}
              className="inline-flex items-center gap-1.5 text-xs font-semibold text-teal-700 hover:text-teal-900 cursor-pointer"
            >
              Explore Claims Intelligence
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Illustrative Distribution Chart Preview */}
        <div className="lg:col-span-5 bg-white rounded-xl border border-slate-200/90 p-5 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-start justify-between gap-2 mb-2">
              <div>
                <h3 className="text-sm font-bold text-slate-900">
                  Risk Tier Distribution Preview
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Illustrative risk bucketing framework for incoming claims triage.
                </p>
              </div>
              <span className="text-[10px] font-medium bg-amber-50 text-amber-800 border border-amber-200 px-2 py-0.5 rounded-full shrink-0">
                Empty / Baseline (0 claims)
              </span>
            </div>

            {/* Prominent Clarification Note */}
            <div className="flex items-center gap-2 p-2 rounded-md bg-slate-50 border border-slate-200 text-[11px] text-slate-600 mb-4">
              <Info className="w-4 h-4 text-slate-500 shrink-0" />
              <span>
                Chart reflects zero ingested claims. Tiers show operational screening ranges.
              </span>
            </div>

            {/* Recharts Bar Display */}
            <div className="h-52 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={ILLUSTRATIVE_TIER_PREVIEW}
                  margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis
                    dataKey="tier"
                    tick={{ fontSize: 10, fill: '#64748b' }}
                    interval={0}
                    tickFormatter={(v) => v.split(' ')[0]}
                  />
                  <YAxis
                    tick={{ fontSize: 10, fill: '#64748b' }}
                    domain={[0, 10]}
                    allowDecimals={false}
                  />
                  <Tooltip
                    content={({ payload }) => {
                      if (!payload || !payload.length) return null;
                      const item = payload[0].payload;
                      return (
                        <div className="bg-slate-900 text-white text-xs p-2.5 rounded-md shadow-lg border border-slate-800">
                          <div className="font-semibold text-teal-300">{item.tier}</div>
                          <div className="text-slate-300 mt-1">Current Active Claims: 0</div>
                          <div className="text-[11px] text-slate-400 mt-1">{item.description}</div>
                        </div>
                      );
                    }}
                  />
                  <Bar dataKey="count" fill="#0D9488" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
            <span>Model calibration: Pending Step 3</span>
            <button
              onClick={() => onNavigate('model-insights')}
              className="text-teal-700 hover:text-teal-900 font-semibold cursor-pointer inline-flex items-center gap-1"
            >
              Model Details
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>
        </div>
      </div>

      {/* Module Quick Nav Cards */}
      <div className="bg-slate-50/80 rounded-xl border border-slate-200/90 p-5">
        <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-3">
          Explore Foundation Modules
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          {[
            {
              id: 'claims-intelligence' as PageId,
              title: 'Claims Intelligence',
              desc: 'Single & batch claim screening',
            },
            {
              id: 'investigation-queue' as PageId,
              title: 'Investigation Queue',
              desc: 'Priority human auditor triage',
            },
            {
              id: 'model-insights' as PageId,
              title: 'Model Insights',
              desc: 'SHAP explanations & transparency',
            },
            {
              id: 'data-management' as PageId,
              title: 'Data Management',
              desc: 'Claim ingestion & schemas',
            },
            {
              id: 'settings' as PageId,
              title: 'System Settings',
              desc: 'API connectivity & thresholds',
            },
          ].map((item) => (
            <button
              key={item.id}
              onClick={() => onNavigate(item.id)}
              className="text-left p-3 rounded-lg bg-white border border-slate-200 hover:border-teal-400 hover:shadow-xs transition-all cursor-pointer group focus:outline-hidden focus:ring-2 focus:ring-teal-500"
            >
              <div className="text-xs font-semibold text-slate-900 group-hover:text-teal-700 flex items-center justify-between">
                <span>{item.title}</span>
                <ArrowRight className="w-3 h-3 opacity-0 group-hover:opacity-100 text-teal-600 transition-opacity" />
              </div>
              <div className="text-[11px] text-slate-500 mt-1 leading-snug">{item.desc}</div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
