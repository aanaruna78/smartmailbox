from fastapi import FastAPI
from app.core.logging import setup_logging
from app.routes import auth, admin, mailboxes, jobs, emails, drafts, audit, approval, groups, spam, quarantine, admin_settings, analytics, health, metrics

setup_logging()

app = FastAPI(title="Smart Mailbox API")

app.include_router(auth.router, tags=["auth"])
app.include_router(admin.router, tags=["admin"])
app.include_router(mailboxes.router, tags=["mailboxes"])
app.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
app.include_router(emails.router, prefix="/emails", tags=["emails"])
app.include_router(drafts.router, prefix="/drafts", tags=["drafts"])
app.include_router(audit.router, prefix="/audit", tags=["audit"])
app.include_router(approval.router, prefix="/approvals", tags=["approvals"])
app.include_router(groups.router, prefix="/groups", tags=["groups"])
app.include_router(spam.router, prefix="/spam", tags=["spam"])
app.include_router(quarantine.router, prefix="/quarantine", tags=["quarantine"])
app.include_router(admin_settings.router, prefix="/admin-settings", tags=["admin-settings"])
app.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(metrics.router, prefix="/metrics", tags=["metrics"])

@app.get("/")
def read_root():
    return {"message": "Hello World"}
