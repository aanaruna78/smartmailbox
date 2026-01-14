import React, { useEffect } from 'react';
import { useGoogleLogin } from '@react-oauth/google';
import { Box, Paper, Typography, useTheme, Button } from '@mui/material';
import { Google } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from './AuthProvider';
import { config } from '../../config';

export const LoginPage = () => {
  const { login, isAuthenticated } = useAuth();
  const theme = useTheme();
  const navigate = useNavigate();

  useEffect(() => {
    if (isAuthenticated) {
      navigate('/', { replace: true });
    }
  }, [isAuthenticated, navigate]);

  const handleGoogleLogin = useGoogleLogin({
    onSuccess: async (tokenResponse) => {
      try {
        // Send the access token to backend for Gmail access
        const res = await fetch(`${config.api.baseUrl}/auth/google/oauth`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            access_token: tokenResponse.access_token,
            scope: tokenResponse.scope,
          }),
          credentials: 'include',
        });

        if (res.ok) {
          const data = await res.json();
          if (data.access_token) {
            localStorage.setItem('token', data.access_token);
          }
          await login(); // Trigger re-fetch of user
          navigate('/', { replace: true });
        } else {
          console.error('Login failed');
        }
      } catch (error) {
        console.error('Login error', error);
      }
    },
    onError: () => console.log('Login Failed'),
    scope: 'email profile https://www.googleapis.com/auth/gmail.readonly',
    flow: 'implicit',
  });

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
          backgroundColor:
            theme.palette.mode === 'dark' ? 'rgba(30, 41, 59, 0.7)' : 'rgba(255, 255, 255, 0.8)',
        }}
      >
        <Box
          component="img"
          src="/ai-logo.png"
          alt="AI Smart Mailbox"
          sx={{ width: 80, height: 80, mb: 2 }}
        />
        <Typography component="h1" variant="h4" gutterBottom fontWeight="bold" color="primary">
          Welcome Back
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 4, textAlign: 'center' }}>
          Sign in with Google to access your AI-powered mailbox.
        </Typography>

        <Button
          variant="contained"
          size="large"
          startIcon={<Google />}
          onClick={() => handleGoogleLogin()}
          sx={{
            py: 1.5,
            px: 4,
            borderRadius: 3,
            background: 'linear-gradient(135deg, #4285F4 0%, #34A853 50%, #FBBC05 100%)',
            '&:hover': {
              background: 'linear-gradient(135deg, #357ABD 0%, #2E8B57 50%, #E0A800 100%)',
            },
          }}
        >
          Sign in with Google
        </Button>

        <Typography variant="caption" color="text.secondary" sx={{ mt: 3, textAlign: 'center' }}>
          By signing in, you grant access to your Gmail inbox for AI-powered email management.
        </Typography>
      </Paper>
    </Box>
  );
};
