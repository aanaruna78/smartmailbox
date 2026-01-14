import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
  Chip,
  Box,
  CircularProgress,
} from '@mui/material';
import { Warning, CheckCircle, Block, Send } from '@mui/icons-material';
import { getDrafts, sendEmail, Draft } from '../../api/emails';

interface BulkPreviewDialogProps {
  open: boolean;
  onClose: () => void;
  emailIds: number[];
  onComplete: () => void;
}

interface PreviewItem {
  emailId: number;
  draft: Draft | null;
  status: 'ready' | 'pending_approval' | 'blocked' | 'no_draft';
  statusMessage: string;
}

export const BulkPreviewDialog: React.FC<BulkPreviewDialogProps> = ({
  open,
  onClose,
  emailIds,
  onComplete,
}) => {
  const [items, setItems] = useState<PreviewItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);

  useEffect(() => {
    if (open && emailIds.length > 0) {
      loadPreviews();
    }
  }, [open, emailIds]);

  const loadPreviews = async () => {
    setLoading(true);
    const previews: PreviewItem[] = [];

    for (const emailId of emailIds) {
      try {
        const drafts = await getDrafts(emailId);
        const latestDraft = drafts.length > 0 ? drafts[drafts.length - 1] : null;

        if (!latestDraft) {
          previews.push({
            emailId,
            draft: null,
            status: 'no_draft',
            statusMessage: 'No draft available',
          });
        } else if (latestDraft.approval_status === 'pending') {
          previews.push({
            emailId,
            draft: latestDraft,
            status: 'pending_approval',
            statusMessage: 'Awaiting approval',
          });
        } else if (latestDraft.approval_status === 'rejected') {
          previews.push({
            emailId,
            draft: latestDraft,
            status: 'blocked',
            statusMessage: 'Draft rejected',
          });
        } else {
          previews.push({
            emailId,
            draft: latestDraft,
            status: 'ready',
            statusMessage: 'Ready to send',
          });
        }
      } catch (error) {
        previews.push({
          emailId,
          draft: null,
          status: 'no_draft',
          statusMessage: 'Error loading draft',
        });
      }
    }

    setItems(previews);
    setLoading(false);
  };

  const handleSendAll = async () => {
    setSending(true);
    const readyItems = items.filter((i) => i.status === 'ready' && i.draft);

    for (const item of readyItems) {
      if (item.draft) {
        try {
          // TODO: Get recipient/subject from email details
          // For now, this is a placeholder
          await sendEmail(item.emailId, 'recipient@example.com', 'Re: Subject', item.draft.content);
        } catch (error) {
          console.error(`Failed to send email ${item.emailId}`, error);
        }
      }
    }

    setSending(false);
    onComplete();
    onClose();
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'ready':
        return <CheckCircle color="success" />;
      case 'pending_approval':
        return <Warning color="warning" />;
      case 'blocked':
      case 'no_draft':
        return <Block color="error" />;
      default:
        return undefined;
    }
  };

  const readyCount = items.filter((i) => i.status === 'ready').length;

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Send color="primary" />
          Bulk Send Preview
        </Box>
      </DialogTitle>
      <DialogContent>
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
            <CircularProgress />
          </Box>
        ) : (
          <>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              {readyCount} of {items.length} emails ready to send.
            </Typography>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Email ID</TableCell>
                  <TableCell>Draft Preview</TableCell>
                  <TableCell>Status</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {items.map((item) => (
                  <TableRow key={item.emailId}>
                    <TableCell>#{item.emailId}</TableCell>
                    <TableCell>
                      {item.draft ? item.draft.content.substring(0, 50) + '...' : <em>No draft</em>}
                    </TableCell>
                    <TableCell>
                      <Chip
                        icon={getStatusIcon(item.status)}
                        label={item.statusMessage}
                        size="small"
                        color={
                          item.status === 'ready'
                            ? 'success'
                            : item.status === 'pending_approval'
                            ? 'warning'
                            : 'error'
                        }
                        variant="outlined"
                      />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          variant="contained"
          onClick={handleSendAll}
          disabled={sending || readyCount === 0}
          startIcon={sending ? <CircularProgress size={20} /> : <Send />}
        >
          {sending ? 'Sending...' : `Send ${readyCount} Emails`}
        </Button>
      </DialogActions>
    </Dialog>
  );
};
