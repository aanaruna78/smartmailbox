import http from './http';

export interface Mailbox {
    id: number;
    user_id: number;
    email_address: string;
    provider: string;
    is_active: boolean;
    last_synced_at?: string;
    sync_status?: string;
    created_at: string;
    updated_at: string;
}

export const triggerSync = async (id: number): Promise<{ message: string, job_id: number }> => {
    const response = await http.post(`/mailboxes/${id}/sync`, {});
    return response.data;
};

export const getMailboxes = async (): Promise<Mailbox[]> => {
    const response = await http.get('/mailboxes');
    return response.data;
};

export const createMailbox = async (data: any): Promise<Mailbox> => {
    const response = await http.post('/mailboxes', data);
    return response.data;
};

export const deleteMailbox = async (id: number): Promise<void> => {
    await http.delete(`/mailboxes/${id}`);
};

export const testConnection = async (data: any): Promise<any> => {
    const response = await http.post('/mailboxes/test-connection', data);
    return response.data;
};
