import React from 'react';
import { Typography, Container, Button, Box } from '@mui/material';
import { Link } from 'react-router-dom';

export const Unauthorized = () => {
    return (
        <Container maxWidth="sm" sx={{ textAlign: 'center', mt: 10 }}>
            <Typography variant="h2" color="error" gutterBottom>
                403
            </Typography>
            <Typography variant="h5" gutterBottom>
                Unauthorized Access
            </Typography>
            <Typography variant="body1" color="text.secondary" paragraph>
                You do not have permission to view this page.
            </Typography>
            <Box sx={{ mt: 4 }}>
                <Button component={Link} to="/" variant="contained" color="primary">
                    Go to Dashboard
                </Button>
            </Box>
        </Container>
    );
};
