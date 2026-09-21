export interface User {
  id: number;
  email: string;
  full_name: string;
  role: 'ADMIN' | 'USER';
  is_active: boolean;
  created_at: string;
  assigned_project_ids?: number[];
  assigned_projects_count?: number;
}

export interface DeveloperSummary {
  id: number;
  full_name: string;
  email: string;
  role: string;
}

export interface Project {
  id: number;
  name: string;
  description?: string;
  url: string;
  interval_seconds: number;
  timeout_seconds: number;
  expected_status_codes: string;
  is_enabled: boolean;
  created_at: string;
  updated_at: string;
  developers: DeveloperSummary[];
  developer_count: number;
}

export interface ProjectCardData {
  id: number;
  name: string;
  description?: string;
  url: string;
  is_enabled: boolean;
  interval_seconds: number;
  timeout_seconds: number;
  current_status: 'UP' | 'DOWN' | 'WARNING' | 'PAUSED' | 'PENDING';
  http_status?: number;
  response_time_ms?: number;
  last_checked?: string;
  uptime_percentage: number;
  developer_count: number;
  incident_count: number;
  ssl_valid?: boolean;
  ssl_days_remaining?: number;
}

export interface DashboardMetrics {
  total_projects: number;
  up_count: number;
  down_count: number;
  warning_count: number;
  total_incidents: number;
  total_downtime_seconds: number;
  total_downtime_formatted: string;
}

export interface Incident {
  id: number;
  project_id: number;
  project_name?: string;
  started_at: string;
  resolved_at?: string;
  duration_seconds?: number;
  duration_formatted?: string;
  error_type: string;
  http_status?: number;
  error_message?: string;
  is_resolved: boolean;
}

export interface MonitoringLog {
  id: number;
  project_id: number;
  project_name?: string;
  timestamp: string;
  status: string;
  http_status?: number;
  response_time_ms?: number;
  error_type?: string;
  error_message?: string;
  redirect_url?: string;
  ssl_valid?: boolean;
  ssl_days_remaining?: number;
  ssl_issuer?: string;
  incident_id?: number;
}

export interface PaginatedLogs {
  items: MonitoringLog[];
  total: number;
  page: number;
  size: number;
  total_pages: number;
}

export interface HeatmapBlock {
  timestamp: string;
  label: string;
  status: 'UP' | 'DOWN' | 'WARNING' | 'NO_DATA';
  response_time_ms?: number;
  http_status?: number;
  error_type?: string;
}

export interface ChartPoint {
  timestamp: string;
  label: string;
  response_time_ms?: number;
  uptime_pct?: number;
  incident_count?: number;
}

export interface ErrorStat {
  error_type: string;
  count: number;
  percentage: number;
}

export interface ProjectAnalytics {
  project_id: number;
  project_name: string;
  range_start: string;
  range_end: string;
  range_label: string;
  uptime_pct: number;
  downtime_pct: number;
  total_uptime_seconds: number;
  total_downtime_seconds: number;
  total_uptime_formatted: string;
  total_downtime_formatted: string;
  incident_count: number;
  avg_incident_duration_seconds: number;
  avg_incident_duration_formatted: string;
  longest_incident_seconds: number;
  longest_incident_formatted: string;
  avg_response_time_ms: number;
  max_response_time_ms: number;
  successful_checks: number;
  failed_checks: number;
  warning_checks: number;
  total_checks: number;
  heatmap_blocks: HeatmapBlock[];
  response_time_chart: ChartPoint[];
  error_distribution: ErrorStat[];
}

export interface ProjectComparison {
  project_id: number;
  project_name: string;
  uptime_pct: number;
  downtime_seconds: number;
  downtime_formatted: string;
  incident_count: number;
  avg_response_time_ms: number;
}

export interface GlobalAnalytics {
  range_start: string;
  range_end: string;
  range_label: string;
  overall_uptime_pct: number;
  total_downtime_seconds: number;
  total_downtime_formatted: string;
  total_incidents: number;
  avg_response_time_ms: number;
  total_errors: number;
  total_projects: number;
  project_comparisons: ProjectComparison[];
  error_distribution: ErrorStat[];
  response_time_trends: any[];
}

export interface SystemHealth {
  monitoring_worker: 'ONLINE' | 'OFFLINE';
  database: 'CONNECTED' | 'DISCONNECTED';
  database_dialect: string;
  database_latency_ms: number;
  email: 'AVAILABLE' | 'SIMULATED' | 'ERROR';
  last_monitoring_cycle?: string;
  last_worker_heartbeat?: string;
  enabled_projects_count: number;
  total_projects_count: number;
  active_incidents_count: number;
}
