import sys
import os
import requests
import time
from datetime import datetime

# Add the apps/api directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'apps', 'api'))

from app.services.workers import process_sync_email_job # We import worker to simulate execution

API_URL = "http://localhost:8000"

def get_auth_token():
    try:
        response = requests.post(f"{API_URL}/token", data={
            "username": "admin@example.com",
            "password": "admin"
        })
        if response.status_code == 200:
            return response.json()["access_token"]
    except:
        pass
    print("Failed to login. Ensure server is running.")
    return None

def main():
    print("--- Verifying Sync Endpoint Flow ---")
    
    token = get_auth_token()
    if not token: 
        return
        
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Get first mailbox
    print("Fetching mailboxes...")
    resp = requests.get(f"{API_URL}/mailboxes", headers=headers)
    if resp.status_code != 200 or not resp.json():
        print("No mailboxes found. Please create one globally first.")
        return
    
    mailbox = resp.json()[0]
    mailbox_id = mailbox["id"]
    print(f"Target Mailbox ID: {mailbox_id} ({mailbox['email_address']})")
    print(f"Initial Status: {mailbox.get('sync_status')}")
    
    # 2. Trigger Sync
    print("Triggering Sync...")
    resp = requests.post(f"{API_URL}/mailboxes/{mailbox_id}/sync", headers=headers)
    if resp.status_code == 202:
        data = resp.json()
        job_id = data["job_id"]
        print(f"✅ Sync started. Job ID: {job_id}")
        
        # 3. Check Mailbox Status (Should be 'syncing')
        # Wait a moment for DB commit if needed, though API responds after commit
        resp = requests.get(f"{API_URL}/mailboxes", headers=headers)
        mb_updated = next(m for m in resp.json() if m["id"] == mailbox_id)
        print(f"Status after trigger: {mb_updated.get('sync_status')}")
        
        if mb_updated.get('sync_status') == 'syncing':
            print("✅ Mailbox status updated to 'syncing'.")
        else:
            print("❌ Mailbox status NOT updated.")
            
        # 4. Simulate Worker Execution
        print(">> Simulating Worker Execution...")
        try:
             # We invoke the worker function directly to simulate background processing
             # NOTE: This runs in the script process, not the server process, 
             # but it connects to the same DB if sharing env/config.
             # Ensure TEST_EMAIL_ADDRESS/PASSWORD matches the mailbox if relying on that, 
             # OR ensure the mailbox in DB has valid encrypted credentials.
             process_sync_email_job(job_id)
        except Exception as e:
            print(f"Worker simulation error: {e}")

        # 5. Check Final Status
        print("Checking final status...")
        resp = requests.get(f"{API_URL}/mailboxes", headers=headers)
        mb_final = next(m for m in resp.json() if m["id"] == mailbox_id)
        print(f"Final Status: {mb_final.get('sync_status')}")
        print(f"Last Synced: {mb_final.get('last_synced_at')}")
        
        if mb_final.get('sync_status') == 'idle' and mb_final.get('last_synced_at'):
             print("✅ Sync flow completed successfully defined.")
        elif mb_final.get('sync_status') == 'failed':
             print("⚠️ Sync failed (expected if credentials invalid).")
        else:
             print("❌ Status did not return to idle/failed.")

    else:
        print(f"❌ Trigger failed: {resp.status_code} - {resp.text}")

if __name__ == "__main__":
    main()
