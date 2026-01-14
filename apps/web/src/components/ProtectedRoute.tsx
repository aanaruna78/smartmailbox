import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../features/auth/AuthProvider';
import { Box, CircularProgress } from '@mui/material';

export const ProtectedRoute = () => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <Box
        sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}
      >
        <CircularProgress />
      </Box>
    );
  }

  return isAuthenticated ? <Outlet /> : <Navigate to="/login" replace />;
};
