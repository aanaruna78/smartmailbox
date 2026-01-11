import React from 'react';
import { GoogleOAuthProvider } from '@react-oauth/google';
import '@fontsource/inter/300.css';
import '@fontsource/inter/400.css';
import '@fontsource/inter/500.css';
import '@fontsource/inter/700.css';

import { AuthProvider } from './features/auth/AuthProvider';
import { LoginPage } from './features/auth/LoginPage';
import { ThemeProvider } from './context/ThemeContext';
import { config } from './config';
import './App.css';



import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/Layout';
import { ProtectedRoute } from './components/ProtectedRoute';
import { RoleRoute } from './components/RoleRoute';
import { Dashboard } from './pages/Dashboard';
import { AdminDashboard } from './pages/AdminDashboard';
import { Unauthorized } from './pages/Unauthorized';
import { MailboxList } from './features/mailbox_setup/MailboxList';
import { MailboxForm } from './features/mailbox_setup/MailboxForm';
import { JobMonitor } from './features/jobs/JobMonitor';
import { InboxList } from './features/inbox/InboxList';
import { EmailDetail } from './features/inbox/EmailDetail';

const AppContent = () => {
    return (
        <Layout>
            <Routes>
                {/* Public Routes */}
                <Route path="/login" element={<LoginPage />} />
                <Route path="/unauthorized" element={<Unauthorized />} />

                {/* Protected Routes */}
                <Route element={<ProtectedRoute />}>
                    <Route path="/" element={<Dashboard />} />
                    <Route path="/mailboxes" element={<MailboxList />} />
                    <Route path="/mailboxes/new" element={<MailboxForm />} />
                    <Route path="/jobs" element={<JobMonitor />} />
                    <Route path="/inbox" element={<InboxList />} />
                    <Route path="/inbox/:id" element={<EmailDetail />} />

                    {/* Admin Routes */}
                    <Route element={<RoleRoute allowedRoles={['admin']} />}>
                        <Route path="/admin" element={<AdminDashboard />} />
                    </Route>
                </Route>

                {/* Fallback */}
                <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
        </Layout>
    );
}

function App() {
    return (
        <GoogleOAuthProvider clientId={config.auth.googleClientId}>
            <ThemeProvider>
                <AuthProvider>
                    <BrowserRouter>
                        <div className="App">
                            <AppContent />
                        </div>
                    </BrowserRouter>
                </AuthProvider>
            </ThemeProvider>
        </GoogleOAuthProvider>
    );
}

