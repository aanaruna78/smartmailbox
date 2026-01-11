# Smart Mailbox - MVP Milestone

> **Goal**: Launch fast with core functionality, then iterate.

---

## MVP Scope (Epics 1-8)

### ✅ Epic 1: Authentication & RBAC
- [x] Google OAuth login
- [x] JWT tokens with refresh
- [x] Role-based access (admin/user)
- [x] Protected routes

### ✅ Epic 2: Mailbox Setup
- [x] Add mailbox (IMAP/SMTP credentials)
- [x] Encrypted credential storage
- [x] Connection validation

### ✅ Epic 3: Email Sync
- [x] IMAP sync worker
- [x] Paginated inbox fetch
- [x] Folder support

### ✅ Epic 4: Inbox View
- [x] Email list with search
- [x] Email detail view
- [x] Thread display

### ✅ Epic 5: AI Draft Generation
- [x] LLM integration (Ollama)
- [x] Draft generation endpoint
- [x] Tone/instruction controls
- [x] Draft editing UI

### ✅ Epic 6: Send Reply
- [x] SMTP send
- [x] Draft → Sent workflow
- [x] Audit logging

### ✅ Epic 7: Job Queue
- [x] Background workers
- [x] Job status tracking
- [x] Retry logic

### ✅ Epic 8: Job Monitor
- [x] Job list UI
- [x] Status indicators
- [x] Polling updates

---

## MVP Launch Checklist

```
[ ] Database migrations applied
[ ] Environment variables configured
[ ] OAuth credentials set up
[ ] SMTP/IMAP tested with real mailbox
[ ] Ollama model pulled (llama3.2)
[ ] Health checks passing
[ ] Basic smoke test completed
```

---

## Post-MVP Enhancements

| Priority | Feature | Epic |
|----------|---------|------|
| P1 | Bulk draft generation | 9 |
| P1 | Smart grouping & suggestions | 10 |
| P2 | Spam filters & quarantine | 11 |
| P2 | Analytics dashboard | 12 |
| P3 | Admin LLM settings | 12 |
| P3 | Observability & metrics | 12 |

---

## MVP Timeline Estimate

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| Setup | 1 day | Dev environment, OAuth, DB |
| Core backend | 3 days | Auth, mailbox, sync, send |
| AI integration | 2 days | Draft generation, editing |
| Frontend | 3 days | Inbox, detail, compose |
| Testing | 2 days | E2E flows, bug fixes |
| **Total** | **~11 days** | **MVP Ready** |

---

## Success Criteria

1. User can log in via Google
2. User can add and sync a mailbox
3. User can view emails in inbox
4. User can generate AI draft reply
5. User can edit and send reply
6. All actions are audited

---

## Quick Start (MVP)

```bash
# 1. Clone and configure
git clone <repo>
cp .env.example .env
# Edit .env with your credentials

# 2. Start services
docker-compose up -d

# 3. Run migrations
docker exec smartmailbox-api alembic upgrade head

# 4. Pull LLM model
docker exec smartmailbox-ollama ollama pull llama3.2

# 5. Verify
curl http://localhost:8000/health/
```
