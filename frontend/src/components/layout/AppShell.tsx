import React, { useState } from 'react';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import type { PageId } from '../../types/navigation';
import type { ApiConnectionState, HealthResponse } from '../../types/health';

interface AppShellProps {
  activePage: PageId;
  onSelectPage: (page: PageId) => void;
  apiState: ApiConnectionState;
  healthData: HealthResponse | null;
  onRefreshHealth: () => void;
  children: React.ReactNode;
}

export const AppShell: React.FC<AppShellProps> = ({
  activePage,
  onSelectPage,
  apiState,
  healthData,
  onRefreshHealth,
  children,
}) => {
  const [isOpenMobile, setIsOpenMobile] = useState<boolean>(false);

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex font-sans antialiased">
      {/* Sidebar Navigation */}
      <Sidebar
        activePage={activePage}
        onSelectPage={onSelectPage}
        isOpenMobile={isOpenMobile}
        onCloseMobile={() => setIsOpenMobile(false)}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 lg:pl-72">
        {/* Sticky Header */}
        <Header
          activePage={activePage}
          apiState={apiState}
          modelReadiness={healthData?.model_readiness ?? null}
          onRefreshHealth={onRefreshHealth}
          onOpenMobileSidebar={() => setIsOpenMobile(true)}
        />

        {/* Page Container */}
        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto">
          {children}
        </main>

        {/* Page Footer */}
        <footer className="border-t border-slate-200/80 bg-white py-4 px-6 text-center text-xs text-slate-500">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-2 max-w-7xl mx-auto">
            <span className="font-medium text-slate-600">
              MediLens AI &copy; 2026. Explainable Healthcare Claim Fraud Screening.
            </span>
            <span className="text-slate-400">
              Predictions indicate potential fraud risk for human auditor review, not proof of fraud.
            </span>
          </div>
        </footer>
      </div>
    </div>
  );
};
