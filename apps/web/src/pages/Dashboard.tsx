import React from 'react';
import { Typography, Paper, Grid } from '@mui/material';
import { useAuth } from '../features/auth/AuthProvider';

export const Dashboard = () => {
    const { user } = useAuth();

    return (
        <div>
            <Typography variant="h4" gutterBottom>
                Dashboard
            </Typography>
            <Typography variant="body1" paragraph>
                Welcome back, {user?.full_name || user?.email}!
            </Typography>

            <Grid container spacing={3}>
                <Grid item xs={12} md={6} lg={4}>
                    <Paper sx={{ p: 2, display: 'flex', flexDirection: 'column', height: 140 }}>
                        <Typography variant="h6" color="primary" gutterBottom>
                            Recent Emails
                        </Typography>
                        <Typography component="p" variant="h4">
                            0
                        </Typography>
                        <Typography color="text.secondary" sx={{ flex: 1 }}>
                            Unread
                        </Typography>
                    </Paper>
                </Grid>
                {/* More widgets can go here */}
            </Grid>
        </div>
    );
};
