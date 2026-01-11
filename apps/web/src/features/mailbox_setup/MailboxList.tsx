import React, { useEffect, useState } from 'react';
import {
    Box,
    Typography,
    Button,
    Paper,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Chip,
    IconButton,
    Alert,
    CircularProgress
} from '@mui/material';
import { Add, Delete, Edit, Refresh } from '@mui/icons-material';
import { getMailboxes, Mailbox, deleteMailbox } from '../../api/mailboxes';
import { useNavigate } from 'react-router-dom';

export const MailboxList = () => {
    const [mailboxes, setMailboxes] = useState<Mailbox[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const navigate = useNavigate();

    const fetchMailboxes = async () => {
        try {
            setLoading(true);
            const data = await getMailboxes();
            setMailboxes(data);
            setError(null);
        } catch (err) {
            setError('Failed to load mailboxes');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchMailboxes();
    }, []);

    const handleDelete = async (id: number) => {
        if (window.confirm('Are you sure you want to delete this mailbox?')) {
            try {
                await deleteMailbox(id);
                setMailboxes(mailboxes.filter(m => m.id !== id));
            } catch (err) {
                console.error('Failed to delete mailbox', err);
                // Could verify with a toast here
            }
        }
    }
};

const handleSync = async (id: number) => {
    try {
        await import('../../api/mailboxes').then(mod => mod.triggerSync(id));
        // Ideally we'd show a toast or optimistically update the status
        // For now, let's just refresh the list
        fetchMailboxes();
    } catch (err) {
        console.error('Failed to trigger sync', err);
        alert('Failed to trigger sync');
    }
};

return (
    <Box>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
            <Typography variant="h4" component="h1">
                Mailboxes
            </Typography>
            <Button
                variant="contained"
                startIcon={<Add />}
                onClick={() => console.log("Navigate to create")}
            // onClick={() => navigate('/mailboxes/new')} 
            >
                Connect Mailbox
            </Button>
        </Box>

        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

        {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
                <CircularProgress />
            </Box>
        ) : mailboxes.length === 0 ? (
            <Paper sx={{ p: 4, textAlign: 'center' }}>
                <Typography color="text.secondary" gutterBottom>
                    No mailboxes connected yet.
                </Typography>
                <Button variant="outlined" startIcon={<Add />} onClick={() => navigate('/mailboxes/new')}>
                    Connect your first mailbox
                </Button>
            </Paper>
        ) : (
            <TableContainer component={Paper}>
                <Table>
                    <TableHead>
                        <TableRow>
                            <TableCell>Email Address</TableCell>
                            <TableCell>Provider</TableCell>
                            <TableCell>Status</TableCell>
                            <TableCell>Last Synced</TableCell>
                            <TableCell align="right">Actions</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {mailboxes.map((mailbox) => (
                            <TableRow key={mailbox.id}>
                                <TableCell>{mailbox.email_address}</TableCell>
                                <TableCell>
                                    <Chip
                                </TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </TableContainer>
        )}
    </Box>
);
};
