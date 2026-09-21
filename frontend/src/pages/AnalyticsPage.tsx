import React, { useEffect, useState } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from 'recharts';
import { Download, Calendar, Activity, CheckCircle2, AlertTriangle, Clock } from 'lucide-react';
import { api } from '../api/client';
import { GlobalAnalytics } from '../types';

export const AnalyticsPage: React.FC = () => {
  const [analytics, setAnalytics] = useState<GlobalAnalytics | null>(null);
  const [rangePreset, setRangePreset] = useState<string>('last_30_days');
  const [loading, setLoading] = useState(true);

  const rangeOptions = [
    { id: 'today', label: 'Today' },
    { id: 'this_week', label: 'This Week' },
    { id: 'last_7_days', label: 'Last 7 Days' },
    { id: 'this_month', label: 'This Month' },
    { id: 'last_30_days', label: 'Last 30 Days' },
    { id: 'last_90_days', label: 'Last 90 Days' },
  ];

  const fetchGlobalAnalytics = async () => {
    setLoading(true);
    try {
      const data = await api.getGlobalAnalytics(rangePreset);
      setAnalytics(data);
    } catch (err) {
      console.error('Failed to load global analytics:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGlobalAnalytics();
  }, [rangePreset]);

  const handleExportCsv = () => {
    const url = `http://localhost:8000/api/analytics/export/csv?range_preset=${rangePreset}`;
    window.open(url, '_blank');
  };

  const PIE_COLORS = ['#0078BD', '#583896', '#BE185D', '#0284C7', '#64748B'];

  if (loading || !analytics) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-8 bg-slate-200 rounded w-48 mb-4" />
        <div className="grid grid-cols-5 gap-4">
          {[1, 2, 3, 4, 5].map((n) => (
            <div key={n} className="h-24 bg-white rounded-xl border border-slate-200" />
          ))}
        </div>
        <div className="h-72 bg-white rounded-xl border border-slate-200" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Header & Range Controls */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-black text-slate-900 tracking-tight">
            Enterprise Infrastructure Analytics
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Cross-service reliability comparisons, availability SLAs, and error analysis
          </p>
        </div>

        <div className="flex items-center space-x-2 w-full sm:w-auto">
          {/* Range Selector */}
          <div className="flex items-center space-x-1 bg-white p-1 rounded-xl border border-slate-200 shadow-sm overflow-x-auto">
            {rangeOptions.map((opt) => (
              <button
                key={opt.id}
                onClick={() => setRangePreset(opt.id)}
                className={`px-2.5 py-1 text-xs font-bold rounded-lg transition-all ${
                  rangePreset === opt.id
                    ? 'bg-gradient-to-r from-[#0078BD] via-[#583896] to-[#BE185D] text-white shadow-sm'
                    : 'text-slate-600 hover:bg-slate-100'
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>

          <button
            onClick={handleExportCsv}
            className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 text-xs font-bold shadow-sm transition-colors"
          >
            <Download className="w-3.5 h-3.5 text-[#583896]" />
            <span>Export CSV</span>
          </button>
        </div>
      </div>

      {/* 5 Core Executive Metrics */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
        <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-subtle border-l-4 border-l-emerald-600">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 block">
            Overall Portfolio Uptime
          </span>
          <span className="text-2xl font-black text-slate-900 mt-1 block">
            {analytics.overall_uptime_pct.toFixed(2)}%
          </span>
          <span className="text-xs text-emerald-600 font-semibold mt-0.5 block">
            Across {analytics.total_projects} services
          </span>
        </div>

        <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-subtle border-l-4 border-l-rose-600">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 block">
            Total Combined Downtime
          </span>
          <span className="text-2xl font-black text-rose-600 mt-1 block">
            {analytics.total_downtime_formatted}
          </span>
          <span className="text-xs text-slate-400 font-medium mt-0.5 block">
            Cumulative outage time
          </span>
        </div>

        <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-subtle border-l-4 border-l-amber-500">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 block">
            Total Incidents
          </span>
          <span className="text-2xl font-black text-slate-900 mt-1 block">
            {analytics.total_incidents}
          </span>
          <span className="text-xs text-slate-400 font-medium mt-0.5 block">
            In selected range
          </span>
        </div>

        <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-subtle border-l-4 border-l-sky-500">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 block">
            Average Response Time
          </span>
          <span className="text-2xl font-black text-slate-900 mt-1 block">
            {analytics.avg_response_time_ms} ms
          </span>
          <span className="text-xs text-slate-400 font-medium mt-0.5 block">
            Portfolio latency
          </span>
        </div>

        <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-subtle border-l-4 border-l-indigo-500">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 block">
            Total Probe Errors
          </span>
          <span className="text-2xl font-black text-slate-900 mt-1 block">
            {analytics.total_errors}
          </span>
          <span className="text-xs text-slate-400 font-medium mt-0.5 block">
            Failed checks logged
          </span>
        </div>
      </div>

      {/* Comparison Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Uptime % by Project */}
        <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-subtle">
          <h4 className="text-sm font-bold text-slate-900 mb-1">Uptime Availability by Project (%)</h4>
          <p className="text-xs text-slate-500 mb-4">{analytics.range_label} SLA performance</p>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={analytics.project_comparisons} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" horizontal={false} />
                <XAxis type="number" domain={[90, 100]} unit="%" stroke="#94a3b8" fontSize={10} />
                <YAxis dataKey="project_name" type="category" width={140} stroke="#475569" fontSize={10} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0f172a',
                    borderRadius: '8px',
                    color: '#fff',
                    fontSize: '12px',
                    border: 'none',
                  }}
                  formatter={(val: any) => [`${val}%`, 'Uptime']}
                />
                <Bar dataKey="uptime_pct" fill="#16A34A" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Incidents by Project */}
        <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-subtle">
          <h4 className="text-sm font-bold text-slate-900 mb-1">Outage Incidents by Project</h4>
          <p className="text-xs text-slate-500 mb-4">Total number of service outage events</p>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={analytics.project_comparisons}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="project_name" stroke="#94a3b8" fontSize={10} />
                <YAxis stroke="#94a3b8" fontSize={10} allowDecimals={false} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0f172a',
                    borderRadius: '8px',
                    color: '#fff',
                    fontSize: '12px',
                    border: 'none',
                  }}
                />
                <Bar dataKey="incident_count" fill="#BE185D" radius={[4, 4, 0, 0]} name="Incidents" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Global Comparison Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-subtle overflow-hidden">
        <div className="p-5 border-b border-slate-100 flex items-center justify-between">
          <div>
            <h4 className="text-sm font-bold text-slate-900">Project Availability Breakdown</h4>
            <p className="text-xs text-slate-500">Comparative metrics across all active monitoring targets</p>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-500 uppercase font-semibold border-b border-slate-200">
              <tr>
                <th className="px-5 py-3">Website / Project</th>
                <th className="px-5 py-3">Uptime SLA</th>
                <th className="px-5 py-3">Total Downtime</th>
                <th className="px-5 py-3">Incidents</th>
                <th className="px-5 py-3">Avg Latency</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-medium">
              {analytics.project_comparisons.map((item) => (
                <tr key={item.project_id} className="hover:bg-slate-50/80 transition-colors">
                  <td className="px-5 py-3 font-bold text-slate-900">{item.project_name}</td>
                  <td className="px-5 py-3 font-bold">
                    <span
                      className={`px-2 py-0.5 rounded ${
                        item.uptime_pct >= 99.5
                          ? 'bg-emerald-50 text-emerald-700'
                          : 'bg-rose-50 text-rose-700'
                      }`}
                    >
                      {item.uptime_pct.toFixed(2)}%
                    </span>
                  </td>
                  <td className="px-5 py-3 font-mono text-slate-700">{item.downtime_formatted}</td>
                  <td className="px-5 py-3 font-bold text-slate-800">{item.incident_count}</td>
                  <td className="px-5 py-3 font-mono text-slate-600">
                    {item.avg_response_time_ms} ms
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
