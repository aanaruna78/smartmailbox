import imaplib
import email
from email.header import decode_header
from email.utils import parsedate_to_datetime
import datetime
from typing import List, Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)

class IMAPClient:
    def __init__(self, host: str, port: int, email_address: str, password: str):
        self.host = host
        self.port = port
        self.email_address = email_address
        self.password = password
        self.connection = None

    def connect(self):
        """Connect to the IMAP server and login."""
        try:
            self.connection = imaplib.IMAP4_SSL(self.host, self.port)
            self.connection.login(self.email_address, self.password)
            logger.info(f"Connected to IMAP server {self.host} as {self.email_address}")
        except Exception as e:
            logger.error(f"Failed to connect to IMAP server: {e}")
            raise

    def disconnect(self):
        """Logout and close the connection."""
        if self.connection:
            try:
                self.connection.logout()
            except Exception:
                pass
            self.connection = None

    def list_folders(self) -> List[str]:
        """List available folders on the server."""
        if not self.connection:
            raise Exception("Not connected")
        
        try:
            status, folders_data = self.connection.list()
            if status != 'OK':
                raise Exception(f"Failed to list folders: {status}")
            
            folders = []
            for folder_bytes in folders_data:
                # Parse folder name from the response (e.g., '(\\HasNoChildren) "/" "INBOX"')
                folder_str = folder_bytes.decode('utf-8')
                # A simple split usually works, but robust parsing might be needed for quoted names with spaces
                # This is a basic extraction logic
                if ' "' in folder_str and '" ' in folder_str: # Quoted separator
                    parts = folder_str.split('"')
                    # The folder name is usually the last part, stripped of quotes if any
                    folder_name = parts[-2]
                elif '"' in folder_str: # End quote
                    folder_name = folder_str.split('"')[-2]
                else: 
                     folder_name = folder_str.split(' ')[-1]
                
                folders.append(folder_name)
            return folders
        except Exception as e:
            logger.error(f"Error listing folders: {e}")
            raise

    def select_folder(self, folder: str = "INBOX"):
        """Select a folder to perform operations on."""
        if not self.connection:
            raise Exception("Not connected")
        status, _ = self.connection.select(f'"{folder}"') # Quote folder name to handle spaces
        if status != 'OK':
             # Try without quotes if failed (some servers behave differently)
            status, _ = self.connection.select(folder)
            if status != 'OK':
                raise Exception(f"Failed to select folder {folder}")

    def fetch_emails(self, folder: str = "INBOX", limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch latest emails from the selected folder."""
        self.select_folder(folder)
        
        # Search for all emails
        status, messages = self.connection.search(None, "ALL")
        if status != 'OK':
            raise Exception("Failed to search emails")
        
        email_ids = messages[0].split()
        # Get the latest 'limit' emails
        latest_email_ids = email_ids[-limit:]
        
        results = []
        
        for email_id in reversed(latest_email_ids): # Process newest first
            try:
                # Fetch the email body (RFC822)
                status, msg_data = self.connection.fetch(email_id, "(RFC822)")
                if status != 'OK':
                    logger.warning(f"Failed to fetch email {email_id}")
                    continue
                
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        parsed_email = self._parse_email(msg, email_id.decode())
                        results.append(parsed_email)
            except Exception as e:
                logger.error(f"Error fetching email {email_id}: {e}")
                continue
                
        return results

    def _parse_email(self, msg, uid: str) -> Dict[str, Any]:
        """Parse raw email message into a dictionary."""
        subject = self._decode_header_str(msg["Subject"])
        sender = self._decode_header_str(msg["From"])
        recipients = self._decode_header_str(msg["To"])
        date_str = msg["Date"]
        message_id = msg.get("Message-ID", "")
        
        try:
            received_at = parsedate_to_datetime(date_str)
        except Exception:
            received_at = datetime.datetime.utcnow()

        body_text = ""
        body_html = ""

        attachments = []

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))

                try:
                    # Detect attachment
                    if "attachment" in content_disposition:
                        filename = part.get_filename()
                        if filename:
                            # In a real worker, we would decode the payload and save it to storage here
                            # For now, we return the metadata and the raw content might be handled by the caller
                            # or we can simply extract the content bytes.
                            file_data = part.get_payload(decode=True)
                            attachments.append({
                                "filename": self._decode_header_str(filename),
                                "content_type": content_type,
                                "size": len(file_data) if file_data else 0,
                                "content": file_data 
                            })
                            continue # Skip body processing for this part

                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset()
                        if charset:
                            decoded_payload = payload.decode(charset, errors="replace")
                        else:
                            decoded_payload = payload.decode("utf-8", errors="replace")

                        if content_type == "text/plain" and "attachment" not in content_disposition:
                            body_text += decoded_payload
                        elif content_type == "text/html" and "attachment" not in content_disposition:
                            body_html += decoded_payload
                except Exception as e:
                    logger.warning(f"Failed to parse email part: {e}")
        else:
             # ... (existing single part logic) ...
            try:
                payload = msg.get_payload(decode=True)
                if payload:
                    charset = msg.get_content_charset()
                    if charset:
                         decoded_payload = payload.decode(charset, errors="replace")
                    else:
                         decoded_payload = payload.decode("utf-8", errors="replace")
                         
                    content_type = msg.get_content_type()
                    if content_type == "text/plain":
                        body_text = decoded_payload
                    elif content_type == "text/html":
                        body_html = decoded_payload
            except Exception as e:
                logger.warning(f"Failed to parse email body: {e}")


        return {
            "uid": uid,
            "message_id": message_id,
            "subject": subject,
            "sender": sender,
            "recipients": recipients,
            "received_at": received_at,
            "body_text": body_text,
            "body_html": body_html,
            "folder": "INBOX",
            "attachments": attachments
        }

    def _decode_header_str(self, header_value: Optional[str]) -> str:
        """Decode email header value."""
        if not header_value:
            return ""
        try:
            decoded_list = decode_header(header_value)
            parts = []
            for content, encoding in decoded_list:
                if isinstance(content, bytes):
                    if encoding:
                         # Handle 'unknown-8bit' or special encodings gently
                        try:
                            parts.append(content.decode(encoding, errors="replace"))
                        except LookupError:
                            parts.append(content.decode("utf-8", errors="replace"))
                    else:
                        parts.append(content.decode("utf-8", errors="replace"))
                else:
                    parts.append(str(content))
            return "".join(parts)
        except Exception as e:
            logger.error(f"Error decoding header: {e}")
            return str(header_value)

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
