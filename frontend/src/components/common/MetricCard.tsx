import React from 'react';
import type { LucideIcon } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string;
  subtitle: string;
  icon: LucideIcon;
  badgeLabel?: string;
  badgeVariant?: 'neutral' | 'teal' | 'amber';
  infoTooltip?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  badgeLabel = 'Baseline / Idle',
  badgeVariant = 'neutral',
  infoTooltip,
}) => {
  const badgeStyles = {
    neutral: 'bg-slate-100 text-slate-700 border-slate-200',
    teal: 'bg-teal-50 text-teal-800 border-teal-200',
    amber: 'bg-amber-50 text-amber-800 border-amber-200',
  };

  return (
    <div
      className="bg-white rounded-xl border border-slate-200/90 p-5 shadow-xs hover:border-slate-300 transition-colors"
      title={infoTooltip}
    >
      <div className="flex items-center justify-between gap-2 mb-3">
        <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">{title}</span>
        <div className="w-9 h-9 rounded-lg bg-slate-50 text-slate-600 flex items-center justify-center border border-slate-100">
          <Icon className="w-4 h-4 text-slate-700" aria-hidden="true" />
        </div>
      </div>

      <div className="flex items-baseline gap-2 mb-2">
        <span className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900">{value}</span>
      </div>

      <div className="flex items-center justify-between gap-2 pt-2 border-t border-slate-100">
        <span className="text-xs text-slate-500 truncate">{subtitle}</span>
        <span className={`text-[11px] font-medium px-2 py-0.5 rounded-full border shrink-0 ${badgeStyles[badgeVariant]}`}>
          {badgeLabel}
        </span>
      </div>
    </div>
  );
};
