import React from 'react';
import {
  Server,
  Sliders,
  Lock,
} from 'lucide-react';
import type { HealthResponse } from '../../types/health';
import { API_BASE_URL } from '../../services/api';
import { DisclaimerBanner } from '../common/DisclaimerBanner';

interface SettingsPageProps {
  healthData: HealthResponse | null;
}

export const SettingsPage: React.FC<SettingsPageProps> = ({ healthData }) => {
  return (
    <div className="space-y-6">
      <DisclaimerBanner />

      {/* Header */}
      <div className="bg-white rounded-xl border border-slate-200/90 p-5 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base font-bold text-slate-900">
                System Configuration & Runtime Settings
              </h2>
              <span className="text-[11px] font-semibold bg-slate-100 text-slate-700 border border-slate-200 px-2.5 py-0.5 rounded-full">
                Read-Only (Phase 01)
              </span>
            </div>
            <p className="text-xs text-slate-600 mt-1 max-w-2xl">
              Inspect current operational parameters, active API endpoints, risk tier thresholds, and governance policies. Modifiable settings will activate once database persistence is integrated.
            </p>
          </div>

          <div className="flex items-center gap-2 text-xs">
            <span className="text-slate-500">Config Mode:</span>
            <span className="font-semibold text-slate-800 bg-slate-100 px-2.5 py-1 rounded-md border border-slate-200">
              Environment Variables
            </span>
          </div>
        </div>
      </div>

      {/* Grid: Active Runtime Parameters & Default Risk Scoring Thresholds */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Active Runtime Parameters */}
        <div className="bg-white rounded-xl border border-slate-200/90 p-5 shadow-xs">
          <div className="flex items-center gap-2 mb-4">
            <Server className="w-4 h-4 text-teal-600" />
            <h3 className="text-sm font-bold text-slate-900">Active Runtime Parameters</h3>
          </div>

          <div className="space-y-3 text-xs">
            <div className="p-3 rounded-lg bg-slate-50 border border-slate-200/80 flex items-center justify-between">
              <span className="text-slate-600 font-medium">Backend API URL</span>
              <span className="font-mono text-slate-900 font-semibold bg-white px-2 py-0.5 rounded-sm border border-slate-200">
                {API_BASE_URL}
              </span>
            </div>

            <div className="p-3 rounded-lg bg-slate-50 border border-slate-200/80 flex items-center justify-between">
              <span className="text-slate-600 font-medium">Application Environment</span>
              <span className="font-mono text-slate-900 bg-white px-2 py-0.5 rounded-sm border border-slate-200">
                {healthData?.environment ?? 'development'}
              </span>
            </div>

            <div className="p-3 rounded-lg bg-slate-50 border border-slate-200/80 flex items-center justify-between">
              <span className="text-slate-600 font-medium">FastAPI Core Version</span>
              <span className="font-mono text-slate-900 bg-white px-2 py-0.5 rounded-sm border border-slate-200">
                {healthData?.version ?? '0.1.0'}
              </span>
            </div>

            <div className="p-3 rounded-lg bg-slate-50 border border-slate-200/80 flex items-center justify-between">
              <span className="text-slate-600 font-medium">CORS Permitted Origins</span>
              <span className="font-mono text-slate-900 text-[11px] bg-white px-2 py-0.5 rounded-sm border border-slate-200 truncate max-w-[200px]">
                http://localhost:5173
              </span>
            </div>
          </div>
        </div>

        {/* Fraud Screening Threshold Defaults */}
        <div className="bg-white rounded-xl border border-slate-200/90 p-5 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Sliders className="w-4 h-4 text-teal-600" />
                <h3 className="text-sm font-bold text-slate-900">
                  Risk Tier Calibration Thresholds
                </h3>
              </div>
              <span className="text-[10px] text-slate-400 bg-slate-100 px-2 py-0.5 rounded-sm">
                Default Calibration
              </span>
            </div>

            <p className="text-xs text-slate-500 mb-4">
              Configures the probability boundaries used by the ML estimator to classify incoming claims into investigation priority tiers:
            </p>

            <div className="space-y-2.5 text-xs">
              {[
                { tier: 'High Suspicion Tier', value: '≥ 0.85', desc: 'Mandatory priority queue routing' },
                { tier: 'Elevated Risk Tier', value: '0.65 - 0.84', desc: 'Secondary auditor review' },
                { tier: 'Moderate Risk Tier', value: '0.30 - 0.64', desc: 'Automated policy rule check' },
                { tier: 'Low Risk Tier', value: '< 0.30', desc: 'Standard adjudication path' },
              ].map((t, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between p-2.5 rounded-lg bg-slate-50 border border-slate-200/70"
                >
                  <div>
                    <span className="font-semibold text-slate-800 text-xs">{t.tier}</span>
                    <span className="text-slate-400 text-[11px] block">{t.desc}</span>
                  </div>
                  <span className="font-mono font-bold text-slate-900 bg-white border border-slate-200 px-2 py-0.5 rounded-sm">
                    {t.value}
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-100 flex items-center gap-2 text-[11px] text-slate-500">
            <Lock className="w-3.5 h-3.5 text-slate-400 shrink-0" />
            <span>Threshold editing controls will unlock when PostgreSQL persistence is added.</span>
          </div>
        </div>
      </div>
    </div>
  );
};
