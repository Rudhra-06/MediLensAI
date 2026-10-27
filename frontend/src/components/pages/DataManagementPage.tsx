import React from 'react';
import {
  Database,
  ShieldCheck,
  CheckCircle2,
  FileCheck,
  Lock,
} from 'lucide-react';
import { EmptyState } from '../common/EmptyState';
import { DisclaimerBanner } from '../common/DisclaimerBanner';

export const DataManagementPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <DisclaimerBanner />

      {/* Header with Pipeline Status */}
      <div className="bg-white rounded-xl border border-slate-200/90 p-5 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base font-bold text-slate-900">
                Claim Data Management & Validation
              </h2>
              <span className="text-[11px] font-semibold bg-amber-50 text-amber-800 border border-amber-200 px-2.5 py-0.5 rounded-full">
                Ingestion Engine: Not Yet Implemented
              </span>
            </div>
            <p className="text-xs text-slate-600 mt-1 max-w-2xl">
              Handles parsing, schema normalization, pre-validation checks, and storage for professional (CMS-1500) and institutional (UB-04) healthcare claims.
            </p>
          </div>

          <div className="flex items-center gap-2 text-xs">
            <span className="text-slate-500">Storage Backend:</span>
            <span className="font-mono bg-slate-100 text-slate-800 px-2 py-0.5 rounded-sm border border-slate-200">
              PostgreSQL (Planned)
            </span>
          </div>
        </div>
      </div>

      {/* Honest Empty State for Data Ingestion */}
      <EmptyState
        icon={Database}
        title="No Claim Datasets Ingested"
        description="The data ingestion pipeline has not yet been implemented. No external files have been loaded, and the database connection is intentionally unconfigured in this initial foundation step."
        badgeText="Pipeline Inactive"
        badgeType="neutral"
        secondaryNotice="To guarantee strict patient privacy and data compliance, MediLens AI operates strictly on synthetic or de-identified datasets. Never upload real Protected Health Information (PHI)."
      />

      {/* Ingestion Schema Specifications & Data Governance */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Healthcare Data Governance Notice */}
        <div className="bg-white rounded-xl border border-slate-200/90 p-5 shadow-xs">
          <div className="flex items-center gap-2 mb-3">
            <Lock className="w-4 h-4 text-teal-600" />
            <h3 className="text-sm font-bold text-slate-900">Data Governance & PHI Safety</h3>
          </div>

          <p className="text-xs text-slate-600 leading-relaxed mb-4">
            MediLens AI adheres to strict healthcare compliance principles. The platform enforces the following data rules:
          </p>

          <div className="space-y-2.5 text-xs">
            <div className="p-3 rounded-lg bg-teal-50/50 border border-teal-200/60 flex items-start gap-2.5">
              <ShieldCheck className="w-4 h-4 text-teal-700 shrink-0 mt-0.5" />
              <div className="text-slate-700">
                <span className="font-semibold text-slate-900">Synthetic Data Exclusivity: </span>
                All demonstration, unit testing, and ML calibration workflows use synthetic claims schemas (e.g., Synthea / CMS Synthetic Claims).
              </div>
            </div>

            <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 flex items-start gap-2.5">
              <CheckCircle2 className="w-4 h-4 text-slate-600 shrink-0 mt-0.5" />
              <div className="text-slate-700">
                <span className="font-semibold text-slate-900">Zero Direct Patient Identifiers: </span>
                Beneficiary identifiers are tokenized hashes with no direct Social Security Numbers (SSN) or patient names.
              </div>
            </div>
          </div>
        </div>

        {/* Planned Validation Matrix */}
        <div className="bg-white rounded-xl border border-slate-200/90 p-5 shadow-xs">
          <div className="flex items-center gap-2 mb-3">
            <FileCheck className="w-4 h-4 text-teal-600" />
            <h3 className="text-sm font-bold text-slate-900">Planned Ingestion Pre-Validation Checks</h3>
          </div>

          <p className="text-xs text-slate-600 leading-relaxed mb-3">
            Before reaching the ML inference layer, all ingested claims must satisfy standard health insurance billing invariants:
          </p>

          <ul className="space-y-2 text-xs text-slate-600">
            {[
              { rule: 'NPI Checksum & Registry', desc: 'Validates 10-digit National Provider Identifier using Luhn algorithm' },
              { rule: 'Date Sequence Invariant', desc: 'Admission date <= Service date <= Claim submission date' },
              { rule: 'ICD-10 / CPT Format', desc: 'Checks valid ICD-10 diagnosis codes and 5-digit CPT procedure codes' },
              { rule: 'Positive Financial Values', desc: 'Billed amount > 0, Co-pay >= 0, Deductible >= 0' },
            ].map((item, idx) => (
              <li key={idx} className="flex items-start gap-2 p-2 rounded-md bg-slate-50 border border-slate-100">
                <span className="w-1.5 h-1.5 rounded-full bg-teal-500 mt-1.5 shrink-0" />
                <div>
                  <span className="font-semibold text-slate-800">{item.rule}: </span>
                  <span className="text-slate-500">{item.desc}</span>
                </div>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
};
