from twilio.rest import Client
from app.core.config import settings
import logging

logger = logging.getLogger("whatsapp-sender")

class WhatsAppService:
    def __init__(self):
        try:
            if settings.TWILIO_ACCOUNT_SID:
                self.client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            else:
                self.client = None
        except Exception:
            self.client = None

    def send_whatsapp(self, to_number: str, message: str) -> bool:
        if not self.client:
            logger.error("Twilio client not initialized")
            return False
            
        try:
            # Twilio sandbox requires numbers prefixed with "whatsapp:"
            from_ = f"whatsapp:{settings.TWILIO_FROM_NUMBER}"
            to_ = f"whatsapp:{to_number}"
            
            message = self.client.messages.create(
                from_=from_,
                body=message,
                to=to_
            )
            return True if message.sid else False
            
        except Exception as e:
            logger.error(f"WhatsApp failed to {to_number}: {e}")
            return False

whatsapp_service = WhatsAppService()
