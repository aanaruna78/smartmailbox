import React from 'react';
import { Paper, Typography, Button, Box, IconButton } from '@mui/material';
import { Close, Reply, Visibility } from '@mui/icons-material';

interface BulkSelectionBarProps {
  selectedCount: number;
  onClear: () => void;
  onBulkReply: () => void;
  onPreview: () => void;
}

export const BulkSelectionBar: React.FC<BulkSelectionBarProps> = ({
  selectedCount,
  onClear,
  onBulkReply,
  onPreview,
}) => {
  if (selectedCount === 0) return null;

  return (
    <Paper
      elevation={6}
      sx={{
        position: 'fixed',
        bottom: 24,
        left: '50%',
        transform: 'translateX(-50%)',
        py: 1.5,
        px: 3,
        display: 'flex',
        alignItems: 'center',
        gap: 2,
        borderRadius: 3,
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        color: 'white',
        zIndex: 1300,
        minWidth: 400,
        justifyContent: 'space-between',
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Typography variant="body1" fontWeight="bold">
          {selectedCount} email{selectedCount !== 1 ? 's' : ''} selected
        </Typography>
      </Box>

      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Button
          variant="contained"
          size="small"
          startIcon={<Visibility />}
          onClick={onPreview}
          sx={{
            bgcolor: 'rgba(255,255,255,0.2)',
            '&:hover': { bgcolor: 'rgba(255,255,255,0.3)' },
          }}
        >
          Preview
        </Button>
        <Button
          variant="contained"
          size="small"
          startIcon={<Reply />}
          onClick={onBulkReply}
          sx={{
            bgcolor: 'rgba(255,255,255,0.2)',
            '&:hover': { bgcolor: 'rgba(255,255,255,0.3)' },
          }}
        >
          Generate Drafts
        </Button>
        <IconButton size="small" onClick={onClear} sx={{ color: 'white' }}>
          <Close />
        </IconButton>
      </Box>
    </Paper>
  );
};
