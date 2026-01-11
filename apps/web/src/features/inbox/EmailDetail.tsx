import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
    Box,
    Typography,
    Paper,
    Button,
    Divider,
    CircularProgress,
    List,
    ListItem,
    ListItemText,
    ListItemIcon,
    Chip,
    TextField,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
} from '@mui/material';
import { ArrowBack, AttachFile, Download, LocalOffer, PersonAdd, AutoAwesome } from '@mui/icons-material';
import { getEmail, EmailDetail as EmailDetailType, addTag, removeTag, assignEmail } from '../../api/emails';
import { DraftEditor } from '../draft_editor/DraftEditor';

export const EmailDetail = () => {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const [email, setEmail] = useState<EmailDetailType | null>(null);
    const [loading, setLoading] = useState(true);

    // Tag State
    const [tagInput, setTagInput] = useState('');
    const [showTagInput, setShowTagInput] = useState(false);

    // Assign State
    const [showAssignDialog, setShowAssignDialog] = useState(false);
    const [assignUserId, setAssignUserId] = useState('');

    // Draft Editor State
    const [showDraftEditor, setShowDraftEditor] = useState(false);

    const refreshEmail = () => {
        if (id) {
            getEmail(parseInt(id)).then(setEmail).catch(console.error);
        }
    };

    const handleAddTag = async () => {
        if (!email || !tagInput.trim()) return;
        try {
            await addTag(email.id, tagInput.trim());
            setTagInput('');
            setShowTagInput(false);
            refreshEmail();
        } catch (error) {
            console.error("Failed to add tag", error);
        }
    };

    const handleRemoveTag = async (tagId: number) => {
        if (!email) return;
        try {
            await removeTag(email.id, tagId);
            refreshEmail();
        } catch (error) {
            console.error("Failed to remove tag", error);
        }
    };

    const handleAssign = async () => {
        if (!email || !assignUserId) return;
        try {
            await assignEmail(email.id, parseInt(assignUserId));
            setShowAssignDialog(false);
            refreshEmail();
        } catch (error) {
            console.error("Failed to assign", error);
        }
    };

    useEffect(() => {
        if (id) {
            getEmail(parseInt(id))
                .then(setEmail)
                .catch((err) => console.error(err))
                .finally(() => setLoading(false));
        }
    }, [id]);

    if (loading) {
        return <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}><CircularProgress /></Box>;
    }

    if (!email) {
        return <Typography>Email not found.</Typography>;
    }

    // Sanitize or just render for now. In prod, use DOMPurify.
    const renderBody = () => {
        if (email.body_html) {
            return (
                <div
                    dangerouslySetInnerHTML={{ __html: email.body_html }}
                    style={{ padding: '20px', border: '1px solid #ddd', minHeight: '300px' }}
                />
            );
        }
        return <Typography sx={{ whiteSpace: 'pre-wrap', p: 2 }}>{email.body_text}</Typography>;
    };

    return (
        <Box>
            <Button startIcon={<ArrowBack />} onClick={() => navigate('/inbox')} sx={{ mb: 2 }}>
                Back to Inbox
            </Button>

            <Paper sx={{ p: 3 }}>
                <Box sx={{ mb: 3 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                        <Typography variant="h5" gutterBottom>{email.subject}</Typography>
                        <Box>
                            <Button startIcon={<AutoAwesome />} onClick={() => setShowDraftEditor(true)} sx={{ mr: 1 }} variant="contained" color="secondary">
                                AI Reply
                            </Button>
                            <Button startIcon={<PersonAdd />} onClick={() => setShowAssignDialog(true)} variant="outlined">
                                {email.assigned_user_id ? `Assigned: ${email.assigned_user_id}` : 'Assign'}
                            </Button>
                        </Box>
                    </Box>

                    <Box sx={{ display: 'flex', gap: 1, mb: 1, flexWrap: 'wrap', alignItems: 'center' }}>
                        {email.tags.map(tag => (
                            <Chip
                                key={tag.id}
                                label={tag.name}
                                onDelete={() => handleRemoveTag(tag.id)}
                                size="small"
                                color="primary"
                                variant="outlined"
                            />
                        ))}
                        {showTagInput ? (
                            <Box sx={{ display: 'flex', alignItems: 'center' }}>
                                <TextField
                                    size="small"
                                    value={tagInput}
                                    onChange={(e) => setTagInput(e.target.value)}
                                    placeholder="Tag name"
                                    onBlur={() => !tagInput && setShowTagInput(false)}
                                    autoFocus
                                />
                                <Button onClick={handleAddTag} size="small">Add</Button>
                            </Box>
                        ) : (
                            <Chip
                                icon={<LocalOffer />}
                                label="Add Tag"
                                onClick={() => setShowTagInput(true)}
                                size="small"
                                variant="outlined"
                                sx={{ borderStyle: 'dashed' }}
                            />
                        )}
                    </Box>

                    <Box sx={{ display: 'flex', justifyContent: 'space-between', color: 'text.secondary' }}>
                        <Typography variant="body2">From: {email.sender}</Typography>
                        <Typography variant="body2">{new Date(email.received_at).toLocaleString()}</Typography>
                    </Box>
                    <Typography variant="body2" color="text.secondary">To: {email.recipients}</Typography>
                </Box>

                <Divider sx={{ mb: 3 }} />

                {renderBody()}

                {email.attachments && email.attachments.length > 0 && (
                    <Box sx={{ mt: 3 }}>
                        <Typography variant="h6" gutterBottom>Attachments</Typography>
                        <List>
                            {email.attachments.map((att) => (
                                <ListItem key={att.id} sx={{ bgcolor: 'background.paper', mb: 1, border: '1px solid #eee' }}>
                                    <ListItemIcon>
                                        <AttachFile />
                                    </ListItemIcon>
                                    <ListItemText primary={att.filename} secondary={`${(att.size / 1024).toFixed(1)} KB`} />
                                    {/* Placeholder download link - needs backend endpoint for download */}
                                    <Button size="small" startIcon={<Download />} disabled>Download</Button>
                                </ListItem>
                            ))}
                        </List>
                    </Box>
                )}
            </Paper>

            <Dialog open={showAssignDialog} onClose={() => setShowAssignDialog(false)}>
                <DialogTitle>Assign Email</DialogTitle>
                <DialogContent>
                    <Typography variant="body2" sx={{ mb: 2 }}>
                        Enter User ID to assign this email to.
                    </Typography>
                    <TextField
                        fullWidth
                        label="User ID"
                        value={assignUserId}
                        onChange={(e) => setAssignUserId(e.target.value)}
                        type="number"
                    />
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setShowAssignDialog(false)}>Cancel</Button>
                    <Button onClick={handleAssign} variant="contained">Assign</Button>
                </DialogActions>
            </Dialog>

            {/* Draft Editor Component */}
            <DraftEditor
                emailId={email.id}
                open={showDraftEditor}
                onClose={() => setShowDraftEditor(false)}
            />
        </Box>
    );
};
