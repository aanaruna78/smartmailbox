import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class SMTPClient:
    def __init__(self, host: str, port: int, email_address: str, password: str):
        self.host = host
        self.port = port
        self.email_address = email_address
        self.password = password
        self.connection = None

    def connect(self):
        """Connect to the SMTP server."""
        try:
            # Try connecting with SSL (common for port 465)
            if self.port == 465:
                self.connection = smtplib.SMTP_SSL(self.host, self.port)
            else:
                self.connection = smtplib.SMTP(self.host, self.port)
                # Try StartTLS (common for port 587)
                try:
                    self.connection.starttls()
                except smtplib.SMTPNotSupportedError:
                    pass # Server might not support starttls or it's already secure

            self.connection.login(self.email_address, self.password)
            logger.info(f"Connected to SMTP server {self.host} as {self.email_address}")
        except Exception as e:
            logger.error(f"Failed to connect to SMTP server: {e}")
            raise

    def disconnect(self):
        """Quit the SMTP connection."""
        if self.connection:
            try:
                self.connection.quit()
            except Exception:
                pass
            self.connection = None

    def send_email(self, to_email: str, subject: str, body: str, html_body: Optional[str] = None):
        """Send an email to a recipient."""
        if not self.connection:
            raise Exception("Not connected")

        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.email_address
            msg['To'] = to_email

            # Create the body of the message (a plain-text and an HTML version)
            part1 = MIMEText(body, 'plain')
            msg.attach(part1)

            if html_body:
                part2 = MIMEText(html_body, 'html')
                msg.attach(part2)

            self.connection.sendmail(self.email_address, to_email, msg.as_string())
            logger.info(f"Email sent to {to_email}")
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            raise

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
