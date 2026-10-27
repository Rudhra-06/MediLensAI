import React from 'react';
import {
  ListFilter,
  ArrowUpDown,
  Filter,
  UserCheck,
} from 'lucide-react';
import { EmptyState } from '../common/EmptyState';
import { DisclaimerBanner } from '../common/DisclaimerBanner';

export const InvestigationQueuePage: React.FC = () => {
  return (
    <div className="space-y-6">
      <DisclaimerBanner />

      {/* Queue Overview Header */}
      <div className="bg-white rounded-xl border border-slate-200/90 p-5 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base font-bold text-slate-900">
                Fraud Review & Investigation Queue
              </h2>
              <span className="text-[11px] font-semibold bg-slate-100 text-slate-700 border border-slate-200 px-2.5 py-0.5 rounded-full">
                0 Active Cases
              </span>
            </div>
            <p className="text-xs text-slate-600 mt-1 max-w-2xl">
              Human-in-the-loop review station. High-risk and anomalous claims flagged by the ML screening pipeline are routed here for certified clinical and claims auditor review.
            </p>
          </div>

          <div className="flex items-center gap-2 text-xs">
            <span className="text-slate-500 font-medium">Auditor Role:</span>
            <span className="font-semibold text-slate-800 bg-slate-100 px-2.5 py-1 rounded-md border border-slate-200">
              Senior SIU Investigator (Demo)
            </span>
          </div>
        </div>

        {/* Filter Controls Bar (Disabled in Empty State) */}
        <div className="mt-5 pt-4 border-t border-slate-100 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2 text-xs">
            <button
              disabled
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-slate-100 text-slate-400 border border-slate-200 cursor-not-allowed"
            >
              <Filter className="w-3.5 h-3.5" />
              <span>Risk Tier: All</span>
            </button>
            <button
              disabled
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-slate-100 text-slate-400 border border-slate-200 cursor-not-allowed"
            >
              <span>Status: Awaiting Triage</span>
            </button>
            <button
              disabled
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-slate-100 text-slate-400 border border-slate-200 cursor-not-allowed"
            >
              <span>Sort: Priority Desc</span>
              <ArrowUpDown className="w-3 h-3" />
            </button>
          </div>

          <div className="text-[11px] text-slate-400">
            Filters disabled while queue is empty
          </div>
        </div>
      </div>

      {/* Honest Empty Queue State */}
      <EmptyState
        icon={ListFilter}
        title="Investigation Queue is Empty"
        description="There are currently zero claims awaiting human investigation. When claims are ingested and scored with risk probabilities above the screening threshold, they will automatically populate this priority review table."
        badgeText="Zero Pending Claims"
        badgeType="neutral"
        secondaryNotice="Auditors make final determinations. MediLens AI predictions serve as triage indicators and never constitute automated claims denial."
      />

      {/* Planned Review Table Schema Specification Preview */}
      <div className="bg-white rounded-xl border border-slate-200/90 p-5 shadow-xs">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
            Planned Queue Schema Contract
          </h3>
          <span className="text-[10px] text-slate-500 font-mono">
            Table Preview (Header Layout Only)
          </span>
        </div>

        <div className="overflow-x-auto border border-slate-200 rounded-lg">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200">
              <tr>
                <th className="py-2.5 px-3">Claim ID</th>
                <th className="py-2.5 px-3">Provider NPI</th>
                <th className="py-2.5 px-3">Billed / Allowed</th>
                <th className="py-2.5 px-3">Risk Tier</th>
                <th className="py-2.5 px-3">Primary Trigger Feature</th>
                <th className="py-2.5 px-3">Audit Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-500">
              <tr>
                <td colSpan={6} className="py-8 text-center text-slate-400 bg-slate-50/50">
                  <div className="flex flex-col items-center justify-center gap-1">
                    <UserCheck className="w-5 h-5 text-slate-300 mb-1" />
                    <span>No records to display. Queue will be populated in Phase 05.</span>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
