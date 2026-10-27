import React from 'react';
import type { ApiConnectionState, ModelReadiness } from '../../types/health';

interface ApiStatusBadgeProps {
  state: ApiConnectionState;
  onClickRetry?: () => void;
}

export const ApiStatusBadge: React.FC<ApiStatusBadgeProps> = ({ state, onClickRetry }) => {
  if (state === 'checking') {
    return (
      <span
        className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-slate-100 text-slate-700 border border-slate-300"
        title="Checking backend connection..."
      >
        <span className="w-2 h-2 rounded-full bg-slate-400 animate-pulse" />
        API: Checking...
      </span>
    );
  }

  if (state === 'connected') {
    return (
      <span
        className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-teal-50 text-teal-800 border border-teal-200"
        title="Backend API is connected and responding"
      >
        <span className="w-2 h-2 rounded-full bg-teal-500" />
        API: Connected
      </span>
    );
  }

  return (
    <div className="inline-flex items-center gap-1.5">
      <span
        className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-rose-50 text-rose-800 border border-rose-200"
        title="Backend API is unreachable at the configured address"
      >
        <span className="w-2 h-2 rounded-full bg-rose-500" />
        API: Disconnected
      </span>
      {onClickRetry && (
        <button
          onClick={onClickRetry}
          type="button"
          className="text-xs text-teal-700 hover:text-teal-900 underline font-medium focus:outline-hidden focus:ring-2 focus:ring-teal-500 rounded-sm px-1 cursor-pointer"
        >
          Retry
        </button>
      )}
    </div>
  );
};

interface ModelReadinessBadgeProps {
  modelReadiness: ModelReadiness | null;
}

export const ModelReadinessBadge: React.FC<ModelReadinessBadgeProps> = ({ modelReadiness }) => {
  if (!modelReadiness || !modelReadiness.ready) {
    return (
      <span
        className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-amber-50 text-amber-800 border border-amber-200"
        title={modelReadiness?.reason || 'ML model pipeline not yet trained or loaded'}
      >
        <span className="w-2 h-2 rounded-full bg-amber-500" />
        ML Engine: Not Ready
      </span>
    );
  }

  return (
    <span
      className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-teal-50 text-teal-800 border border-teal-200"
      title={`Active Model: ${modelReadiness.loaded_model_version || 'Ready'}`}
    >
      <span className="w-2 h-2 rounded-full bg-teal-500" />
      ML Engine: Ready
    </span>
  );
};
