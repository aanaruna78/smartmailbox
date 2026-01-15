import http from './http';

export interface SLAMetrics {
  period_days: number;
  total_received: number;
  backlog: number;
  backlog_rate: number;
  avg_response_time_hours: number;
  responses_under_1h: number;
  responses_under_4h: number;
  responses_under_24h: number;
  total_responses: number;
  overall_total?: number;
  overall_unread?: number;
}

export interface AIUsageMetrics {
  period_days: number;
  total_drafts_generated: number;
  drafts_accepted: number;
  acceptance_rate: number;
  total_emails_sent: number;
  edit_rate: number;
  generation_jobs: {
    total: number;
    completed: number;
    failed: number;
    success_rate: number;
  };
}

export interface Highlights {
  backlog_status: string;
  response_time_status: string;
  ai_adoption: string;
}

export interface DashboardSummary {
  period_days: number;
  sla: SLAMetrics;
  ai_usage: AIUsageMetrics;
  highlights: Highlights;
}

export const getDashboardSummary = async (days: number = 7): Promise<DashboardSummary> => {
  const response = await http.get('/analytics/dashboard', { params: { days } });
  return response.data;
};
