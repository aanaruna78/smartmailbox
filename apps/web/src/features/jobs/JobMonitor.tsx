import React, { useEffect, useState } from 'react';
import {
    Box,
    Typography,
    Paper,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Chip,
    CircularProgress,
    Button
} from '@mui/material';
import { Refresh } from '@mui/icons-material';
import { getJobs, Job } from '../../api/jobs';

export const JobMonitor = () => {
    const [jobs, setJobs] = useState<Job[]>([]);
    const [loading, setLoading] = useState(true);

    const fetchJobs = async () => {
        setLoading(true);
        try {
            const data = await getJobs();
            setJobs(data);
        } catch (error) {
            console.error("Failed to fetch jobs", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchJobs();
        const interval = setInterval(fetchJobs, 5000); // Auto-refresh every 5s
        return () => clearInterval(interval);
    }, []);

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'completed': return 'success';
            case 'failed': return 'error';
            case 'processing': return 'info';
            default: return 'default';
        }
    };

    return (
        <Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                <Typography variant="h4">Job Monitor</Typography>
                <Button startIcon={<Refresh />} onClick={fetchJobs}>Refresh</Button>
            </Box>

            {loading && jobs.length === 0 ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
                    <CircularProgress />
                </Box>
            ) : (
                <TableContainer component={Paper}>
                    <Table>
                        <TableHead>
                            <TableRow>
                                <TableCell>ID</TableCell>
                                <TableCell>Type</TableCell>
                                <TableCell>Status</TableCell>
                                <TableCell>Created At</TableCell>
                                <TableCell>Completed At</TableCell>
                                <TableCell>Attempts</TableCell>
                                <TableCell>Result/Error</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {jobs.map((job) => (
                                <TableRow key={job.id}>
                                    <TableCell>#{job.id}</TableCell>
                                    <TableCell>{job.type}</TableCell>
                                    <TableCell>
                                        <Chip label={job.status} color={getStatusColor(job.status)} size="small" />
                                    </TableCell>
                                    <TableCell>{new Date(job.created_at).toLocaleString()}</TableCell>
                                    <TableCell>{job.completed_at ? new Date(job.completed_at).toLocaleString() : '-'}</TableCell>
                                    <TableCell>{job.attempts}</TableCell>
                                    <TableCell sx={{ maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                        {job.error ? (
                                            <Typography color="error" variant="body2">{job.error}</Typography>
                                        ) : (
                                            JSON.stringify(job.result)
                                        )}
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </TableContainer>
            )}
        </Box>
    );
};
