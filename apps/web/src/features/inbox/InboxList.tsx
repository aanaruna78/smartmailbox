import React, { useEffect, useState } from 'react';
import {
    Box,
    Typography,
    Paper,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    TextField,
    Chip,
    TablePagination,
    InputAdornment,
    IconButton,
    Button
} from '@mui/material';
import { Search, Flag } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { getEmails, Email } from '../../api/emails';

import { BulkDraftDialog } from './BulkDraftDialog';
import { BulkSelectionBar } from './BulkSelectionBar';
import { BulkPreviewDialog } from './BulkPreviewDialog';
import { Checkbox } from '@mui/material';

export const InboxList = () => {
    const navigate = useNavigate();
    const [emails, setEmails] = useState<Email[]>([]);
    const [total, setTotal] = useState(0);
    const [page, setPage] = useState(0);
    const [rowsPerPage, setRowsPerPage] = useState(10);
    const [search, setSearch] = useState('');
    const [filterRead, setFilterRead] = useState<boolean | undefined>(undefined);

    // Selection
    const [selected, setSelected] = useState<number[]>([]);
    const [showBulkDialog, setShowBulkDialog] = useState(false);
    const [showPreviewDialog, setShowPreviewDialog] = useState(false);

    const fetchEmails = async () => {
        try {
            const data = await getEmails({
                page: page + 1,
                size: rowsPerPage,
                q: search,
                is_read: filterRead
            });
            setEmails(data.items);
            setTotal(data.total);
            // Clear selection on page change or filter if needed, but keeping for now
            // simpler to clear
            setSelected([]);
        } catch (error) {
            console.error("Failed to fetch emails", error);
        }
    };

    useEffect(() => {
        fetchEmails();
    }, [page, rowsPerPage, search, filterRead]);

    const handleChangePage = (event: unknown, newPage: number) => {
        setPage(newPage);
    };

    const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
        setRowsPerPage(parseInt(event.target.value, 10));
        setPage(0);
    };

    const handleSelectAll = (event: React.ChangeEvent<HTMLInputElement>) => {
        if (event.target.checked) {
            const newSelected = emails.map((n) => n.id);
            setSelected(newSelected);
            return;
        }
        setSelected([]);
    };

    const handleClick = (event: React.MouseEvent<unknown>, id: number) => {
        event.stopPropagation();
        const selectedIndex = selected.indexOf(id);
        let newSelected: number[] = [];

        if (selectedIndex === -1) {
            newSelected = newSelected.concat(selected, id);
        } else if (selectedIndex === 0) {
            newSelected = newSelected.concat(selected.slice(1));
        } else if (selectedIndex === selected.length - 1) {
            newSelected = newSelected.concat(selected.slice(0, -1));
        } else if (selectedIndex > 0) {
            newSelected = newSelected.concat(
                selected.slice(0, selectedIndex),
                selected.slice(selectedIndex + 1),
            );
        }
        setSelected(newSelected);
    };

    const isSelected = (id: number) => selected.indexOf(id) !== -1;

    return (
        <Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                <Typography variant="h4">Inbox</Typography>
                <Box sx={{ display: 'flex', gap: 2 }}>
                    {selected.length > 0 && (
                        <Button
                            variant="contained"
                            color="secondary"
                            onClick={() => setShowBulkDialog(true)}
                        >
                            Bulk Reply ({selected.length})
                        </Button>
                    )}
                    <TextField
                        size="small"
                        placeholder="Search emails..."
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        InputProps={{
                            startAdornment: (
                                <InputAdornment position="start">
                                    <Search />
                                </InputAdornment>
                            ),
                        }}
                    />
                </Box>
            </Box>

            <Box sx={{ mb: 2, display: 'flex', gap: 1 }}>
                <Chip
                    label="All"
                    onClick={() => setFilterRead(undefined)}
                    color={filterRead === undefined ? 'primary' : 'default'}
                    variant={filterRead === undefined ? 'filled' : 'outlined'}
                />
                <Chip
                    label="Unread"
                    onClick={() => setFilterRead(false)}
                    color={filterRead === false ? 'primary' : 'default'}
                    variant={filterRead === false ? 'filled' : 'outlined'}
                />
                <Chip
                    label="Read"
                    onClick={() => setFilterRead(true)}
                    color={filterRead === true ? 'primary' : 'default'}
                    variant={filterRead === true ? 'filled' : 'outlined'}
                />
            </Box>

            <TableContainer component={Paper}>
                <Table>
                    <TableHead>
                        <TableRow>
                            <TableCell padding="checkbox">
                                <Checkbox
                                    color="primary"
                                    indeterminate={selected.length > 0 && selected.length < emails.length}
                                    checked={emails.length > 0 && selected.length === emails.length}
                                    onChange={handleSelectAll}
                                />
                            </TableCell>
                            <TableCell>Sender</TableCell>
                            <TableCell>Subject</TableCell>
                            <TableCell>Date</TableCell>
                            <TableCell>Status</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {emails.map((email) => {
                            const isItemSelected = isSelected(email.id);
                            return (
                                <TableRow
                                    key={email.id}
                                    hover
                                    role="checkbox"
                                    aria-checked={isItemSelected}
                                    selected={isItemSelected}
                                    onClick={() => navigate(`/inbox/${email.id}`)}
                                    sx={{ cursor: 'pointer', fontWeight: !email.is_read ? 'bold' : 'normal' }}
                                >
                                    <TableCell padding="checkbox" onClick={(e) => handleClick(e, email.id)}>
                                        <Checkbox
                                            color="primary"
                                            checked={isItemSelected}
                                        />
                                    </TableCell>
                                    <TableCell>{email.sender}</TableCell>
                                    <TableCell>
                                        {email.subject}
                                        {email.is_flagged && <Flag fontSize="small" color="warning" sx={{ ml: 1, verticalAlign: 'middle' }} />}
                                    </TableCell>
                                    <TableCell>{new Date(email.received_at).toLocaleDateString()}</TableCell>
                                    <TableCell>
                                        {!email.is_read && <Chip label="New" color="error" size="small" />}
                                    </TableCell>
                                </TableRow>
                            );
                        })}
                    </TableBody>
                </Table>
                <TablePagination
                    rowsPerPageOptions={[5, 10, 25]}
                    component="div"
                    count={total}
                    rowsPerPage={rowsPerPage}
                    page={page}
                    onPageChange={handleChangePage}
                    onRowsPerPageChange={handleChangeRowsPerPage}
                />
            </TableContainer>

            {/* Floating Selection Bar */}
            <BulkSelectionBar
                selectedCount={selected.length}
                onClear={() => setSelected([])}
                onBulkReply={() => setShowBulkDialog(true)}
                onPreview={() => setShowPreviewDialog(true)}
            />

            {/* Bulk Draft Generation Dialog */}
            <BulkDraftDialog
                open={showBulkDialog}
                onClose={() => setShowBulkDialog(false)}
                selectedCount={selected.length}
                emailIds={selected}
                onSuccess={() => {
                    setSelected([]);
                    fetchEmails();
                }}
            />

            {/* Bulk Preview & Send Dialog */}
            <BulkPreviewDialog
                open={showPreviewDialog}
                onClose={() => setShowPreviewDialog(false)}
                emailIds={selected}
                onComplete={() => {
                    setSelected([]);
                    fetchEmails();
                }}
            />
        </Box>
    );
};
