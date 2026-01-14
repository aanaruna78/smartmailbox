import http from './http';

/**
 * Gmail API types matching backend response
 */
export interface GmailMessage {
  id: string;
  thread_id: string;
  subject: string;
  sender: string;
  to: string;
  date: string;
  snippet: string;
  body: string;
  labels: string[];
  is_read: boolean;
}

export interface GmailInboxResponse {
  messages: GmailMessage[];
  count: number;
  nextPageToken?: string;
}

export interface GmailStats {
  connected: boolean;
  unread_count: number;
  user_email?: string;
  error?: string;
}

export interface AutoReplyResponse {
  message_id: string;
  original_subject: string;
  original_sender: string;
  reply_text: string;
  tone: string;
}

export interface SendReplyResponse {
  success: boolean;
  message: string;
  to: string;
  subject: string;
}

/**
 * Get Gmail inbox messages with pagination
 */
export const getGmailInbox = async (
  maxResults: number = 50,
  pageToken?: string,
): Promise<GmailInboxResponse> => {
  const params: Record<string, any> = { max_results: maxResults };
  if (pageToken) {
    params.page_token = pageToken;
  }
  const response = await http.get('/gmail/inbox', { params });
  return response.data;
};

/**
 * Get a specific Gmail message by ID
 */
export const getGmailMessage = async (messageId: string): Promise<GmailMessage> => {
  const response = await http.get(`/gmail/message/${messageId}`);
  return response.data;
};

/**
 * Get Gmail inbox statistics
 */
export const getGmailStats = async (): Promise<GmailStats> => {
  const response = await http.get('/gmail/stats');
  return response.data;
};

/**
 * Generate an AI auto-reply for a message
 * Pass email content to skip slow Gmail API fetch on backend
 */
export const generateAutoReply = async (
  messageId: string,
  tone: string = 'professional',
  instructions?: string,
  emailContent?: { subject: string; sender: string; body: string },
): Promise<AutoReplyResponse> => {
  const payload: Record<string, any> = { tone, instructions };
  if (emailContent) {
    payload.subject = emailContent.subject;
    payload.sender = emailContent.sender;
    payload.body = emailContent.body;
  }
  const response = await http.post(`/gmail/auto-reply/${messageId}`, payload);
  return response.data;
};

/**
 * Send a reply to a Gmail message
 */
export const sendGmailReply = async (
  messageId: string,
  body: string,
  subject?: string,
): Promise<SendReplyResponse> => {
  const response = await http.post(`/gmail/send-reply/${messageId}`, { body, subject });
  return response.data;
};
