const API_BASE = import.meta.env.VITE_API_BASE || '/api';

export class ApiError extends Error {
  status: number;
  data: any;
  constructor(message: string, status: number, data: any) {
    super(message);
    this.status = status;
    this.data = data;
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('adani_auth_token');
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    localStorage.removeItem('adani_auth_token');
    localStorage.removeItem('adani_auth_user');
    if (!window.location.pathname.includes('/login')) {
      window.location.href = '/login';
    }
  }

  if (!response.ok) {
    let errorData;
    try {
      errorData = await response.json();
    } catch {
      errorData = { detail: response.statusText };
    }
    const message = errorData.detail || 'API request failed';
    throw new ApiError(typeof message === 'string' ? message : JSON.stringify(message), response.status, errorData);
  }

  if (response.status === 204) {
    return null as unknown as T;
  }

  return response.json();
}

export const api = {
  // Auth
  login: (credentials: { email: string; password: string }) =>
    request<{ access_token: string; token_type: string; user: any }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    }),
  getMe: () => request<any>('/auth/me'),

  // Dashboard
  getDashboard: () => request<{ metrics: any; projects: any[] }>('/dashboard'),

  // Projects
  getProjects: () => request<any[]>('/projects'),
  getProject: (id: number) => request<any>(`/projects/${id}`),
  createProject: (data: any) =>
    request<any>('/projects', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  updateProject: (id: number, data: any) =>
    request<any>(`/projects/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
  deleteProject: (id: number) =>
    request<void>(`/projects/${id}`, {
      method: 'DELETE',
    }),
  toggleProject: (id: number) =>
    request<any>(`/projects/${id}/toggle`, {
      method: 'POST',
    }),
  testProject: (id: number) =>
    request<any>(`/projects/${id}/test`, {
      method: 'POST',
    }),

  // Developers & Users
  getDevelopers: () => request<any[]>('/developers'),
  createDeveloper: (data: any) =>
    request<any>('/developers', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  updateDeveloper: (id: number, data: any) =>
    request<any>(`/developers/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
  deleteDeveloper: (id: number) =>
    request<void>(`/developers/${id}`, {
      method: 'DELETE',
    }),

  // Incidents
  getIncidents: (params: { project_id?: number; is_resolved?: boolean; error_type?: string; limit?: number } = {}) => {
    const query = new URLSearchParams();
    if (params.project_id) query.append('project_id', String(params.project_id));
    if (params.is_resolved !== undefined) query.append('is_resolved', String(params.is_resolved));
    if (params.error_type) query.append('error_type', params.error_type);
    if (params.limit) query.append('limit', String(params.limit));
    return request<any[]>(`/incidents?${query.toString()}`);
  },

  // Logs
  getLogs: (params: { project_id?: number; status?: string; error_type?: string; page?: number; size?: number } = {}) => {
    const query = new URLSearchParams();
    if (params.project_id) query.append('project_id', String(params.project_id));
    if (params.status) query.append('status', params.status);
    if (params.error_type) query.append('error_type', params.error_type);
    if (params.page) query.append('page', String(params.page));
    if (params.size) query.append('size', String(params.size));
    return request<any>(`/logs?${query.toString()}`);
  },

  // Analytics
  getProjectAnalytics: (projectId: number, rangePreset: string = 'last_30_days') =>
    request<any>(`/analytics/project/${projectId}?range_preset=${rangePreset}`),
  getGlobalAnalytics: (rangePreset: string = 'last_30_days') =>
    request<any>(`/analytics/global?range_preset=${rangePreset}`),

  // Health
  getHealth: () => request<any>('/health'),

  // Settings
  getSettings: () => request<any>('/settings'),
  updateMonitoringSettings: (data: any) =>
    request<any>('/settings/monitoring', { method: 'PUT', body: JSON.stringify(data) }),
  updateEmailSettings: (data: any) =>
    request<any>('/settings/email', { method: 'PUT', body: JSON.stringify(data) }),
  updateDailyReportSettings: (data: any) =>
    request<any>('/settings/daily-report', { method: 'PUT', body: JSON.stringify(data) }),
  testEmail: (recipient: string) =>
    request<any>('/settings/test-email', { method: 'POST', body: JSON.stringify({ recipient }) }),
  sendDailyReportNow: (recipients?: string) =>
    request<any>('/settings/send-daily-report', { method: 'POST', body: JSON.stringify({ recipients }) }),
};
