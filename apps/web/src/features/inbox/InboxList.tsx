import React, { useEffect, useState, useRef, useCallback } from 'react';
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
  Alert,
  Button,
  IconButton,
  Tooltip,
} from '@mui/material';
import { Refresh, MailOutline, AutoAwesome } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { getGmailInbox, GmailMessage } from '../../api/gmail';
import { AutoReplyDialog } from './AutoReplyDialog';
import { useNotification } from '../../context/NotificationContext';

export const InboxList = () => {
  const navigate = useNavigate();
  const [emails, setEmails] = useState<GmailMessage[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notConnected, setNotConnected] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [nextPageToken, setNextPageToken] = useState<string | undefined>(undefined);

  // Auto-reply dialog state
  const [autoReplyOpen, setAutoReplyOpen] = useState(false);
  const [selectedEmail, setSelectedEmail] = useState<GmailMessage | null>(null);

  // Polling ref
  const pollingRef = useRef<NodeJS.Timeout | null>(null);
  const isFetchingRef = useRef<boolean>(false);

  const { showNotification } = useNotification();

  const fetchEmails = useCallback(async (showLoading = true) => {
    if (isFetchingRef.current) return;
    isFetchingRef.current = true;
    if (showLoading) setLoading(true);
    setError(null);
    setNotConnected(false);
    try {
      const data = await getGmailInbox(50);

      // Check for new emails if this is a background refresh
      if (!showLoading && emails.length > 0 && data.messages.length > emails.length) {
        const diff = data.messages.length - emails.length;
        showNotification(`You have ${diff} new email(s)!`, 'info');
      } else if (!showLoading && emails.length > 0 && data.messages[0]?.id !== emails[0]?.id) {
        // Even if count is same, check if first email changed
        showNotification(`You have new emails!`, 'info');
      }

      setEmails(data.messages);
      setNextPageToken(data.nextPageToken);
      setLastUpdated(new Date());
    } catch (err: any) {
      const errorMessage = err?.response?.data?.detail || err.message || 'Failed to fetch emails';
      if (errorMessage.includes('not connected') || errorMessage.includes('Gmail not connected')) {
        setNotConnected(true);
      } else {
        setError(errorMessage);
      }
    } finally {
      if (showLoading) setLoading(false);
      isFetchingRef.current = false;
    }
  }, []);

  const loadMore = async () => {
    if (!nextPageToken || loadingMore) return;
    setLoadingMore(true);
    try {
      const data = await getGmailInbox(50, nextPageToken);
      setEmails((prev) => [...prev, ...data.messages]);
      setNextPageToken(data.nextPageToken);
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Failed to load more emails');
    } finally {
      setLoadingMore(false);
    }
  };

  // Initial fetch and setup polling
  useEffect(() => {
    fetchEmails();

    // Start polling every 30 seconds for new emails
    pollingRef.current = setInterval(() => {
      fetchEmails(false); // Silent refresh
    }, 30000);

    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
      }
    };
  }, [fetchEmails]);

  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      const now = new Date();
      const isToday = date.toDateString() === now.toDateString();

      if (isToday) {
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      }
      return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
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

  const handleAutoReplyClick = (e: React.MouseEvent, email: GmailMessage) => {
    e.stopPropagation();
    setSelectedEmail(email);
    setAutoReplyOpen(true);
  };

  const handleAutoReplyClose = () => {
    setAutoReplyOpen(false);
    setSelectedEmail(null);
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
        <CircularProgress />
        <Typography sx={{ ml: 2 }}>Loading your Gmail inbox...</Typography>
      </Box>
    );
  }

  if (notConnected) {
    return (
      <Box sx={{ textAlign: 'center', py: 8 }}>
        <MailOutline sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
        <Typography variant="h5" gutterBottom>
          Gmail Not Connected
        </Typography>
        <Typography color="text.secondary" sx={{ mb: 3 }}>
          Please sign in with Google and grant Gmail access to view your inbox.
        </Typography>
        <Button variant="contained" onClick={() => navigate('/login')}>
          Connect Gmail
        </Button>
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ py: 4 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
        <Button startIcon={<Refresh />} onClick={() => fetchEmails()}>
          Try Again
        </Button>
      </Box>
    );
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Inbox</Typography>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          {lastUpdated && (
            <Typography variant="caption" color="text.secondary">
              Updated {lastUpdated.toLocaleTimeString()}
            </Typography>
          )}
          <Chip label={`${emails.length} emails`} size="small" variant="outlined" />
          <Button startIcon={<Refresh />} onClick={() => fetchEmails()} size="small">
            Refresh
          </Button>
        </Box>
      </Box>

      {emails.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <MailOutline sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
          <Typography color="text.secondary">Your inbox is empty</Typography>
        </Paper>
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell sx={{ fontWeight: 600 }}>From</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Subject</TableCell>
                <TableCell sx={{ fontWeight: 600, width: 100 }}>Date</TableCell>
                <TableCell sx={{ fontWeight: 600, width: 80 }}>Status</TableCell>
                <TableCell sx={{ fontWeight: 600, width: 80, textAlign: 'center' }}>
                  <Tooltip title="AI Auto-Reply">
                    <AutoAwesome fontSize="small" color="primary" />
                  </Tooltip>
                </TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {emails.map((email) => (
                <TableRow
                  key={email.id}
                  hover
                  onClick={() => navigate(`/inbox/${email.id}`)}
                  sx={{
                    cursor: 'pointer',
                    backgroundColor: !email.is_read ? 'action.hover' : 'inherit',
                  }}
                >
                  <TableCell sx={{ fontWeight: !email.is_read ? 600 : 400 }}>
                    {extractSenderName(email.sender)}
                  </TableCell>
                  <TableCell>
                    <Box sx={{ fontWeight: !email.is_read ? 600 : 400 }}>
                      {email.subject || '(No Subject)'}
                    </Box>
                    <Typography
                      variant="body2"
                      color="text.secondary"
                      sx={{
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                        maxWidth: 400,
                      }}
                    >
                      {email.snippet}
                    </Typography>
                  </TableCell>
                  <TableCell sx={{ whiteSpace: 'nowrap' }}>{formatDate(email.date)}</TableCell>
                  <TableCell>
                    {!email.is_read && <Chip label="New" color="primary" size="small" />}
                  </TableCell>
                  <TableCell sx={{ textAlign: 'center' }}>
                    <Tooltip title="Generate AI Reply">
                      <IconButton
                        size="small"
                        color="secondary"
                        onClick={(e) => handleAutoReplyClick(e, email)}
                        sx={{
                          background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
                          color: 'white',
                          '&:hover': {
                            background: 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)',
                          },
                        }}
                      >
                        <AutoAwesome fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* Load More Button */}
      {nextPageToken && !loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
          <Button
            variant="outlined"
            onClick={loadMore}
            disabled={loadingMore}
            startIcon={loadingMore ? <CircularProgress size={16} /> : null}
          >
            {loadingMore ? 'Loading...' : 'Load More Emails'}
          </Button>
        </Box>
      )}

      {/* Auto-Reply Dialog */}
      <AutoReplyDialog
        open={autoReplyOpen}
        onClose={handleAutoReplyClose}
        email={selectedEmail}
        onSuccess={() => fetchEmails()}
      />
    </Box>
  );
};
