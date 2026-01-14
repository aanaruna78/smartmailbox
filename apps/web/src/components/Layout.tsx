import React from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  IconButton,
  Box,
  Container,
  useTheme,
  alpha,
} from '@mui/material';
import {
  Brightness4,
  Brightness7,
  Logout,
  Mail,
  Inbox,
  Work,
  Dashboard,
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../features/auth/AuthProvider';
import { useColorMode } from '../context/ThemeContext';

export const Layout = ({ children }: { children: React.ReactNode }) => {
  const { logout, user, isAuthenticated } = useAuth();
  const { toggleColorMode, mode } = useColorMode();
  const navigate = useNavigate();
  const location = useLocation();
  const theme = useTheme();

  const isActive = (path: string) => location.pathname === path;

  const navButtonStyle = (path: string) => ({
    mx: 0.5,
    px: 2,
    py: 1,
    borderRadius: 2,
    color: isActive(path) ? 'primary.main' : 'text.secondary',
    backgroundColor: isActive(path) ? alpha(theme.palette.primary.main, 0.1) : 'transparent',
    fontWeight: isActive(path) ? 600 : 500,
    '&:hover': {
      backgroundColor: alpha(theme.palette.primary.main, 0.08),
    },
  });

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        minHeight: '100vh',
        bgcolor: 'background.default',
        color: 'text.primary',
      }}
    >
      <AppBar
        position="sticky"
        elevation={0}
        sx={{
          bgcolor: alpha(theme.palette.background.paper, 0.8),
          backdropFilter: 'blur(12px)',
          borderBottom: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
        }}
      >
        <Toolbar sx={{ px: { xs: 2, sm: 3, md: 4 } }}>
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              cursor: 'pointer',
              '&:hover': { opacity: 0.9 },
            }}
            onClick={() => navigate('/')}
          >
            <Box
              component="img"
              src="/ai-logo.png"
              alt="AI Smart Mailbox"
              sx={{
                width: 40,
                height: 40,
                mr: 1.5,
              }}
            />
            <Box sx={{ display: { xs: 'none', sm: 'block' } }}>
              <Typography
                variant="h6"
                sx={{
                  fontWeight: 700,
                  background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  lineHeight: 1.2,
                }}
              >
                Smart Mailbox
              </Typography>
              <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.65rem' }}>
                Powered by AI
              </Typography>
            </Box>
          </Box>

          <Box sx={{ flexGrow: 1 }} />

          {isAuthenticated && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              <Button
                startIcon={<Dashboard fontSize="small" />}
                onClick={() => navigate('/')}
                sx={navButtonStyle('/')}
              >
                <Box sx={{ display: { xs: 'none', md: 'block' } }}>Dashboard</Box>
              </Button>
              <Button
                startIcon={<Inbox fontSize="small" />}
                onClick={() => navigate('/inbox')}
                sx={navButtonStyle('/inbox')}
              >
                <Box sx={{ display: { xs: 'none', md: 'block' } }}>Inbox</Box>
              </Button>
              <Button
                startIcon={<Mail fontSize="small" />}
                onClick={() => navigate('/mailboxes')}
                sx={navButtonStyle('/mailboxes')}
              >
                <Box sx={{ display: { xs: 'none', md: 'block' } }}>Mailboxes</Box>
              </Button>
              <Button
                startIcon={<Work fontSize="small" />}
                onClick={() => navigate('/jobs')}
                sx={navButtonStyle('/jobs')}
              >
                <Box sx={{ display: { xs: 'none', md: 'block' } }}>Jobs</Box>
              </Button>
            </Box>
          )}

          <Box sx={{ display: 'flex', alignItems: 'center', ml: 2 }}>
            <IconButton onClick={toggleColorMode} sx={{ mr: 1 }}>
              {mode === 'dark' ? <Brightness7 /> : <Brightness4 />}
            </IconButton>

            {isAuthenticated && (
              <>
                <Typography
                  variant="body2"
                  sx={{
                    mr: 2,
                    display: { xs: 'none', lg: 'block' },
                    color: 'text.secondary',
                    fontWeight: 500,
                  }}
                >
                  {user?.full_name || user?.email}
                </Typography>
                <Button
                  variant="outlined"
                  size="small"
                  onClick={logout}
                  startIcon={<Logout fontSize="small" />}
                  sx={{
                    borderColor: alpha(theme.palette.divider, 0.3),
                    color: 'text.secondary',
                    '&:hover': {
                      borderColor: theme.palette.error.main,
                      color: theme.palette.error.main,
                      backgroundColor: alpha(theme.palette.error.main, 0.05),
                    },
                  }}
                >
                  <Box sx={{ display: { xs: 'none', sm: 'block' } }}>Logout</Box>
                </Button>
              </>
            )}
          </Box>
        </Toolbar>
      </AppBar>

      <Container
        component="main"
        maxWidth="xl"
        sx={{
          mt: 4,
          mb: 4,
          px: { xs: 2, sm: 3, md: 4 },
          flexGrow: 1,
        }}
      >
        {children}
      </Container>

      <Box
        component="footer"
        sx={{
          py: 3,
          px: 2,
          mt: 'auto',
          borderTop: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
          backgroundColor: alpha(theme.palette.background.paper, 0.5),
        }}
      >
        <Container maxWidth="xl">
          <Typography variant="body2" color="text.secondary" align="center" sx={{ mb: 1 }}>
            © {new Date().getFullYear()} AI Smart Mailbox. All rights reserved.
          </Typography>
          <Typography variant="body2" color="text.secondary" align="center">
            Developed by{' '}
            <Box
              component="a"
              href="https://www.thinkhivelabs.com"
              target="_blank"
              rel="noopener noreferrer"
              sx={{
                color: 'primary.main',
                textDecoration: 'none',
                fontWeight: 600,
                '&:hover': { textDecoration: 'underline' },
              }}
            >
              ThinkHive Labs
            </Box>
          </Typography>
        </Container>
      </Box>
    </Box>
  );
};
