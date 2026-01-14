import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TableContainer,
  Button,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControlLabel,
  Checkbox,
  CircularProgress,
  Tooltip,
} from '@mui/material';
import { CheckCircle, Block, Delete, Refresh, Visibility, Security } from '@mui/icons-material';
import http from '../../api/http';

interface QuarantineEntry {
  id: number;
  email_id: number;
  mailbox_id: number;
  spam_score: number;
  spam_label: string;
  reasons: string;
  status: string;
  quarantined_at: string;
}

export const QuarantineReviewPage: React.FC = () => {
  const [entries, setEntries] = useState<QuarantineEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedEntry, setSelectedEntry] = useState<QuarantineEntry | null>(null);
  const [dialogType, setDialogType] = useState<'release' | 'confirm' | null>(null);
  const [notes, setNotes] = useState('');
  const [addToList, setAddToList] = useState(false);
  const [processing, setProcessing] = useState(false);

  useEffect(() => {
    fetchQueue();
  }, []);

  const fetchQueue = async () => {
    setLoading(true);
    try {
      const response = await http.get('/quarantine/queue');
      setEntries(response.data);
    } catch (error) {
      console.error('Failed to fetch quarantine queue', error);
    }
    setLoading(false);
  };

  const handleRelease = async () => {
    if (!selectedEntry) return;
    setProcessing(true);
    try {
      await http.post(`/quarantine/${selectedEntry.id}/release`, {
        notes,
        add_to_allowlist: addToList,
      });
      setEntries(entries.filter((e) => e.id !== selectedEntry.id));
      closeDialog();
    } catch (error) {
      console.error('Failed to release', error);
    }
    setProcessing(false);
  };

  const handleConfirmSpam = async () => {
    if (!selectedEntry) return;
    setProcessing(true);
    try {
      await http.post(`/quarantine/${selectedEntry.id}/confirm-spam`, {
        notes,
        add_to_blocklist: addToList,
      });
      setEntries(entries.filter((e) => e.id !== selectedEntry.id));
      closeDialog();
    } catch (error) {
      console.error('Failed to confirm spam', error);
    }
    setProcessing(false);
  };

  const handleDelete = async (entry: QuarantineEntry) => {
    if (!confirm('Permanently delete this email?')) return;
    try {
      await http.delete(`/quarantine/${entry.id}`);
      setEntries(entries.filter((e) => e.id !== entry.id));
    } catch (error) {
      console.error('Failed to delete', error);
    }
  };

  const openDialog = (entry: QuarantineEntry, type: 'release' | 'confirm') => {
    setSelectedEntry(entry);
    setDialogType(type);
    setNotes('');
    setAddToList(false);
  };

  const closeDialog = () => {
    setSelectedEntry(null);
    setDialogType(null);
  };

  const getLabelColor = (label: string) => {
    switch (label) {
      case 'spam':
        return 'error';
      case 'suspicious':
        return 'warning';
      default:
        return 'success';
    }
  };

  const parseReasons = (reasons: string) => {
    try {
      return JSON.parse(reasons);
    } catch {
      return [reasons];
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Security color="primary" />
          <Typography variant="h4">Quarantine Review</Typography>
          <Chip label={entries.length} color="warning" size="small" />
        </Box>
        <Button startIcon={<Refresh />} onClick={fetchQueue}>
          Refresh
        </Button>
      </Box>

      {entries.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <CheckCircle sx={{ fontSize: 60, color: 'success.main', mb: 2 }} />
          <Typography variant="h6">All clear!</Typography>
          <Typography color="text.secondary">No emails pending review</Typography>
        </Paper>
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Score</TableCell>
                <TableCell>Label</TableCell>
                <TableCell>Email ID</TableCell>
                <TableCell>Quarantined</TableCell>
                <TableCell>Reasons</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {entries.map((entry) => (
                <TableRow key={entry.id}>
                  <TableCell>
                    <Typography
                      fontWeight="bold"
                      color={
                        entry.spam_score >= 60
                          ? 'error'
                          : entry.spam_score >= 30
                          ? 'warning.main'
                          : 'success.main'
                      }
                    >
                      {entry.spam_score}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={entry.spam_label}
                      color={getLabelColor(entry.spam_label) as any}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>#{entry.email_id}</TableCell>
                  <TableCell>{new Date(entry.quarantined_at).toLocaleDateString()}</TableCell>
                  <TableCell sx={{ maxWidth: 300 }}>
                    <Tooltip title={parseReasons(entry.reasons).join(', ')}>
                      <Typography variant="body2" noWrap>
                        {parseReasons(entry.reasons).slice(0, 2).join(', ')}
                        {parseReasons(entry.reasons).length > 2 && '...'}
                      </Typography>
                    </Tooltip>
                  </TableCell>
                  <TableCell align="right">
                    <Tooltip title="Release">
                      <IconButton color="success" onClick={() => openDialog(entry, 'release')}>
                        <CheckCircle />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Confirm Spam">
                      <IconButton color="error" onClick={() => openDialog(entry, 'confirm')}>
                        <Block />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Delete">
                      <IconButton onClick={() => handleDelete(entry)}>
                        <Delete />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* Action Dialog */}
      <Dialog open={!!dialogType} onClose={closeDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          {dialogType === 'release' ? 'Release from Quarantine' : 'Confirm as Spam'}
        </DialogTitle>
        <DialogContent>
          <TextField
            label="Notes (optional)"
            fullWidth
            multiline
            rows={2}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            sx={{ mt: 2 }}
          />
          <FormControlLabel
            control={
              <Checkbox checked={addToList} onChange={(e) => setAddToList(e.target.checked)} />
            }
            label={dialogType === 'release' ? 'Add sender to allowlist' : 'Add sender to blocklist'}
            sx={{ mt: 1 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={closeDialog}>Cancel</Button>
          <Button
            variant="contained"
            color={dialogType === 'release' ? 'success' : 'error'}
            onClick={dialogType === 'release' ? handleRelease : handleConfirmSpam}
            disabled={processing}
          >
            {processing ? (
              <CircularProgress size={20} />
            ) : dialogType === 'release' ? (
              'Release'
            ) : (
              'Confirm Spam'
            )}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};
