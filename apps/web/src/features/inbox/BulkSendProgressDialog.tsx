import React, { useState, useEffect } from 'react';
import {
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Button,
    Typography,
    Box,
    LinearProgress,
    List,
    ListItem,
    ListItemIcon,
    ListItemText,
    Chip
} from '@mui/material';
import { CheckCircle, Error, Pending, Send } from '@mui/icons-material';
import { sendEmail } from '../../api/emails';

interface SendItem {
    emailId: number;
    recipient: string;
    subject: string;
    body: string;
    status: 'pending' | 'sending' | 'success' | 'error';
    error?: string;
}

interface BulkSendProgressDialogProps {
    open: boolean;
    onClose: () => void;
    items: SendItem[];
    onComplete: () => void;
}

export const BulkSendProgressDialog: React.FC<BulkSendProgressDialogProps> = ({
    open,
    onClose,
    items,
    onComplete
}) => {
    const [sendItems, setSendItems] = useState<SendItem[]>([]);
    const [sending, setSending] = useState(false);
    const [completed, setCompleted] = useState(false);

    useEffect(() => {
        if (open && items.length > 0) {
            setSendItems(items.map(item => ({ ...item, status: 'pending' as const })));
            setCompleted(false);
        }
    }, [open, items]);

    const startSending = async () => {
        setSending(true);

        for (let i = 0; i < sendItems.length; i++) {
            const item = sendItems[i];

            // Update status to sending
            setSendItems(prev => prev.map((p, idx) =>
                idx === i ? { ...p, status: 'sending' as const } : p
            ));

            try {
                await sendEmail(item.emailId, item.recipient, item.subject, item.body);

                setSendItems(prev => prev.map((p, idx) =>
                    idx === i ? { ...p, status: 'success' as const } : p
                ));
            } catch (error: any) {
                setSendItems(prev => prev.map((p, idx) =>
                    idx === i ? { ...p, status: 'error' as const, error: error.message } : p
                ));
            }

            // Small delay between sends for rate limiting
            await new Promise(resolve => setTimeout(resolve, 500));
        }

        setSending(false);
        setCompleted(true);
    };

    const getStatusIcon = (status: SendItem['status']) => {
        switch (status) {
            case 'pending':
                return <Pending color="disabled" />;
            case 'sending':
                return <Send color="primary" />;
            case 'success':
                return <CheckCircle color="success" />;
            case 'error':
                return <Error color="error" />;
        }
    };

    const successCount = sendItems.filter(i => i.status === 'success').length;
    const errorCount = sendItems.filter(i => i.status === 'error').length;
    const progress = sendItems.length > 0
        ? ((successCount + errorCount) / sendItems.length) * 100
        : 0;

    return (
        <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
            <DialogTitle>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Send color="primary" />
                    Sending Emails
                </Box>
            </DialogTitle>
            <DialogContent>
                {sending && (
                    <Box sx={{ mb: 2 }}>
                        <LinearProgress variant="determinate" value={progress} />
                        <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5 }}>
                            {successCount + errorCount} / {sendItems.length} completed
                        </Typography>
                    </Box>
                )}

                {completed && (
                    <Box sx={{ mb: 2, display: 'flex', gap: 1 }}>
                        <Chip
                            icon={<CheckCircle />}
                            label={`${successCount} sent`}
                            color="success"
                            variant="outlined"
                        />
                        {errorCount > 0 && (
                            <Chip
                                icon={<Error />}
                                label={`${errorCount} failed`}
                                color="error"
                                variant="outlined"
                            />
                        )}
                    </Box>
                )}

                <List dense>
                    {sendItems.map((item, index) => (
                        <ListItem key={index}>
                            <ListItemIcon>
                                {getStatusIcon(item.status)}
                            </ListItemIcon>
                            <ListItemText
                                primary={item.subject}
                                secondary={item.recipient}
                            />
                            {item.error && (
                                <Typography variant="caption" color="error">
                                    {item.error}
                                </Typography>
                            )}
                        </ListItem>
                    ))}
                </List>
            </DialogContent>
            <DialogActions>
                {!sending && !completed && (
                    <>
                        <Button onClick={onClose}>Cancel</Button>
                        <Button
                            variant="contained"
                            onClick={startSending}
                            startIcon={<Send />}
                        >
                            Send All ({sendItems.length})
                        </Button>
                    </>
                )}
                {completed && (
                    <Button
                        variant="contained"
                        onClick={() => {
                            onComplete();
                            onClose();
                        }}
                    >
                        Done
                    </Button>
                )}
            </DialogActions>
        </Dialog>
    );
};
