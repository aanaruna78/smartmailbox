import sys
import os
import requests
from datetime import datetime

# Add the apps/api directory to sys.path to access app modules directly for db setup
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'apps', 'api'))

from app.db.session import SessionLocal
from app.models.job import Job

# API URL
API_URL = "http://localhost:8000"

def get_auth_token():
    # Login to get a token (assuming admin@example.com / admin exists)
    response = requests.post(f"{API_URL}/token", data={
        "username": "admin@example.com",
        "password": "admin"
    })
    if response.status_code == 200:
        return response.json()["access_token"]
    print("Failed to login. Please ensure the server is running and admin user exists.")
    return None

def create_dummy_job():
    db = SessionLocal()
    try:
        job = Job(
            type="test_job",
            status="pending",
            payload={"foo": "bar"},
            created_at=datetime.utcnow()
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        print(f"Created dummy job in DB with ID: {job.id}")
        return job.id
    finally:
        db.close()

def main():
    print("--- Verifying Job Status API ---")
    
    token = get_auth_token()
    if not token:
        return

    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Create a job manually in DB
    job_id = create_dummy_job()
    
    # 2. Query it via API
    print(f"Fetching job {job_id} status via API...")
    response = requests.get(f"{API_URL}/jobs/{job_id}", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print("✅ API Response Success:")
        print(f"   ID: {data['id']}")
        print(f"   Type: {data['type']}")
        print(f"   Status: {data['status']}")
        print(f"   Payload: {data['payload']}")
        
        if data['status'] == 'pending' and data['payload']['foo'] == 'bar':
             print(f"   Attempts: {data.get('attempts')}")
             print(f"   Next Retry: {data.get('next_retry_at')}")
             print("✅ Data validation successful")
        else:
             print("❌ Data validation failed")
    else:
        print(f"❌ Failed to fetch job. Status Code: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    main()
