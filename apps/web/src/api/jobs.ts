import http from './http';

export interface Job {
  id: number;
  type: string;
  status: string; // pending, processing, completed, failed
  payload: any;
  result?: any;
  error?: string;
  attempts: number;
  next_retry_at?: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
}

export const getJobs = async (): Promise<Job[]> => {
  const response = await http.get('/jobs');
  return response.data;
};
