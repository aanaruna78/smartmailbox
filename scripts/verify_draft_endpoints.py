import sys
import os
import datetime
from sqlalchemy.orm import Session

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'apps', 'api'))

from app.db.session import SessionLocal
from app.models.job import Job
from app.models.email import Email
from app.models.mailbox import Mailbox
from app.models.user import User
from app.models.draft import Draft

# Ideally we would use `requests` to test the API via HTTP, 
# but simply verifying the Service function or Route logic via Mock DB calls is faster for now.
# However, the task asked for "Endpoints", so let's import the routers and call functions directly 
# simulating Dependency Injection.

from app.routes import emails as email_routes
from app.routes import drafts as draft_routes
from app.schemas.draft import DraftUpdate
from app.routes.emails import DraftRequest

def verify_endpoints():
    print("--- Verifying Draft Endpoints ---")
    db = SessionLocal()
    
    try:
        # 1. Setup Data
        user = db.query(User).filter(User.email == "test@example.com").first()
        if not user:
            print("❌ User not found, run previous verification scripts first.")
            return

        # Ensure we have an email owned by this user
        email = db.query(Email).join(Email.mailbox).filter(Mailbox.user_id == user.id).first()
        if not email:
            print("❌ No owned email found.")
            return

        print(f"Using User: {user.email}, Email ID: {email.id}")

        # 2. Test Enqueue Job (POST /emails/{id}/draft-job)
        print("\n[POST] /emails/{id}/draft-job")
        req = DraftRequest(instructions="Test draft", tone="friendly")
        response = email_routes.enqueue_draft_generation(
            email_id=email.id,
            body=req,
            db=db,
            current_user=user
        )
        print(f"✅ Job Enqueued: {response}")
        job_id = response["job_id"]
        
        # 3. Simulate Job Completion (Manually create a draft linked to this email)
        # Because we can't wait for actual worker here easily without running it.
        print("\n[Simulating Worker] Creating Dummy Draft...")
        draft = Draft(
            email_id=email.id,
            content="This is version 1.",
            created_at=datetime.datetime.utcnow(),
            updated_at=datetime.datetime.utcnow()
        )
        db.add(draft)
        db.commit()
        db.refresh(draft)
        draft_id = draft.id
        
        # 4. Test Get Drafts (GET /emails/{id}/drafts)
        print("\n[GET] /emails/{id}/drafts")
        drafts_list = email_routes.list_email_drafts(
            email_id=email.id,
            db=db,
            current_user=user
        )
        print(f"✅ Drafts Found: {len(drafts_list)}")
        found = any(d.id == draft_id for d in drafts_list)
        if found:
            print("   Target draft is present.")
        else:
            print("❌ Target draft NOT present.")

        # 5. Test Update Draft (PUT /drafts/{id})
        print("\n[PUT] /drafts/{id}")
        update_data = DraftUpdate(content="This is version 2 (Edited).")
        updated_draft = draft_routes.update_draft(
            draft_id=draft_id,
            draft_in=update_data,
            db=db,
            current_user=user
        )
        print(f"✅ Draft Updated: {updated_draft.content}")
        
        if updated_draft.updated_at > draft.created_at: 
             print("   Updated_at timestamp updated correctly.")
        
        # 6. Test Get Draft Detail (GET /drafts/{id})
        print("\n[GET] /drafts/{id}")
        fetched_draft = draft_routes.get_draft(
            draft_id=draft_id,
            db=db,
            current_user=user
        )
        print(f"✅ Draft Fetched: {fetched_draft.content}")

    except Exception as e:
        print(f"❌ Verification Failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    verify_endpoints()
