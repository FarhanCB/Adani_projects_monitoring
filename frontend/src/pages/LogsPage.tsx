import React, { useEffect, useState } from 'react';
import { Download, Filter, RefreshCw, ChevronLeft, ChevronRight, Activity } from 'lucide-react';
import { api } from '../api/client';
import { StatusBadge } from '../components/StatusBadge';
import { MonitoringLog, PaginatedLogs, Project } from '../types';

export const LogsPage: React.FC = () => {
  const [logsData, setLogsData] = useState<PaginatedLogs>({
    items: [],
    total: 0,
    page: 1,
    size: 25,
    total_pages: 1,
  });
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [selectedProjectId, setSelectedProjectId] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [page, setPage] = useState<number>(1);
  const [pageSize, setPageSize] = useState<number>(25);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const data = await api.getLogs({
        project_id: selectedProjectId ? parseInt(selectedProjectId) : undefined,
        status: statusFilter || undefined,
        page,
        size: pageSize,
      });
      setLogsData(data);
    } catch (err) {
      console.error('Failed to load logs:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    api.getProjects().then(setProjects).catch(console.error);
  }, []);

  useEffect(() => {
    fetchLogs();
  }, [page, pageSize, selectedProjectId, statusFilter]);

  const handleDownloadCsv = () => {
    const token = localStorage.getItem('adani_auth_token');
    const params = new URLSearchParams();
    if (selectedProjectId) params.append('project_id', selectedProjectId);
    if (statusFilter) params.append('status', statusFilter);

    const url = `http://localhost:8000/api/logs/export/csv?${params.toString()}`;
    window.open(url, '_blank');
  };

  return (
    <div className="space-y-6">
      {/* Top Header & Export */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-black text-slate-900 tracking-tight">
            Monitoring Checks & Probe Logs
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Full telemetry audit trail recorded by the automated monitoring worker
          </p>
        </div>

        <button
          onClick={handleDownloadCsv}
          className="inline-flex items-center space-x-1.5 px-3.5 py-2 rounded-xl bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 text-xs font-bold shadow-sm transition-colors"
        >
          <Download className="w-3.5 h-3.5 text-[#0078BD]" />
          <span>Export Logs as CSV</span>
        </button>
      </div>

      {/* Filter Toolbar */}
      <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-subtle flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-3">
          {/* Project Filter */}
          <div className="flex items-center space-x-2">
            <span className="text-xs font-semibold text-slate-500">Website:</span>
            <select
              value={selectedProjectId}
              onChange={(e) => {
                setSelectedProjectId(e.target.value);
                setPage(1);
              }}
              className="text-xs border border-slate-200 rounded-lg px-3 py-1.5 bg-white text-slate-800 focus:ring-2 focus:ring-[#0078BD] focus:outline-none"
            >
              <option value="">All Monitored Websites</option>
              {projects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>

          {/* Status Filter */}
          <div className="flex items-center space-x-2">
            <span className="text-xs font-semibold text-slate-500">Status:</span>
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPage(1);
              }}
              className="text-xs border border-slate-200 rounded-lg px-3 py-1.5 bg-white text-slate-800 focus:ring-2 focus:ring-[#0078BD] focus:outline-none"
            >
              <option value="">All Statuses</option>
              <option value="UP">UP Only</option>
              <option value="DOWN">DOWN Only</option>
              <option value="WARNING">WARNING Only</option>
            </select>
          </div>
        </div>

        {/* Total results info */}
        <div className="text-xs text-slate-500">
          Showing <span className="font-bold text-slate-900">{logsData.items.length}</span> of{' '}
          <span className="font-bold text-slate-900">{logsData.total}</span> checks
        </div>
      </div>

      {/* Logs Table (Requirement 11) */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-subtle overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-slate-400 text-xs">
            <RefreshCw className="w-8 h-8 animate-spin text-[#0078BD] mx-auto mb-2" />
            Loading monitoring checks...
          </div>
        ) : logsData.items.length === 0 ? (
          <div className="p-12 text-center text-slate-400 text-xs">
            No monitoring check records found matching filters.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-500 uppercase font-semibold border-b border-slate-200">
                <tr>
                  <th className="px-5 py-3">Timestamp (UTC)</th>
                  <th className="px-5 py-3">Monitored Service</th>
                  <th className="px-5 py-3">Result</th>
                  <th className="px-5 py-3">HTTP Status</th>
                  <th className="px-5 py-3">Response Time</th>
                  <th className="px-5 py-3">Error Classification</th>
                  <th className="px-5 py-3">Error Details</th>
                  <th className="px-5 py-3">Incident #</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-medium">
                {logsData.items.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="px-5 py-3 text-slate-600 font-mono text-[11px]">
                      {new Date(log.timestamp).toLocaleString([], {
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                        second: '2-digit',
                      })}
                    </td>

                    <td className="px-5 py-3 font-bold text-slate-900">{log.project_name}</td>

                    <td className="px-5 py-3">
                      <StatusBadge status={log.status} size="sm" showPulse={false} />
                    </td>

                    <td className="px-5 py-3 font-mono">
                      {log.http_status ? (
                        <span
                          className={`font-bold ${
                            log.http_status < 400 ? 'text-slate-800' : 'text-rose-600'
                          }`}
                        >
                          {log.http_status}
                        </span>
                      ) : (
                        <span className="text-slate-400">—</span>
                      )}
                    </td>

                    <td className="px-5 py-3 font-bold text-slate-800">
                      {log.response_time_ms ? `${log.response_time_ms} ms` : '—'}
                    </td>

                    <td className="px-5 py-3">
                      {log.error_type ? (
                        <span className="font-bold text-rose-600">{log.error_type}</span>
                      ) : (
                        <span className="text-slate-400 font-normal">None</span>
                      )}
                    </td>

                    <td className="px-5 py-3 text-slate-500 max-w-xs truncate" title={log.error_message}>
                      {log.error_message || '—'}
                    </td>

                    <td className="px-5 py-3 font-mono text-[11px]">
                      {log.incident_id ? (
                        <span className="text-[#0078BD] font-bold">#{log.incident_id}</span>
                      ) : (
                        <span className="text-slate-300">—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Server-Side Pagination Controls */}
        <div className="p-4 border-t border-slate-100 flex items-center justify-between text-xs text-slate-600 bg-slate-50/50">
          <div className="flex items-center space-x-2">
            <span>Rows per page:</span>
            <select
              value={pageSize}
              onChange={(e) => {
                setPageSize(parseInt(e.target.value));
                setPage(1);
              }}
              className="border border-slate-200 rounded px-2 py-1 bg-white text-xs"
            >
              <option value="15">15</option>
              <option value="25">25</option>
              <option value="50">50</option>
              <option value="100">100</option>
            </select>
          </div>

          <div className="flex items-center space-x-3">
            <span>
              Page <span className="font-bold text-slate-900">{logsData.page}</span> of{' '}
              <span className="font-bold text-slate-900">{logsData.total_pages}</span>
            </span>

            <div className="flex items-center space-x-1">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={logsData.page <= 1}
                className="p-1.5 rounded border border-slate-200 bg-white hover:bg-slate-100 disabled:opacity-40"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>

              <button
                onClick={() => setPage((p) => Math.min(logsData.total_pages, p + 1))}
                disabled={logsData.page >= logsData.total_pages}
                className="p-1.5 rounded border border-slate-200 bg-white hover:bg-slate-100 disabled:opacity-40"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
