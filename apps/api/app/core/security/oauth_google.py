from typing import Optional, Dict, Any
from google.oauth2 import id_token
from google.auth.transport import requests
from app.core.config import settings

async def verify_google_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify the Google ID Token.
    Checks the signature and the 'aud' claim (Client ID).
    """
    try:
        # Create a request for verifying the token
        request = requests.Request()
        
        # Verify the token
        id_info = id_token.verify_oauth2_token(
            token, 
            request, 
            settings.GOOGLE_CLIENT_ID
        )

        # ID token is valid.
        # id_info contains the user information (email, name, sub, etc.)
        return id_info

    except ValueError as e:
        # Invalid token
        print(f"Token verification failed: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error during token verification: {e}")
        return None
