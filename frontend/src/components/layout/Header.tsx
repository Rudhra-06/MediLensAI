import React from 'react';
import { Menu, BookOpen, ExternalLink, RefreshCw } from 'lucide-react';
import type { ApiConnectionState, ModelReadiness } from '../../types/health';
import { ApiStatusBadge, ModelReadinessBadge } from '../common/StatusBadge';
import type { PageId } from '../../types/navigation';
import { API_BASE_URL } from '../../services/api';

interface HeaderProps {
  activePage: PageId;
  apiState: ApiConnectionState;
  modelReadiness: ModelReadiness | null;
  onRefreshHealth: () => void;
  onOpenMobileSidebar: () => void;
}

const pageTitles: Record<PageId, { title: string; subtitle: string }> = {
  overview: {
    title: 'Platform Overview',
    subtitle: 'System readiness, claims ingestion status, and fraud screening baseline',
  },
  'claims-intelligence': {
    title: 'Claims Intelligence',
    subtitle: 'High-throughput batch screening and explainable individual claim risk triage',
  },
  'provider-risk': {
    title: 'Provider Risk Assessment',
    subtitle: 'Score a manually entered provider-level feature vector with the saved model',
  },
  'investigation-queue': {
    title: 'Investigation Queue',
    subtitle: 'Priority review cases flagged by ML risk estimators for human auditor verification',
  },
  'model-insights': {
    title: 'Model Insights & SHAP',
    subtitle: 'Explainability diagnostics, global feature contributions, and audit transparency',
  },
  'data-management': {
    title: 'Data Management & Ingestion',
    subtitle: 'CMS-1500/UB-04 ingestion pipelines, schema validation, and data integrity',
  },
  settings: {
    title: 'System Settings',
    subtitle: 'API endpoints, screening sensitivity thresholds, and audit logging configuration',
  },
};

export const Header: React.FC<HeaderProps> = ({
  activePage,
  apiState,
  modelReadiness,
  onRefreshHealth,
  onOpenMobileSidebar,
}) => {
  const current = pageTitles[activePage];

  return (
    <header className="h-16 bg-white border-b border-slate-200/80 px-4 sm:px-8 flex items-center justify-between sticky top-0 z-30 shadow-2xs">
      {/* Left: Mobile trigger & breadcrumbs */}
      <div className="flex items-center gap-3">
        <button
          onClick={onOpenMobileSidebar}
          className="lg:hidden p-2 rounded-lg text-slate-600 hover:text-slate-900 hover:bg-slate-100 focus:outline-hidden focus:ring-2 focus:ring-teal-500 cursor-pointer"
          aria-label="Open sidebar navigation"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div>
          <h1 className="text-base sm:text-lg font-bold text-slate-900 leading-tight">
            {current.title}
          </h1>
          <p className="hidden md:block text-xs text-slate-500 truncate max-w-xl">
            {current.subtitle}
          </p>
        </div>
      </div>

      {/* Right: API Connectivity & Model Readiness Badges */}
      <div className="flex items-center gap-2 sm:gap-3">
        {/* Backend API Connection status badge */}
        <div className="flex items-center gap-1.5">
          <ApiStatusBadge state={apiState} onClickRetry={onRefreshHealth} />
          <button
            onClick={onRefreshHealth}
            title="Recheck API health"
            aria-label="Recheck API health"
            className="p-1 rounded-md text-slate-400 hover:text-slate-700 hover:bg-slate-100 focus:outline-hidden focus:ring-2 focus:ring-teal-500 cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${apiState === 'checking' ? 'animate-spin' : ''}`} />
          </button>
        </div>

        {/* ML Model Engine Readiness Badge */}
        <div className="hidden sm:block">
          <ModelReadinessBadge modelReadiness={modelReadiness} />
        </div>

        {/* API Docs Link */}
        <a
          href={`${API_BASE_URL}/docs`}
          target="_blank"
          rel="noopener noreferrer"
          className="hidden xl:inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium text-slate-600 hover:text-slate-900 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-md transition-colors"
          title="Open FastAPI Swagger Interactive API Documentation"
        >
          <BookOpen className="w-3.5 h-3.5 text-slate-500" />
          <span>API Docs</span>
          <ExternalLink className="w-3 h-3 text-slate-400" />
        </a>
      </div>
    </header>
  );
};
