import React from 'react';
import type { LucideIcon } from 'lucide-react';

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description: string;
  badgeText?: string;
  badgeType?: 'neutral' | 'info' | 'amber';
  secondaryNotice?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon: Icon,
  title,
  description,
  badgeText,
  badgeType = 'neutral',
  secondaryNotice,
}) => {
  const badgeColors = {
    neutral: 'bg-slate-100 text-slate-700 border-slate-200',
    info: 'bg-teal-50 text-teal-800 border-teal-200',
    amber: 'bg-amber-50 text-amber-800 border-amber-200',
  };

  return (
    <div className="flex flex-col items-center justify-center text-center p-8 sm:p-12 bg-white rounded-xl border border-slate-200/80 shadow-xs max-w-2xl mx-auto my-6">
      <div className="w-14 h-14 rounded-full bg-slate-100 text-slate-600 flex items-center justify-center mb-4">
        <Icon className="w-7 h-7" aria-hidden="true" />
      </div>

      {badgeText && (
        <span
          className={`inline-block px-2.5 py-0.5 text-xs font-medium rounded-full border mb-3 ${badgeColors[badgeType]}`}
        >
          {badgeText}
        </span>
      )}

      <h3 className="text-base sm:text-lg font-semibold text-slate-900 mb-2">{title}</h3>
      <p className="text-sm text-slate-600 max-w-md leading-relaxed mb-4">{description}</p>

      {secondaryNotice && (
        <div className="text-xs text-slate-500 bg-slate-50 border border-slate-200 rounded-md p-3 max-w-lg">
          {secondaryNotice}
        </div>
      )}
    </div>
  );
};
