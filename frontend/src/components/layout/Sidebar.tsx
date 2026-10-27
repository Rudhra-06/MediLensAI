import React from 'react';
import {
  LayoutDashboard,
  FileSearch,
  ListFilter,
  BrainCircuit,
  Database,
  Settings,
  Shield,
  X,
} from 'lucide-react';
import type { PageId } from '../../types/navigation';

interface SidebarProps {
  activePage: PageId;
  onSelectPage: (page: PageId) => void;
  isOpenMobile: boolean;
  onCloseMobile: () => void;
}

interface NavItem {
  id: PageId;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  tag?: string;
}

const navItems: NavItem[] = [
  { id: 'overview', label: 'Overview', icon: LayoutDashboard },
  { id: 'claims-intelligence', label: 'Claims Intelligence', icon: FileSearch, tag: 'Screening' },
  { id: 'investigation-queue', label: 'Investigation Queue', icon: ListFilter, tag: 'Queue' },
  { id: 'model-insights', label: 'Model Insights', icon: BrainCircuit, tag: 'SHAP / ML' },
  { id: 'data-management', label: 'Data Management', icon: Database },
  { id: 'settings', label: 'Settings', icon: Settings },
];

export const Sidebar: React.FC<SidebarProps> = ({
  activePage,
  onSelectPage,
  isOpenMobile,
  onCloseMobile,
}) => {
  return (
    <>
      {/* Mobile Backdrop */}
      {isOpenMobile && (
        <div
          className="fixed inset-0 bg-slate-950/60 z-40 lg:hidden backdrop-blur-xs transition-opacity"
          onClick={onCloseMobile}
          aria-hidden="true"
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 w-72 bg-[#0B192C] text-slate-200 flex flex-col border-r border-[#1E3E62]/40 transform transition-transform duration-200 ease-in-out lg:translate-x-0 ${
          isOpenMobile ? 'translate-x-0' : '-translate-x-full'
        }`}
        aria-label="Main Navigation"
      >
        {/* Brand Header */}
        <div className="h-16 px-6 flex items-center justify-between border-b border-[#1E3E62]/50">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-teal-500/10 border border-teal-500/30 flex items-center justify-center text-teal-400">
              <Shield className="w-5 h-5" aria-hidden="true" />
            </div>
            <div>
              <div className="font-semibold text-white tracking-tight text-base flex items-center gap-1.5">
                MediLens <span className="text-teal-400 font-bold">AI</span>
              </div>
              <p className="text-[11px] text-slate-400 leading-none">Fraud Screening & Review</p>
            </div>
          </div>

          <button
            onClick={onCloseMobile}
            className="lg:hidden p-1.5 rounded-md text-slate-400 hover:text-white hover:bg-slate-800/60 focus:outline-hidden focus:ring-2 focus:ring-teal-400 cursor-pointer"
            aria-label="Close navigation"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          <div className="px-3 pb-2 text-[11px] font-semibold tracking-wider text-slate-400 uppercase">
            Platform Modules
          </div>

          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activePage === item.id;

            return (
              <button
                key={item.id}
                onClick={() => {
                  onSelectPage(item.id);
                  onCloseMobile();
                }}
                className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 cursor-pointer focus:outline-hidden focus:ring-2 focus:ring-teal-400 ${
                  isActive
                    ? 'bg-[#1E3E62] text-white shadow-xs border-l-3 border-teal-400'
                    : 'text-slate-300 hover:bg-[#132438] hover:text-white'
                }`}
                aria-current={isActive ? 'page' : undefined}
              >
                <div className="flex items-center gap-3 truncate">
                  <Icon
                    className={`w-4 h-4 shrink-0 ${
                      isActive ? 'text-teal-400' : 'text-slate-400 group-hover:text-slate-200'
                    }`}
                  />
                  <span className="truncate">{item.label}</span>
                </div>
                {item.tag && (
                  <span
                    className={`text-[10px] font-semibold px-2 py-0.5 rounded-md ${
                      isActive
                        ? 'bg-teal-500/20 text-teal-300 border border-teal-500/30'
                        : 'bg-slate-800/80 text-slate-400 border border-slate-700/50'
                    }`}
                  >
                    {item.tag}
                  </span>
                )}
              </button>
            );
          })}
        </nav>

        {/* Sidebar Footer with Compliance & Architecture status */}
        <div className="p-4 border-t border-[#1E3E62]/40 bg-[#070E17]/60">
          <div className="bg-[#0B192C] border border-[#1E3E62]/60 rounded-lg p-3 text-xs">
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-[11px] font-medium text-slate-400">Environment</span>
              <span className="text-[10px] font-mono text-teal-400 bg-teal-500/10 px-1.5 py-0.5 rounded-sm">
                Local Dev
              </span>
            </div>
            <div className="text-[11px] text-slate-400 leading-tight">
              MediLens AI Foundation v0.1.0
            </div>
            <div className="mt-2 text-[10px] text-slate-400">
              Predictions = risk indicators, not proof.
            </div>
          </div>
        </div>
      </aside>
    </>
  );
};
