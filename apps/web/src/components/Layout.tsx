import React from 'react';
import { AppBar, Toolbar, Typography, Button, IconButton, Box, Container } from '@mui/material';
import { Brightness4, Brightness7, Logout } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../features/auth/AuthProvider';
import { useColorMode } from '../context/ThemeContext';

export const Layout = ({ children }: { children: React.ReactNode }) => {
    const { logout, user, isAuthenticated } = useAuth();
    const { toggleColorMode, mode } = useColorMode();
    const navigate = useNavigate();

    return (
        <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh', bgcolor: 'background.default', color: 'text.primary' }}>
            <AppBar position="static" color="default" elevation={1}>
                <Toolbar>
                    <Typography variant="h6" component="div" sx={{ flexGrow: 1, fontWeight: 700 }}>
                        Smart Mailbox
                    </Typography>

                    <IconButton sx={{ ml: 1 }} onClick={toggleColorMode} color="inherit">
                        {mode === 'dark' ? <Brightness7 /> : <Brightness4 />}
                    </IconButton>

                    {isAuthenticated && (
                        <Box sx={{ display: 'flex', alignItems: 'center', ml: 2 }}>
                            <Typography variant="body2" sx={{ mr: 2, display: { xs: 'none', sm: 'block' } }}>
                                {user?.email}
                            </Typography>
                            <Button color="inherit" onClick={() => navigate('/inbox')}>
                                Inbox
                            </Button>
                            <Button color="inherit" onClick={() => navigate('/mailboxes')}>
                                Mailboxes
                            </Button>
                            <Button color="inherit" onClick={() => navigate('/jobs')}>
                                Jobs
                            </Button>
                            <Button color="inherit" onClick={logout} endIcon={<Logout />}>
                                Logout
                            </Button>
                        </Box>
                    )}
                </Toolbar>
            </AppBar>

            <Container component="main" sx={{ mt: 4, mb: 4, flexGrow: 1 }}>
                {children}
            </Container>

            <Box component="footer" sx={{ py: 3, px: 2, mt: 'auto', backgroundColor: (theme) => theme.palette.mode === 'light' ? theme.palette.grey[200] : theme.palette.grey[800] }}>
                <Container maxWidth="sm">
                    <Typography variant="body2" color="text.secondary" align="center">
                        {'© '}
                        {new Date().getFullYear()}
                        {' Smart Mailbox. All rights reserved.'}
                    </Typography>
                </Container>
            </Box>
        </Box>
    );
};
