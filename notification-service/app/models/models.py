from sqlalchemy import Column, String, DateTime, Enum, JSON, Integer, ForeignKey, Text
from datetime import datetime
from app.core.database import Base
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class NotificationLog(Base):
    __tablename__ = "notification_logs"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    factory_id = Column(String(36), nullable=False)
    alert_id = Column(String(36), nullable=False) # ForeignKey("alerts.id") if desired, but loose coupling is fine
    
    channel = Column(Enum("email", "whatsapp"), nullable=False)
    recipient = Column(String(255), nullable=False)
    subject = Column(String(255), nullable=True) # Email subject
    message_body = Column(Text, nullable=False)
    
    status = Column(Enum("pending", "sent", "failed"), default="pending")
    retry_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    sent_at = Column(DateTime, nullable=True)

class User(Base):
    __tablename__ = "users"
    id = Column(String(36), primary_key=True)
    factory_id = Column(String(36))
    email = Column(String(255))
    phone_number = Column(String(50))
    role = Column(String(50))
    # We map to this table to find recipients for factory admins
