import socket
import ssl
import imaplib
import smtplib

def map_connection_error(e: Exception) -> str:
    """
    Maps various technical exceptions to human-readable error messages
    for Mailbox connection testing (IMAP/SMTP).
    """
    error_str = str(e)
    
    # DNS / Network Resolution Errors
    if isinstance(e, socket.gaierror):
        return "Unable to resolve the server address. Please check if the Hostname is correct."
    
    # Timeout Errors
    if isinstance(e, (socket.timeout, TimeoutError)):
        return "Connection timed out. The server is not responding. Check the Port and your internet connection."
    
    # Connection Refused (often wrong port or firewall)
    if isinstance(e, ConnectionRefusedError):
        return "Connection refused. Please check if the Port is correct and the server accepts connections."
            
    # SSL/TLS Errors
    if isinstance(e, ssl.SSLError):
        return "Secure connection failed (SSL/TLS). Check if the server supports SSL on this port."

    # IMAP Specific Errors
    if isinstance(e, imaplib.IMAP4.error):
        # Specific auth failure often contains "AUTHENTICATIONFAILED" or similar keywords
        if "AUTHENTICATIONFAILED" in error_str or "login failed" in error_str.lower():
            return "Authentication failed. Please check your Email and Password. (Note: Gmail/Outlook require an App Password)."
        return f"IMAP Error: {error_str}"

    # SMTP Specific Errors
    if isinstance(e, smtplib.SMTPAuthenticationError):
        return "Authentication failed. Please check your Email and Password. (Note: Gmail/Outlook require an App Password)."
    
    if isinstance(e, smtplib.SMTPConnectError):
        return "Failed to connect to the SMTP server. Check Hostname and Port."
    
    if isinstance(e, smtplib.SMTPHeloError):
        return "The server refused our HELO message."

    # Fallback for generic exceptions
    return f"Connection failed: {error_str}"
