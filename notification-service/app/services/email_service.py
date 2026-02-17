import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings
import logging

logger = logging.getLogger("email-sender")

class EmailService:
    def send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        try:
            msg = MIMEMultipart()
            msg["From"] = settings.SMTP_FROM_EMAIL
            msg["To"] = to_email
            msg["Subject"] = subject
            
            msg.attach(MIMEText(html_content, "html"))
            
            # Use context manager for SMTP connection
            with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)
                
            return True
        except Exception as e:
            logger.error(f"Email failed to {to_email}: {e}")
            return False

email_service = EmailService()
