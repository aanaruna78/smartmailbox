"""
Gmail-specific routes for authenticated user's inbox.
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel

from app.db.session import get_db
from app.models.user import User
from app.core.security.deps import get_current_active_user
from app.services.gmail_service import GmailService
from app.services.llm import LLMService

router = APIRouter()


class AutoReplyRequest(BaseModel):
    tone: str = "professional"
    instructions: Optional[str] = None
    # Optional: Pass email content to skip Gmail API fetch
    subject: Optional[str] = None
    sender: Optional[str] = None
    body: Optional[str] = None


class SendReplyRequest(BaseModel):
    body: str
    subject: Optional[str] = None


@router.get("/gmail/inbox")
async def get_gmail_inbox(
    max_results: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get emails from local database for authenticated user with pagination."""
    from app.models.email import Email
    from app.models.mailbox import Mailbox
    
    try:
        # Query emails joined with mailboxes to filter by user_id
        emails_query = db.query(Email).join(Mailbox).filter(
            Mailbox.user_id == current_user.id
        ).order_by(Email.received_at.desc())
        
        total_count = emails_query.count()
        emails = emails_query.offset(offset).limit(max_results).all()
        
        # Convert to a format compatible with the frontend expectations
        messages = []
        for email in emails:
            messages.append({
                "id": email.message_id,
                "thread_id": email.thread_id,
                "sender": email.sender,
                "subject": email.subject,
                "snippet": email.snippet,
                "body": email.body_text,
                "date": email.received_at.isoformat() if email.received_at else None,
                "is_read": email.is_read
            })
            
        return {
            "messages": messages,
            "count": len(messages),
            "total_count": total_count,
            "next_offset": offset + max_results if offset + max_results < total_count else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch emails from DB: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch Gmail: {str(e)}")


@router.get("/gmail/stats")
async def get_gmail_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get Gmail inbox statistics."""
    if not current_user.google_access_token:
        return {
            "connected": False,
            "unread_count": 0,
            "total_count": 0
        }
    
    try:
        gmail = GmailService(
            access_token=current_user.google_access_token,
            refresh_token=current_user.google_refresh_token
        )
        
        unread_count = gmail.get_unread_count()
        message_refs = gmail.list_messages(max_results=1)
        
        return {
            "connected": True,
            "unread_count": unread_count,
            "user_email": current_user.email
        }
    except Exception as e:
        return {
            "connected": False,
            "error": str(e)
        }


@router.get("/gmail/message/{message_id}")
async def get_gmail_message(
    message_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific Gmail message."""
    if not current_user.google_access_token:
        raise HTTPException(status_code=400, detail="Gmail not connected")
    
    try:
        gmail = GmailService(
            access_token=current_user.google_access_token,
            refresh_token=current_user.google_refresh_token
        )
        
        message = gmail.get_message(message_id)
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        
        return message
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch message: {str(e)}")


@router.post("/gmail/auto-reply/{message_id}")
async def generate_auto_reply(
    message_id: str,
    request: AutoReplyRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Generate an AI auto-reply for a Gmail message using Ollama."""
    if not current_user.google_access_token:
        raise HTTPException(status_code=400, detail="Gmail not connected")
    
    try:
        # Use request body if email content is provided (faster - skips Gmail API call)
        if request.subject and request.sender and request.body:
            sender_name = request.sender
            if '<' in sender_name:
                sender_name = sender_name.split('<')[0].strip().strip('"')
            subject = request.subject
            body = request.body[:500]  # Limit for faster processing
        else:
            # Fallback: fetch from Gmail API
            gmail = GmailService(
                access_token=current_user.google_access_token,
                refresh_token=current_user.google_refresh_token
            )
            message = gmail.get_message(message_id)
            if not message:
                raise HTTPException(status_code=404, detail="Message not found")
            
            sender_name = message.get('sender', 'Unknown')
            if '<' in sender_name:
                sender_name = sender_name.split('<')[0].strip().strip('"')
            subject = message.get('subject', 'your inquiry')
            body = message.get('body', message.get('snippet', ''))[:500]
        
        # Build a short, efficient prompt
        tone_map = {
            "professional": "formal",
            "friendly": "warm and casual",
            "assertive": "direct and confident",
            "urgent": "concise and urgent"
        }
        
        prompt = f"""Reply briefly to this email in a {tone_map.get(request.tone, 'professional')} tone.

Email from {sender_name}: "{subject}" - {body[:200]}

Write a 2-3 sentence reply:"""

        # Use Ollama to generate reply
        llm_service = LLMService()
        response = await llm_service.generate_draft(prompt, timeout=60.0)
        
        return {
            "message_id": message_id,
            "original_subject": subject,
            "original_sender": sender_name,
            "reply_text": response.text.strip(),
            "tone": request.tone
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate reply: {str(e)}")


@router.post("/gmail/auto-reply-stream/{message_id}")
async def generate_auto_reply_stream(
    message_id: str,
    request: AutoReplyRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Generate a streaming AI auto-reply for a Gmail message."""
    if not current_user.google_access_token:
        raise HTTPException(status_code=400, detail="Gmail not connected")
    
    try:
        gmail = GmailService(
            access_token=current_user.google_access_token,
            refresh_token=current_user.google_refresh_token
        )
        
        message = gmail.get_message(message_id)
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        
        subject = message.get('subject', '')
        sender = message.get('sender', '')
        body = message.get('body', message.get('snippet', ''))
        
        prompt = f"""
        You are an AI assistant helping a user manage their emails.
        Generate a {request.tone} reply to the following email.
        
        Email Details:
        From: {sender}
        Subject: {subject}
        Content: {body}
        
        Additional Instructions: {request.instructions or "None"}
        
        Requirements:
        1. Keep the tone {request.tone}.
        2. Be concise but professional.
        3. Only provide the reply text, no preamble or extra commentary.
        """
        
        llm = LLMService()
        
        async def stream_generator():
            async for chunk in llm.stream_draft(prompt):
                yield chunk

        return StreamingResponse(stream_generator(), media_type="text/plain")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stream reply: {str(e)}")


def analyze_email_context(content: str, subject: str) -> dict:
    """Analyze email content to understand context and extract key details."""
    import re
    
    context = {
        "type": "general",
        "action": "acknowledge",
        "details": [],
        "entities": [],
        "action_items": []
    }
    
    # Extract property name with unit number (e.g., "Sobha Manhattan 5172")
    property_patterns = [
        r'(sobha\s+\w+\s*\d+)',  # Sobha Manhattan 5172
        r'(apartment\s+\d+)',  # Apartment 123
        r'(flat\s+(?:no\.?\s*)?\d+)',  # Flat No. 123
        r'(unit\s+\d+)',  # Unit 5172
        r'(villa\s+\d+)',  # Villa 123
    ]
    
    for pattern in property_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        for match in matches:
            clean_match = ' '.join(match.split()).title()
            if clean_match and clean_match not in context["entities"]:
                context["entities"].append(clean_match)
    
    # Detect action requests
    if any(word in content for word in ['possession', 'handover', 'keys', 'move in', 'move-in']):
        context["type"] = "possession"
        context["action"] = "proceed_possession"
        context["action_items"].append("proceed with the possession formalities")
    
    elif any(word in content for word in ['meeting', 'schedule', 'calendar', 'appointment', 'call', 'zoom', 'teams', 'discuss']):
        context["type"] = "meeting"
        context["action"] = "confirm_availability"
        context["action_items"].append("schedule the meeting")
    
    elif any(word in content for word in ['?', 'how', 'what', 'when', 'where', 'why', 'could you', 'can you', 'please explain']):
        context["type"] = "question"
        context["action"] = "provide_answer"
        context["action_items"].append("provide the requested information")
    
    elif any(word in content for word in ['invoice', 'payment', 'bill', 'amount', 'transaction', 'contract note', 'statement', 'receipt']):
        context["type"] = "financial"
        context["action"] = "acknowledge_receipt"
        context["action_items"].append("review and keep on file")
    
    elif any(word in content for word in ['request', 'need', 'require', 'help', 'assist', 'support', "let's", 'lets']):
        context["type"] = "request"
        context["action"] = "fulfill_request"
        # Try to extract what they're requesting
        action_match = re.search(r"let'?s\s+(take\s+the\s+possession|proceed|complete|finalize|schedule)", content, re.IGNORECASE)
        if action_match:
            context["action_items"].append(action_match.group(1).strip())
    
    elif any(word in content for word in ['confirm', 'update', 'status', 'progress', 'complete', 'done', 'finished']):
        context["type"] = "update"
        context["action"] = "acknowledge_update"
    
    elif any(word in content for word in ['order', 'delivery', 'shipping', 'tracking', 'package', 'dispatch']):
        context["type"] = "order"
        context["action"] = "track_order"
    
    return context



def build_contextual_reply(sender_name: str, subject: str, context: dict, tone: str) -> str:
    """Build a highly contextual reply based on analyzed content."""
    
    # Greeting based on tone
    if tone == "friendly":
        greeting = f"Hi {sender_name},"
        closing = "Thank you.\nBest Regards,"
    elif tone == "urgent":
        greeting = f"Dear {sender_name},"
        closing = "Best regards,"
    else:
        greeting = f"Hi {sender_name},"
        closing = "Thank you.\nBest Regards,"
    
    # Extract entity info for the reply
    entity_text = ""
    if context.get("entities"):
        # Clean up entities for display
        entities = [e.strip() for e in context["entities"] if e.strip()]
        if entities:
            entity_text = " – " + ", ".join(entities[:2])
    
    # Build action-specific body
    if context["type"] == "possession":
        action = context["action_items"][0] if context["action_items"] else "proceed with the possession formalities"
        body = f"Noted. We will {action} for {subject.replace('Regarding the ', '').replace('Re: ', '')}{entity_text} and keep you updated on the next steps."

    elif context["type"] == "meeting":
        if tone == "friendly":
            body = f'Thanks for reaching out! I will check my calendar and get back to you with available times for our discussion about {subject}.'
        else:
            body = f'Noted. I will review my calendar and confirm my availability for the meeting regarding {subject}.'

    elif context["type"] == "question":
        body = f'I have reviewed your query regarding {subject}. I will gather the information you need and get back to you shortly.'

    elif context["type"] == "financial":
        body = f'Noted. I have received and reviewed the financial documentation regarding {subject}. I will keep this on file and reach out if I have any questions.'

    elif context["type"] == "request":
        if context["action_items"]:
            action = context["action_items"][0]
            body = f'Noted. We will proceed with {action} and keep you updated on the next steps.'
        else:
            body = f'Noted. I have received your request regarding {subject} and will proceed accordingly. I will keep you updated on the progress.'

    elif context["type"] == "update":
        body = f'Noted. Thank you for the update on {subject}. I have noted the information and will take appropriate action.'

    elif context["type"] == "order":
        body = f'Noted. I have received the order/delivery details regarding {subject}. I will monitor the status and follow up if needed.'

    else:  # general
        if tone == "friendly":
            body = f'Thanks for your email regarding {subject}. I have noted the details and will get back to you shortly.'
        else:
            body = f'Noted. I have received your message regarding {subject} and will respond with the necessary information shortly.'

    return f"""{greeting}

{body}

{closing}"""


@router.post("/gmail/send-reply/{message_id}")
async def send_gmail_reply(
    message_id: str,
    request: SendReplyRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Send a reply to a Gmail message."""
    if not current_user.google_access_token:
        raise HTTPException(status_code=400, detail="Gmail not connected")
    
    try:
        gmail = GmailService(
            access_token=current_user.google_access_token,
            refresh_token=current_user.google_refresh_token
        )
        
        # Get original message to extract sender
        message = gmail.get_message(message_id)
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        
        # Extract sender email
        sender = message.get('sender', '')
        # Parse email from "Name <email@example.com>" format
        import re
        email_match = re.search(r'<([^>]+)>', sender)
        to_email = email_match.group(1) if email_match else sender
        
        # Build subject
        original_subject = message.get('subject', '')
        subject = request.subject or (f"Re: {original_subject}" if not original_subject.startswith("Re:") else original_subject)
        
        # Send reply
        success = gmail.send_email(to=to_email, subject=subject, body=request.body)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to send email")
        
        return {
            "success": True,
            "message": "Reply sent successfully",
            "to": to_email,
            "subject": subject
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send reply: {str(e)}")

