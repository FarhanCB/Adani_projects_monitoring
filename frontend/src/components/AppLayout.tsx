import React, { useState } from 'react';
import {
  LayoutDashboard,
  Globe,
  AlertTriangle,
  FileText,
  BarChart3,
  Settings,
  Activity,
  LogOut,
  Menu,
  X,
  Radio,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { AdaniLogo } from './AdaniLogo';

interface AppLayoutProps {
  currentPage: string;
  onNavigate: (page: string, params?: any) => void;
  children: React.ReactNode;
  pageTitle?: string;
}

export const AppLayout: React.FC<AppLayoutProps> = ({
  currentPage,
  onNavigate,
  children,
  pageTitle = 'Dashboard',
}) => {
  const { user, logout, isAdmin } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'projects', label: 'Projects', icon: Globe },
    { id: 'incidents', label: 'Incidents', icon: AlertTriangle },
    { id: 'logs', label: 'Monitoring Logs', icon: FileText },
    { id: 'analytics', label: 'Global Analytics', icon: BarChart3 },
    { id: 'settings', label: 'Settings', icon: Settings },
    { id: 'health', label: 'System Health', icon: Activity },
  ];

  return (
    <div className="min-h-screen flex bg-slate-50 text-slate-900 font-sans">
      {/* Sidebar - Desktop */}
      <aside className="hidden lg:flex flex-col w-64 bg-white border-r border-slate-200 fixed inset-y-0 z-30 shadow-subtle">
        {/* Brand Header with Official Logo */}
        <div className="h-16 flex items-center px-5 border-b border-slate-100 bg-white">
          <AdaniLogo size="md" showSubtitle={true} />
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentPage === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onNavigate(item.id)}
                className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-semibold transition-all duration-150 ${
                  isActive
                    ? 'bg-gradient-to-r from-sky-50 via-purple-50 to-pink-50 text-[#583896] border border-purple-200/60 shadow-sm font-bold'
                    : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                }`}
              >
                <Icon
                  className={`w-4 h-4 ${
                    isActive ? 'text-[#583896]' : 'text-slate-400 group-hover:text-slate-600'
                  }`}
                />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        {/* User Profile in Sidebar Footer */}
        <div className="p-4 border-t border-slate-100 bg-slate-50/50">
          <div className="flex items-center space-x-3 mb-3">
            <div className="w-9 h-9 rounded-full bg-gradient-to-tr from-[#0078BD] via-[#583896] to-[#BE185D] text-white flex items-center justify-center font-bold text-sm shadow-sm">
              {user?.full_name?.charAt(0) || 'U'}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-bold text-slate-900 truncate">
                {user?.full_name || 'User'}
              </p>
              <p className="text-[10px] text-slate-400 mt-0.5 truncate">
                {user?.email}
              </p>
            </div>
          </div>

          <button
            onClick={logout}
            className="w-full flex items-center justify-center space-x-2 px-3 py-1.5 text-xs font-semibold text-slate-700 bg-white border border-slate-200 hover:bg-slate-50 hover:text-[#BE185D] rounded-lg transition-colors shadow-sm"
          >
            <LogOut className="w-3.5 h-3.5" />
            <span>Sign Out</span>
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 lg:pl-64 flex flex-col min-h-screen">
        {/* Top Header */}
        <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-6 sticky top-0 z-20 shadow-subtle">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="lg:hidden p-2 rounded-lg text-slate-600 hover:bg-slate-100"
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
            <h1 className="text-lg font-extrabold text-slate-900 capitalize">
              {pageTitle}
            </h1>
          </div>

          <div className="flex items-center space-x-3">
            {/* User Avatar Menu */}
            <div className="flex items-center space-x-2 pl-2">
              <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-[#0078BD] to-[#583896] text-white flex items-center justify-center font-bold text-xs shadow-sm">
                {user?.full_name?.charAt(0) || 'A'}
              </div>
              <span className="hidden md:inline text-xs font-semibold text-slate-800">
                {user?.full_name?.split(' ')[0]}
              </span>
            </div>
          </div>
        </header>

        {/* Mobile Navigation Drawer */}
        {mobileMenuOpen && (
          <div className="lg:hidden fixed inset-0 z-40 bg-slate-900/50 backdrop-blur-sm">
            <div className="w-64 bg-white h-full p-4 shadow-xl flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-6 pb-3 border-b border-slate-100">
                  <AdaniLogo size="sm" showSubtitle={true} />
                  <button onClick={() => setMobileMenuOpen(false)}>
                    <X className="w-5 h-5 text-slate-500" />
                  </button>
                </div>
                <nav className="space-y-1">
                  {navItems.map((item) => {
                    const Icon = item.icon;
                    return (
                      <button
                        key={item.id}
                        onClick={() => {
                          onNavigate(item.id);
                          setMobileMenuOpen(false);
                        }}
                        className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-semibold ${
                          currentPage === item.id
                            ? 'bg-purple-50 text-[#583896] font-bold'
                            : 'text-slate-600'
                        }`}
                      >
                        <Icon className="w-4 h-4" />
                        <span>{item.label}</span>
                      </button>
                    );
                  })}
                </nav>
              </div>

              <button
                onClick={logout}
                className="w-full flex items-center justify-center space-x-2 px-3 py-2 text-sm font-bold text-slate-700 bg-slate-100 rounded-lg hover:text-[#BE185D]"
              >
                <LogOut className="w-4 h-4" />
                <span>Sign Out</span>
              </button>
            </div>
          </div>
        )}

        {/* Page Content */}
        <main className="flex-1 p-6 max-w-7xl w-full mx-auto animate-fade-in">
          {children}
        </main>
      </div>
    </div>
  );
};
