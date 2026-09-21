import React, { useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { AppLayout } from './components/AppLayout';
import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';
import { ProjectDetailPage } from './pages/ProjectDetailPage';
import { ProjectsPage } from './pages/ProjectsPage';
import { IncidentsPage } from './pages/IncidentsPage';
import { LogsPage } from './pages/LogsPage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { SettingsPage } from './pages/SettingsPage';
import { SystemHealthPage } from './pages/SystemHealthPage';

const MainApp: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();
  const [currentPage, setCurrentPage] = useState<string>('dashboard');
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="flex flex-col items-center space-y-3">
          <div className="w-10 h-10 border-3 border-[#0078BD] border-t-transparent rounded-full animate-spin" />
          <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
            Loading Adani Monitoring...
          </span>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <LoginPage />;
  }

  const handleNavigate = (page: string, params?: any) => {
    setCurrentPage(page);
    if (page === 'project_detail' && params?.projectId) {
      setSelectedProjectId(params.projectId);
    } else if (page !== 'project_detail') {
      setSelectedProjectId(null);
    }
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleSelectProject = (id: number) => {
    setSelectedProjectId(id);
    setCurrentPage('project_detail');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const getPageTitle = () => {
    switch (currentPage) {
      case 'dashboard':
        return 'Executive Overview';
      case 'project_detail':
        return 'Website Analytics & Telemetry';
      case 'projects':
        return 'Monitored Websites';
      case 'incidents':
        return 'Outages & Incidents';
      case 'logs':
        return 'Telemetry & Probe Logs';
      case 'analytics':
        return 'Enterprise Analytics';
      case 'settings':
        return 'Platform Settings';
      case 'health':
        return 'System Health';
      default:
        return 'Dashboard';
    }
  };

  return (
    <AppLayout
      currentPage={currentPage}
      onNavigate={handleNavigate}
      pageTitle={getPageTitle()}
    >
      {currentPage === 'dashboard' && (
        <DashboardPage
          onSelectProject={handleSelectProject}
          onNavigate={handleNavigate}
        />
      )}

      {currentPage === 'project_detail' && selectedProjectId && (
        <ProjectDetailPage
          projectId={selectedProjectId}
          onBack={() => handleNavigate('dashboard')}
        />
      )}

      {currentPage === 'projects' && (
        <ProjectsPage onSelectProject={handleSelectProject} />
      )}

      {currentPage === 'incidents' && (
        <IncidentsPage onSelectProject={handleSelectProject} />
      )}

      {currentPage === 'logs' && <LogsPage />}

      {currentPage === 'analytics' && <AnalyticsPage />}

      {currentPage === 'settings' && <SettingsPage />}

      {currentPage === 'health' && <SystemHealthPage />}
    </AppLayout>
  );
};

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <MainApp />
    </AuthProvider>
  );
};

export default App;
