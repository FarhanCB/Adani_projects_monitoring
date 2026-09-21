import React, { useEffect, useState } from 'react';
import {
  Activity,
  Database,
  Mail,
  Radio,
  RefreshCw,
  Server,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Layers,
} from 'lucide-react';
import { api } from '../api/client';
import { SystemHealth } from '../types';

export const SystemHealthPage: React.FC = () => {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [loading, setLoading] = useState(true);
  const [probing, setProbing] = useState(false);

  const fetchHealth = async () => {
    try {
      const data = await api.getHealth();
      setHealth(data);
    } catch (err) {
      console.error('Failed to load system health:', err);
    } finally {
      setLoading(false);
      setProbing(false);
    }
  };

  useEffect(() => {
    fetchHealth();
    const timer = setInterval(fetchHealth, 10000);
    return () => clearInterval(timer);
  }, []);

  const handleManualProbe = () => {
    setProbing(true);
    fetchHealth();
  };

  if (loading || !health) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-8 bg-slate-200 rounded w-48 mb-4" />
        <div className="grid grid-cols-3 gap-6">
          {[1, 2, 3].map((n) => (
            <div key={n} className="h-44 bg-white rounded-2xl border border-slate-200" />
          ))}
        </div>
      </div>
    );
  }

  const isWorkerOnline = health.monitoring_worker === 'ONLINE';
  const isDbConnected = health.database === 'CONNECTED';

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-black text-slate-900 tracking-tight">
            System & Service Health
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Real-time diagnostics of the background monitoring engine, database connection, and alert dispatcher
          </p>
        </div>

        <button
          onClick={handleManualProbe}
          disabled={probing}
          className="inline-flex items-center space-x-1.5 px-3.5 py-2 rounded-xl bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 text-xs font-bold shadow-sm transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${probing ? 'animate-spin text-[#0078BD]' : ''}`} />
          <span>Ping Services</span>
        </button>
      </div>

      {/* 3 Core System Pillar Cards (Requirement 14) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* 1. Monitoring Worker */}
        <div
          className={`bg-white rounded-2xl p-6 border shadow-subtle flex flex-col justify-between ${
            isWorkerOnline ? 'border-emerald-200' : 'border-rose-200'
          }`}
        >
          <div>
            <div className="flex items-center justify-between mb-4">
              <div
                className={`p-3 rounded-xl ${
                  isWorkerOnline
                    ? 'bg-emerald-50 text-emerald-600'
                    : 'bg-rose-50 text-rose-600'
                }`}
              >
                <Radio className="w-6 h-6" />
              </div>

              <span
                className={`inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-bold border ${
                  isWorkerOnline
                    ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                    : 'bg-rose-50 text-rose-700 border-rose-200'
                }`}
              >
                <span
                  className={`w-2 h-2 rounded-full ${
                    isWorkerOnline ? 'bg-emerald-500' : 'bg-rose-500'
                  }`}
                />
                <span>{health.monitoring_worker}</span>
              </span>
            </div>

            <h3 className="text-base font-bold text-slate-900">Monitoring Engine</h3>
            <p className="text-xs text-slate-500 mt-1">
              Separate background scheduler executing independent HTTP probes and SSL evaluations.
            </p>
          </div>

          <div className="pt-4 mt-6 border-t border-slate-100 text-xs text-slate-500 space-y-1.5">
            <div className="flex justify-between">
              <span>Last Heartbeat:</span>
              <span className="font-mono text-slate-800 font-bold">
                {health.last_worker_heartbeat
                  ? new Date(health.last_worker_heartbeat).toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit',
                      second: '2-digit',
                    })
                  : 'Never'}
              </span>
            </div>
            <div className="flex justify-between">
              <span>Last Probe Cycle:</span>
              <span className="font-mono text-slate-800 font-bold">
                {health.last_monitoring_cycle
                  ? new Date(health.last_monitoring_cycle).toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit',
                      second: '2-digit',
                    })
                  : 'Never'}
              </span>
            </div>
          </div>
        </div>

        {/* 2. Database Connection */}
        <div
          className={`bg-white rounded-2xl p-6 border shadow-subtle flex flex-col justify-between ${
            isDbConnected ? 'border-emerald-200' : 'border-rose-200'
          }`}
        >
          <div>
            <div className="flex items-center justify-between mb-4">
              <div
                className={`p-3 rounded-xl ${
                  isDbConnected
                    ? 'bg-emerald-50 text-emerald-600'
                    : 'bg-rose-50 text-rose-600'
                }`}
              >
                <Database className="w-6 h-6" />
              </div>

              <span
                className={`inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-bold border ${
                  isDbConnected
                    ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                    : 'bg-rose-50 text-rose-700 border-rose-200'
                }`}
              >
                <span
                  className={`w-2 h-2 rounded-full ${
                    isDbConnected ? 'bg-emerald-500' : 'bg-rose-500'
                  }`}
                />
                <span>{health.database}</span>
              </span>
            </div>

            <h3 className="text-base font-bold text-slate-900">Database Engine</h3>
            <p className="text-xs text-slate-500 mt-1">
              Persistent relational store containing users, projects, check logs, and incidents.
            </p>
          </div>

          <div className="pt-4 mt-6 border-t border-slate-100 text-xs text-slate-500 space-y-1.5">
            <div className="flex justify-between">
              <span>Dialect:</span>
              <span className="font-bold text-slate-800">{health.database_dialect}</span>
            </div>
            <div className="flex justify-between">
              <span>Ping Latency:</span>
              <span className="font-mono text-emerald-600 font-bold">
                {health.database_latency_ms} ms
              </span>
            </div>
          </div>
        </div>

        {/* 3. Email Alerting Service */}
        <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-subtle flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 rounded-xl bg-sky-50 text-sky-600">
                <Mail className="w-6 h-6" />
              </div>

              <span className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-bold bg-sky-50 text-sky-700 border border-sky-200">
                <span>{health.email}</span>
              </span>
            </div>

            <h3 className="text-base font-bold text-slate-900">Email & Outage Alerts</h3>
            <p className="text-xs text-slate-500 mt-1">
              SMTP transport for immediate developer notifications and daily status summaries.
            </p>
          </div>

          <div className="pt-4 mt-6 border-t border-slate-100 text-xs text-slate-500 space-y-1.5">
            <div className="flex justify-between">
              <span>Mode:</span>
              <span className="font-bold text-slate-800">
                {health.email === 'AVAILABLE' ? 'Live SMTP Transport' : 'Sandbox / Simulation'}
              </span>
            </div>
            <div className="flex justify-between">
              <span>Status:</span>
              <span className="text-emerald-600 font-semibold">Operational</span>
            </div>
          </div>
        </div>
      </div>

      {/* Operational Capacity Statistics */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-subtle">
        <h3 className="text-base font-bold text-slate-900 mb-1">Monitoring Capacity & Workload</h3>
        <p className="text-xs text-slate-500 mb-6">Current load handled by the worker cluster</p>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80">
            <span className="text-xs font-bold uppercase text-slate-500 block mb-1">
              Active Monitored Websites
            </span>
            <div className="text-2xl font-black text-slate-900">
              {health.enabled_projects_count}{' '}
              <span className="text-sm font-normal text-slate-400">
                / {health.total_projects_count} registered
              </span>
            </div>
          </div>

          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80">
            <span className="text-xs font-bold uppercase text-slate-500 block mb-1">
              Active Outage Incidents
            </span>
            <div
              className={`text-2xl font-black ${
                health.active_incidents_count > 0 ? 'text-rose-600' : 'text-slate-900'
              }`}
            >
              {health.active_incidents_count}
            </div>
          </div>

          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80">
            <span className="text-xs font-bold uppercase text-slate-500 block mb-1">
              Worker Engine Process
            </span>
            <div className="text-sm font-bold text-emerald-700 flex items-center space-x-1.5 mt-1">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span>Independent Asynchronous Loop</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
