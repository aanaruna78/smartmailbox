import sys
import os
import asyncio
from dotenv import load_dotenv

# Add the apps/api directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'apps', 'api'))

from app.integrations.imap.client import IMAPClient

# Load environment variables (optional, if you want to hardcode for a quick test locally)
load_dotenv()

def main():
    print("--- IMAP Client Verification ---")
    
    # You can hardcode these for your manual test or use env vars
    email_address = os.getenv("TEST_EMAIL_ADDRESS")
    password = os.getenv("TEST_EMAIL_PASSWORD")
    host = os.getenv("TEST_IMAP_HOST", "imap.gmail.com")
    port = int(os.getenv("TEST_IMAP_PORT", "993"))

    if not email_address or not password:
        print("Error: Please set TEST_EMAIL_ADDRESS and TEST_EMAIL_PASSWORD env vars, or hardcode them in the script.")
        # Interactive fallback
        email_address = input("Enter Email Address: ").strip()
        password = input("Enter Email Password (App Password): ").strip()
        if not email_address or not password:
            print("Aborted.")
            return

    print(f"Connecting to {host}:{port} as {email_address}...")
    
    try:
        with IMAPClient(host, port, email_address, password) as client:
            print("✅ Connected!")
            
            print("\nListing Folders:")
            folders = client.list_folders()
            for f in folders:
                print(f" - {f}")
            
            target_folder = "INBOX"
            limit = 3
            print(f"\nFetching last {limit} emails from {target_folder}...")
            
            emails = client.fetch_emails(target_folder, limit)
            
            for i, email in enumerate(emails):
                print(f"\n--- Email {i+1} ---")
                print(f"Subject: {email['subject']}")
                print(f"Sender: {email['sender']}")
                print(f"Date: {email['received_at']}")
                print(f"Has Text Body: {'Yes' if email['body_text'] else 'No'}")
                print(f"Has HTML Body: {'Yes' if email['body_html'] else 'No'}")
                # print(f"Preview: {email['body_text'][:100]}...")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
