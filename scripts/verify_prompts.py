import sys
import os
import datetime

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'apps', 'api'))

from app.services.prompts.builder import PromptBuilder

# Mock Email Object
class MockEmail:
    def __init__(self, sender, subject, body, received_at):
        self.sender = sender
        self.recipients = "me@example.com"
        self.subject = subject
        self.body_text = body
        self.received_at = received_at

def test_prompt_builder():
    print("--- Verifying Prompt Builder ---")
    
    # Setup Data
    email = MockEmail(
        sender="boss@corp.com", 
        subject="Project Deadline", 
        body="Hey, when is the project due? We need it by Friday.",
        received_at=datetime.datetime.now()
    )
    
    instructions = "Tell him it will be done on Thursday."
    tone = "professional"
    
    # Unpack Builder
    builder = PromptBuilder()
    prompt = builder.build_draft_prompt(email, instructions, tone)
    
    print("\n--- Generated Prompt ---")
    print(prompt)
    print("\n------------------------")
    
    # Basic Validations
    if "boss@corp.com" in prompt and "Thursday" in prompt and "professional" in prompt:
        print("✅ Prompt contains key elements.")
    else:
        print("❌ Prompt missing key elements.")

if __name__ == "__main__":
    test_prompt_builder()
