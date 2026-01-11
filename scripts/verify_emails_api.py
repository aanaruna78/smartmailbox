import sys
import os
import requests
import json

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
    print("Failed to login.")
    return None

def main():
    print("--- Verifying Emails API ---")
    
    token = get_auth_token()
    if not token: 
        return
        
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. List Emails
    print("Listing emails...")
    resp = requests.get(f"{API_URL}/emails?size=5", headers=headers)
    if resp.status_code == 200:
        data = resp.json()
        print(f"✅ Listed {len(data['items'])} emails (Total: {data['total']})")
        
        if data['items']:
            first_email = data['items'][0]
            print(f"   First Email: [{first_email['id']}] {first_email['subject']} (Att: {len(first_email['attachments'])})")
            
            # 2. Get Detail
            print(f"Fetching details for email {first_email['id']}...")
            detail_resp = requests.get(f"{API_URL}/emails/{first_email['id']}", headers=headers)
            if detail_resp.status_code == 200:
                detail = detail_resp.json()
                print("✅ Fetched Detail.")
                print(f"   Body Preview: {detail['body_text'][:50]}...")
            else:
                 print(f"❌ Failed to fetch detail: {detail_resp.status_code}")
                 
            # 3. Search
            print(f"Searching for 'Test'...") # Assuming some email has "Test"
            search_resp = requests.get(f"{API_URL}/emails?q=Test", headers=headers)
            if search_resp.status_code == 200:
                 s_data = search_resp.json()
                 print(f"✅ Search found {s_data['total']} results")
            else:
                 print(f"❌ Search failed: {search_resp.status_code}")

        else:
            print("⚠️ No emails found. Run the sync worker first.")
    else:
        print(f"❌ Failed to list emails: {resp.status_code}")
        print(resp.text)

if __name__ == "__main__":
    main()
