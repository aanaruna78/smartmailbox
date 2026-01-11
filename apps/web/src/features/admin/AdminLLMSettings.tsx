import React, { useState, useEffect } from 'react';
import {
    Box,
    Paper,
    Typography,
    Tabs,
    Tab,
    TextField,
    Button,
    Select,
    MenuItem,
    FormControl,
    InputLabel,
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableRow,
    TableContainer,
    IconButton,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Chip,
    CircularProgress,
    Alert
} from '@mui/material';
import { Settings, Add, Delete, Edit, Save } from '@mui/icons-material';
import http from '../../api/http';

interface LLMSettings {
    id: number;
    model_provider: string;
    model_name: string;
    temperature: string;
    max_tokens: number;
    api_base_url: string | null;
}

interface PromptTemplate {
    id: number;
    name: string;
    description: string | null;
    system_prompt: string;
    user_prompt_template: string | null;
    version: number;
}

interface PolicyRule {
    id: number;
    name: string;
    description: string | null;
    rule_type: string;
    config: any;
    severity: string;
}

export const AdminLLMSettings: React.FC = () => {
    const [tab, setTab] = useState(0);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [success, setSuccess] = useState('');

    // LLM Settings
    const [llmSettings, setLLMSettings] = useState<LLMSettings | null>(null);

    // Prompts
    const [prompts, setPrompts] = useState<PromptTemplate[]>([]);
    const [editingPrompt, setEditingPrompt] = useState<PromptTemplate | null>(null);

    // Policies
    const [policies, setPolicies] = useState<PolicyRule[]>([]);
    const [newPolicyDialog, setNewPolicyDialog] = useState(false);

    useEffect(() => {
        fetchAll();
    }, []);

    const fetchAll = async () => {
        setLoading(true);
        try {
            const [llmRes, promptsRes, policiesRes] = await Promise.all([
                http.get('/admin-settings/llm'),
                http.get('/admin-settings/prompts'),
                http.get('/admin-settings/policies')
            ]);
            setLLMSettings(llmRes.data);
            setPrompts(promptsRes.data);
            setPolicies(policiesRes.data);
        } catch (error) {
            console.error('Failed to fetch settings', error);
        }
        setLoading(false);
    };

    const saveLLMSettings = async () => {
        if (!llmSettings) return;
        setSaving(true);
        try {
            await http.put('/admin-settings/llm', llmSettings);
            setSuccess('LLM settings saved');
            setTimeout(() => setSuccess(''), 3000);
        } catch (error) {
            console.error('Failed to save', error);
        }
        setSaving(false);
    };

    const savePrompt = async () => {
        if (!editingPrompt) return;
        setSaving(true);
        try {
            await http.put(`/admin-settings/prompts/${editingPrompt.id}`, editingPrompt);
            fetchAll();
            setEditingPrompt(null);
            setSuccess('Prompt saved');
            setTimeout(() => setSuccess(''), 3000);
        } catch (error) {
            console.error('Failed to save', error);
        }
        setSaving(false);
    };

    const deletePolicy = async (id: number) => {
        if (!confirm('Delete this policy?')) return;
        try {
            await http.delete(`/admin-settings/policies/${id}`);
            setPolicies(policies.filter(p => p.id !== id));
        } catch (error) {
            console.error('Failed to delete', error);
        }
    };

    if (loading) {
        return (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                <CircularProgress />
            </Box>
        );
    }

    return (
        <Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
                <Settings color="primary" sx={{ fontSize: 32 }} />
                <Typography variant="h4">Admin LLM Settings</Typography>
            </Box>

            {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}

            <Paper>
                <Tabs value={tab} onChange={(_, v) => setTab(v)}>
                    <Tab label="Model Settings" />
                    <Tab label="Prompt Templates" />
                    <Tab label="Policy Rules" />
                </Tabs>

                <Box sx={{ p: 3 }}>
                    {/* Model Settings Tab */}
                    {tab === 0 && llmSettings && (
                        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, maxWidth: 500 }}>
                            <FormControl fullWidth>
                                <InputLabel>Provider</InputLabel>
                                <Select
                                    value={llmSettings.model_provider}
                                    label="Provider"
                                    onChange={(e) => setLLMSettings({ ...llmSettings, model_provider: e.target.value })}
                                >
                                    <MenuItem value="ollama">Ollama (Local)</MenuItem>
                                    <MenuItem value="openai">OpenAI</MenuItem>
                                    <MenuItem value="anthropic">Anthropic</MenuItem>
                                </Select>
                            </FormControl>
                            <TextField
                                label="Model Name"
                                value={llmSettings.model_name}
                                onChange={(e) => setLLMSettings({ ...llmSettings, model_name: e.target.value })}
                            />
                            <TextField
                                label="Temperature"
                                value={llmSettings.temperature}
                                onChange={(e) => setLLMSettings({ ...llmSettings, temperature: e.target.value })}
                            />
                            <TextField
                                label="Max Tokens"
                                type="number"
                                value={llmSettings.max_tokens}
                                onChange={(e) => setLLMSettings({ ...llmSettings, max_tokens: parseInt(e.target.value) })}
                            />
                            <TextField
                                label="API Base URL"
                                value={llmSettings.api_base_url || ''}
                                onChange={(e) => setLLMSettings({ ...llmSettings, api_base_url: e.target.value })}
                            />
                            <Button
                                variant="contained"
                                startIcon={saving ? <CircularProgress size={20} /> : <Save />}
                                onClick={saveLLMSettings}
                                disabled={saving}
                            >
                                Save Settings
                            </Button>
                        </Box>
                    )}

                    {/* Prompt Templates Tab */}
                    {tab === 1 && (
                        <TableContainer>
                            <Table>
                                <TableHead>
                                    <TableRow>
                                        <TableCell>Name</TableCell>
                                        <TableCell>Description</TableCell>
                                        <TableCell>Version</TableCell>
                                        <TableCell>Actions</TableCell>
                                    </TableRow>
                                </TableHead>
                                <TableBody>
                                    {prompts.map((prompt) => (
                                        <TableRow key={prompt.id}>
                                            <TableCell>{prompt.name}</TableCell>
                                            <TableCell>{prompt.description}</TableCell>
                                            <TableCell>
                                                <Chip label={`v${prompt.version}`} size="small" />
                                            </TableCell>
                                            <TableCell>
                                                <IconButton onClick={() => setEditingPrompt(prompt)}>
                                                    <Edit />
                                                </IconButton>
                                            </TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </TableContainer>
                    )}

                    {/* Policy Rules Tab */}
                    {tab === 2 && (
                        <>
                            <Button
                                variant="outlined"
                                startIcon={<Add />}
                                sx={{ mb: 2 }}
                                onClick={() => setNewPolicyDialog(true)}
                            >
                                Add Policy
                            </Button>
                            <TableContainer>
                                <Table>
                                    <TableHead>
                                        <TableRow>
                                            <TableCell>Name</TableCell>
                                            <TableCell>Type</TableCell>
                                            <TableCell>Severity</TableCell>
                                            <TableCell>Actions</TableCell>
                                        </TableRow>
                                    </TableHead>
                                    <TableBody>
                                        {policies.map((policy) => (
                                            <TableRow key={policy.id}>
                                                <TableCell>{policy.name}</TableCell>
                                                <TableCell>{policy.rule_type}</TableCell>
                                                <TableCell>
                                                    <Chip
                                                        label={policy.severity}
                                                        color={policy.severity === 'block' ? 'error' : 'warning'}
                                                        size="small"
                                                    />
                                                </TableCell>
                                                <TableCell>
                                                    <IconButton color="error" onClick={() => deletePolicy(policy.id)}>
                                                        <Delete />
                                                    </IconButton>
                                                </TableCell>
                                            </TableRow>
                                        ))}
                                    </TableBody>
                                </Table>
                            </TableContainer>
                        </>
                    )}
                </Box>
            </Paper>

            {/* Edit Prompt Dialog */}
            <Dialog open={!!editingPrompt} onClose={() => setEditingPrompt(null)} maxWidth="md" fullWidth>
                <DialogTitle>Edit Prompt Template</DialogTitle>
                <DialogContent>
                    {editingPrompt && (
                        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
                            <TextField
                                label="Description"
                                value={editingPrompt.description || ''}
                                onChange={(e) => setEditingPrompt({ ...editingPrompt, description: e.target.value })}
                            />
                            <TextField
                                label="System Prompt"
                                multiline
                                rows={6}
                                value={editingPrompt.system_prompt}
                                onChange={(e) => setEditingPrompt({ ...editingPrompt, system_prompt: e.target.value })}
                            />
                            <TextField
                                label="User Prompt Template"
                                multiline
                                rows={4}
                                value={editingPrompt.user_prompt_template || ''}
                                onChange={(e) => setEditingPrompt({ ...editingPrompt, user_prompt_template: e.target.value })}
                            />
                        </Box>
                    )}
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setEditingPrompt(null)}>Cancel</Button>
                    <Button variant="contained" onClick={savePrompt} disabled={saving}>
                        {saving ? <CircularProgress size={20} /> : 'Save'}
                    </Button>
                </DialogActions>
            </Dialog>
        </Box>
    );
};
