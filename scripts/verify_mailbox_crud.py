import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

# Add the project root to sys.path so we can import app
# Assuming script is run from project root or scripts folder
sys.path.append(os.path.join(os.path.dirname(__file__), "../apps/api"))

from app.main import app
from app.db.session import Base, get_db
from app.models.user import User
from app.core.security.deps import get_current_active_user

# Setup in-memory SQLite database
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)

# Dependency override
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# Create a mock user
mock_user = User(
    id=1,
    email="test@example.com",
    full_name="Test User",
    is_active=True,
    role="user"
)

def override_get_current_active_user():
    return mock_user

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_active_user] = override_get_current_active_user

client = TestClient(app)

def run_verification():
    print("Starting Mailbox CRUD Verification...")
    
    # 1. Create a mailbox
    print("\n1. Testing Create Mailbox...")
    response = client.post(
        "/mailboxes",
        json={
            "email_address": "mymailbox@example.com",
            "provider": "gmail",
            "imap_host": "imap.gmail.com",
            "smtp_host": "smtp.gmail.com",
            "password": "securepassword"
        }
    )
    if response.status_code == 200:
        data = response.json()
        print(f"   SUCCESS: Created mailbox with ID {data['id']}")
        mailbox_id = data['id']
    else:
        print(f"   FAILURE: {response.text}")
        return

    # 2. List mailboxes
    print("\n2. Testing List Mailboxes...")
    response = client.get("/mailboxes")
    if response.status_code == 200:
        data = response.json()
        print(f"   SUCCESS: Found {len(data)} mailboxes")
        assert len(data) >= 1
        assert data[0]['email_address'] == "mymailbox@example.com"
    else:
        print(f"   FAILURE: {response.text}")

    # 3. Get mailbox details
    print(f"\n3. Testing Get Mailbox {mailbox_id}...")
    response = client.get(f"/mailboxes/{mailbox_id}")
    if response.status_code == 200:
        data = response.json()
        print(f"   SUCCESS: Retrieved mailbox {data['email_address']}")
    else:
        print(f"   FAILURE: {response.text}")

    # 4. Update mailbox
    print(f"\n4. Testing Update Mailbox {mailbox_id}...")
    response = client.put(
        f"/mailboxes/{mailbox_id}",
        json={"provider": "outlook"}
    )
    if response.status_code == 200:
        data = response.json()
        print(f"   SUCCESS: Updated provider to {data['provider']}")
        assert data['provider'] == "outlook"
    else:
        print(f"   FAILURE: {response.text}")

    # 5. Delete mailbox
    print(f"\n5. Testing Delete Mailbox {mailbox_id}...")
    response = client.delete(f"/mailboxes/{mailbox_id}")
    if response.status_code == 200:
        print("   SUCCESS: Mailbox deleted")
    else:
        print(f"   FAILURE: {response.text}")

    # 6. Verify deletion
    print(f"\n6. Verifying Deletion...")
    response = client.get(f"/mailboxes/{mailbox_id}")
    if response.status_code == 404:
        print("   SUCCESS: Mailsbox not found (as expected)")
    else:
        print(f"   FAILURE: Expected 404 but got {response.status_code}")

    # 7. Test Connection (Mock)
    print(f"\n7. Testing Connection...")
    # Mocking imaplib and smtplib would be needed for true success, 
    # but we just want to ensure the endpoint is reachable and attempts connection.
    # We expect failure here because we are not mocking the actual network calls in this script,
    # and the hosts are dummy values.
    response = client.post(
        "/mailboxes/test-connection",
        json={
            "email_address": "test@example.com",
            "password": "wrongpassword",
            "imap_host": "imap.gmail.com",
            "imap_port": 993,
            "smtp_host": "smtp.gmail.com",
            "smtp_port": 587
        }
    )
    if response.status_code == 200:
        data = response.json()
        print(f"   SUCCESS: Endpoint reached. Result: {data}")
    else:
        print(f"   FAILURE: {response.text}")


if __name__ == "__main__":
    run_verification()
