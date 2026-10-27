import React from 'react';
import { ShieldAlert } from 'lucide-react';

export const DisclaimerBanner: React.FC = () => {
  return (
    <div
      role="region"
      aria-label="Clinical and Fraud Review Compliance Notice"
      className="bg-amber-50 border-l-4 border-amber-500 p-3 sm:p-4 rounded-r-md text-amber-900 shadow-xs flex items-start gap-3 my-4"
    >
      <ShieldAlert className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" aria-hidden="true" />
      <div className="text-xs sm:text-sm leading-relaxed">
        <span className="font-semibold text-amber-950">Investigation Support Disclaimer: </span>
        MediLens AI generates statistical fraud risk estimations and explainability indicators
        solely to prioritize and assist human clinical/claims review. Predictions indicate potential
        risk patterns, <strong className="font-semibold underline">never proof of fraud</strong>. No automated denial or adverse claim determination should ever be made without certified human auditor review.
      </div>
    </div>
  );
};
