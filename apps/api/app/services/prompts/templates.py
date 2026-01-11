# Prompt Templates
# We use simple f-string style replacement or Jinja2 style. 
# For simplicity and no extra deps, we'll use Python's str.format or f-strings in the builder, 
# but storing them here as raw strings with placeholders helps organization.

DRAFT_REPLY_SYSTEM_PROMPT_V1 = """
You are an intelligent email assistant. Your job is to draft a reply to an email based on the context provided.
Follow these policies:
- Maintain a {tone} tone.
- Be concise and clear.
- Do not make up facts not present in the context.
- {custom_constraints}

Context:
{context}

User Instructions:
{instructions}

Draft the email reply:
"""

# Context format
EMAIL_CONTEXT_TEMPLATE = """
From: {sender}
To: {recipients}
Subject: {subject}
Date: {date}

Body:
{body}
"""
