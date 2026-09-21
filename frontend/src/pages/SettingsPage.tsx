import React, { useEffect, useState } from 'react';
import {
  Users,
  Mail,
  Clock,
  Send,
  Save,
  Plus,
  Trash2,
  CheckCircle2,
  AlertCircle,
  Shield,
  Layers,
} from 'lucide-react';
import { api } from '../api/client';
import { Project, User } from '../types';
import { useAuth } from '../context/AuthContext';

export const SettingsPage: React.FC = () => {
  const { user: currentUser } = useAuth();
  const [activeTab, setActiveTab] = useState<'developers' | 'monitoring' | 'email' | 'daily_report'>('developers');

  // Developers state
  const [developers, setDevelopers] = useState<User[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [devModalOpen, setDevModalOpen] = useState(false);
  const [newDev, setNewDev] = useState({
    full_name: '',
    email: '',
    password: '',
    role: 'USER',
    project_ids: [] as number[],
  });

  // Settings State
  const [settingsData, setSettingsData] = useState<any>({
    monitoring: {
      default_interval_seconds: 1800,
      default_timeout_seconds: 10,
      warning_response_time_ms: 2000,
      ssl_warning_days: 14,
    },
    email: {
      smtp_server: 'smtp.adani.com',
      smtp_port: 25,
      smtp_from_email: 'farhan.vhora@adani.com',
      smtp_user: '',
      smtp_password: '',
      smtp_use_tls: false,
      smtp_use_ssl: false,
      smtp_enabled: false,
    },
    daily_report: {
      daily_report_time: '20:11',
      daily_report_timezone: 'Asia/Kolkata',
      daily_report_recipients: 'admin@adani.com,farhan.vhora@adani.com',
      daily_report_enabled: true,
    },
  });

  const [testEmailRecipient, setTestEmailRecipient] = useState(currentUser?.email || 'farhan.vhora@adani.com');
  const [statusMsg, setStatusMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [loading, setLoading] = useState(false);

  const loadData = async () => {
    try {
      const [devs, projs, cfg] = await Promise.all([
        api.getDevelopers(),
        api.getProjects(),
        api.getSettings(),
      ]);
      setDevelopers(devs);
      setProjects(projs);
      setSettingsData(cfg);
    } catch (err) {
      console.error('Failed to load settings:', err);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreateDeveloper = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatusMsg(null);
    try {
      await api.createDeveloper(newDev);
      setStatusMsg({ type: 'success', text: `Developer ${newDev.full_name} created successfully!` });
      setDevModalOpen(false);
      setNewDev({ full_name: '', email: '', password: '', role: 'USER', project_ids: [] });
      await loadData();
    } catch (err: any) {
      setStatusMsg({ type: 'error', text: err.message || 'Failed to create developer.' });
    }
  };

  const handleDeleteUser = async (id: number) => {
    if (!confirm('Are you sure you want to delete this user?')) return;
    try {
      await api.deleteDeveloper(id);
      setStatusMsg({ type: 'success', text: 'User removed successfully.' });
      await loadData();
    } catch (err: any) {
      setStatusMsg({ type: 'error', text: err.message || 'Could not delete user.' });
    }
  };

  const saveMonitoringConfig = async () => {
    setStatusMsg(null);
    try {
      await api.updateMonitoringSettings(settingsData.monitoring);
      setStatusMsg({ type: 'success', text: 'Monitoring configuration saved.' });
    } catch (err: any) {
      setStatusMsg({ type: 'error', text: err.message || 'Failed to save monitoring settings.' });
    }
  };

  const saveEmailConfig = async () => {
    setStatusMsg(null);
    try {
      await api.updateEmailSettings(settingsData.email);
      setStatusMsg({ type: 'success', text: 'SMTP Email settings saved.' });
    } catch (err: any) {
      setStatusMsg({ type: 'error', text: err.message || 'Failed to save email settings.' });
    }
  };

  const saveDailyReportConfig = async () => {
    setStatusMsg(null);
    try {
      await api.updateDailyReportSettings(settingsData.daily_report);
      setStatusMsg({ type: 'success', text: 'Daily Report configuration saved.' });
    } catch (err: any) {
      setStatusMsg({ type: 'error', text: err.message || 'Failed to save daily report settings.' });
    }
  };

  const handleSendTestEmail = async () => {
    setStatusMsg(null);
    setLoading(true);
    try {
      const res = await api.testEmail(testEmailRecipient);
      setStatusMsg({
        type: 'success',
        text: `Test email dispatched! Result: ${res.status} (${res.message || 'Check inbox or console'})`,
      });
    } catch (err: any) {
      setStatusMsg({ type: 'error', text: err.message || 'Failed to send test email.' });
    } finally {
      setLoading(false);
    }
  };

  const handleSendDailyReportNow = async () => {
    setStatusMsg(null);
    setLoading(true);
    try {
      const res = await api.sendDailyReportNow();
      setStatusMsg({
        type: 'success',
        text: `Daily status report dispatched successfully (${res.status})!`,
      });
    } catch (err: any) {
      setStatusMsg({ type: 'error', text: err.message || 'Failed to send daily report.' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div>
        <h2 className="text-xl font-black text-slate-900 tracking-tight">
          System Settings & Configuration
        </h2>
        <p className="text-xs text-slate-500 mt-0.5">
          Manage developer accounts, monitoring thresholds, SMTP alerting, and scheduled daily reports
        </p>
      </div>

      {statusMsg && (
        <div
          className={`p-4 rounded-xl text-xs font-semibold flex items-center space-x-2 ${
            statusMsg.type === 'success'
              ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
              : 'bg-rose-50 text-rose-800 border border-rose-200'
          }`}
        >
          {statusMsg.type === 'success' ? (
            <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
          ) : (
            <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0" />
          )}
          <span>{statusMsg.text}</span>
        </div>
      )}

      {/* Tabs */}
      <div className="flex border-b border-slate-200 space-x-6 text-xs font-bold">
        {[
          { id: 'developers', label: 'Developers & Users', icon: Users },
          { id: 'monitoring', label: 'Monitoring Engine', icon: Clock },
          { id: 'email', label: 'Email & SMTP Alerts', icon: Mail },
          { id: 'daily_report', label: 'Daily Status Report', icon: Send },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => {
                setActiveTab(tab.id as any);
                setStatusMsg(null);
              }}
              className={`flex items-center space-x-2 py-3 border-b-2 transition-all ${
                isActive
                  ? 'border-[#583896] text-[#583896]'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Tab 1: Developers & Users (Requirement 1) */}
      {activeTab === 'developers' && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold text-slate-900">Team Members & Accounts</h3>
              <p className="text-xs text-slate-500">
                Developers receive instant email alerts when their assigned websites go DOWN
              </p>
            </div>
            <button
              onClick={() => setDevModalOpen(true)}
              className="inline-flex items-center space-x-1.5 px-3.5 py-2 rounded-xl bg-gradient-to-r from-[#0078BD] via-[#583896] to-[#BE185D] text-white text-xs font-bold shadow-adani hover:opacity-95"
            >
              <Plus className="w-4 h-4" />
              <span>Create User / Developer</span>
            </button>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 shadow-subtle overflow-hidden">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-500 uppercase font-semibold border-b border-slate-200">
                <tr>
                  <th className="px-5 py-3">Full Name</th>
                  <th className="px-5 py-3">Email Address</th>
                  <th className="px-5 py-3">Assigned Projects</th>
                  <th className="px-5 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-medium">
                {developers.map((dev) => (
                  <tr key={dev.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="px-5 py-3 font-bold text-slate-900">{dev.full_name}</td>
                    <td className="px-5 py-3 font-mono text-slate-600">{dev.email}</td>
                    <td className="px-5 py-3 text-slate-600">
                      <span className="font-bold text-slate-900">
                        {dev.assigned_projects_count || 0}
                      </span>{' '}
                      sites assigned
                    </td>
                    <td className="px-5 py-3 text-right">
                      {dev.id !== currentUser?.id && (
                        <button
                          onClick={() => handleDeleteUser(dev.id)}
                          className="p-1.5 rounded text-rose-600 hover:bg-rose-50 border border-rose-200"
                          title="Delete user"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 2: Monitoring Engine Config */}
      {activeTab === 'monitoring' && (
        <div className="bg-white rounded-xl p-6 border border-slate-200 shadow-subtle max-w-2xl space-y-4">
          <h3 className="text-base font-bold text-slate-900">Default Probe Parameters</h3>
          <p className="text-xs text-slate-500">
            System defaults applied to new projects. Projects can customize individual settings.
          </p>

          <div className="grid grid-cols-2 gap-4 pt-2">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">
                Default Interval (Seconds)
              </label>
              <input
                type="number"
                value={settingsData.monitoring.default_interval_seconds}
                onChange={(e) =>
                  setSettingsData({
                    ...settingsData,
                    monitoring: {
                      ...settingsData.monitoring,
                      default_interval_seconds: parseInt(e.target.value) || 1800,
                    },
                  })
                }
                className="w-full text-xs px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-[#0078BD]"
              />
              <span className="text-[10px] text-slate-400">Default: 1800s (30 minutes)</span>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">
                Default Timeout (Seconds)
              </label>
              <input
                type="number"
                value={settingsData.monitoring.default_timeout_seconds}
                onChange={(e) =>
                  setSettingsData({
                    ...settingsData,
                    monitoring: {
                      ...settingsData.monitoring,
                      default_timeout_seconds: parseInt(e.target.value) || 10,
                    },
                  })
                }
                className="w-full text-xs px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-[#0078BD]"
              />
              <span className="text-[10px] text-slate-400">Default: 10 seconds</span>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">
                Warning Latency Threshold (ms)
              </label>
              <input
                type="number"
                value={settingsData.monitoring.warning_response_time_ms}
                onChange={(e) =>
                  setSettingsData({
                    ...settingsData,
                    monitoring: {
                      ...settingsData.monitoring,
                      warning_response_time_ms: parseInt(e.target.value) || 2000,
                    },
                  })
                }
                className="w-full text-xs px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-[#0078BD]"
              />
              <span className="text-[10px] text-slate-400">Flags WARNING if exceeded</span>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">
                SSL Expiry Warning (Days)
              </label>
              <input
                type="number"
                value={settingsData.monitoring.ssl_warning_days}
                onChange={(e) =>
                  setSettingsData({
                    ...settingsData,
                    monitoring: {
                      ...settingsData.monitoring,
                      ssl_warning_days: parseInt(e.target.value) || 14,
                    },
                  })
                }
                className="w-full text-xs px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-[#0078BD]"
              />
              <span className="text-[10px] text-slate-400">Flags WARNING if cert expires soon</span>
            </div>
          </div>

          <div className="pt-4 border-t border-slate-100 flex justify-end">
            <button
              onClick={saveMonitoringConfig}
              className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-lg bg-gradient-to-r from-[#0078BD] via-[#583896] to-[#BE185D] text-white text-xs font-bold hover:opacity-95 shadow-sm"
            >
              <Save className="w-3.5 h-3.5" />
              <span>Save Monitoring Settings</span>
            </button>
          </div>
        </div>
      )}

      {/* Tab 3: Email & SMTP Alerts (Requirement 5) */}
      {activeTab === 'email' && (
        <div className="space-y-6 max-w-2xl">
          <div className="bg-white rounded-xl p-6 border border-slate-200 shadow-subtle space-y-4">
            <h3 className="text-base font-bold text-slate-900">SMTP Server Configuration</h3>
            <p className="text-xs text-slate-500">
              Dispatches immediate [DOWN] and [RESOLVED] email alerts to developers
            </p>

            <div className="grid grid-cols-2 gap-4 pt-2">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  SMTP Server Host
                </label>
                <input
                  type="text"
                  value={settingsData.email.smtp_server}
                  onChange={(e) =>
                    setSettingsData({
                      ...settingsData,
                      email: { ...settingsData.email, smtp_server: e.target.value },
                    })
                  }
                  placeholder="smtp.adani.com"
                  className="w-full text-xs px-3 py-2 border border-slate-300 rounded-lg font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">SMTP Port</label>
                <input
                  type="number"
                  value={settingsData.email.smtp_port}
                  onChange={(e) =>
                    setSettingsData({
                      ...settingsData,
                      email: { ...settingsData.email, smtp_port: parseInt(e.target.value) || 25 },
                    })
                  }
                  placeholder="25 or 587"
                  className="w-full text-xs px-3 py-2 border border-slate-300 rounded-lg font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  From Email Address
                </label>
                <input
                  type="email"
                  value={settingsData.email.smtp_from_email}
                  onChange={(e) =>
                    setSettingsData({
                      ...settingsData,
                      email: { ...settingsData.email, smtp_from_email: e.target.value },
                    })
                  }
                  placeholder="farhan.vhora@adani.com"
                  className="w-full text-xs px-3 py-2 border border-slate-300 rounded-lg"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">SMTP Username</label>
                <input
                  type="text"
                  value={settingsData.email.smtp_user}
                  onChange={(e) =>
                    setSettingsData({
                      ...settingsData,
                      email: { ...settingsData.email, smtp_user: e.target.value },
                    })
                  }
                  placeholder="Optional username"
                  className="w-full text-xs px-3 py-2 border border-slate-300 rounded-lg"
                />
              </div>
            </div>

            <div className="flex items-center space-x-6 pt-2">
              <label className="flex items-center space-x-2 text-xs font-semibold text-slate-700 cursor-pointer">
                <input
                  type="checkbox"
                  checked={settingsData.email.smtp_use_tls}
                  onChange={(e) =>
                    setSettingsData({
                      ...settingsData,
                      email: { ...settingsData.email, smtp_use_tls: e.target.checked },
                    })
                  }
                  className="rounded text-[#0078BD] focus:ring-[#0078BD]"
                />
                <span>Enable STARTTLS</span>
              </label>

              <label className="flex items-center space-x-2 text-xs font-semibold text-slate-700 cursor-pointer">
                <input
                  type="checkbox"
                  checked={settingsData.email.smtp_enabled}
                  onChange={(e) =>
                    setSettingsData({
                      ...settingsData,
                      email: { ...settingsData.email, smtp_enabled: e.target.checked },
                    })
                  }
                  className="rounded text-[#0078BD] focus:ring-[#0078BD]"
                />
                <span>Enable Real SMTP Dispatch (otherwise simulated)</span>
              </label>
            </div>

            <div className="pt-4 border-t border-slate-100 flex justify-end">
              <button
                onClick={saveEmailConfig}
                className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-lg bg-gradient-to-r from-[#0078BD] via-[#583896] to-[#BE185D] text-white text-xs font-bold hover:opacity-95 shadow-sm"
              >
                <Save className="w-3.5 h-3.5" />
                <span>Save SMTP Settings</span>
              </button>
            </div>
          </div>

          {/* Test Email Box */}
          <div className="bg-white rounded-xl p-6 border border-slate-200 shadow-subtle space-y-3">
            <h4 className="text-sm font-bold text-slate-900">Send Test Email</h4>
            <div className="flex items-center space-x-3">
              <input
                type="email"
                value={testEmailRecipient}
                onChange={(e) => setTestEmailRecipient(e.target.value)}
                placeholder="recipient@adani.com"
                className="flex-1 text-xs px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-[#0078BD]"
              />
              <button
                onClick={handleSendTestEmail}
                disabled={loading}
                className="px-4 py-2 bg-gradient-to-r from-[#0078BD] via-[#583896] to-[#BE185D] hover:opacity-95 text-white rounded-lg text-xs font-bold shadow-sm disabled:opacity-50"
              >
                {loading ? 'Sending...' : 'Dispatch Test Email'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Tab 4: Scheduled Daily Report */}
      {activeTab === 'daily_report' && (
        <div className="bg-white rounded-xl p-6 border border-slate-200 shadow-subtle max-w-2xl space-y-4">
          <h3 className="text-base font-bold text-slate-900">Scheduled Daily Status Report</h3>
          <p className="text-xs text-slate-500">
            Automatically emails an executive HTML summary of uptime, downtime, and outages.
          </p>

          <div className="space-y-4 pt-2">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">
                Scheduled Daily Time (Default: 8:11 PM IST)
              </label>
              <input
                type="text"
                value={settingsData.daily_report.daily_report_time}
                onChange={(e) =>
                  setSettingsData({
                    ...settingsData,
                    daily_report: {
                      ...settingsData.daily_report,
                      daily_report_time: e.target.value,
                    },
                  })
                }
                placeholder="20:11"
                className="w-48 text-xs px-3 py-2 font-mono border border-slate-300 rounded-lg focus:ring-2 focus:ring-[#0078BD]"
              />
              <span className="text-[10px] text-slate-400 mt-0.5 block">
                Format: HH:MM in {settingsData.daily_report.daily_report_timezone}
              </span>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">
                Report Recipients (Comma-separated)
              </label>
              <input
                type="text"
                value={settingsData.daily_report.daily_report_recipients}
                onChange={(e) =>
                  setSettingsData({
                    ...settingsData,
                    daily_report: {
                      ...settingsData.daily_report,
                      daily_report_recipients: e.target.value,
                    },
                  })
                }
                placeholder="admin@adani.com, farhan.vhora@adani.com"
                className="w-full text-xs px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-[#0078BD]"
              />
            </div>

            <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
              <button
                onClick={handleSendDailyReportNow}
                disabled={loading}
                className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-bold transition-colors"
              >
                <Send className="w-3.5 h-3.5 text-[#0078BD]" />
                <span>Send Daily Report Right Now</span>
              </button>

              <button
                onClick={saveDailyReportConfig}
                className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-lg bg-gradient-to-r from-[#0078BD] via-[#583896] to-[#BE185D] text-white text-xs font-bold hover:opacity-95 shadow-sm"
              >
                <Save className="w-3.5 h-3.5" />
                <span>Save Schedule</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Developer Creation Modal (Requirement 1) */}
      {devModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm animate-fade-in overflow-y-auto">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-200 my-8">
            <h3 className="text-lg font-black text-slate-900 mb-4">Add Developer / User</h3>

            <form onSubmit={handleCreateDeveloper} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Full Name *</label>
                <input
                  type="text"
                  required
                  value={newDev.full_name}
                  onChange={(e) => setNewDev({ ...newDev, full_name: e.target.value })}
                  placeholder="e.g. Farhan Vhora"
                  className="w-full text-xs px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-[#0078BD]"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Email *</label>
                <input
                  type="email"
                  required
                  value={newDev.email}
                  onChange={(e) => setNewDev({ ...newDev, email: e.target.value })}
                  placeholder="farhan@adani.com"
                  className="w-full text-xs px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-[#0078BD]"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Password *</label>
                <input
                  type="password"
                  required
                  minLength={6}
                  value={newDev.password}
                  onChange={(e) => setNewDev({ ...newDev, password: e.target.value })}
                  placeholder="••••••••••••"
                  className="w-full text-xs px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-[#0078BD]"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  Assign Websites (No limit)
                </label>
                <div className="border border-slate-200 rounded-lg max-h-32 overflow-y-auto p-2 space-y-1 bg-slate-50">
                  {projects.map((p) => {
                    const isChecked = newDev.project_ids.includes(p.id);
                    return (
                      <label
                        key={p.id}
                        className="flex items-center space-x-2 text-xs text-slate-700 cursor-pointer p-1 rounded hover:bg-slate-200/50"
                      >
                        <input
                          type="checkbox"
                          checked={isChecked}
                          onChange={() => {
                            setNewDev({
                              ...newDev,
                              project_ids: isChecked
                                ? newDev.project_ids.filter((id) => id !== p.id)
                                : [...newDev.project_ids, p.id],
                            });
                          }}
                          className="rounded text-[#0078BD] focus:ring-[#0078BD]"
                        />
                        <span>{p.name}</span>
                      </label>
                    );
                  })}
                </div>
              </div>

              <div className="flex items-center justify-end space-x-3 pt-4 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setDevModalOpen(false)}
                  className="px-4 py-2 text-xs font-bold text-slate-600 bg-slate-100 rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 text-xs font-bold text-white bg-gradient-to-r from-[#0078BD] via-[#583896] to-[#BE185D] hover:opacity-95 rounded-lg shadow-sm"
                >
                  Create User
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
