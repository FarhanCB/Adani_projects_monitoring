import React, { useState } from 'react';
import { ExternalLink, Play, Clock, AlertTriangle, Users, Activity, ShieldCheck } from 'lucide-react';
import { StatusBadge } from './StatusBadge';
import { ProjectCardData } from '../types';

interface ProjectCardProps {
  project: ProjectCardData;
  onSelect: (id: number) => void;
  onTestNow: (id: number) => Promise<void>;
}

export const ProjectCard: React.FC<ProjectCardProps> = ({
  project,
  onSelect,
  onTestNow,
}) => {
  const [testing, setTesting] = useState(false);

  const handleTestClick = async (e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      setTesting(true);
      await onTestNow(project.id);
    } finally {
      setTesting(false);
    }
  };

  const formatLastChecked = (dtStr?: string) => {
    if (!dtStr) return 'Never checked';
    try {
      const dt = new Date(dtStr);
      return dt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    } catch {
      return dtStr;
    }
  };

  const getUptimeColor = (pct: number) => {
    if (pct >= 99.5) return 'text-emerald-700 bg-emerald-50 border-emerald-200';
    if (pct >= 95.0) return 'text-amber-700 bg-amber-50 border-amber-200';
    return 'text-rose-700 bg-rose-50 border-rose-200';
  };

  return (
    <div
      onClick={() => onSelect(project.id)}
      className="bg-white rounded-xl border border-slate-200 shadow-subtle hover:shadow-card hover:border-slate-300 transition-all duration-200 cursor-pointer overflow-hidden flex flex-col group"
    >
      {/* Top Banner with Official Adani Brand Gradient */}
      <div className="h-1.5 w-full bg-gradient-to-r from-[#0078BD] via-[#583896] to-[#BE185D]" />

      <div className="p-5 flex-1 flex flex-col justify-between">
        <div>
          {/* Header row: Project Title & Live Status */}
          <div className="flex items-start justify-between gap-3 mb-2">
            <h3 className="font-bold text-slate-900 text-base group-hover:text-[#583896] transition-colors line-clamp-1">
              {project.name}
            </h3>
            <StatusBadge status={project.current_status} size="sm" />
          </div>

          {/* URL with external link */}
          <div className="flex items-center space-x-1 text-xs text-slate-500 mb-4 font-mono">
            <span className="truncate max-w-[260px]">{project.url}</span>
            <a
              href={project.url}
              target="_blank"
              rel="noopener noreferrer"
              onClick={(e) => e.stopPropagation()}
              className="text-slate-400 hover:text-slate-700 p-0.5"
              title="Open website in new tab"
            >
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
          </div>

          {/* Key Metrics Grid */}
          <div className="grid grid-cols-2 gap-3 py-3 border-y border-slate-100 mb-4 bg-slate-50/50 rounded-lg px-3">
            <div>
              <span className="text-[11px] font-medium uppercase tracking-wider text-slate-400 block mb-0.5">
                Response Time
              </span>
              <div className="flex items-center space-x-1.5">
                <Activity className="w-3.5 h-3.5 text-slate-400" />
                <span className="text-sm font-bold text-slate-800">
                  {project.response_time_ms ? `${project.response_time_ms} ms` : '—'}
                </span>
              </div>
            </div>

            <div>
              <span className="text-[11px] font-medium uppercase tracking-wider text-slate-400 block mb-0.5">
                HTTP Code
              </span>
              <span className={`inline-block text-xs font-bold px-2 py-0.5 rounded ${
                project.http_status && project.http_status < 400
                  ? 'bg-slate-200/80 text-slate-800'
                  : 'bg-rose-100 text-rose-800'
              }`}>
                {project.http_status ? `HTTP ${project.http_status}` : 'None'}
              </span>
            </div>
          </div>
        </div>

        <div>
          {/* Uptime & Incidents row */}
          <div className="flex items-center justify-between text-xs mb-3">
            <div className="flex items-center space-x-1.5">
              <span className="text-slate-500">Uptime (30d):</span>
              <span className={`font-bold px-2 py-0.5 rounded border text-[11px] ${getUptimeColor(project.uptime_percentage)}`}>
                {project.uptime_percentage.toFixed(2)}%
              </span>
            </div>

            <div className="flex items-center space-x-3 text-slate-500">
              <span className="flex items-center space-x-1" title={`${project.incident_count} Incidents`}>
                <AlertTriangle className="w-3.5 h-3.5 text-amber-500" />
                <span>{project.incident_count}</span>
              </span>
              <span className="flex items-center space-x-1" title={`${project.developer_count} Developers assigned`}>
                <Users className="w-3.5 h-3.5 text-slate-400" />
                <span>{project.developer_count}</span>
              </span>
            </div>
          </div>

          {/* Footer: Last checked & Test Now button */}
          <div className="flex items-center justify-between pt-3 border-t border-slate-100 text-xs text-slate-500">
            <div className="flex items-center space-x-1 truncate">
              <Clock className="w-3 h-3 text-slate-400" />
              <span>Checked: {formatLastChecked(project.last_checked)}</span>
            </div>

            <button
              onClick={handleTestClick}
              disabled={testing}
              className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-md text-xs font-semibold bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 hover:border-purple-300 hover:text-[#583896] transition-colors shadow-sm disabled:opacity-50"
              title="Probe website right now"
            >
              <Play className={`w-3 h-3 ${testing ? 'animate-spin' : 'text-[#0078BD]'}`} />
              <span>{testing ? 'Testing...' : 'Test Now'}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
