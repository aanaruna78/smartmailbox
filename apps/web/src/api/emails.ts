import http from './http';

export interface Attachment {
  id: number;
  filename: string;
  content_type: string;
  size: number;
}

export interface Tag {
  id: number;
  name: string;
  color: string;
}

export interface Email {
  id: number;
  mailbox_id: number;
  message_id: string;
  sender: string;
  recipients?: any;
  subject: string;
  folder: string;
  is_read: boolean;
  is_flagged: boolean;
  received_at: string;
  created_at: string;
  assigned_user_id?: number;
  attachments: Attachment[];
  tags: Tag[];
}

export interface EmailDetail extends Email {
  body_text?: string;
  body_html?: string;
}

export interface EmailListResponse {
  items: Email[];
  total: number;
  page: number;
  size: number;
}

export const getEmails = async (params: {
  page?: number;
  size?: number;
  mailbox_id?: number;
  folder?: string;
  is_read?: boolean;
  q?: string;
}): Promise<EmailListResponse> => {
  const response = await http.get('/emails', { params });
  return response.data;
};

export const getEmail = async (id: number): Promise<EmailDetail> => {
  const response = await http.get(`/emails/${id}`);
  return response.data;
};

export const assignEmail = async (id: number, userId: number): Promise<void> => {
  await http.post(`/emails/${id}/assign`, { user_id: userId });
};

export const addTag = async (id: number, name: string, color?: string): Promise<Tag> => {
  const response = await http.post(`/emails/${id}/tags`, { name, color });
  return response.data;
};

export const removeTag = async (id: number, tagId: number): Promise<void> => {
  await http.delete(`/emails/${id}/tags/${tagId}`);
};

// Draft Types
export interface JobResponse {
  id: number;
  type: string;
  status: string;
  result?: any;
  error?: string;
}

export interface Draft {
  id: number;
  email_id: number;
  content: string;
  is_accepted: boolean;
  approval_status?: string; // pending, approved, rejected, not_required
  confidence_score?: number;
  created_at: string;
  updated_at: string;
}

// APIs
export const generateDraftJob = async (
  id: number,
  instructions: string,
  tone: string,
): Promise<{ job_id: number; status: string }> => {
  const response = await http.post(`/emails/${id}/draft-job`, { instructions, tone });
  return response.data;
};

export const getJobStatus = async (jobId: number): Promise<JobResponse> => {
  const response = await http.get(`/jobs/${jobId}`);
  return response.data;
};

export const getDrafts = async (emailId: number): Promise<Draft[]> => {
  const response = await http.get(`/emails/${emailId}/drafts`);
  return response.data;
};

export const updateDraft = async (
  draftId: number,
  content: string,
  is_accepted?: boolean,
): Promise<Draft> => {
  const response = await http.put(`/drafts/${draftId}`, { content, is_accepted });
  return response.data;
};

// Send Email
export const sendEmail = async (
  emailId: number,
  recipient: string,
  subject: string,
  body_html?: string,
  body_text?: string,
): Promise<{ message: string; job_id: number }> => {
  const response = await http.post(`/emails/${emailId}/send`, {
    recipient,
    subject,
    body_html,
    body_text,
  });
  return response.data;
};

// Audit Logs
export interface AuditLog {
  id: number;
  user_id?: number;
  event_type: string;
  timestamp: string;
  details?: any;
  ip_address?: string;
  user_agent?: string;
}

// Audit Logs
export const getAuditLogs = async (): Promise<AuditLog[]> => {
  const response = await http.get('/audit/');
  return response.data;
};

// Bulk Actions
export const bulkGenerateDrafts = async (
  emailIds: number[],
  instructions: string,
  tone: string,
): Promise<{ message: string; job_id: number }> => {
  const response = await http.post('/jobs/bulk-draft', { email_ids: emailIds, instructions, tone });
  return response.data;
};
