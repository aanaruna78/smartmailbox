"""
Gmail API Service for fetching emails using OAuth tokens.
"""
import json
from typing import List, Optional, Dict, Any
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import base64
from email.mime.text import MIMEText

from app.core.config import settings


class GmailService:
    """Service for interacting with Gmail API using OAuth credentials."""
    
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.send',
    ]
    
    def __init__(self, access_token: str, refresh_token: str = None):
        """Initialize Gmail service with OAuth tokens."""
        self.credentials = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri='https://oauth2.googleapis.com/token',
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            scopes=self.SCOPES
        )
        
        # Refresh if expired
        if self.credentials.expired and self.credentials.refresh_token:
            self.credentials.refresh(Request())
        
        self.service = build('gmail', 'v1', credentials=self.credentials)
    
    def get_new_access_token(self) -> Optional[str]:
        """Return new access token if refreshed."""
        if self.credentials.token:
            return self.credentials.token
        return None
    
    def list_messages(self, max_results: int = 20, label_ids: List[str] = None, q: str = None, page_token: str = None) -> Dict[str, Any]:
        """List messages from Gmail inbox with pagination support."""
        try:
            query_params = {
                'userId': 'me',
                'maxResults': max_results,
            }
            if label_ids:
                query_params['labelIds'] = label_ids
            if q:
                query_params['q'] = q
            if page_token:
                query_params['pageToken'] = page_token
            
            results = self.service.users().messages().list(**query_params).execute()
            return {
                'messages': results.get('messages', []),
                'nextPageToken': results.get('nextPageToken'),
            }
        except HttpError as error:
            print(f'Gmail API error: {error}')
            return {'messages': [], 'nextPageToken': None}
    
    def get_message(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific message by ID."""
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            return self._parse_message(message)
        except HttpError as error:
            print(f'Gmail API error: {error}')
            return None
    
    def _parse_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Gmail API message into simplified format."""
        headers = {h['name']: h['value'] for h in message['payload'].get('headers', [])}
        
        # Get body
        body = ''
        payload = message['payload']
        if 'body' in payload and payload['body'].get('data'):
            body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
        elif 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain' and part['body'].get('data'):
                    body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                    break
                elif part['mimeType'] == 'text/html' and part['body'].get('data'):
                    body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
        
        return {
            'id': message['id'],
            'thread_id': message['threadId'],
            'subject': headers.get('Subject', '(No Subject)'),
            'sender': headers.get('From', ''),
            'to': headers.get('To', ''),
            'date': headers.get('Date', ''),
            'snippet': message.get('snippet', ''),
            'body': body,
            'labels': message.get('labelIds', []),
            'is_read': 'UNREAD' not in message.get('labelIds', []),
        }
    
    def get_inbox_messages(self, max_results: int = 20, page_token: str = None) -> Dict[str, Any]:
        """Get messages from inbox with full details and pagination support."""
        result = self.list_messages(max_results=max_results, label_ids=['INBOX'], page_token=page_token)
        messages = []
        for ref in result['messages'][:max_results]:
            msg = self.get_message(ref['id'])
            if msg:
                messages.append(msg)
        return {
            'messages': messages,
            'nextPageToken': result.get('nextPageToken'),
        }
    
    def get_unread_count(self) -> int:
        """Get count of unread messages."""
        try:
            results = self.service.users().messages().list(
                userId='me',
                labelIds=['INBOX', 'UNREAD'],
                maxResults=1
            ).execute()
            return results.get('resultSizeEstimate', 0)
        except HttpError:
            return 0
    
    def send_email(self, to: str, subject: str, body: str) -> bool:
        """Send an email."""
        try:
            message = MIMEText(body)
            message['to'] = to
            message['subject'] = subject
            
            encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            self.service.users().messages().send(
                userId='me',
                body={'raw': encoded_message}
            ).execute()
            return True
        except HttpError as error:
            print(f'Gmail send error: {error}')
            return False
