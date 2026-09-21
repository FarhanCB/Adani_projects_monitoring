import React, { useEffect, useState } from 'react';
import {
  ArrowLeft,
  ExternalLink,
  Play,
  Clock,
  AlertTriangle,
  Users,
  Activity,
  CheckCircle2,
  XCircle,
  ShieldCheck,
  Calendar,
  Layers,
} from 'lucide-react';
import {
  AreaChart,
  Area,
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
import { api } from '../api/client';
import { StatusBadge } from '../components/StatusBadge';
import { UptimeHeatmap } from '../components/UptimeHeatmap';
import { Incident, Project, ProjectAnalytics } from '../types';

interface ProjectDetailPageProps {
  projectId: number;
  onBack: () => void;
}

export const ProjectDetailPage: React.FC<ProjectDetailPageProps> = ({
  projectId,
  onBack,
}) => {
  const [project, setProject] = useState<Project | null>(null);
  const [analytics, setAnalytics] = useState<ProjectAnalytics | null>(null);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [rangePreset, setRangePreset] = useState<string>('last_30_days');
  const [loading, setLoading] = useState<boolean>(true);
  const [testing, setTesting] = useState<boolean>(false);

  const rangeOptions = [
    { id: 'today', label: 'Today' },
    { id: 'this_week', label: 'This Week' },
    { id: 'last_7_days', label: 'Last 7 Days' },
    { id: 'this_month', label: 'This Month' },
    { id: 'last_30_days', label: 'Last 30 Days' },
    { id: 'last_90_days', label: 'Last 90 Days' },
  ];

  const loadData = async () => {
    try {
      const [projData, analyticsData, incidentsData] = await Promise.all([
        api.getProject(projectId),
        api.getProjectAnalytics(projectId, rangePreset),
        api.getIncidents({ project_id: projectId, limit: 10 }),
      ]);
      setProject(projData);
      setAnalytics(analyticsData);
      setIncidents(incidentsData);
    } catch (err) {
      console.error('Failed to load project details:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [projectId, rangePreset]);

  const handleManualTest = async () => {
    try {
      setTesting(true);
      await api.testProject(projectId);
      await loadData();
    } catch (err) {
      console.error('Test failed:', err);
    } finally {
      setTesting(false);
    }
  };

  if (loading || !project || !analytics) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-8 bg-slate-200 rounded w-48 mb-4" />
        <div className="h-32 bg-white rounded-xl border border-slate-200" />
        <div className="grid grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-24 bg-white rounded-xl border border-slate-200" />
          ))}
        </div>
      </div>
    );
  }

  const PIE_COLORS = ['#0078BD', '#583896', '#BE185D', '#0284C7', '#64748B'];

  return (
    <div className="space-y-6">
      {/* Top Breadcrumb & Action Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <button
          onClick={onBack}
          className="inline-flex items-center space-x-1.5 text-xs font-bold text-slate-600 hover:text-[#0078BD] transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to All Websites</span>
        </button>

        {/* Date Range Selector Buttons */}
        <div className="flex items-center space-x-1 bg-white p-1 rounded-xl border border-slate-200 shadow-sm overflow-x-auto max-w-full">
          <span className="text-xs font-semibold text-slate-400 px-2 flex items-center">
            <Calendar className="w-3.5 h-3.5 mr-1" /> Range:
          </span>
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
      </div>

      {/* Project Banner Card */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-subtle flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div className="space-y-2">
          <div className="flex items-center space-x-3">
            <h2 className="text-2xl font-black text-slate-900 tracking-tight">
              {project.name}
            </h2>
            <StatusBadge
              status={
                analytics.heatmap_blocks[analytics.heatmap_blocks.length - 1]?.status ||
                'UP'
              }
              size="md"
            />
          </div>

          <p className="text-xs text-slate-600 max-w-2xl">
            {project.description || 'Enterprise internal service monitored continuously.'}
          </p>

          <div className="flex flex-wrap items-center gap-4 text-xs text-slate-500 pt-1">
            <a
              href={project.url}
              target="_blank"
              rel="noopener noreferrer"
              className="font-mono text-[#0078BD] hover:text-[#583896] hover:underline flex items-center space-x-1"
            >
              <span>{project.url}</span>
              <ExternalLink className="w-3 h-3" />
            </a>

            <span className="flex items-center space-x-1">
              <Clock className="w-3.5 h-3.5 text-slate-400" />
              <span>Interval: {project.interval_seconds}s</span>
            </span>

            <span className="flex items-center space-x-1">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
              <span>Timeout: {project.timeout_seconds}s</span>
            </span>

            <span className="flex items-center space-x-1">
              <Users className="w-3.5 h-3.5 text-slate-400" />
              <span>
                {project.developers.length} Developers: {project.developers.map((d) => d.full_name).join(', ') || 'None assigned'}
              </span>
            </span>
          </div>
        </div>

        {/* Action button */}
        <button
          onClick={handleManualTest}
          disabled={testing}
          className="inline-flex items-center space-x-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-[#0078BD] via-[#583896] to-[#BE185D] text-white text-xs font-bold shadow-adani hover:opacity-95 transition-opacity disabled:opacity-50 flex-shrink-0"
        >
          <Play className={`w-4 h-4 ${testing ? 'animate-spin' : ''}`} />
          <span>{testing ? 'Testing Website...' : 'Test Website Manually'}</span>
        </button>
      </div>

      {/* Analytics Key Metrics (Requirement 8 & 9) */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
        <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-subtle border-l-4 border-l-emerald-500">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 block">
            Uptime Percentage
          </span>
          <span className="text-2xl font-black text-slate-900 mt-1 block">
            {analytics.uptime_pct.toFixed(2)}%
          </span>
          <span className="text-xs text-emerald-600 font-semibold mt-0.5 block">
            Downtime: {analytics.downtime_pct.toFixed(2)}%
          </span>
        </div>

        <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-subtle border-l-4 border-l-rose-500">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 block">
            Total Downtime
          </span>
          <span className="text-2xl font-black text-rose-600 mt-1 block">
            {analytics.total_downtime_formatted}
          </span>
          <span className="text-xs text-slate-400 font-medium mt-0.5 block">
            Uptime: {analytics.total_uptime_formatted}
          </span>
        </div>

        <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-subtle border-l-4 border-l-amber-500">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 block">
            Incidents
          </span>
          <span className="text-2xl font-black text-slate-900 mt-1 block">
            {analytics.incident_count}
          </span>
          <span className="text-xs text-slate-400 font-medium mt-0.5 block">
            In selected range
          </span>
        </div>

        <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-subtle border-l-4 border-l-indigo-500">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 block">
            Avg Outage Duration
          </span>
          <span className="text-2xl font-black text-slate-900 mt-1 block">
            {analytics.avg_incident_duration_formatted}
          </span>
          <span className="text-xs text-slate-400 font-medium mt-0.5 block">
            Longest: {analytics.longest_incident_formatted}
          </span>
        </div>

        <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-subtle border-l-4 border-l-sky-500">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 block">
            Avg Response Time
          </span>
          <span className="text-2xl font-black text-slate-900 mt-1 block">
            {analytics.avg_response_time_ms} ms
          </span>
          <span className="text-xs text-slate-400 font-medium mt-0.5 block">
            Max: {analytics.max_response_time_ms} ms
          </span>
        </div>

        <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-subtle border-l-4 border-l-slate-400">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 block">
            Probe Checks
          </span>
          <span className="text-2xl font-black text-slate-900 mt-1 block">
            {analytics.total_checks}
          </span>
          <span className="text-xs text-slate-500 font-medium mt-0.5 block">
            {analytics.successful_checks} UP • {analytics.failed_checks} DOWN
          </span>
        </div>
      </div>

      {/* Heatmap Timeline (Requirement 10) */}
      <UptimeHeatmap
        blocks={analytics.heatmap_blocks}
        rangeLabel={analytics.range_label}
        uptimePct={analytics.uptime_pct}
      />

      {/* Charts Grid: Response Time & Error Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Response Time Area Chart */}
        <div className="lg:col-span-2 bg-white rounded-xl p-5 border border-slate-200 shadow-subtle">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h4 className="text-sm font-bold text-slate-900">Response Time Trend (ms)</h4>
              <p className="text-xs text-slate-500">Continuous latency telemetry</p>
            </div>
            <div className="text-xs font-bold text-slate-700 bg-slate-100 px-2.5 py-1 rounded border border-slate-200">
              Avg: {analytics.avg_response_time_ms} ms
            </div>
          </div>

          <div className="h-64 w-full">
            {analytics.response_time_chart.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={analytics.response_time_chart}>
                  <defs>
                    <linearGradient id="rtGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#583896" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="#0078BD" stopOpacity={0.0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="label" stroke="#94a3b8" fontSize={10} tickLine={false} />
                  <YAxis stroke="#94a3b8" fontSize={10} tickLine={false} unit="ms" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1e1b4b',
                      borderRadius: '8px',
                      color: '#fff',
                      fontSize: '12px',
                      border: 'none',
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="response_time_ms"
                    stroke="#583896"
                    strokeWidth={2}
                    fillOpacity={1}
                    fill="url(#rtGradient)"
                    name="Response Time (ms)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-xs text-slate-400">
                No latency data recorded in this date range.
              </div>
            )}
          </div>
        </div>

        {/* Error Distribution Chart */}
        <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-subtle flex flex-col justify-between">
          <div>
            <h4 className="text-sm font-bold text-slate-900">Error Classification</h4>
            <p className="text-xs text-slate-500">Distribution of outage types</p>
          </div>

          <div className="h-52 w-full my-2">
            {analytics.error_distribution.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={analytics.error_distribution}
                    dataKey="count"
                    nameKey="error_type"
                    cx="50%"
                    cy="50%"
                    innerRadius={45}
                    outerRadius={75}
                    paddingAngle={3}
                  >
                    {analytics.error_distribution.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0f172a',
                      borderRadius: '8px',
                      color: '#fff',
                      fontSize: '12px',
                      border: 'none',
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-xs text-slate-400">
                <CheckCircle2 className="w-8 h-8 text-emerald-500 mb-1" />
                <span className="block mt-1">100% Error-Free</span>
              </div>
            )}
          </div>

          <div className="space-y-1.5 pt-2 border-t border-slate-100 max-h-32 overflow-y-auto">
            {analytics.error_distribution.map((err, i) => (
              <div key={i} className="flex items-center justify-between text-xs">
                <div className="flex items-center space-x-2 truncate">
                  <span
                    className="w-2.5 h-2.5 rounded-full"
                    style={{ backgroundColor: PIE_COLORS[i % PIE_COLORS.length] }}
                  />
                  <span className="text-slate-700 font-medium truncate">{err.error_type}</span>
                </div>
                <span className="font-mono text-slate-500 font-bold ml-2">
                  {err.count} ({err.percentage}%)
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Incidents Timeline Table (Requirement 10) */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-subtle overflow-hidden">
        <div className="p-5 border-b border-slate-100 flex items-center justify-between">
          <div>
            <h4 className="text-sm font-bold text-slate-900">Incident History & Root-Cause Analysis</h4>
            <p className="text-xs text-slate-500">
              Detailed outage log — click any incident to see full diagnostics, error reason, and fix steps
            </p>
          </div>
          <span className="text-xs font-bold text-slate-600 bg-slate-100 px-2.5 py-1 rounded">
            {incidents.length} Outage Events
          </span>
        </div>

        {incidents.length === 0 ? (
          <div className="p-8 text-center text-slate-400 text-xs">
            <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto mb-2" />
            No recorded outages for this website.
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {incidents.map((inc) => (
              <IncidentDiagnosticRow key={inc.id} inc={inc} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// ─── Expandable Diagnostic Row ──────────────────────────────────────────────
interface DiagnosticRowProps { inc: Incident; }
const IncidentDiagnosticRow: React.FC<DiagnosticRowProps> = ({ inc }) => {
  const [expanded, setExpanded] = React.useState(false);

  // Build diagnostic info from error_type and http_status
  const diagnostic = buildDiagnostic(inc.error_type, inc.http_status, inc.error_message);

  return (
    <>
      <div
        className="px-5 py-3.5 flex flex-wrap items-start gap-3 cursor-pointer hover:bg-slate-50/80 transition-colors"
        onClick={() => setExpanded((v) => !v)}
      >
        {/* ID */}
        <span className="font-mono font-black text-slate-700 text-xs w-10 flex-shrink-0">#{inc.id}</span>

        {/* Status badge */}
        <span className="flex-shrink-0">
          {inc.is_resolved ? (
            <span className="px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 text-[11px] font-bold">
              RESOLVED
            </span>
          ) : (
            <span className="px-2 py-0.5 rounded-full bg-rose-50 text-rose-700 border border-rose-200 text-[11px] font-bold">
              ACTIVE OUTAGE
            </span>
          )}
        </span>

        {/* Error classification pill */}
        <span className="inline-flex items-center space-x-1 px-2 py-0.5 bg-rose-50 border border-rose-200 rounded text-[11px] font-bold text-rose-700 flex-shrink-0">
          <AlertTriangle className="w-3 h-3" />
          <span>{inc.error_type || 'Unknown Error'}</span>
          {inc.http_status && <span className="font-mono ml-1 text-slate-500">HTTP {inc.http_status}</span>}
        </span>

        {/* Time range */}
        <span className="text-xs text-slate-500 flex-1 min-w-0">
          <span className="font-semibold text-slate-700">
            {new Date(inc.started_at).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
          </span>
          {' → '}
          {inc.resolved_at
            ? new Date(inc.resolved_at).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
            : <span className="text-rose-600 font-bold">Ongoing</span>}
          {inc.duration_formatted && (
            <span className="ml-2 px-1.5 py-0.5 bg-slate-100 rounded text-[11px] font-bold text-slate-600">
              {inc.duration_formatted}
            </span>
          )}
        </span>

        {/* Expand toggle */}
        <span className="text-[11px] font-bold text-[#0078BD] flex-shrink-0 flex items-center space-x-1">
          <span>{expanded ? '▲ Hide Root Cause' : '▼ View Root Cause'}</span>
        </span>
      </div>

      {/* Expandable Diagnostic Panel */}
      {expanded && (
        <div className="px-5 pb-5 bg-gradient-to-br from-slate-50 to-indigo-50/30 border-t border-slate-100">
          <div className="pt-4 space-y-4">
            {/* Summary banner */}
            <div className="rounded-xl border border-rose-200 bg-rose-50 p-4">
              <p className="text-xs font-black text-rose-800 mb-1 uppercase tracking-wider">
                🔍 Root Cause: {diagnostic.title}
              </p>
              <p className="text-xs text-rose-700 leading-relaxed">
                {diagnostic.why_it_came}
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Likely Causes */}
              <div className="bg-white rounded-lg border border-amber-200 p-4">
                <p className="text-xs font-black text-amber-800 mb-2 uppercase tracking-wider flex items-center space-x-1">
                  <AlertTriangle className="w-3.5 h-3.5" />
                  <span>Likely Causes</span>
                </p>
                <ul className="space-y-1.5">
                  {diagnostic.likely_causes.map((cause: string, i: number) => (
                    <li key={i} className="flex items-start space-x-1.5 text-[11px] text-amber-900">
                      <span className="font-black mt-0.5 text-amber-500 flex-shrink-0">•</span>
                      <span>{cause}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Fix Steps */}
              <div className="bg-white rounded-lg border border-emerald-200 p-4">
                <p className="text-xs font-black text-emerald-800 mb-2 uppercase tracking-wider flex items-center space-x-1">
                  <Activity className="w-3.5 h-3.5" />
                  <span>Troubleshooting Steps</span>
                </p>
                <ul className="space-y-1.5">
                  {diagnostic.action_steps.map((step: string, i: number) => (
                    <li key={i} className="flex items-start space-x-1.5 text-[11px] text-emerald-900">
                      <span className="font-black mt-0.5 text-emerald-500 flex-shrink-0">{i + 1}.</span>
                      <span>{step.replace(/^\d+\.\s*/, '')}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            {/* Raw error message */}
            {inc.error_message && (
              <div className="bg-slate-900 rounded-lg p-3 text-[11px] font-mono text-slate-300 border border-slate-700 overflow-x-auto">
                <span className="text-rose-400 font-bold">ERROR: </span>
                {inc.error_message}
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
};

// ─── Diagnostic builder (client-side fallback catalog) ───────────────────────
function buildDiagnostic(errorType?: string, httpStatus?: number, msg?: string) {
  const et = (errorType || '').toLowerCase();
  const code = httpStatus ? String(httpStatus) : '';

  const catalog: Record<string, { title: string; why_it_came: string; likely_causes: string[]; action_steps: string[] }> = {
    '502': {
      title: '502 Bad Gateway — Upstream Application Crashed',
      why_it_came: 'The reverse proxy (Nginx/ALB) reached the web server, but the upstream application process (FastAPI/Node.js/Gunicorn/IIS) crashed, is stopped, or returned malformed bytes instead of a valid HTTP response.',
      likely_causes: [
        'Backend application container or systemd service has crashed or is in a restart loop.',
        'Process killed by Linux Out-Of-Memory (OOM) killer due to RAM exhaustion.',
        'Reverse proxy misconfigured to forward traffic to wrong internal host/port.',
        'Internal firewall or Docker bridge network blocked proxy↔backend communication.',
      ],
      action_steps: [
        'Check backend service: `systemctl status <service>` or `docker ps` to verify container is running.',
        'Inspect crash logs: `docker logs --tail 200 <container>` for unhandled tracebacks.',
        'Check Nginx error logs: `/var/log/nginx/error.log` for "connect() failed (111: Connection refused)".',
        'Verify port binding: `ss -tulpn` to confirm application listens on expected port.',
        'Restart the backend: `systemctl restart <service>` or `docker restart <container>`.',
      ],
    },
    '504': {
      title: '504 Gateway Timeout — Upstream Processing Too Slow',
      why_it_came: 'The reverse proxy successfully routed the request, but the backend took longer than the configured gateway timeout. The proxy aborted the connection before the application responded.',
      likely_causes: [
        'A heavy or unindexed database query is blocking the backend thread.',
        'Backend made a synchronous HTTP call to a slow or hung third-party API.',
        'Thread pool starvation: all server workers are tied up handling long requests.',
        'Database connection pool exhausted — requests waiting for an available DB connection.',
      ],
      action_steps: [
        'Check slow DB queries: `SELECT * FROM pg_stat_activity WHERE state != \'idle\';` in PostgreSQL.',
        'Profile which external APIs or microservices the route calls and measure their latency.',
        'Increase worker concurrency or scale horizontal replicas to handle queue backlog.',
        'Check server CPU and RAM: `htop` or cloud monitoring dashboards.',
        'Offload heavy processing to an async background worker (Celery/Redis).',
      ],
    },
    '500': {
      title: '500 Internal Server Error — Unhandled Code Exception',
      why_it_came: 'The web application encountered an unexpected runtime exception in its code (NullPointerError, KeyError, DB connection refusal, missing env var) and the framework returned HTTP 500.',
      likely_causes: [
        'Unhandled exception in backend route handler (missing key, null object, assertion error).',
        'Database credentials invalid or migration table missing.',
        'Missing required environment variable (API key, secret key, DB URL).',
        'Dependency injection or import failure during request execution.',
      ],
      action_steps: [
        'Check application error logs for the full stack trace (Sentry, CloudWatch, or local log file).',
        'Verify database health and run pending migrations.',
        'Audit `.env` configuration on the target server for missing variables.',
        'Reproduce in staging with the same payload to debug the exact code path.',
      ],
    },
    '503': {
      title: '503 Service Unavailable — Server Overloaded or Maintenance',
      why_it_came: 'The server is temporarily unable to handle requests due to overloading, zero ready pods (Kubernetes deployment in progress), or maintenance mode.',
      likely_causes: [
        'Traffic spike exceeded worker thread pool / max connection backlog.',
        'Kubernetes deployment in progress with 0 healthy replica pods.',
        'Maintenance mode enabled in reverse proxy or load balancer.',
        'Web server worker crash limits reached (IIS AppPool / Apache MPM).',
      ],
      action_steps: [
        'Check Kubernetes pod readiness: `kubectl get pods`, then `kubectl describe pod <name>`.',
        'Verify server CPU/RAM utilization — above 95% indicates resource exhaustion.',
        'Scale up replica count or increase worker process concurrency.',
        'Review Nginx/Apache worker connection limits and increase if necessary.',
      ],
    },
    '404': {
      title: '404 Not Found — URL Route Does Not Exist',
      why_it_came: 'The web server processed the request, but no route or file matched the given URL path. The endpoint may have been renamed, moved, or a SPA fallback config is missing.',
      likely_causes: [
        'Typo in the monitored URL or a missing/extra trailing slash.',
        'The API route was renamed or deprecated in a recent deployment.',
        'React/Vue SPA: Nginx missing `try_files $uri /index.html` fallback.',
      ],
      action_steps: [
        'Verify the exact URL path in project settings vs. the Swagger/OpenAPI documentation.',
        'Check if a trailing slash is required (e.g. `/details/` vs `/details`).',
        'For SPAs: ensure Nginx has `try_files $uri $uri/ /index.html;` configured.',
      ],
    },
    '403': {
      title: '403 Forbidden — WAF Block or VPN/IP Restriction',
      why_it_came: 'The web server understood the request but explicitly denied access. Commonly triggered by WAF IP rules, corporate intranet VPN restrictions, or directory permission settings.',
      likely_causes: [
        'WAF / Cloudflare blocked the monitoring probe\'s IP or User-Agent.',
        'Website restricted to internal corporate IP subnets (VPN required).',
        'Server directory permission (chmod) prevents access.',
      ],
      action_steps: [
        'Verify whether the monitored website requires corporate VPN connectivity.',
        'Whitelist the monitoring server\'s IP in the WAF or security group rules.',
        'Check web server directory permissions (`chmod 755` for dirs, `644` for files).',
      ],
    },
    '401': {
      title: '401 Unauthorized — Authentication Required',
      why_it_came: 'The endpoint requires a valid authentication token or session cookie, which the probe did not provide. Monitor should point to a public health check endpoint.',
      likely_causes: [
        'Monitored URL is a private dashboard route, not a public health endpoint.',
        'API key or Bearer token has expired.',
      ],
      action_steps: [
        'Change the monitored URL to a public health check endpoint (e.g. `/health`, `/healthz`, `/api/health`).',
        'If monitoring an authenticated endpoint is required, configure probe auth headers.',
      ],
    },
    'dns': {
      title: 'DNS Resolution Failed — Internal VPN/Intranet Required',
      why_it_came: 'The hostname could not be resolved to an IP address. Adani internal UAT/intranet endpoints are hosted on private corporate DNS servers that only resolve when connected to the Adani Corporate VPN.',
      likely_causes: [
        'Monitoring worker machine is not connected to Adani Corporate VPN / internal network.',
        'The internal UAT hostname does not exist in public DNS (8.8.8.8 / 1.1.1.1).',
        'Local DNS cache is stale or primary DNS server is unreachable.',
      ],
      action_steps: [
        'Connect the host machine to the Adani Corporate VPN.',
        'Test DNS resolution: `nslookup <hostname>` or `ping <hostname>` in terminal.',
        'Ensure internal corporate DNS servers (10.x.x.x) are set in `/etc/resolv.conf` or Windows network adapter settings.',
      ],
    },
    'connection': {
      title: 'TCP Connection Refused — Web Server Service Stopped',
      why_it_came: 'The server IP was reached successfully, but the OS actively rejected the TCP connection on port 80/443. This means no web server process is listening on that port.',
      likely_causes: [
        'Web server daemon (Nginx, Apache, Caddy, IIS) is stopped or crashed.',
        'Service is bound to 127.0.0.1 instead of 0.0.0.0 (not accepting external connections).',
        'Host firewall (iptables / Windows Firewall) is actively blocking inbound connections.',
      ],
      action_steps: [
        'SSH into server and check web server status: `systemctl status nginx` or `systemctl status apache2`.',
        'Start or restart the service: `systemctl start nginx`.',
        'Verify listening sockets: `ss -tulpn | grep -E \':80|:443\'` to confirm binding to 0.0.0.0.',
      ],
    },
    'timeout': {
      title: 'Network Timeout (>30s) — Server Unresponsive / Packets Dropped',
      why_it_came: 'The probe sent packets but received no response within the 30-second timeout. Packets are being silently dropped by a firewall or the server is under extreme load.',
      likely_causes: [
        'Cloud security group / network firewall silently dropping TCP packets.',
        'Target server is powered off, rebooting, or severely overloaded.',
        'Routing blackhole or VPN tunnel disconnection.',
      ],
      action_steps: [
        'Run `ping <host>` and `traceroute <host>` to find where packets are dropped.',
        'Check cloud security group rules: verify inbound port 443 is open.',
        'Verify server power state in the hypervisor or cloud console.',
      ],
    },
    'ssl': {
      title: 'SSL/TLS Certificate Error — Handshake Failure',
      why_it_came: 'The HTTPS TLS handshake failed because the server\'s certificate is expired, self-signed, or the domain name on the cert doesn\'t match the URL.',
      likely_causes: [
        'SSL/TLS certificate has passed its expiration date.',
        'Internal self-signed certificate with a root CA not in the system trust store.',
        'Certificate\'s Subject Alternative Name (SAN) doesn\'t match the accessed URL domain.',
      ],
      action_steps: [
        'Check certificate expiry: `openssl s_client -connect <host>:443 -servername <host>`.',
        'Renew SSL certificate via Let\'s Encrypt/Certbot or internal enterprise CA.',
        'Ensure the certificate SAN contains the exact domain being monitored.',
      ],
    },
    'slow': {
      title: 'High Latency — Response Time Degradation',
      why_it_came: 'Website responded with HTTP 200 but took longer than the 2000ms warning threshold. End users experience sluggish page loads.',
      likely_causes: [
        'Cold start of serverless / containerized backend.',
        'Unoptimized database queries missing indexes.',
        'High concurrent server load or memory pressure.',
      ],
      action_steps: [
        'Profile the endpoint\'s database queries and add missing indexes.',
        'Implement Redis or in-memory caching for frequently-requested data.',
        'Scale up application server CPU and RAM resources.',
      ],
    },
  };

  // Match by HTTP status code first
  if (catalog[code]) return catalog[code];

  // Match by error type keywords
  if (et.includes('dns') || (msg || '').toLowerCase().includes('getaddrinfo')) return catalog['dns'];
  if (et.includes('connection') || et.includes('refused')) return catalog['connection'];
  if (et.includes('timeout') || et.includes('timed')) return catalog['timeout'];
  if (et.includes('ssl') || et.includes('cert')) return catalog['ssl'];
  if (et.includes('slow') || et.includes('latency')) return catalog['slow'];
  if (et.includes('5xx') || code.startsWith('5')) return catalog['500'];
  if (et.includes('4xx') || code === '404') return catalog['404'];
  if (code === '403') return catalog['403'];
  if (code === '401') return catalog['401'];

  // Generic fallback
  return {
    title: `${errorType || 'Service Disruption'} Detected`,
    why_it_came: msg || 'An unexpected issue interrupted communication with the target website. Review the raw error message and check server logs for details.',
    likely_causes: [
      'Temporary network routing anomaly or firewall block.',
      'Web service configuration change or restart in progress.',
      'Resource exhaustion or unresponsive worker thread on the host server.',
    ],
    action_steps: [
      'Test the URL manually in a browser or via `curl -v <url>`.',
      'Review application error logs on the host server.',
      'Verify network routing and firewall rules allow inbound traffic.',
    ],
  };
}

