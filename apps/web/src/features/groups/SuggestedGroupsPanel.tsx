import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Button,
  Chip,
  CircularProgress,
  IconButton,
  Collapse,
  Divider,
} from '@mui/material';
import { AutoAwesome, ExpandMore, ExpandLess, Tag, Reply } from '@mui/icons-material';
import http from '../../api/http';

interface GroupSuggestion {
  cluster_id: number;
  topic: string;
  email_count: number;
  email_ids: number[];
  sample_subjects: string[];
}

interface SuggestedGroupsPanelProps {
  mailboxId?: number;
  onAcceptGroup: (emailIds: number[], topic: string) => void;
}

export const SuggestedGroupsPanel: React.FC<SuggestedGroupsPanelProps> = ({
  mailboxId,
  onAcceptGroup,
}) => {
  const [suggestions, setSuggestions] = useState<GroupSuggestion[]>([]);
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState<number | null>(null);
  const [accepting, setAccepting] = useState<number | null>(null);

  const fetchSuggestions = async () => {
    setLoading(true);
    try {
      const params = mailboxId ? `?mailbox_id=${mailboxId}` : '';
      const response = await http.get(`/groups/groups/suggest${params}`);
      setSuggestions(response.data);
    } catch (error) {
      console.error('Failed to fetch group suggestions', error);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchSuggestions();
  }, [mailboxId]);

  const handleAcceptGroup = async (suggestion: GroupSuggestion) => {
    setAccepting(suggestion.cluster_id);

    try {
      // Apply tag to all emails in group
      const tagName = suggestion.topic.toLowerCase().replace(/\s+/g, '-');
      await http.post('/emails/bulk-tag', {
        email_ids: suggestion.email_ids,
        tag_name: tagName,
      });

      // Trigger bulk draft flow
      onAcceptGroup(suggestion.email_ids, suggestion.topic);
    } catch (error) {
      console.error('Failed to accept group', error);
    }

    setAccepting(null);
  };

  const toggleExpand = (clusterId: number) => {
    setExpanded(expanded === clusterId ? null : clusterId);
  };

  if (loading) {
    return (
      <Paper sx={{ p: 2, textAlign: 'center' }}>
        <CircularProgress size={24} />
        <Typography variant="body2" sx={{ mt: 1 }}>
          Analyzing emails...
        </Typography>
      </Paper>
    );
  }

  if (suggestions.length === 0) {
    return (
      <Paper sx={{ p: 2, textAlign: 'center', color: 'text.secondary' }}>
        <AutoAwesome sx={{ fontSize: 40, mb: 1, opacity: 0.5 }} />
        <Typography variant="body2">No group suggestions available yet.</Typography>
      </Paper>
    );
  }

  return (
    <Paper sx={{ overflow: 'hidden' }}>
      <Box
        sx={{
          p: 2,
          bgcolor: 'primary.main',
          color: 'white',
          display: 'flex',
          alignItems: 'center',
          gap: 1,
        }}
      >
        <AutoAwesome />
        <Typography variant="h6">Suggested Groups</Typography>
        <Chip
          label={suggestions.length}
          size="small"
          sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: 'white' }}
        />
      </Box>

      <List disablePadding>
        {suggestions.map((suggestion, index) => (
          <React.Fragment key={suggestion.cluster_id}>
            {index > 0 && <Divider />}
            <ListItem
              sx={{
                flexDirection: 'column',
                alignItems: 'stretch',
                py: 2,
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                <Box sx={{ flex: 1 }}>
                  <Typography variant="subtitle1" fontWeight="bold">
                    {suggestion.topic}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {suggestion.email_count} emails
                  </Typography>
                </Box>
                <IconButton size="small" onClick={() => toggleExpand(suggestion.cluster_id)}>
                  {expanded === suggestion.cluster_id ? <ExpandLess /> : <ExpandMore />}
                </IconButton>
              </Box>

              <Collapse in={expanded === suggestion.cluster_id}>
                <Box sx={{ mt: 1, pl: 1 }}>
                  <Typography variant="caption" color="text.secondary">
                    Sample emails:
                  </Typography>
                  {suggestion.sample_subjects.map((subject, i) => (
                    <Typography key={i} variant="body2" sx={{ ml: 1 }}>
                      • {subject}
                    </Typography>
                  ))}
                </Box>
              </Collapse>

              <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
                <Button
                  size="small"
                  variant="outlined"
                  startIcon={<Tag />}
                  onClick={() => handleAcceptGroup(suggestion)}
                  disabled={accepting === suggestion.cluster_id}
                >
                  {accepting === suggestion.cluster_id ? 'Applying...' : 'Tag & Draft'}
                </Button>
                <Button
                  size="small"
                  variant="contained"
                  startIcon={<Reply />}
                  onClick={() => onAcceptGroup(suggestion.email_ids, suggestion.topic)}
                >
                  Bulk Reply
                </Button>
              </Box>
            </ListItem>
          </React.Fragment>
        ))}
      </List>
    </Paper>
  );
};
