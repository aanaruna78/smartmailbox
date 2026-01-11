from cryptography.fernet import Fernet
from app.core.config import settings

def get_fernet():
    return Fernet(settings.ENCRYPTION_KEY)

def encrypt_password(password: str) -> str:
    f = get_fernet()
    return f.encrypt(password.encode()).decode()

def decrypt_password(encrypted_password: str) -> str:
    f = get_fernet()
    return f.decrypt(encrypted_password.encode()).decode()
