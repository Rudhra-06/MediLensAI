import React, { useState, useEffect, useCallback } from 'react';
import { AppShell } from './components/layout/AppShell';
import type { PageId } from './types/navigation';
import type { HealthResponse, ApiConnectionState } from './types/health';
import { fetchHealthStatus, API_BASE_URL } from './services/api';

// Pages
import { OverviewPage } from './components/pages/OverviewPage';
import { ClaimsIntelligencePage } from './components/pages/ClaimsIntelligencePage';
import { InvestigationQueuePage } from './components/pages/InvestigationQueuePage';
import { ModelInsightsPage } from './components/pages/ModelInsightsPage';
import { DataManagementPage } from './components/pages/DataManagementPage';
import { SettingsPage } from './components/pages/SettingsPage';

export const App: React.FC = () => {
  const [activePage, setActivePage] = useState<PageId>('overview');
  const [apiState, setApiState] = useState<ApiConnectionState>('checking');
  const [healthData, setHealthData] = useState<HealthResponse | null>(null);

  const checkApiHealth = useCallback(async (isManualRefresh = false) => {
    if (isManualRefresh) {
      setApiState('checking');
    }
    try {
      const data = await fetchHealthStatus();
      setHealthData(data);
      setApiState('connected');
    } catch {
      setHealthData(null);
      setApiState('disconnected');
    }
  }, []);

  useEffect(() => {
    let ignore = false;
    fetchHealthStatus()
      .then((data) => {
        if (!ignore) {
          setHealthData(data);
          setApiState('connected');
        }
      })
      .catch(() => {
        if (!ignore) {
          setHealthData(null);
          setApiState('disconnected');
        }
      });
    return () => {
      ignore = true;
    };
  }, []);

  const renderActivePage = () => {
    switch (activePage) {
      case 'overview':
        return (
          <OverviewPage
            healthData={healthData}
            apiState={apiState}
            onNavigate={setActivePage}
          />
        );
      case 'claims-intelligence':
        return <ClaimsIntelligencePage />;
      case 'investigation-queue':
        return <InvestigationQueuePage />;
      case 'model-insights':
        return <ModelInsightsPage />;
      case 'data-management':
        return <DataManagementPage />;
      case 'settings':
        return <SettingsPage healthData={healthData} />;
      default:
        return (
          <OverviewPage
            healthData={healthData}
            apiState={apiState}
            onNavigate={setActivePage}
          />
        );
    }
  };

  return (
    <AppShell
      activePage={activePage}
      onSelectPage={setActivePage}
      apiState={apiState}
      healthData={healthData}
      onRefreshHealth={() => checkApiHealth(true)}
    >
      {/* Backend Disconnection Alert if API is down */}
      {apiState === 'disconnected' && (
        <div
          role="alert"
          className="mb-6 p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-900 text-xs sm:text-sm flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-xs"
        >
          <div>
            <span className="font-bold">Backend API Unreachable ({API_BASE_URL}): </span>
            Ensure the FastAPI backend server is running via{' '}
            <code className="bg-rose-100 text-rose-950 px-1.5 py-0.5 rounded-sm font-mono text-xs">
              uvicorn backend.app.main:app --port 8000
            </code>
            .
          </div>
          <button
            onClick={() => checkApiHealth(true)}
            className="px-3 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-700 text-white font-semibold text-xs transition-colors shrink-0 cursor-pointer focus:outline-hidden focus:ring-2 focus:ring-rose-500"
          >
            Retry Connection
          </button>
        </div>
      )}

      {/* Render Current Destination */}
      {renderActivePage()}
    </AppShell>
  );
};

export default App;
