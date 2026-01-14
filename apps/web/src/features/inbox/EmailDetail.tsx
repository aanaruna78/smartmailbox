import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Paper,
  Button,
  Divider,
  CircularProgress,
  Chip,
  Alert,
} from '@mui/material';
import { ArrowBack, Refresh } from '@mui/icons-material';
import { getGmailMessage, GmailMessage } from '../../api/gmail';

export const EmailDetail = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [email, setEmail] = useState<GmailMessage | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchEmail = async () => {
    if (!id) return;
    setLoading(true);
    setError(null);
    try {
      const data = await getGmailMessage(id);
      setEmail(data);
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Failed to load email');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEmail();
  }, [id]);

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleString();
    } catch {
      return dateString;
    }
  };

  const extractSenderName = (sender: string) => {
    const match = sender.match(/^([^<]+)/);
    if (match) {
      return match[1].trim().replace(/"/g, '');
    }
    return sender;
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
        <CircularProgress />
        <Typography sx={{ ml: 2 }}>Loading email...</Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ py: 4 }}>
        <Button startIcon={<ArrowBack />} onClick={() => navigate('/inbox')} sx={{ mb: 2 }}>
          Back to Inbox
        </Button>
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
        <Button startIcon={<Refresh />} onClick={fetchEmail}>
          Try Again
        </Button>
      </Box>
    );
  }

  if (!email) {
    return (
      <Box>
        <Button startIcon={<ArrowBack />} onClick={() => navigate('/inbox')} sx={{ mb: 2 }}>
          Back to Inbox
        </Button>
        <Typography>Email not found.</Typography>
      </Box>
    );
  }

  const renderBody = () => {
    // Check if body contains HTML
    const isHtml = email.body.includes('<') && email.body.includes('>');
    if (isHtml) {
      return (
        <Box
          dangerouslySetInnerHTML={{ __html: email.body }}
          sx={{
            p: 2,
            bgcolor: 'background.paper',
            border: '1px solid',
            borderColor: 'divider',
            borderRadius: 1,
            minHeight: 200,
            '& a': { color: 'primary.main' },
            '& img': { maxWidth: '100%' },
          }}
        />
      );
    }
    return (
      <Typography sx={{ whiteSpace: 'pre-wrap', p: 2 }}>{email.body || email.snippet}</Typography>
    );
  };

  return (
    <Box>
      <Button startIcon={<ArrowBack />} onClick={() => navigate('/inbox')} sx={{ mb: 2 }}>
        Back to Inbox
      </Button>

      <Paper sx={{ p: 3 }}>
        <Box sx={{ mb: 3 }}>
          <Typography variant="h5" gutterBottom sx={{ fontWeight: 600 }}>
            {email.subject || '(No Subject)'}
          </Typography>

          <Box sx={{ display: 'flex', gap: 1, mb: 2, flexWrap: 'wrap' }}>
            {email.labels.map((label) => (
              <Chip key={label} label={label} size="small" variant="outlined" />
            ))}
            {!email.is_read && <Chip label="Unread" color="primary" size="small" />}
          </Box>

          <Box sx={{ display: 'flex', justifyContent: 'space-between', color: 'text.secondary' }}>
            <Box>
              <Typography variant="body2" sx={{ fontWeight: 500 }}>
                From: {extractSenderName(email.sender)}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.8rem' }}>
                {email.sender}
              </Typography>
            </Box>
            <Typography variant="body2">{formatDate(email.date)}</Typography>
          </Box>
          {email.to && (
            <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
              To: {email.to}
            </Typography>
          )}
        </Box>

        <Divider sx={{ mb: 3 }} />

        {renderBody()}
      </Paper>
    </Box>
  );
};
