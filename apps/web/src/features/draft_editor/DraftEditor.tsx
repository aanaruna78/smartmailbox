import React, { useState, useEffect, useRef } from 'react';
import {
    Box,
    Button,
    TextField,
    Select,
    MenuItem,
    Typography,
    CircularProgress,
    Chip,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Paper,
    Divider,
    Tabs,
    Tab,
    Alert
} from '@mui/material';
import { AutoAwesome, Save, Replay, CompareArrows, Visibility, VisibilityOff, Send } from '@mui/icons-material';
import { generateDraftJob, getJobStatus, getDrafts, updateDraft, Draft, sendEmail } from '../../api/emails';

interface DraftEditorProps {
    emailId: number;
    open: boolean;
    onClose: () => void;
}

export const DraftEditor: React.FC<DraftEditorProps> = ({ emailId, open, onClose }) => {
    // State
    const [instructions, setInstructions] = useState('');
    const [tone, setTone] = useState('professional');
    const [drafts, setDrafts] = useState<Draft[]>([]);
    const [currentDraftId, setCurrentDraftId] = useState<number | null>(null);
    const [editedContent, setEditedContent] = useState('');
    const [isGenerating, setIsGenerating] = useState(false);

    // View Mode: 'edit', 'preview', 'diff'
    const [viewMode, setViewMode] = useState<'edit' | 'diff'>('edit');

    // Polling
    const pollingRef = useRef<NodeJS.Timeout | null>(null);

    // Initial Load
    useEffect(() => {
        if (open && emailId) {
            fetchDrafts();
        }
        return () => stopPolling();
    }, [open, emailId]);

    // Update editedContent when draft changes
    useEffect(() => {
        if (currentDraftId) {
            const draft = drafts.find(d => d.id === currentDraftId);
            if (draft) {
                // If we switched drafts, reset to that draft's content.
                // Note: Real-world apps might warn about unsaved changes here.
                setEditedContent(draft.content);
            }
        } else {
            setEditedContent('');
        }
    }, [currentDraftId, drafts]);

    const stopPolling = () => {
        if (pollingRef.current) clearInterval(pollingRef.current);
        pollingRef.current = null;
    };

    const fetchDrafts = async () => {
        try {
            const fetched = await getDrafts(emailId);
            setDrafts(fetched);
            // Select latest if none selected, or if we just generated a new one
            if (fetched.length > 0 && !currentDraftId) {
                setCurrentDraftId(fetched[fetched.length - 1].id);
            }
        } catch (e) {
            console.error("Failed to fetch drafts", e);
        }
    };

    const handleGenerate = async () => {
        setIsGenerating(true);
        setViewMode('edit');
        try {
            const { job_id } = await generateDraftJob(emailId, instructions, tone);

            // Poll
            pollingRef.current = setInterval(async () => {
                try {
                    const job = await getJobStatus(job_id);
                    if (job.status === 'completed') {
                        stopPolling();
                        setIsGenerating(false);
                        const newDrafts = await getDrafts(emailId);
                        setDrafts(newDrafts);
                        if (job.result && job.result.draft_id) {
                            setCurrentDraftId(job.result.draft_id);
                        } else {
                            // Fallback to latest
                            setCurrentDraftId(newDrafts[newDrafts.length - 1].id);
                        }
                    } else if (job.status === 'failed') {
                        stopPolling();
                        setIsGenerating(false);
                        alert(`Generation Failed: ${job.error}`);
                    }
                } catch (e) {
                    stopPolling();
                    setIsGenerating(false);
                }
            }, 2000);

        } catch (e) {
            console.error(e);
            setIsGenerating(false);
            alert("Failed to start generation");
        }
    };

    const handleSave = async () => {
        if (!currentDraftId) return;
        try {
            await updateDraft(currentDraftId, editedContent);
            // Update local state to reflect saved status (optional, if we tracked dirty state)
            fetchDrafts(); // Refresh to ensure sync
            alert("Draft saved!");
        } catch (e) {
            console.error(e);
            alert("Failed to save draft");
        }
    };


    // Send Confirmation State
    const [showSendDialog, setShowSendDialog] = useState(false);
    const [sendRecipient, setSendRecipient] = useState('');
    const [sendSubject, setSendSubject] = useState('');

    const handleSendClick = () => {
        // Pre-fill from email context if available, but we only have ID here.
        // We'll trust the user to verify/enter. 
        // Ideally we pass recipient in props or fetch it.
        // For now let's just default to empty or a placeholder if we don't fetch detail here.
        setSendRecipient('recipient@example.com');
        setSendSubject('Re: Your Email');
        setShowSendDialog(true);
    };

    const handleConfirmSend = async () => {
        setIsGenerating(true); // Re-use spinner state or create new one
        try {
            const { job_id } = await sendEmail(emailId, sendRecipient, sendSubject, undefined, editedContent);
            setShowSendDialog(false);

            // Poll for Send Completion
            pollingRef.current = setInterval(async () => {
                try {
                    const job = await getJobStatus(job_id);
                    if (job.status === 'completed') {
                        stopPolling();
                        setIsGenerating(false);
                        alert("Email Sent Successfully!");
                        onClose(); // Close editor
                    } else if (job.status === 'failed') {
                        stopPolling();
                        setIsGenerating(false);
                        alert(`Send Failed: ${job.error}`);
                    }
                } catch (e) {
                    stopPolling();
                    setIsGenerating(false);
                }
            }, 2000);

        } catch (e) {
            console.error(e);
            setIsGenerating(false);
            alert("Failed to enqueue send job");
        }
    };

    const currentDraftOriginal = drafts.find(d => d.id === currentDraftId)?.content || '';

    return (
        <Dialog open={open} onClose={onClose} maxWidth="lg" fullWidth>
            <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <AutoAwesome color="primary" />
                    AI Draft Editor
                </Box>
                <Box>
                    <Button onClick={onClose} color="inherit">Close</Button>
                </Box>
            </DialogTitle>
            <DialogContent dividers>
                {/* Controls Area */}
                <Box sx={{ mb: 3, p: 2, bgcolor: 'background.default', borderRadius: 1 }}>
                    <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
                        <TextField
                            fullWidth
                            size="small"
                            label="Instructions"
                            placeholder="e.g. Reply politely and ask for a meeting next Tuesday"
                            value={instructions}
                            onChange={e => setInstructions(e.target.value)}
                            disabled={isGenerating}
                        />
                        <Select
                            size="small"
                            value={tone}
                            onChange={e => setTone(e.target.value)}
                            sx={{ minWidth: 150 }}
                            disabled={isGenerating}
                        >
                            <MenuItem value="professional">Professional</MenuItem>
                            <MenuItem value="friendly">Friendly</MenuItem>
                            <MenuItem value="assertive">Assertive</MenuItem>
                            <MenuItem value="urgent">Urgent</MenuItem>
                        </Select>
                        <Button
                            variant="contained"
                            startIcon={isGenerating ? <CircularProgress size={20} color="inherit" /> : <AutoAwesome />}
                            onClick={handleGenerate}
                            disabled={isGenerating || !instructions}
                        >
                            {isGenerating ? 'Generating...' : drafts.length > 0 ? 'Regenerate' : 'Generate'}
                        </Button>
                    </Box>

                    {/* Versions */}
                    {drafts.length > 0 && (
                        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', flexWrap: 'wrap' }}>
                            <Typography variant="body2" color="text.secondary">Versions:</Typography>
                            {drafts.map((d, i) => (
                                <Chip
                                    key={d.id}
                                    label={`V${i + 1} - ${new Date(d.created_at).toLocaleTimeString()}`}
                                    onClick={() => setCurrentDraftId(d.id)}
                                    color={currentDraftId === d.id ? 'primary' : 'default'}
                                    variant={currentDraftId === d.id ? 'filled' : 'outlined'}
                                    clickable
                                />
                            ))}
                        </Box>
                    )}
                </Box>

                {currentDraftId ? (
                    <Box>
                        {/* Editor Toolbar */}
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1, alignItems: 'center' }}>
                            <Tabs value={viewMode} onChange={(e, v) => setViewMode(v)} sx={{ minHeight: 40, height: 40 }}>
                                <Tab label="Edit" value="edit" icon={<Visibility sx={{ fontSize: 16 }} />} iconPosition="start" sx={{ minHeight: 40 }} />
                                <Tab label="Diff vs Original" value="diff" icon={<CompareArrows sx={{ fontSize: 16 }} />} iconPosition="start" sx={{ minHeight: 40 }} />
                            </Tabs>
                            <Box sx={{ display: 'flex', gap: 1 }}>
                                <Button
                                    variant="outlined"
                                    startIcon={<Save />}
                                    onClick={handleSave}
                                    disabled={isGenerating}
                                >
                                    Save Draft
                                </Button>
                                <Button
                                    variant="contained"
                                    color="success"
                                    startIcon={<Send />}
                                    onClick={handleSendClick}
                                    disabled={isGenerating}
                                >
                                    Send
                                </Button>
                            </Box>
                        </Box>

                        <Divider sx={{ mb: 2 }} />

                        {viewMode === 'edit' ? (
                            <TextField
                                fullWidth
                                multiline
                                minRows={15}
                                value={editedContent}
                                onChange={e => setEditedContent(e.target.value)}
                                placeholder="Draft content..."
                                variant="outlined"
                                sx={{
                                    fontFamily: 'monospace',
                                    '& .MuiInputBase-root': { fontFamily: 'monospace' }
                                }}
                            />
                        ) : (
                            // Simple Split View Diff
                            <Box sx={{ display: 'flex', gap: 2, height: '400px' }}>
                                <Paper elevation={0} variant="outlined" sx={{ flex: 1, p: 2, overflow: 'auto', bgcolor: '#f8f9fa' }}>
                                    <Typography variant="subtitle2" color="text.secondary" gutterBottom>Original AI Suggestion</Typography>
                                    <Typography sx={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace', fontSize: '0.875rem', color: 'text.secondary' }}>
                                        {currentDraftOriginal}
                                    </Typography>
                                </Paper>
                                <Paper elevation={0} variant="outlined" sx={{ flex: 1, p: 2, overflow: 'auto', bgcolor: '#fff' }}>
                                    <Typography variant="subtitle2" color="primary" gutterBottom>Your Current Edits</Typography>
                                    <Typography sx={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace', fontSize: '0.875rem' }}>
                                        {editedContent}
                                    </Typography>
                                </Paper>
                            </Box>
                        )}
                    </Box>
                ) : (
                    <Box sx={{ p: 4, textAlign: 'center', color: 'text.secondary' }}>
                        <AutoAwesome sx={{ fontSize: 40, mb: 2, opacity: 0.5 }} />
                        <Typography>Enter instructions above to generate your first draft.</Typography>
                    </Box>
                )}

            </DialogContent>

            {/* Send Confirmation Dialog */}
            <Dialog open={showSendDialog} onClose={() => setShowSendDialog(false)}>
                <DialogTitle>Confirm Send</DialogTitle>
                <DialogContent>
                    <Box sx={{ pt: 1, display: 'flex', flexDirection: 'column', gap: 2, minWidth: 400 }}>
                        <TextField
                            label="Recipient"
                            fullWidth
                            value={sendRecipient}
                            onChange={e => setSendRecipient(e.target.value)}
                        />
                        <TextField
                            label="Subject"
                            fullWidth
                            value={sendSubject}
                            onChange={e => setSendSubject(e.target.value)}
                        />
                        <Typography variant="body2" color="text.secondary">
                            This will send the email immediately via connected SMTP.
                        </Typography>
                    </Box>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setShowSendDialog(false)}>Cancel</Button>
                    <Button
                        onClick={handleConfirmSend}
                        variant="contained"
                        color="primary"
                        disabled={!sendRecipient || !sendSubject}
                    >
                        Confirm & Send
                    </Button>
                </DialogActions>
            </Dialog>

            {drafts.length > 0 && viewMode === 'diff' && (
                // Legend for Diff
                <Box sx={{ px: 3, py: 1, bgcolor: 'background.default', display: 'flex', gap: 2 }}>
                    <Typography variant="caption" color="text.secondary">
                        * Comparison view shows the original AI generation on the left and your current edits on the right.
                    </Typography>
                </Box>
            )}
        </Dialog>
    );
};
