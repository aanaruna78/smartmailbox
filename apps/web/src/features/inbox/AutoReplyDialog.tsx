import React, { useState, useEffect, useCallback } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Typography,
  Box,
  CircularProgress,
  Alert,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  IconButton,
} from '@mui/material';
import { AutoAwesome, Send, Close, Edit, Block } from '@mui/icons-material';
import { generateAutoReply, sendGmailReply, GmailMessage } from '../../api/gmail';

// Cache for auto-replies to persist during session
const replyCache = new Map<string, { text: string; tone: string; timestamp: number }>();
const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

interface AutoReplyDialogProps {
  open: boolean;
  onClose: () => void;
  email: GmailMessage | null;
  onSuccess?: () => void;
}

export const AutoReplyDialog: React.FC<AutoReplyDialogProps> = ({
  open,
  onClose,
  email,
  onSuccess,
}) => {
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [replyText, setReplyText] = useState('');
  const [isEditing, setIsEditing] = useState(false);
  const [tone, setTone] = useState('professional');
  const [instructions, setInstructions] = useState('');
  const [generated, setGenerated] = useState(false);
  const [fromCache, setFromCache] = useState(false);
  const [loadingStatus, setLoadingStatus] = useState('');

  const handleGenerateReply = useCallback(async () => {
    if (!email) return;

    // Check cache first
    const cacheKey = `${email.id}-${tone}-${instructions}`;
    const cached = replyCache.get(cacheKey);
    if (cached && Date.now() - cached.timestamp < CACHE_DURATION) {
      setReplyText(cached.text);
      setGenerated(true);
      setIsEditing(false);
      setFromCache(true);
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);
    setFromCache(false);
    setReplyText('');

    try {
      // Show progress status
      setLoadingStatus('AI is generating your reply...');

      // Pass email content to skip Gmail API fetch on backend
      const response = await generateAutoReply(email.id, tone, instructions, {
        subject: email.subject || '',
        sender: email.sender || '',
        body: email.body || email.snippet || '',
      });

      setReplyText(response.reply_text);
      setGenerated(true);

      // Store in cache
      replyCache.set(cacheKey, {
        text: response.reply_text,
        tone: tone,
        timestamp: Date.now(),
      });
      setIsEditing(false);
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || 'Failed to generate reply');
    } finally {
      setLoading(false);
      setLoadingStatus('');
    }
  }, [email, tone, instructions]);

  const handleApply = async () => {
    if (!email || !replyText.trim()) return;
    setSending(true);
    setError(null);

    try {
      await sendGmailReply(email.id, replyText);
      setSuccess('Reply sent successfully!');

      // Clear cache for this email after sending
      replyCache.delete(`${email.id}-${tone}-${instructions}`);

      setTimeout(() => {
        onSuccess?.();
        handleClose();
      }, 1500);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to send reply');
    } finally {
      setSending(false);
    }
  };

  const handleDeny = () => {
    handleClose();
  };

  const handleEdit = () => {
    setIsEditing(true);
    setFromCache(false); // User is editing, so mark as modified
  };

  const handleClose = () => {
    setReplyText('');
    setInstructions('');
    setError(null);
    setSuccess(null);
    setGenerated(false);
    setIsEditing(false);
    setFromCache(false);
    onClose();
  };

  // Auto-generate when dialog opens or tone changes
  useEffect(() => {
    if (open && email) {
      handleGenerateReply();
    }
  }, [open, email, handleGenerateReply]);

  const extractSenderName = (sender: string) => {
    const match = sender.match(/^([^<]+)/);
    if (match) return match[1].trim().replace(/"/g, '');
    return sender;
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <AutoAwesome color="primary" />
          <Typography variant="h6">AI Auto-Reply</Typography>
          {fromCache && (
            <Typography variant="caption" color="text.secondary" sx={{ ml: 1 }}>
              (cached)
            </Typography>
          )}
        </Box>
        <IconButton onClick={handleClose} size="small">
          <Close />
        </IconButton>
      </DialogTitle>

      <DialogContent dividers>
        {email && (
          <Box sx={{ mb: 2, p: 2, bgcolor: 'action.hover', borderRadius: 1 }}>
            <Typography variant="body2" color="text.secondary">
              Replying to:
            </Typography>
            <Typography variant="subtitle2">{extractSenderName(email.sender)}</Typography>
            <Typography variant="body2" color="text.secondary">
              Subject: {email.subject || '(No Subject)'}
            </Typography>
          </Box>
        )}

        <Box sx={{ mb: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
            <FormControl size="small" sx={{ minWidth: 150 }}>
              <InputLabel>Tone</InputLabel>
              <Select
                value={tone}
                label="Tone"
                onChange={(e) => {
                  setTone(e.target.value);
                  setGenerated(false); // Trigger regeneration
                }}
                disabled={loading}
              >
                <MenuItem value="professional">Professional</MenuItem>
                <MenuItem value="friendly">Friendly</MenuItem>
                <MenuItem value="assertive">Assertive</MenuItem>
                <MenuItem value="urgent">Urgent</MenuItem>
              </Select>
            </FormControl>
            <TextField
              size="small"
              label="Additional Instructions"
              placeholder="e.g., Mention the discount, Ask for a meeting..."
              value={instructions}
              onChange={(e) => setInstructions(e.target.value)}
              disabled={loading}
              sx={{ flexGrow: 1 }}
            />
            <Button
              variant="outlined"
              startIcon={loading ? <CircularProgress size={16} /> : <AutoAwesome />}
              onClick={handleGenerateReply}
              disabled={loading}
              size="small"
            >
              {generated ? 'Regenerate' : 'Generate'}
            </Button>
          </Box>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {success && (
          <Alert severity="success" sx={{ mb: 2 }}>
            {success}
          </Alert>
        )}

        {loading ? (
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', py: 4 }}>
            <CircularProgress />
            <Typography sx={{ mt: 2, fontWeight: 500 }}>
              {loadingStatus || 'Generating AI reply...'}
            </Typography>
          </Box>
        ) : (
          <TextField
            fullWidth
            multiline
            minRows={10}
            maxRows={20}
            value={replyText}
            onChange={(e) => setReplyText(e.target.value)}
            disabled={!isEditing && generated}
            placeholder="AI-generated reply will appear here..."
            sx={{
              '& .MuiInputBase-root': {
                fontFamily: 'inherit',
                bgcolor: isEditing ? 'background.paper' : 'action.hover',
              },
            }}
          />
        )}
      </DialogContent>

      <DialogActions sx={{ p: 2, gap: 1 }}>
        <Button
          variant="outlined"
          color="error"
          startIcon={<Block />}
          onClick={handleDeny}
          disabled={sending}
        >
          Deny
        </Button>
        <Button
          variant="outlined"
          startIcon={<Edit />}
          onClick={handleEdit}
          disabled={!generated || sending || isEditing}
        >
          Edit
        </Button>
        <Button
          variant="contained"
          color="success"
          startIcon={sending ? <CircularProgress size={16} color="inherit" /> : <Send />}
          onClick={handleApply}
          disabled={!replyText.trim() || sending || loading}
        >
          {sending ? 'Sending...' : 'Apply & Send'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};
