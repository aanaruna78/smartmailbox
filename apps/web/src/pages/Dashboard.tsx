import React from 'react';
import { Typography, Paper, Grid, Box, alpha, useTheme, CircularProgress } from '@mui/material';
import { Email, Send, Inbox, TrendingUp, AutoAwesome } from '@mui/icons-material';
import { useAuth } from '../features/auth/AuthProvider';
import { getDashboardSummary, DashboardSummary } from '../api/analytics';

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle: string;
  icon: React.ReactNode;
  gradient: string;
}

const StatCard = ({ title, value, subtitle, icon, gradient }: StatCardProps) => {
  const theme = useTheme();
  return (
    <Paper
      sx={{
        p: 3,
        height: '100%',
        position: 'relative',
        overflow: 'hidden',
        cursor: 'pointer',
        '&:hover': {
          transform: 'translateY(-4px)',
          boxShadow: '0 12px 20px -8px rgba(0,0,0,0.15)',
        },
      }}
    >
      <Box
        sx={{
          position: 'absolute',
          top: -20,
          right: -20,
          width: 100,
          height: 100,
          borderRadius: '50%',
          background: gradient,
          opacity: 0.1,
        }}
      />
      <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
        <Box>
          <Typography variant="body2" color="text.secondary" fontWeight={500} gutterBottom>
            {title}
          </Typography>
          <Typography variant="h3" fontWeight={700} sx={{ mb: 0.5 }}>
            {value}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {subtitle}
          </Typography>
        </Box>
        <Box
          sx={{
            width: 48,
            height: 48,
            borderRadius: 3,
            background: gradient,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white',
          }}
        >
          {icon}
        </Box>
      </Box>
    </Paper>
  );
};

export const Dashboard = () => {
  const { user } = useAuth();
  const theme = useTheme();
  const [loading, setLoading] = React.useState(true);
  const [data, setData] = React.useState<DashboardSummary | null>(null);

  React.useEffect(() => {
    const fetchData = async () => {
      try {
        const summary = await getDashboardSummary();
        setData(summary);
      } catch (error) {
        console.error('Failed to fetch dashboard data', error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const stats = [
    {
      title: 'Total Emails',
      value: data?.sla.overall_total ?? 0,
      subtitle: `${data?.sla.total_received ?? 0} in last ${data?.period_days} days`,
      icon: <Email />,
      gradient: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
    },
    {
      title: 'Unread',
      value: data?.sla.overall_unread ?? 0,
      subtitle: `${data?.sla.backlog ?? 0} in last ${data?.period_days} days`,
      icon: <Inbox />,
      gradient: 'linear-gradient(135deg, #f59e0b 0%, #f97316 100%)',
    },
    {
      title: 'Sent Period',
      value: data?.ai_usage.total_emails_sent ?? 0,
      subtitle: 'Replies sent',
      icon: <Send />,
      gradient: 'linear-gradient(135deg, #14b8a6 0%, #10b981 100%)',
    },
    {
      title: 'AI Acceptance',
      value: `${data?.ai_usage.acceptance_rate ?? 0}%`,
      subtitle: 'Drafts accepted',
      icon: <AutoAwesome />,
      gradient: 'linear-gradient(135deg, #ec4899 0%, #f43f5e 100%)',
    },
  ];

  return (
    <Box>
      {/* Welcome Section */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" fontWeight={700} gutterBottom>
          Welcome back, {user?.full_name || user?.email?.split('@')[0]}! 👋
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Your AI assistant is ready to help manage your inbox today.
        </Typography>
      </Box>

      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
          <CircularProgress />
        </Box>
      ) : (
        <Grid container spacing={3} sx={{ mb: 4 }}>
          {stats.map((stat, index) => (
            <Grid item xs={12} sm={6} lg={3} key={index}>
              <StatCard {...stat} />
            </Grid>
          ))}
        </Grid>
      )}

      {/* Quick Actions */}
      <Paper sx={{ p: 4, textAlign: 'center' }}>
        <Box
          sx={{
            width: 80,
            height: 80,
            borderRadius: 4,
            background: `linear-gradient(135deg, ${alpha(
              theme.palette.primary.main,
              0.1,
            )} 0%, ${alpha(theme.palette.secondary.main, 0.1)} 100%)`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            mx: 'auto',
            mb: 3,
          }}
        >
          <Inbox sx={{ fontSize: 40, color: 'primary.main' }} />
        </Box>
        <Typography variant="h6" fontWeight={600} gutterBottom>
          🤖 Get Started with AI
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ maxWidth: 400, mx: 'auto' }}>
          Connect your mailbox and let our AI help you draft replies, categorize emails, and boost
          your productivity. Go to <strong>Mailboxes</strong> to add your first email account.
        </Typography>
      </Paper>
    </Box>
  );
};
