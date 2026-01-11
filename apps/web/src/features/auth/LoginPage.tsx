import React from 'react';
import { GoogleLogin, CredentialResponse } from '@react-oauth/google';
import { Box, Paper, Typography, useTheme } from '@mui/material';
import { useAuth } from './AuthProvider';
import { config } from '../../config';

export const LoginPage = () => {
    const { login } = useAuth();
    const theme = useTheme();

    const handleSuccess = async (credentialResponse: CredentialResponse) => {
        if (credentialResponse.credential) {
            try {
                const res = await fetch(`${config.api.baseUrl}/auth/google/login`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ token: credentialResponse.credential }),
                });

                if (res.ok) {
                    login(); // Trigger re-fetch of user
                } else {
                    console.error('Login failed');
                }
            } catch (error) {
                console.error('Login error', error);
            }
        }
    };

    return (
        <Box
            sx={{
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                minHeight: '80vh',
            }}
        >
            <Paper
                elevation={3}
                sx={{
                    p: 4,
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    maxWidth: 400,
                    width: '100%',
                    borderRadius: 4,
                    backdropFilter: 'blur(10px)',
                    backgroundColor: theme.palette.mode === 'dark' ? 'rgba(30, 41, 59, 0.7)' : 'rgba(255, 255, 255, 0.8)',
                }}
            >
                <Typography component="h1" variant="h4" gutterBottom fontWeight="bold" color="primary">
                    Welcome Back
                </Typography>
                <Typography variant="body1" color="text.secondary" sx={{ mb: 4, textAlign: 'center' }}>
                    Sign in to access your smart mailbox dashboard.
                </Typography>

                <Box sx={{ mt: 2 }}>
                    <GoogleLogin
                        onSuccess={handleSuccess}
                        onError={() => console.log('Login Failed')}
                        theme={theme.palette.mode === 'dark' ? 'filled_black' : 'outline'}
                        shape="pill"
                    />
                </Box>
            </Paper>
        </Box>
    );
};
