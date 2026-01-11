import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings

class SMTPService:
    def __init__(self):
        self.host = settings.SMTP_HOST
        self.port = settings.SMTP_PORT
        self.user = settings.SMTP_USER
        self.password = settings.SMTP_PASSWORD
        self.from_email = settings.EMAILS_FROM_EMAIL or self.user

    def send_email(self, to_email: str, subject: str, body_html: str, body_text: str = None) -> bool:
        """
        Sends an email using SMTP.
        """
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.from_email
            msg["To"] = to_email

            if body_text:
                part1 = MIMEText(body_text, "plain")
                msg.attach(part1)
            
            if body_html:
                part2 = MIMEText(body_html, "html")
                msg.attach(part2)

            with smtplib.SMTP(self.host, self.port) as server:
                if settings.SMTP_TLS:
                    server.starttls()
                if self.user and self.password:
                    server.login(self.user, self.password)
                
                server.sendmail(self.from_email, to_email, msg.as_string())
            
            return True
        except Exception as e:
            print(f"SMTP Error: {e}")
            # In a real app, log with a proper logger
            return False
