import React, { useEffect, useState } from 'react';
import {
  Globe,
  Plus,
  Edit2,
  Trash2,
  Power,
  Play,
  ExternalLink,
  Users,
  Clock,
  Shield,
  Search,
  Check,
} from 'lucide-react';
import { api } from '../api/client';
import { ConfirmDialog } from '../components/ConfirmDialog';
import { StatusBadge } from '../components/StatusBadge';
import { Project, User } from '../types';
import { useAuth } from '../context/AuthContext';

interface ProjectsPageProps {
  onSelectProject: (id: number) => void;
}

export const ProjectsPage: React.FC<ProjectsPageProps> = ({ onSelectProject }) => {
  const { isAdmin } = useAuth();
  const [projects, setProjects] = useState<Project[]>([]);
  const [developers, setDevelopers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  // Modal State
  const [modalOpen, setModalOpen] = useState(false);
  const [editingProject, setEditingProject] = useState<Project | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    url: '',
    interval_seconds: 1800,
    timeout_seconds: 10,
    expected_status_codes: '200,201,202,204',
    is_enabled: true,
    developer_ids: [] as number[],
  });
  const [formError, setFormError] = useState('');
  const [saving, setSaving] = useState(false);

  // Delete Confirm State
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [projectToDelete, setProjectToDelete] = useState<Project | null>(null);

  const loadData = async () => {
    try {
      const [projList, devList] = await Promise.all([
        api.getProjects(),
        api.getDevelopers(),
      ]);
      setProjects(projList);
      setDevelopers(devList);
    } catch (err) {
      console.error('Failed to load projects:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const openCreateModal = () => {
    setEditingProject(null);
    setFormData({
      name: '',
      description: '',
      url: 'https://',
      interval_seconds: 1800,
      timeout_seconds: 10,
      expected_status_codes: '200,201,202,204',
      is_enabled: true,
      developer_ids: [],
    });
    setFormError('');
    setModalOpen(true);
  };

  const openEditModal = (proj: Project) => {
    setEditingProject(proj);
    setFormData({
      name: proj.name,
      description: proj.description || '',
      url: proj.url,
      interval_seconds: proj.interval_seconds,
      timeout_seconds: proj.timeout_seconds,
      expected_status_codes: proj.expected_status_codes,
      is_enabled: proj.is_enabled,
      developer_ids: proj.developers.map((d) => d.id),
    });
    setFormError('');
    setModalOpen(true);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError('');
    setSaving(true);
    try {
      if (editingProject) {
        await api.updateProject(editingProject.id, formData);
      } else {
        await api.createProject(formData);
      }
      setModalOpen(false);
      await loadData();
    } catch (err: any) {
      setFormError(err.message || 'Failed to save project');
    } finally {
      setSaving(false);
    }
  };

  const handleToggle = async (proj: Project) => {
    try {
      await api.toggleProject(proj.id);
      await loadData();
    } catch (err) {
      console.error('Toggle failed:', err);
    }
  };

  const handleDelete = async () => {
    if (!projectToDelete) return;
    try {
      await api.deleteProject(projectToDelete.id);
      setDeleteConfirmOpen(false);
      setProjectToDelete(null);
      await loadData();
    } catch (err) {
      console.error('Delete failed:', err);
    }
  };

  const toggleDevSelection = (devId: number) => {
    setFormData((prev) => {
      const exists = prev.developer_ids.includes(devId);
      return {
        ...prev,
        developer_ids: exists
          ? prev.developer_ids.filter((id) => id !== devId)
          : [...prev.developer_ids, devId],
      };
    });
  };

  const filtered = projects.filter(
    (p) =>
      p.name.toLowerCase().includes(search.toLowerCase()) ||
      p.url.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-black text-slate-900 tracking-tight">
            Monitored Websites & Endpoints
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Configure monitoring frequencies, HTTP expectations, and developer alert notifications
          </p>
        </div>

        <button
          onClick={openCreateModal}
          className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-gradient-to-r from-[#0078BD] via-[#583896] to-[#BE185D] text-white text-xs font-bold shadow-adani hover:opacity-95 transition-opacity"
        >
          <Plus className="w-4 h-4" />
          <span>Add New Website</span>
        </button>
      </div>

      {/* Search Input */}
      <div className="relative max-w-md">
        <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 transform -translate-y-1/2" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Filter projects by title or URL..."
          className="w-full pl-9 pr-4 py-2 text-xs border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#583896]"
        />
      </div>

      {/* Projects Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-subtle overflow-hidden">
        {filtered.length === 0 ? (
          <div className="p-12 text-center text-slate-400 text-xs">
            <Globe className="w-10 h-10 mx-auto text-slate-300 mb-2" />
            No websites found matching your search.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-500 uppercase font-semibold border-b border-slate-200">
                <tr>
                  <th className="px-5 py-3">Website / Service</th>
                  <th className="px-5 py-3">Target URL</th>
                  <th className="px-5 py-3">Interval</th>
                  <th className="px-5 py-3">Status</th>
                  <th className="px-5 py-3">Assigned Engineers</th>
                  <th className="px-5 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-medium">
                {filtered.map((p) => (
                  <tr key={p.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="px-5 py-3">
                      <button
                        onClick={() => onSelectProject(p.id)}
                        className="font-bold text-slate-900 hover:text-[#0078BD] text-left transition-colors"
                      >
                        {p.name}
                      </button>
                      {p.description && (
                        <p className="text-[11px] text-slate-500 truncate max-w-xs">
                          {p.description}
                        </p>
                      )}
                    </td>

                    <td className="px-5 py-3 font-mono text-slate-600">
                      <div className="flex items-center space-x-1">
                        <span className="truncate max-w-[200px]">{p.url}</span>
                        <a
                          href={p.url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-slate-400 hover:text-slate-700"
                        >
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      </div>
                    </td>

                    <td className="px-5 py-3 text-slate-600">
                      <span className="flex items-center space-x-1">
                        <Clock className="w-3 h-3 text-slate-400" />
                        <span>{p.interval_seconds}s</span>
                      </span>
                    </td>

                    <td className="px-5 py-3">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-bold ${
                          p.is_enabled
                            ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                            : 'bg-slate-100 text-slate-600 border border-slate-200'
                        }`}
                      >
                        {p.is_enabled ? 'Active' : 'Disabled'}
                      </span>
                    </td>

                    <td className="px-5 py-3 text-slate-600">
                      <span className="flex items-center space-x-1">
                        <Users className="w-3 h-3 text-slate-400" />
                        <span className="truncate max-w-xs">
                          {p.developers.map((d) => d.full_name).join(', ') || 'None assigned'}
                        </span>
                      </span>
                    </td>

                    <td className="px-5 py-3 text-right">
                      <div className="flex items-center justify-end space-x-2">
                        <button
                          onClick={() => handleToggle(p)}
                          title={p.is_enabled ? 'Disable monitoring' : 'Enable monitoring'}
                          className={`p-1.5 rounded-lg border transition-colors ${
                            p.is_enabled
                              ? 'text-emerald-700 border-emerald-200 hover:bg-emerald-50'
                              : 'text-slate-400 border-slate-200 hover:bg-slate-100'
                          }`}
                        >
                          <Power className="w-3.5 h-3.5" />
                        </button>

                        <button
                          onClick={() => openEditModal(p)}
                          title="Edit website settings"
                          className="p-1.5 rounded-lg border border-slate-200 text-slate-600 hover:text-slate-900 hover:bg-slate-50 transition-colors"
                        >
                          <Edit2 className="w-3.5 h-3.5" />
                        </button>

                        <button
                          onClick={() => {
                            setProjectToDelete(p);
                            setDeleteConfirmOpen(true);
                          }}
                          title="Delete website"
                          className="p-1.5 rounded-lg border border-rose-200 text-rose-600 hover:bg-rose-50 transition-colors"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Add / Edit Project Modal */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm animate-fade-in overflow-y-auto">
          <div className="bg-white rounded-2xl max-w-xl w-full p-6 shadow-2xl border border-slate-200 my-8">
            <h3 className="text-lg font-black text-slate-900 tracking-tight mb-4">
              {editingProject ? 'Edit Monitored Website' : 'Add Monitored Website'}
            </h3>

            {formError && (
              <div className="p-3 mb-4 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs">
                {formError}
              </div>
            )}

            <form onSubmit={handleSave} className="space-y-4">
              <div>
                <label className="block text-xs font-bold uppercase text-slate-700 mb-1">
                  Project / Service Name *
                </label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="e.g. Plant Maintenance Portal"
                  className="w-full text-xs px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-[#0078BD] focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-bold uppercase text-slate-700 mb-1">
                  Target Website URL *
                </label>
                <input
                  type="url"
                  required
                  value={formData.url}
                  onChange={(e) => setFormData({ ...formData, url: e.target.value })}
                  placeholder="https://example.adani.com/healthz"
                  className="w-full text-xs px-3 py-2 font-mono border border-slate-300 rounded-lg focus:ring-2 focus:ring-[#0078BD] focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-bold uppercase text-slate-700 mb-1">
                  Description (Optional)
                </label>
                <textarea
                  rows={2}
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Operational purpose, environment, or tier..."
                  className="w-full text-xs px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-[#0078BD] focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold uppercase text-slate-700 mb-1">
                    Interval (Seconds)
                  </label>
                  <input
                    type="number"
                    min={10}
                    max={86400}
                    value={formData.interval_seconds}
                    onChange={(e) =>
                      setFormData({ ...formData, interval_seconds: parseInt(e.target.value) || 1800 })
                    }
                    className="w-full text-xs px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-[#0078BD] focus:outline-none"
                  />
                  <span className="text-[10px] text-slate-400 mt-0.5 block">
                    Default: 1800s (30 minutes)
                  </span>
                </div>

                <div>
                  <label className="block text-xs font-bold uppercase text-slate-700 mb-1">
                    Timeout (Seconds)
                  </label>
                  <input
                    type="number"
                    min={1}
                    max={120}
                    value={formData.timeout_seconds}
                    onChange={(e) =>
                      setFormData({ ...formData, timeout_seconds: parseInt(e.target.value) || 10 })
                    }
                    className="w-full text-xs px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-[#0078BD] focus:outline-none"
                  />
                  <span className="text-[10px] text-slate-400 mt-0.5 block">Default: 10s</span>
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold uppercase text-slate-700 mb-1">
                  Expected HTTP Status Codes
                </label>
                <input
                  type="text"
                  value={formData.expected_status_codes}
                  onChange={(e) =>
                    setFormData({ ...formData, expected_status_codes: e.target.value })
                  }
                  placeholder="200,201,202,204"
                  className="w-full text-xs px-3 py-2 font-mono border border-slate-300 rounded-lg focus:ring-2 focus:ring-[#0078BD] focus:outline-none"
                />
              </div>

              {/* Unlimited Developer Assignment Checkboxes (Requirement 1 & 2) */}
              <div>
                <label className="block text-xs font-bold uppercase text-slate-700 mb-1">
                  Assign Developers (Receive Outage Alerts)
                </label>
                <div className="border border-slate-200 rounded-lg max-h-36 overflow-y-auto p-2 space-y-1.5 bg-slate-50/50">
                  {developers.length === 0 ? (
                    <div className="text-[11px] text-slate-400 p-2">
                      No developers registered yet. Add them in Settings.
                    </div>
                  ) : (
                    developers.map((dev) => {
                      const isAssigned = formData.developer_ids.includes(dev.id);
                      return (
                        <div
                          key={dev.id}
                          onClick={() => toggleDevSelection(dev.id)}
                          className={`flex items-center justify-between p-2 rounded cursor-pointer text-xs transition-colors ${
                            isAssigned
                              ? 'bg-indigo-50 text-[#583896] font-bold border border-indigo-200'
                              : 'bg-white hover:bg-slate-100 text-slate-700 border border-slate-100'
                          }`}
                        >
                          <div className="flex items-center space-x-2">
                            <div
                              className={`w-4 h-4 rounded flex items-center justify-center border ${
                                isAssigned
                                  ? 'bg-gradient-to-r from-[#0078BD] to-[#583896] border-[#0078BD] text-white'
                                  : 'border-slate-300'
                              }`}
                            >
                              {isAssigned && <Check className="w-3 h-3" />}
                            </div>
                            <span>{dev.full_name}</span>
                            <span className="text-slate-400 font-normal">({dev.email})</span>
                          </div>
                        </div>
                      );
                    })
                  )}
                </div>
              </div>

              <div className="flex items-center justify-end space-x-3 pt-4 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setModalOpen(false)}
                  className="px-4 py-2 text-xs font-bold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="px-5 py-2 text-xs font-bold text-white bg-gradient-to-r from-[#0078BD] via-[#583896] to-[#BE185D] hover:opacity-95 rounded-lg shadow-adani transition-opacity disabled:opacity-50"
                >
                  {saving ? 'Saving...' : editingProject ? 'Update Website' : 'Create & Probe Now'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={deleteConfirmOpen}
        title="Delete Monitored Website"
        message={`Are you sure you want to permanently delete '${projectToDelete?.name}'? All monitoring checks, uptime history, and incidents will be removed.`}
        confirmLabel="Delete Website"
        isDangerous={true}
        onConfirm={handleDelete}
        onCancel={() => setDeleteConfirmOpen(false)}
      />
    </div>
  );
};
