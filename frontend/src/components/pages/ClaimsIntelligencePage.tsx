import React from 'react';
import {
  FileSearch,
  UploadCloud,
  FileCheck2,
} from 'lucide-react';
import { EmptyState } from '../common/EmptyState';
import { DisclaimerBanner } from '../common/DisclaimerBanner';

export const ClaimsIntelligencePage: React.FC = () => {
  return (
    <div className="space-y-6">
      <DisclaimerBanner />

      {/* Header Description */}
      <div className="bg-white rounded-xl border border-slate-200/90 p-5 shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base font-bold text-slate-900">
                Claims Intelligence & Fraud Risk Screening
              </h2>
              <span className="text-[11px] font-semibold bg-amber-50 text-amber-800 border border-amber-200 px-2.5 py-0.5 rounded-full">
                Implementation: Phase 02
              </span>
            </div>
            <p className="text-xs text-slate-600 mt-1 max-w-2xl">
              This module will support both real-time individual claim risk triage and high-throughput batch screening. Automated screening outputs risk indicators and SHAP explanations to support certified fraud investigators.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500 bg-slate-100 px-3 py-1.5 rounded-lg border border-slate-200 font-medium">
              ML Model Status: Unloaded / Training Pending
            </span>
          </div>
        </div>
      </div>

      {/* Two Modality Cards: Single Claim Screening & Batch Processing */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Modality 1: Single-Claim Ad-Hoc Evaluation */}
        <div className="bg-white rounded-xl border border-slate-200/90 p-6 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-lg bg-teal-50 text-teal-700 border border-teal-200 flex items-center justify-center">
                <FileCheck2 className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-slate-900">
                  Single-Claim Interactive Screening
                </h3>
                <p className="text-xs text-slate-500">Planned real-time auditor triage tool</p>
              </div>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed mb-4">
              Designed for claims auditors who need immediate risk estimation and feature-level explanations for an individual flagged claim before adjudication.
            </p>

            <div className="bg-slate-50 rounded-lg border border-slate-200 p-4 space-y-2 text-xs">
              <div className="font-semibold text-slate-700 text-[11px] uppercase tracking-wider">
                Planned Input Specifications
              </div>
              <ul className="space-y-1.5 text-slate-600">
                <li className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-teal-500" />
                  Claim ID, Provider NPI, Beneficiary ID
                </li>
                <li className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-teal-500" />
                  Primary & Secondary ICD-10 Diagnosis Codes
                </li>
                <li className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-teal-500" />
                  CPT / HCPCS Procedure Codes & Modifiers
                </li>
                <li className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-teal-500" />
                  Submitted vs. Allowed Billed Amount Ratios
                </li>
              </ul>
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-slate-100 flex items-center justify-between">
            <span className="text-[11px] text-slate-400">Status: Form disabled until API route ready</span>
            <button
              disabled
              className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-100 text-slate-400 border border-slate-200 cursor-not-allowed"
              title="Single-claim screening will activate once ML inference endpoint is connected"
            >
              Single Triage (Coming Soon)
            </button>
          </div>
        </div>

        {/* Modality 2: Batch Claim Screening */}
        <div className="bg-white rounded-xl border border-slate-200/90 p-6 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-lg bg-indigo-50 text-indigo-700 border border-indigo-200 flex items-center justify-center">
                <UploadCloud className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-slate-900">
                  Batch Claim File Screening
                </h3>
                <p className="text-xs text-slate-500">Bulk claims dataset triage & scoring</p>
              </div>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed mb-4">
              Engineered to ingest batches of 1,000 to 50,000 claims, execute automated pre-validation, run vector risk inference, and prioritize flagged claims into the investigation queue.
            </p>

            <div className="bg-slate-50 rounded-lg border border-slate-200 p-4 space-y-2 text-xs">
              <div className="font-semibold text-slate-700 text-[11px] uppercase tracking-wider">
                Planned Batch Capabilities
              </div>
              <ul className="space-y-1.5 text-slate-600">
                <li className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-indigo-500" />
                  Standard CSV, NDJSON & EDI 837 Claim Format Support
                </li>
                <li className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-indigo-500" />
                  Streaming Schema Validation & Error Logging
                </li>
                <li className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-indigo-500" />
                  Fast Parallel Scoring via XGBoost Pipeline
                </li>
                <li className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-indigo-500" />
                  Automatic Population of Investigation Queue
                </li>
              </ul>
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-slate-100 flex items-center justify-between">
            <span className="text-[11px] text-slate-400">Status: File ingestion in Phase 02</span>
            <button
              disabled
              className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-100 text-slate-400 border border-slate-200 cursor-not-allowed"
              title="Batch file upload will be enabled in Phase 02"
            >
              Batch Upload (Coming Soon)
            </button>
          </div>
        </div>
      </div>

      {/* Honest Empty State Banner */}
      <EmptyState
        icon={FileSearch}
        title="No Active Screening Sessions"
        description="The screening engine is currently offline awaiting model calibration and ingestion pipeline initialization. Neither live claims nor fabricated predictions are displayed."
        badgeText="Planned Module"
        badgeType="info"
        secondaryNotice="To prevent erroneous fraud conclusions, synthetic or real risk scoring will only become active once the model validation checks pass."
      />
    </div>
  );
};
