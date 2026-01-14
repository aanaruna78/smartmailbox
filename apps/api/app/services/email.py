import imaplib
import smtplib
import socket
from app.utils.error_mapping import map_connection_error

def test_imap_connection(host: str, port: int, username: str, password: str, use_ssl: bool = True) -> bool:
    try:
        if use_ssl:
            mail = imaplib.IMAP4_SSL(host, port, timeout=10)
        else:
            mail = imaplib.IMAP4(host, port, timeout=10)
        
        mail.login(username, password)
        mail.logout()
        return True, "Connection successful"
    except Exception as e:
        return False, map_connection_error(e)

def test_smtp_connection(host: str, port: int, username: str, password: str, use_ssl: bool = None) -> bool:
    try:
        # Port 465 = SMTP_SSL (direct SSL)
        # Port 587 = SMTP with STARTTLS
        if port == 465:
            server = smtplib.SMTP_SSL(host, port, timeout=10)
        else:
            # Port 587 or others - use STARTTLS
            server = smtplib.SMTP(host, port, timeout=10)
            server.ehlo()
            server.starttls()
            server.ehlo()
            
        server.login(username, password)
        server.quit()
        return True, "Connection successful"
    except Exception as e:
        return False, map_connection_error(e)

