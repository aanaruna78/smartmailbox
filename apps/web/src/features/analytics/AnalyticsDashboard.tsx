import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  CircularProgress,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  LinearProgress,
} from '@mui/material';
import {
  Analytics,
  Timer,
  Inbox,
  SmartToy,
  Send,
  Edit,
  CheckCircle,
  Warning,
  Error,
} from '@mui/icons-material';
import http from '../../api/http';

interface DashboardData {
  period_days: number;
  sla: {
    total_received: number;
    backlog: number;
    backlog_rate: number;
    avg_response_time_hours: number;
    responses_under_1h: number;
    responses_under_4h: number;
    responses_under_24h: number;
    total_responses: number;
  };
  ai_usage: {
    total_drafts_generated: number;
    drafts_accepted: number;
    acceptance_rate: number;
    total_emails_sent: number;
    edit_rate: number;
    generation_jobs: {
      total: number;
      completed: number;
      failed: number;
      success_rate: number;
    };
  };
  highlights: {
    backlog_status: string;
    response_time_status: string;
    ai_adoption: string;
  };
}

const StatusIcon: React.FC<{ status: string }> = ({ status }) => {
  switch (status) {
    case 'good':
    case 'high':
      return <CheckCircle color="success" />;
    case 'warning':
    case 'medium':
      return <Warning color="warning" />;
    default:
      return <Error color="error" />;
  }
};

export const AnalyticsDashboard: React.FC = () => {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [days, setDays] = useState(7);

  useEffect(() => {
    fetchData();
  }, [days]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const response = await http.get(`/analytics/dashboard?days=${days}`);
      setData(response.data);
    } catch (error) {
      console.error('Failed to fetch analytics', error);
    }
    setLoading(false);
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (!data) {
    return <Typography color="error">Failed to load analytics</Typography>;
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Analytics color="primary" sx={{ fontSize: 32 }} />
          <Typography variant="h4">Analytics Dashboard</Typography>
        </Box>
        <FormControl size="small" sx={{ minWidth: 120 }}>
          <InputLabel>Period</InputLabel>
          <Select value={days} label="Period" onChange={(e) => setDays(Number(e.target.value))}>
            <MenuItem value={7}>7 days</MenuItem>
            <MenuItem value={14}>14 days</MenuItem>
            <MenuItem value={30}>30 days</MenuItem>
            <MenuItem value={90}>90 days</MenuItem>
          </Select>
        </FormControl>
      </Box>

      {/* Status Highlights */}
      <Paper sx={{ p: 2, mb: 3, display: 'flex', gap: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <StatusIcon status={data.highlights.backlog_status} />
          <Typography>Backlog: {data.highlights.backlog_status}</Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <StatusIcon status={data.highlights.response_time_status} />
          <Typography>Response Time: {data.highlights.response_time_status}</Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <StatusIcon status={data.highlights.ai_adoption} />
          <Typography>AI Adoption: {data.highlights.ai_adoption}</Typography>
        </Box>
      </Paper>

      <Grid container spacing={3}>
        {/* SLA Metrics */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography
              variant="h6"
              gutterBottom
              sx={{ display: 'flex', alignItems: 'center', gap: 1 }}
            >
              <Timer /> SLA Metrics
            </Typography>

            <Grid container spacing={2}>
              <Grid item xs={6}>
                <Card variant="outlined">
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Inbox color="primary" />
                      <Typography variant="h4">{data.sla.total_received}</Typography>
                    </Box>
                    <Typography variant="body2" color="text.secondary">
                      Emails Received
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={6}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography
                      variant="h4"
                      color={data.sla.backlog_rate > 30 ? 'error' : 'inherit'}
                    >
                      {data.sla.backlog}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Backlog ({data.sla.backlog_rate}%)
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12}>
                <Typography variant="subtitle2" gutterBottom>
                  Avg Response Time
                </Typography>
                <Typography variant="h5">{data.sla.avg_response_time_hours} hours</Typography>
              </Grid>
              <Grid item xs={12}>
                <Typography variant="subtitle2" gutterBottom>
                  Response Time Distribution
                </Typography>
                <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                  <Chip
                    label={`< 1h: ${data.sla.responses_under_1h}`}
                    color="success"
                    size="small"
                  />
                  <Chip label={`< 4h: ${data.sla.responses_under_4h}`} color="info" size="small" />
                  <Chip
                    label={`< 24h: ${data.sla.responses_under_24h}`}
                    color="warning"
                    size="small"
                  />
                </Box>
              </Grid>
            </Grid>
          </Paper>
        </Grid>

        {/* AI Usage Metrics */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography
              variant="h6"
              gutterBottom
              sx={{ display: 'flex', alignItems: 'center', gap: 1 }}
            >
              <SmartToy /> AI Usage Metrics
            </Typography>

            <Grid container spacing={2}>
              <Grid item xs={6}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="h4">{data.ai_usage.total_drafts_generated}</Typography>
                    <Typography variant="body2" color="text.secondary">
                      Drafts Generated
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={6}>
                <Card variant="outlined">
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Send color="success" />
                      <Typography variant="h4">{data.ai_usage.total_emails_sent}</Typography>
                    </Box>
                    <Typography variant="body2" color="text.secondary">
                      Emails Sent
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12}>
                <Typography variant="subtitle2" gutterBottom>
                  Acceptance Rate
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <LinearProgress
                    variant="determinate"
                    value={data.ai_usage.acceptance_rate}
                    sx={{ flex: 1, height: 10, borderRadius: 1 }}
                    color={data.ai_usage.acceptance_rate > 70 ? 'success' : 'warning'}
                  />
                  <Typography>{data.ai_usage.acceptance_rate}%</Typography>
                </Box>
              </Grid>
              <Grid item xs={6}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Edit />
                  <Box>
                    <Typography variant="h6">{data.ai_usage.edit_rate}%</Typography>
                    <Typography variant="caption" color="text.secondary">
                      Edit Rate
                    </Typography>
                  </Box>
                </Box>
              </Grid>
              <Grid item xs={6}>
                <Typography variant="caption" color="text.secondary">
                  Job Success Rate
                </Typography>
                <Typography variant="h6">{data.ai_usage.generation_jobs.success_rate}%</Typography>
              </Grid>
            </Grid>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};
