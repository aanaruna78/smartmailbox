import React, { useState } from 'react';
import {
  Box,
  Typography,
  TextField,
  Button,
  Paper,
  Grid,
  MenuItem,
  Alert,
  CircularProgress,
  Divider,
  Stack,
} from '@mui/material';
import { Save, ArrowBack, CheckCircle, Error as ErrorIcon } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { createMailbox, testConnection } from '../../api/mailboxes';

const PROVIDERS = [
  { value: 'gmail', label: 'Gmail' },
  { value: 'outlook', label: 'Outlook' },
  { value: 'custom', label: 'Custom (IMAP/SMTP)' },
];

const INITIAL_FORM_STATE = {
  email_address: '',
  password: '',
  provider: 'custom',
  imap_host: '',
  imap_port: 993,
  smtp_host: '',
  smtp_port: 587,
};

export const MailboxForm = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState(INITIAL_FORM_STATE);
  const [loading, setLoading] = useState(false);
  const [testLoading, setTestLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [testResults, setTestResults] = useState<{
    imap?: { success: boolean; message: string };
    smtp?: { success: boolean; message: string };
  } | null>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => {
      const newData = { ...prev, [name]: value };

      // Auto-fill hosts for known providers
      if (name === 'provider') {
        if (value === 'gmail') {
          newData.imap_host = 'imap.gmail.com';
          newData.smtp_host = 'smtp.gmail.com';
        } else if (value === 'outlook') {
          newData.imap_host = 'outlook.office365.com';
          newData.smtp_host = 'smtp.office365.com';
        }
      }
      return newData;
    });
  };

  const handleTestConnection = async () => {
    setTestLoading(true);
    setTestResults(null);
    setError(null);
    try {
      const testData = {
        ...formData,
        imap_port: parseInt(formData.imap_port as any, 10),
        smtp_port: parseInt(formData.smtp_port as any, 10),
      };
      const results = await testConnection(testData);
      setTestResults(results);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to test connection. Please check your network or try again.');
      console.error(err);
    } finally {
      setTestLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      // Ensure ports are numbers
      const submissionData = {
        ...formData,
        imap_port: parseInt(formData.imap_port as any, 10),
        smtp_port: parseInt(formData.smtp_port as any, 10),
      };
      await createMailbox(submissionData);
      navigate('/mailboxes');
    } catch (err: any) {
      console.error('Submit error:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to create mailbox');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box maxWidth="md" sx={{ mx: 'auto' }}>
      <Box sx={{ mb: 3, display: 'flex', alignItems: 'center' }}>
        <Button startIcon={<ArrowBack />} onClick={() => navigate('/mailboxes')} sx={{ mr: 2 }}>
          Back
        </Button>
        <Typography variant="h4" component="h1">
          Connect New Mailbox
        </Typography>
      </Box>

      <Paper sx={{ p: 4 }}>
        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}

        <form onSubmit={handleSubmit}>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                Account Details
              </Typography>
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Email Address"
                name="email_address"
                type="email"
                value={formData.email_address}
                onChange={handleChange}
                required
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="App Password"
                name="password"
                type="password"
                value={formData.password}
                onChange={handleChange}
                required
                helperText="Use an App Password for Gmail/Outlook"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                select
                label="Provider"
                name="provider"
                value={formData.provider}
                onChange={handleChange}
              >
                {PROVIDERS.map((option) => (
                  <MenuItem key={option.value} value={option.value}>
                    {option.label}
                  </MenuItem>
                ))}
              </TextField>
            </Grid>

            <Grid item xs={12}>
              <Divider sx={{ my: 2 }} />
              <Typography variant="h6" gutterBottom>
                Server Settings
              </Typography>
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="IMAP Host"
                name="imap_host"
                value={formData.imap_host}
                onChange={handleChange}
                required
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="IMAP Port"
                name="imap_port"
                type="number"
                value={formData.imap_port}
                onChange={handleChange}
                required
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="SMTP Host"
                name="smtp_host"
                value={formData.smtp_host}
                onChange={handleChange}
                required
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="SMTP Port"
                name="smtp_port"
                type="number"
                value={formData.smtp_port}
                onChange={handleChange}
                required
              />
            </Grid>
          </Grid>

          {/* Test Results Display */}
          {testResults && (
            <Box sx={{ mt: 3, p: 2, bgcolor: 'background.default', borderRadius: 1 }}>
              <Typography variant="subtitle2" gutterBottom>
                Connection Test Results:
              </Typography>
              <Stack spacing={1}>
                {testResults.imap && (
                  <Box
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      color: testResults.imap.success ? 'success.main' : 'error.main',
                    }}
                  >
                    {testResults.imap.success ? (
                      <CheckCircle fontSize="small" sx={{ mr: 1 }} />
                    ) : (
                      <ErrorIcon fontSize="small" sx={{ mr: 1 }} />
                    )}
                    <Typography variant="body2">IMAP: {testResults.imap.message}</Typography>
                  </Box>
                )}
                {testResults.smtp && (
                  <Box
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      color: testResults.smtp.success ? 'success.main' : 'error.main',
                    }}
                  >
                    {testResults.smtp.success ? (
                      <CheckCircle fontSize="small" sx={{ mr: 1 }} />
                    ) : (
                      <ErrorIcon fontSize="small" sx={{ mr: 1 }} />
                    )}
                    <Typography variant="body2">SMTP: {testResults.smtp.message}</Typography>
                  </Box>
                )}
              </Stack>
            </Box>
          )}

          <Box sx={{ mt: 4, display: 'flex', justifyContent: 'flex-end', gap: 2 }}>
            <Button
              variant="outlined"
              onClick={handleTestConnection}
              disabled={testLoading || !formData.email_address || !formData.password}
            >
              {testLoading ? <CircularProgress size={24} /> : 'Test Connection'}
            </Button>
            <Button
              type="submit"
              variant="contained"
              size="large"
              disabled={loading}
              startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <Save />}
            >
              Save Mailbox
            </Button>
          </Box>
        </form>
      </Paper>
    </Box>
  );
};
