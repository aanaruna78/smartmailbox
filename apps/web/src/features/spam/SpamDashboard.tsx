import React, { useState, useEffect } from 'react';
import {
    Box,
    Paper,
    Typography,
    Grid,
    Card,
    CardContent,
    CircularProgress,
    Chip,
    LinearProgress
} from '@mui/material';
import { Security, Warning, CheckCircle, Block, TrendingUp } from '@mui/icons-material';
import http from '../../api/http';

interface SpamStats {
    total: number;
    pending: number;
    released: number;
    confirmed_spam: number;
    deleted: number;
    avg_score: number;
    by_label: { clean: number; suspicious: number; spam: number };
}

export const SpamDashboard: React.FC = () => {
    const [stats, setStats] = useState<SpamStats | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchStats();
    }, []);

    const fetchStats = async () => {
        try {
            const response = await http.get('/quarantine/stats');
            setStats(response.data);
        } catch (error) {
            console.error('Failed to fetch spam stats', error);
        }
        setLoading(false);
    };

    if (loading) {
        return (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                <CircularProgress />
            </Box>
        );
    }

    if (!stats) {
        return <Typography color="error">Failed to load stats</Typography>;
    }

    const totalProcessed = stats.released + stats.confirmed_spam + stats.deleted;
    const releaseRate = totalProcessed > 0 ? (stats.released / totalProcessed * 100) : 0;

    return (
        <Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
                <Security color="primary" sx={{ fontSize: 32 }} />
                <Typography variant="h4">Spam Dashboard</Typography>
            </Box>

            <Grid container spacing={3}>
                {/* Summary Cards */}
                <Grid item xs={12} md={3}>
                    <Card sx={{ bgcolor: 'warning.light', color: 'warning.contrastText' }}>
                        <CardContent>
                            <Typography variant="h3">{stats.pending}</Typography>
                            <Typography>Pending Review</Typography>
                        </CardContent>
                    </Card>
                </Grid>
                <Grid item xs={12} md={3}>
                    <Card sx={{ bgcolor: 'success.light', color: 'success.contrastText' }}>
                        <CardContent>
                            <Typography variant="h3">{stats.released}</Typography>
                            <Typography>Released</Typography>
                        </CardContent>
                    </Card>
                </Grid>
                <Grid item xs={12} md={3}>
                    <Card sx={{ bgcolor: 'error.light', color: 'error.contrastText' }}>
                        <CardContent>
                            <Typography variant="h3">{stats.confirmed_spam}</Typography>
                            <Typography>Confirmed Spam</Typography>
                        </CardContent>
                    </Card>
                </Grid>
                <Grid item xs={12} md={3}>
                    <Card>
                        <CardContent>
                            <Typography variant="h3">{stats.avg_score}</Typography>
                            <Typography>Avg Score</Typography>
                        </CardContent>
                    </Card>
                </Grid>

                {/* Detection Breakdown */}
                <Grid item xs={12} md={6}>
                    <Paper sx={{ p: 3 }}>
                        <Typography variant="h6" gutterBottom>Detection Breakdown</Typography>
                        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                            <Chip
                                icon={<CheckCircle />}
                                label={`Clean: ${stats.by_label.clean}`}
                                color="success"
                            />
                            <Chip
                                icon={<Warning />}
                                label={`Suspicious: ${stats.by_label.suspicious}`}
                                color="warning"
                            />
                            <Chip
                                icon={<Block />}
                                label={`Spam: ${stats.by_label.spam}`}
                                color="error"
                            />
                        </Box>

                        <Box sx={{ mt: 3 }}>
                            <Typography variant="body2" color="text.secondary" gutterBottom>
                                Total Processed: {stats.total}
                            </Typography>
                            <LinearProgress
                                variant="determinate"
                                value={(stats.by_label.spam / (stats.total || 1)) * 100}
                                color="error"
                                sx={{ height: 8, borderRadius: 1 }}
                            />
                            <Typography variant="caption" color="text.secondary">
                                {((stats.by_label.spam / (stats.total || 1)) * 100).toFixed(1)}% spam rate
                            </Typography>
                        </Box>
                    </Paper>
                </Grid>

                {/* Resolution Stats */}
                <Grid item xs={12} md={6}>
                    <Paper sx={{ p: 3 }}>
                        <Typography variant="h6" gutterBottom>Resolution Stats</Typography>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                            <TrendingUp color="success" />
                            <Typography variant="h4">{releaseRate.toFixed(1)}%</Typography>
                            <Typography color="text.secondary">Release Rate</Typography>
                        </Box>
                        <Typography variant="body2" color="text.secondary">
                            {stats.released} emails released out of {totalProcessed} processed
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                            {stats.deleted} emails permanently deleted
                        </Typography>
                    </Paper>
                </Grid>
            </Grid>
        </Box>
    );
};
