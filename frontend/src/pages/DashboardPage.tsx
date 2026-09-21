import React, { useEffect, useState } from 'react';
import {
  Globe,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Clock,
  RefreshCw,
  Search,
  Filter,
  Plus,
} from 'lucide-react';
import { api } from '../api/client';
import { MetricsCard } from '../components/MetricsCard';
import { ProjectCard } from '../components/ProjectCard';
import { DashboardMetrics, ProjectCardData } from '../types';
import { useAuth } from '../context/AuthContext';

interface DashboardPageProps {
  onSelectProject: (id: number) => void;
  onNavigate: (page: string) => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({
  onSelectProject,
  onNavigate,
}) => {
  const { isAdmin } = useAuth();
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [projects, setProjects] = useState<ProjectCardData[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [autoRefresh, setAutoRefresh] = useState(true);

  const fetchDashboardData = async (isManual = false) => {
    if (isManual) setRefreshing(true);
    try {
      const data = await api.getDashboard();
      setMetrics(data.metrics);
      setProjects(data.projects);
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
    } finally {
      setLoading(false);
      if (isManual) setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  // Auto-refresh interval (every 20 seconds)
  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(() => {
      fetchDashboardData();
    }, 20000);
    return () => clearInterval(interval);
  }, [autoRefresh]);

  const handleTestProject = async (id: number) => {
    try {
      await api.testProject(id);
      // Refresh dashboard after probe
      await fetchDashboardData();
    } catch (err) {
      console.error('Manual test failed:', err);
    }
  };

  // Filter projects by search and status
  const filteredProjects = projects.filter((p) => {
    const matchesSearch =
      p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.url.toLowerCase().includes(searchQuery.toLowerCase());

    if (!matchesSearch) return false;

    if (statusFilter === 'ALL') return true;
    return p.current_status.toUpperCase() === statusFilter;
  });

  return (
    <div className="space-y-6">
      {/* Top Controls & Banner */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-2">
        <div>
          <h2 className="text-xl font-black text-slate-900 tracking-tight">
            Infrastructure Monitoring Overview
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Real-time status, availability metrics, and outage alerts across enterprise services
          </p>
        </div>

        <div className="flex items-center space-x-2 w-full sm:w-auto">
          <label className="flex items-center space-x-2 text-xs text-slate-600 bg-white border border-slate-200 px-3 py-1.5 rounded-lg shadow-sm cursor-pointer hover:bg-slate-50">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="rounded text-[#0078BD] focus:ring-[#0078BD] h-3.5 w-3.5"
            />
            <span>Auto-refresh (20s)</span>
          </label>

          <button
            onClick={() => fetchDashboardData(true)}
            disabled={refreshing}
            className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-xs font-semibold shadow-sm transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin text-[#583896]' : ''}`} />
            <span>Refresh</span>
          </button>

          <button
            onClick={() => onNavigate('projects')}
            className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-gradient-to-r from-[#0078BD] via-[#583896] to-[#BE185D] text-white text-xs font-bold shadow-adani hover:opacity-95 transition-opacity"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Add Website</span>
          </button>
        </div>
      </div>

      {/* Top 6 Summary Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
        <MetricsCard
          title="Total Sites"
          value={metrics?.total_projects ?? '—'}
          subValue="Monitored endpoints"
          icon={<Globe className="w-5 h-5" />}
          accentColor="slate"
        />

        <MetricsCard
          title="Online (UP)"
          value={metrics?.up_count ?? '—'}
          subValue="Healthy services"
          icon={<CheckCircle2 className="w-5 h-5" />}
          accentColor="green"
        />

        <MetricsCard
          title="Offline (DOWN)"
          value={metrics?.down_count ?? '—'}
          subValue={metrics?.down_count ? 'Critical Outage' : 'No outages'}
          icon={<XCircle className="w-5 h-5" />}
          accentColor="red"
        />

        <MetricsCard
          title="Warning"
          value={metrics?.warning_count ?? '—'}
          subValue="High latency / SSL"
          icon={<AlertTriangle className="w-5 h-5" />}
          accentColor="amber"
        />

        <MetricsCard
          title="Total Incidents"
          value={metrics?.total_incidents ?? '—'}
          subValue="Past 30 days"
          icon={<AlertTriangle className="w-5 h-5" />}
          accentColor="orange"
          onClick={() => onNavigate('incidents')}
        />

        <MetricsCard
          title="Total Downtime"
          value={metrics?.total_downtime_formatted ?? '0m'}
          subValue="Past 30 days"
          icon={<Clock className="w-5 h-5" />}
          accentColor="red"
        />
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-subtle flex flex-col sm:flex-row items-center justify-between gap-3">
        {/* Search */}
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 transform -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search websites by name or URL..."
            className="w-full pl-9 pr-4 py-2 text-xs border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#0078BD] focus:border-transparent"
          />
        </div>

        {/* Status Filter Tabs */}
        <div className="flex items-center space-x-1.5 overflow-x-auto w-full sm:w-auto pb-1 sm:pb-0">
          <span className="text-xs font-semibold text-slate-400 mr-2 flex items-center">
            <Filter className="w-3 h-3 mr-1" /> Filter:
          </span>
          {['ALL', 'UP', 'DOWN', 'WARNING', 'PAUSED'].map((tab) => (
            <button
              key={tab}
              onClick={() => setStatusFilter(tab)}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                statusFilter === tab
                  ? 'bg-slate-900 text-white shadow-sm'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      {/* Projects Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {[1, 2, 3, 4, 5, 6].map((n) => (
            <div
              key={n}
              className="h-56 bg-white rounded-xl border border-slate-200 animate-pulse p-6"
            />
          ))}
        </div>
      ) : filteredProjects.length === 0 ? (
        <div className="bg-white rounded-xl p-12 text-center border border-slate-200 shadow-subtle">
          <Globe className="w-12 h-12 text-slate-300 mx-auto mb-3" />
          <h3 className="text-base font-bold text-slate-800">No websites match your filter</h3>
          <p className="text-xs text-slate-500 mt-1">
            Try adjusting your search keywords or status filter.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredProjects.map((proj) => (
            <ProjectCard
              key={proj.id}
              project={proj}
              onSelect={onSelectProject}
              onTestNow={handleTestProject}
            />
          ))}
        </div>
      )}
    </div>
  );
};
