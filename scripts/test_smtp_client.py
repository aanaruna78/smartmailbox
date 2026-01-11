import sys
import os
from dotenv import load_dotenv

# Add the apps/api directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'apps', 'api'))

from app.integrations.smtp.client import SMTPClient

# Load environment variables
load_dotenv()

def main():
    print("--- SMTP Client Verification ---")
    
    email_address = os.getenv("TEST_EMAIL_ADDRESS")
    password = os.getenv("TEST_EMAIL_PASSWORD")
    host = os.getenv("TEST_SMTP_HOST", "smtp.gmail.com")
    port = int(os.getenv("TEST_SMTP_PORT", "587"))

    if not email_address or not password:
        print("Error: Please set TEST_EMAIL_ADDRESS and TEST_EMAIL_PASSWORD env vars, or hardcode them in the script.")
        email_address = input("Enter Email Address: ").strip()
        password = input("Enter Email Password (App Password): ").strip()
        if not email_address or not password:
            print("Aborted.")
            return

    to_email = input(f"Enter recipient email (default: {email_address}): ").strip() or email_address

    print(f"Connecting to {host}:{port} as {email_address}...")
    
    try:
        with SMTPClient(host, port, email_address, password) as client:
            print("✅ Connected!")
            
            subject = "Test Email from Smart Mailbox SMTP Client"
            body = "This is a plain text test email sent from the Smart Mailbox application verification script."
            html_body = """
            <html>
              <body>
                <h1>Test Email</h1>
                <p>This is a <b>HTML</b> test email sent from the Smart Mailbox application verification script.</p>
                <p>It confirms that your SMTP settings are working correctly.</p>
              </body>
            </html>
            """
            
            print(f"Sending email to {to_email}...")
            client.send_email(to_email, subject, body, html_body)
            print("✅ Email sent successfully!")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
