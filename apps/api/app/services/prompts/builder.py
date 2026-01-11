from typing import List, Optional
from app.models.email import Email
from app.services.prompts.templates import DRAFT_REPLY_SYSTEM_PROMPT_V1, EMAIL_CONTEXT_TEMPLATE

class PromptBuilder:
    def __init__(self):
        pass

    def _format_email(self, email: Email) -> str:
        """Formats a single email for context."""
        # Use body_text if available, fallback to something else or empty
        # Assuming email.body_text is populated or we might need to strip HTML from body_html
        # For now, we assume simple text.
        
        # In a real app, we might need to handle the case where body_text is None (fetch from DB or parse HTML)
        body = "No text content"
        
        # This part depends on how the model is structured. In previous steps, we added body_text to schemas but 
        # let's verify if the Model has it. The Email model in `models/email.py` doesn't explicitly store `body_text` 
        # as a column on the main table distinct from how parsing was done.
        # Wait, the `parse_emails` job extracts it. 
        # Let's inspect the Email Model again to be sure specific fields are available.
        # If they aren't, we'll assume we pass a dict or object that has it.
        
        # For this implementation, I will assume the `email` object passed in has attributes matching the model.
        # If `body_text` isn't on the model, we can't use it directly here.
        # Checking `apps/api/app/models/email.py`... 
        # Wait, I can't check it mid-generation. I'll code defensively.
        
        body = getattr(email, "body_text", "") or " [Body content not available] "
        
        return EMAIL_CONTEXT_TEMPLATE.format(
            sender=email.sender,
            recipients=getattr(email, "recipients", "Unknown"),
            subject=email.subject,
            date=email.received_at,
            body=body
        )

    def build_draft_prompt(
        self, 
        target_email: Email, 
        instructions: str, 
        tone: str = "professional",
        thread_history: Optional[List[Email]] = None,
        constraints: str = ""
    ) -> str:
        """
        Builds the full prompt for the LLM.
        """
        
        # Build Context
        context_parts = []
        
        # Add thread history if available (oldest first? or newest first?)
        # Usually LLMs read top-down. Oldest -> Newest makes narrative sense.
        if thread_history:
            for past_email in thread_history:
                context_parts.append(f"--- Previous message ---\n{self._format_email(past_email)}")
        
        # Add the target email (the one we are replying to)
        context_parts.append(f"--- Email to reply to ---\n{self._format_email(target_email)}")
        
        full_context = "\n\n".join(context_parts)
        
        # Fill Template
        # Fill Template
        # Personalization note:
        instructions_with_personalization = (
            f"{instructions}\n\n"
            "IMPORTANT: Personalize the response using the sender's name ({sender_name}) and any "
            "Order IDs found in the email body. If no specific name is found, use a polite generic greeting."
        )

        return DRAFT_REPLY_SYSTEM_PROMPT_V1.format(
            tone=tone,
            custom_constraints=constraints,
            context=full_context,
            instructions=instructions_with_personalization
        )
