import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Select,
  MenuItem,
  Typography,
  Box,
  CircularProgress,
} from '@mui/material';
import { AutoAwesome } from '@mui/icons-material';
import { bulkGenerateDrafts } from '../../api/emails';

interface BulkDraftDialogProps {
  open: boolean;
  onClose: () => void;
  selectedCount: number;
  emailIds: number[];
  onSuccess: () => void;
}

export const BulkDraftDialog: React.FC<BulkDraftDialogProps> = ({
  open,
  onClose,
  selectedCount,
  emailIds,
  onSuccess,
}) => {
  const [instructions, setInstructions] = useState('');
  const [tone, setTone] = useState('professional');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleGenerate = async () => {
    setIsSubmitting(true);
    try {
      await bulkGenerateDrafts(emailIds, instructions, tone);
      alert('Bulk draft generation started!');
      onSuccess();
      onClose();
    } catch (error) {
      console.error('Failed to start bulk generation', error);
      alert('Failed to start bulk generation');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <AutoAwesome color="primary" />
        Bulk Draft Generation
      </DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Generating drafts for <strong>{selectedCount}</strong> selected emails. They will not be
          sent automatically. You can review them individually.
        </Typography>

        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <TextField
            label="Instructions"
            multiline
            rows={3}
            placeholder="e.g. Apologize for the delay and offer a 10% discount."
            value={instructions}
            onChange={(e) => setInstructions(e.target.value)}
            fullWidth
          />
          <Select value={tone} onChange={(e) => setTone(e.target.value)} fullWidth size="small">
            <MenuItem value="professional">Professional</MenuItem>
            <MenuItem value="friendly">Friendly</MenuItem>
            <MenuItem value="assertive">Assertive</MenuItem>
            <MenuItem value="urgent">Urgent</MenuItem>
          </Select>
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          variant="contained"
          onClick={handleGenerate}
          disabled={isSubmitting || !instructions}
          startIcon={
            isSubmitting ? <CircularProgress size={20} color="inherit" /> : <AutoAwesome />
          }
        >
          {isSubmitting ? 'Starting...' : 'Generate Drafts'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};
