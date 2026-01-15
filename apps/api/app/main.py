from fastapi import FastAPI
from app.core.logging import setup_logging
from app.routes import auth, admin, mailboxes, jobs, emails, drafts, audit, approval, groups, spam, quarantine, admin_settings, analytics, health, metrics, gmail
from app.db.session import engine, Base
from app import models  # Import models to register with Base

setup_logging()

# Create tables on startup for development
Base.metadata.create_all(bind=engine)

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Smart Mailbox API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1", tags=["auth"])
app.include_router(admin.router, prefix="/api/v1", tags=["admin"])
app.include_router(mailboxes.router, prefix="/api/v1", tags=["mailboxes"])
app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["jobs"])
app.include_router(emails.router, prefix="/api/v1/emails", tags=["emails"])
app.include_router(drafts.router, prefix="/api/v1/drafts", tags=["drafts"])
app.include_router(audit.router, prefix="/api/v1/audit", tags=["audit"])
app.include_router(approval.router, prefix="/api/v1/approvals", tags=["approvals"])
app.include_router(groups.router, prefix="/api/v1/groups", tags=["groups"])
app.include_router(spam.router, prefix="/api/v1/spam", tags=["spam"])
app.include_router(quarantine.router, prefix="/api/v1/quarantine", tags=["quarantine"])
app.include_router(admin_settings.router, prefix="/api/v1/admin-settings", tags=["admin-settings"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])
app.include_router(health.router, prefix="/api/v1/health", tags=["health"])
app.include_router(metrics.router, prefix="/api/v1/metrics", tags=["metrics"])
app.include_router(gmail.router, prefix="/api/v1", tags=["gmail"])

@app.get("/")
def read_root():
    return {"message": "Hello World"}

