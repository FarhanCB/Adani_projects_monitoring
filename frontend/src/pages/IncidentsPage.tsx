import React, { useEffect, useState } from 'react';
import { AlertTriangle, CheckCircle2, Filter, Search, Activity } from 'lucide-react';
import { api } from '../api/client';
import { Incident, Project } from '../types';

interface IncidentsPageProps {
  onSelectProject: (id: number) => void;
}

export const IncidentsPage: React.FC<IncidentsPageProps> = ({ onSelectProject }) => {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);

  const [selectedProjectId, setSelectedProjectId] = useState<string>('ALL');
  const [resolvedFilter, setResolvedFilter] = useState<string>('ALL');
  const [search, setSearch] = useState('');

  const loadData = async () => {
    try {
      const [incList, projList] = await Promise.all([
        api.getIncidents({ limit: 200 }),
        api.getProjects(),
      ]);
      setIncidents(incList);
      setProjects(projList);
    } catch (err) {
      console.error('Failed to load incidents:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadData(); }, []);

  const filtered = incidents.filter((inc) => {
    if (selectedProjectId !== 'ALL' && inc.project_id !== parseInt(selectedProjectId)) return false;
    if (resolvedFilter === 'ACTIVE' && inc.is_resolved) return false;
    if (resolvedFilter === 'RESOLVED' && !inc.is_resolved) return false;
    if (search) {
      const q = search.toLowerCase();
      if (!inc.project_name?.toLowerCase().includes(q) &&
          !inc.error_type?.toLowerCase().includes(q) &&
          !inc.error_message?.toLowerCase().includes(q)) return false;
    }
    return true;
  });

  const activeCount = incidents.filter((i) => !i.is_resolved).length;

  if (loading) {
    return (
      <div className="space-y-4 animate-pulse">
        <div className="h-8 bg-slate-200 rounded w-64" />
        <div className="h-16 bg-white rounded-xl border border-slate-200" />
        <div className="h-64 bg-white rounded-xl border border-slate-200" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-black text-slate-900 tracking-tight">
            Outage &amp; Incident Management
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Click any incident row to view full root-cause analysis, likely causes, and troubleshooting steps
          </p>
        </div>
        {activeCount > 0 ? (
          <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-rose-50 border border-rose-200 text-rose-700 text-xs font-bold">
            <span className="w-2 h-2 rounded-full bg-rose-600" />
            <span>{activeCount} Ongoing Service Outages</span>
          </div>
        ) : (
          <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs font-bold">
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            <span>All Monitored Services Healthy</span>
          </div>
        )}
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-subtle p-4 flex flex-wrap gap-3 items-center">
        <div className="flex items-center space-x-1.5 text-xs text-slate-500 font-bold mr-1">
          <Filter className="w-3.5 h-3.5" />
          <span>Filters</span>
        </div>
        <div className="relative flex-1 min-w-[200px]">
          <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search project, error type, message..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-8 pr-3 py-1.5 w-full border border-slate-200 rounded-lg text-xs bg-slate-50 focus:ring-2 focus:ring-[#0078BD] focus:outline-none"
          />
        </div>
        <select
          value={selectedProjectId}
          onChange={(e) => setSelectedProjectId(e.target.value)}
          className="text-xs border border-slate-200 rounded-lg px-3 py-1.5 bg-slate-50 focus:ring-2 focus:ring-[#0078BD] focus:outline-none"
        >
          <option value="ALL">All Websites</option>
          {projects.map((p) => (
            <option key={p.id} value={String(p.id)}>{p.name}</option>
          ))}
        </select>
        <div className="flex bg-slate-100 rounded-lg p-0.5">
          {['ALL', 'ACTIVE', 'RESOLVED'].map((tab) => (
            <button
              key={tab}
              onClick={() => setResolvedFilter(tab)}
              className={`px-3 py-1 text-xs font-bold rounded-md transition-all ${
                resolvedFilter === tab ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      {/* Incidents — Expandable Rows */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-subtle overflow-hidden">
        <div className="px-5 py-3 border-b border-slate-100 flex items-center justify-between">
          <span className="text-xs font-bold text-slate-700">
            {filtered.length} Incident{filtered.length !== 1 ? 's' : ''} Found
          </span>
          <span className="text-[11px] text-slate-400 italic">
            Click any row ▼ for root-cause diagnostics
          </span>
        </div>
        {filtered.length === 0 ? (
          <div className="p-12 text-center text-slate-400 text-xs">
            <CheckCircle2 className="w-10 h-10 text-emerald-500 mx-auto mb-2" />
            No incidents found matching the selected criteria.
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {filtered.map((inc) => (
              <IncidentDiagnosticRow key={inc.id} inc={inc} onSelectProject={onSelectProject} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// ─── Expandable Diagnostic Row ───────────────────────────────────────────────
interface DiagnosticRowProps {
  inc: Incident;
  onSelectProject: (id: number) => void;
}

const IncidentDiagnosticRow: React.FC<DiagnosticRowProps> = ({ inc, onSelectProject }) => {
  const [expanded, setExpanded] = React.useState(false);
  const diagnostic = buildDiagnostic(inc.error_type, inc.http_status, inc.error_message);

  return (
    <>
      <div
        className="px-5 py-3.5 flex flex-wrap items-start gap-3 cursor-pointer hover:bg-slate-50/80 transition-colors select-none"
        onClick={() => setExpanded((v) => !v)}
      >
        <span className="font-mono font-black text-slate-700 text-xs w-10 flex-shrink-0">#{inc.id}</span>

        <button
          onClick={(e) => { e.stopPropagation(); onSelectProject(inc.project_id); }}
          className="text-xs font-bold text-[#0078BD] hover:underline flex-shrink-0 max-w-[200px] truncate text-left"
          title={inc.project_name}
        >
          {inc.project_name}
        </button>

        <span className="flex-shrink-0">
          {inc.is_resolved ? (
            <span className="px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 text-[11px] font-bold">RESOLVED</span>
          ) : (
            <span className="px-2 py-0.5 rounded-full bg-rose-50 text-rose-700 border border-rose-200 text-[11px] font-bold">ACTIVE OUTAGE</span>
          )}
        </span>

        <span className="inline-flex items-center space-x-1 px-2 py-0.5 bg-rose-50 border border-rose-200 rounded text-[11px] font-bold text-rose-700 flex-shrink-0">
          <AlertTriangle className="w-3 h-3 flex-shrink-0" />
          <span>{inc.error_type || 'Unknown'}</span>
          {inc.http_status && <span className="font-mono ml-1 text-slate-500">HTTP {inc.http_status}</span>}
        </span>

        <span className="text-xs text-slate-500 flex-1 min-w-0">
          <span className="font-semibold text-slate-700">
            {new Date(inc.started_at).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
          </span>
          {inc.duration_formatted && (
            <span className="ml-2 px-1.5 py-0.5 bg-slate-100 rounded text-[11px] font-bold text-slate-600">{inc.duration_formatted}</span>
          )}
        </span>

        <span className="text-[11px] font-bold text-[#0078BD] flex-shrink-0">
          {expanded ? '▲ Hide Root Cause' : '▼ View Root Cause'}
        </span>
      </div>

      {expanded && (
        <div className="px-5 pb-5 bg-gradient-to-br from-slate-50 to-indigo-50/30 border-t border-slate-100">
          <div className="pt-4 space-y-4">
            <div className="rounded-xl border border-rose-200 bg-rose-50 p-4">
              <p className="text-xs font-black text-rose-800 mb-1.5 uppercase tracking-wider">
                🔍 Root Cause: {diagnostic.title}
              </p>
              <p className="text-xs text-rose-700 leading-relaxed">{diagnostic.why_it_came}</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-white rounded-lg border border-amber-200 p-4">
                <p className="text-xs font-black text-amber-800 mb-2 uppercase tracking-wider flex items-center space-x-1.5">
                  <AlertTriangle className="w-3.5 h-3.5" /><span>Likely Causes</span>
                </p>
                <ul className="space-y-2">
                  {diagnostic.likely_causes.map((cause: string, i: number) => (
                    <li key={i} className="flex items-start space-x-1.5 text-[11px] text-amber-900 leading-relaxed">
                      <span className="font-black text-amber-500 flex-shrink-0 mt-0.5">•</span>
                      <span>{cause}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="bg-white rounded-lg border border-emerald-200 p-4">
                <p className="text-xs font-black text-emerald-800 mb-2 uppercase tracking-wider flex items-center space-x-1.5">
                  <Activity className="w-3.5 h-3.5" /><span>Troubleshooting Steps</span>
                </p>
                <ul className="space-y-2">
                  {diagnostic.action_steps.map((step: string, i: number) => (
                    <li key={i} className="flex items-start space-x-1.5 text-[11px] text-emerald-900 leading-relaxed">
                      <span className="font-black text-emerald-500 flex-shrink-0 mt-0.5">{i + 1}.</span>
                      <span>{step.replace(/^\d+\.\s*/, '')}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            {inc.error_message && (
              <div className="bg-slate-900 rounded-lg p-3 text-[11px] font-mono text-slate-300 border border-slate-700 overflow-x-auto whitespace-pre-wrap break-all">
                <span className="text-rose-400 font-bold">ERROR: </span>{inc.error_message}
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
};

// ─── Diagnostic Catalog ───────────────────────────────────────────────────────
function buildDiagnostic(
  errorType?: string,
  httpStatus?: number,
  msg?: string,
): { title: string; why_it_came: string; likely_causes: string[]; action_steps: string[] } {
  const et = (errorType || '').toLowerCase();
  const code = httpStatus ? String(httpStatus) : '';

  type DiagEntry = { title: string; why_it_came: string; likely_causes: string[]; action_steps: string[] };
  const C: Record<string, DiagEntry> = {
    '502': {
      title: '502 Bad Gateway — Upstream Application Crashed',
      why_it_came: 'The reverse proxy (Nginx/ALB) reached the web server, but the upstream application (FastAPI/Node.js/Gunicorn) crashed, is stopped, or returned malformed bytes. The proxy cannot forward the request and returns 502.',
      likely_causes: [
        'Backend application container or systemd service has crashed or is in a restart loop.',
        'Process killed by Linux OOM killer due to RAM exhaustion.',
        'Reverse proxy misconfigured — forwarding to wrong internal host/port.',
        'Docker bridge network blocked proxy↔backend communication.',
      ],
      action_steps: [
        'Check backend: `systemctl status <service>` or `docker ps` to verify running.',
        'Inspect crash logs: `docker logs --tail 200 <container>` for tracebacks.',
        'Read Nginx error log: `/var/log/nginx/error.log` for "connect() failed (111)".',
        'Verify port: `ss -tulpn` to confirm application listens on expected port.',
        'Restart: `systemctl restart <service>` or `docker restart <container>`.',
      ],
    },
    '504': {
      title: '504 Gateway Timeout — Backend Processing Too Slow',
      why_it_came: 'The reverse proxy routed the request but the backend took longer than the gateway timeout. The proxy aborted the connection before the application responded.',
      likely_causes: [
        'Heavy or unindexed database query blocking the backend thread.',
        'Synchronous HTTP call to a slow or hung third-party API.',
        'Thread pool starvation — all workers tied up with long-running requests.',
        'Database connection pool exhausted.',
      ],
      action_steps: [
        "Check slow DB queries: `SELECT * FROM pg_stat_activity WHERE state != 'idle';`",
        'Profile which external APIs the endpoint calls and measure their latency.',
        'Increase worker concurrency or add horizontal replicas.',
        'Check CPU/RAM: `htop` or cloud monitoring dashboards.',
        'Move heavy processing to async workers (Celery/Redis).',
      ],
    },
    '500': {
      title: '500 Internal Server Error — Unhandled Code Exception',
      why_it_came: 'The application encountered an unexpected runtime exception (null reference, missing key, DB connection refusal, missing env var) and the framework returned HTTP 500.',
      likely_causes: [
        'Unhandled exception in backend route handler (KeyError, NullPointer, assertion error).',
        'Database credentials invalid or migration table missing.',
        'Missing required environment variable (API key, secret key, DB URL).',
        'Import failure or dependency injection error during request execution.',
      ],
      action_steps: [
        'Check application error logs for the full stack trace (Sentry, CloudWatch, local log).',
        'Verify database health and run pending migrations: `alembic upgrade head`.',
        'Audit `.env` on the target server for missing or incorrect variables.',
        'Reproduce in staging with the same payload to isolate the failing code path.',
      ],
    },
    '503': {
      title: '503 Service Unavailable — Server Overloaded or Maintenance Mode',
      why_it_came: 'The server is temporarily unable to handle requests. Common during Kubernetes rolling deployments (0 ready pods), traffic spikes, or when maintenance mode is active.',
      likely_causes: [
        'Traffic spike exceeded worker thread pool / max connection backlog.',
        'Kubernetes deployment in progress with 0 healthy replica pods.',
        'Maintenance mode enabled in reverse proxy or load balancer.',
        'Web server crash limits reached (IIS AppPool / Apache MPM maxClients).',
      ],
      action_steps: [
        'Check pods: `kubectl get pods`, then `kubectl describe pod <name>` for events.',
        'Verify server CPU/RAM — above 95% indicates resource exhaustion.',
        'Scale up replica count or increase worker concurrency.',
        'Review Nginx/Apache connection limits and raise if necessary.',
      ],
    },
    '404': {
      title: '404 Not Found — URL Route Does Not Exist',
      why_it_came: 'The web server processed the request, but no route or file matched the URL path. The endpoint may have been renamed, removed, or an SPA fallback config is missing.',
      likely_causes: [
        'Typo in the monitored URL or missing/extra trailing slash.',
        'API route renamed or deprecated in a recent deployment.',
        'React/Vue SPA: Nginx missing `try_files $uri /index.html` fallback directive.',
      ],
      action_steps: [
        'Verify exact URL path vs. Swagger/OpenAPI documentation.',
        'Check trailing slash requirement (`/details/` vs `/details`).',
        'For SPAs: ensure Nginx has `try_files $uri $uri/ /index.html;` configured.',
      ],
    },
    '403': {
      title: '403 Forbidden — WAF Block or IP / VPN Restriction',
      why_it_came: 'The web server understood the request but explicitly denied access. Triggered by WAF IP rules, corporate intranet VPN restrictions, or directory permission settings.',
      likely_causes: [
        "WAF / Cloudflare blocked the monitoring probe's IP or User-Agent string.",
        'Website restricted to internal corporate IP subnets (VPN required).',
        'Server directory permissions (chmod) prevent access.',
      ],
      action_steps: [
        'Verify whether the monitored website requires corporate VPN connectivity.',
        "Whitelist the monitoring server's outbound IP in WAF or security group.",
        'Check web server directory permissions (`chmod 755` for dirs, `644` for files).',
      ],
    },
    '401': {
      title: '401 Unauthorized — Authentication Required',
      why_it_came: 'The endpoint requires a valid authentication token or session cookie that the monitoring probe did not provide.',
      likely_causes: [
        'Monitored URL is a protected dashboard route, not a public health endpoint.',
        'API key or Bearer token used by the probe has expired.',
      ],
      action_steps: [
        'Change the monitored URL to a public health endpoint (`/health`, `/healthz`, `/api/health`).',
        'Configure probe auth headers if monitoring an authenticated endpoint is required.',
      ],
    },
    dns: {
      title: 'DNS Resolution Failed — Internal VPN / Intranet Required',
      why_it_came: 'The hostname could not be resolved to an IP. Adani internal UAT endpoints are hosted on private corporate DNS servers that only resolve when connected to the Adani Corporate VPN.',
      likely_causes: [
        'Monitoring worker machine is NOT connected to Adani Corporate VPN / internal network.',
        'Internal UAT hostname does not exist in public DNS (8.8.8.8 / 1.1.1.1).',
        'Local DNS cache is stale or the primary corporate DNS server is unreachable.',
      ],
      action_steps: [
        'Connect the monitoring host to the Adani Corporate VPN.',
        'Test DNS: `nslookup <hostname>` or `ping <hostname>` in terminal.',
        'Ensure internal DNS servers (10.x.x.x) are set in network adapter / resolv.conf.',
      ],
    },
    connection: {
      title: 'TCP Connection Refused — Web Server Service Stopped',
      why_it_came: 'The server IP was reached, but the OS actively rejected the TCP connection on port 80/443. No web server process is listening on that port.',
      likely_causes: [
        'Web server daemon (Nginx, Apache, Caddy, IIS) is stopped or crashed.',
        'Service bound to 127.0.0.1 instead of 0.0.0.0 (not accepting external connections).',
        'Host firewall (iptables / Windows Firewall) is actively blocking inbound connections.',
      ],
      action_steps: [
        'SSH into server: `systemctl status nginx` or `systemctl status apache2`.',
        'Start the service: `systemctl start nginx`.',
        "Verify sockets: `ss -tulpn | grep -E ':80|:443'` to confirm 0.0.0.0 binding.",
      ],
    },
    timeout: {
      title: 'Network Timeout — Server Unresponsive / Packets Dropped',
      why_it_came: 'The probe sent packets but received no response within the timeout window. Packets are being silently dropped by a firewall, or the server is under extreme load.',
      likely_causes: [
        'Cloud security group / network firewall silently dropping TCP packets.',
        'Target server is powered off, rebooting, or severely overloaded.',
        'Routing blackhole or VPN tunnel disconnection.',
      ],
      action_steps: [
        'Run `ping <host>` and `traceroute <host>` to find where packets drop.',
        'Check cloud security group rules: verify inbound port 443 is open.',
        'Verify server power state in the hypervisor or cloud provider console.',
      ],
    },
    ssl: {
      title: 'SSL/TLS Certificate Error — Handshake Failure',
      why_it_came: "The HTTPS TLS handshake failed because the server's certificate is expired, self-signed, or the domain name on the cert doesn't match the URL.",
      likely_causes: [
        'SSL/TLS certificate has passed its expiration date.',
        'Internal self-signed certificate whose root CA is not in the system trust store.',
        "Certificate's SAN doesn't match the accessed URL domain.",
      ],
      action_steps: [
        'Check cert: `openssl s_client -connect <host>:443 -servername <host>`.',
        "Renew via Let's Encrypt/Certbot or internal enterprise CA.",
        'Ensure the cert SAN contains the exact domain being monitored.',
      ],
    },
  };

  if (C[code]) return C[code];
  if (et.includes('dns') || (msg || '').toLowerCase().includes('getaddrinfo')) return C['dns'];
  if (et.includes('connection') || et.includes('refused')) return C['connection'];
  if (et.includes('timeout') || et.includes('timed out')) return C['timeout'];
  if (et.includes('ssl') || et.includes('cert')) return C['ssl'];
  if (code.startsWith('5') || et.includes('5xx')) return C['500'];
  if (code === '404' || et.includes('4xx')) return C['404'];
  if (code === '403') return C['403'];
  if (code === '401') return C['401'];

  return {
    title: `${errorType || 'Service Disruption'} Detected`,
    why_it_came: msg || 'An unexpected issue interrupted communication with the target website. Review the raw error message and check server logs for details.',
    likely_causes: [
      'Temporary network routing anomaly or firewall block.',
      'Web service configuration change or service restart in progress.',
      'Resource exhaustion or unresponsive worker thread on the host server.',
    ],
    action_steps: [
      'Test the URL manually: `curl -v <url>` or open in browser.',
      'Review application error logs on the host server.',
      'Verify network routing and firewall rules allow inbound traffic.',
    ],
  };
}

