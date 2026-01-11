import React, { useEffect, useState } from 'react';
import {
    Typography, Paper, Table, TableBody, TableCell, TableHead, TableRow,
    Select, MenuItem, Switch, TableContainer, SelectChangeEvent, Alert, Snackbar,
    Box, Tabs, Tab
} from '@mui/material';
import { config } from '../config';

interface User {
    id: number;
    email: string;
    role: string;
    is_active: boolean;
    full_name: string;
}

import { getAuditLogs, AuditLog } from '../api/emails';

export const AdminDashboard = () => {
    const [users, setUsers] = useState<User[]>([]);
    const [logs, setLogs] = useState<AuditLog[]>([]);
    const [tab, setTab] = useState(0);
    const [notification, setNotification] = useState<{ message: string, type: 'success' | 'error' } | null>(null);

    const fetchUsers = async () => {
        try {
            const res = await fetch(`${config.api.baseUrl}/admin/users`);
            if (res.ok) {
                setUsers(await res.json());
            }
        } catch (error) {
            console.error(error);
        }
    };

    const fetchLogs = async () => {
        try {
            const fetched = await getAuditLogs();
            setLogs(fetched);
        } catch (error) {
            console.error("Failed to fetch logs", error);
        }
    };

    useEffect(() => {
        fetchUsers();
        fetchLogs();
    }, []);

    const handleUpdate = async (userId: number, updates: Partial<User>) => {
        try {
            const res = await fetch(`${config.api.baseUrl}/admin/users/${userId}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(updates),
            });

            if (res.ok) {
                setUsers(users.map(u => u.id === userId ? { ...u, ...updates } : u));
                setNotification({ message: 'User updated successfully', type: 'success' });
            } else {
                setNotification({ message: 'Failed to update user', type: 'error' });
            }
        } catch (error) {
            setNotification({ message: 'Error updating user', type: 'error' });
        }
    };

    return (
        <div>
            <Typography variant="h4" gutterBottom>
                Admin Console
            </Typography>

            <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
                <Tabs value={tab} onChange={(e, v) => setTab(v)}>
                    <Tab label="Users" />
                    <Tab label="Audit Logs" />
                </Tabs>
            </Box>

            {tab === 0 && (
                <TableContainer component={Paper}>
                    <Table>
                        <TableHead>
                            <TableRow>
                                <TableCell>ID</TableCell>
                                <TableCell>Full Name</TableCell>
                                <TableCell>Email</TableCell>
                                <TableCell>Role</TableCell>
                                <TableCell>Status</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {users.map((user) => (
                                <TableRow key={user.id}>
                                    <TableCell>{user.id}</TableCell>
                                    <TableCell>{user.full_name}</TableCell>
                                    <TableCell>{user.email}</TableCell>
                                    <TableCell>
                                        <Select
                                            size="small"
                                            value={user.role}
                                            onChange={(e: SelectChangeEvent) =>
                                                handleUpdate(user.id, { role: e.target.value })
                                            }
                                        >
                                            <MenuItem value="user">User</MenuItem>
                                            <MenuItem value="admin">Admin</MenuItem>
                                        </Select>
                                    </TableCell>
                                    <TableCell>
                                        <Switch
                                            checked={user.is_active}
                                            onChange={(e) =>
                                                handleUpdate(user.id, { is_active: e.target.checked })
                                            }
                                            color="primary"
                                        />
                                        {user.is_active ? "Active" : "Disabled"}
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </TableContainer>
            )}

            {tab === 1 && (
                <TableContainer component={Paper}>
                    <Table>
                        <TableHead>
                            <TableRow>
                                <TableCell>Timestamp</TableCell>
                                <TableCell>User ID</TableCell>
                                <TableCell>Event</TableCell>
                                <TableCell>Details</TableCell>
                                <TableCell>IP</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {logs.map((log) => (
                                <TableRow key={log.id}>
                                    <TableCell>{new Date(log.timestamp).toLocaleString()}</TableCell>
                                    <TableCell>{log.user_id}</TableCell>
                                    <TableCell>{log.event_type}</TableCell>
                                    <TableCell>
                                        <pre style={{ margin: 0, fontSize: '0.75rem' }}>
                                            {JSON.stringify(log.details, null, 2)}
                                        </pre>
                                    </TableCell>
                                    <TableCell>{log.ip_address}</TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </TableContainer>
            )}

            <Snackbar
                open={!!notification}
                autoHideDuration={6000}
                onClose={() => setNotification(null)}
            >
                <Alert severity={notification?.type as any} onClose={() => setNotification(null)}>
                    {notification?.message}
                </Alert>
            </Snackbar>
        </div>
    );
};
