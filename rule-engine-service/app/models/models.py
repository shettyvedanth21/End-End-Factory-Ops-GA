from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, Integer, Boolean, Text, JSON
from datetime import datetime
from app.core.database import Base
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class Rule(Base):
    __tablename__ = "rules"
    id = Column(String(36), primary_key=True)
    factory_id = Column(String(36), nullable=False)
    device_id = Column(String(36), nullable=False)
    name = Column(String(255), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    conditions = Column(JSON, nullable=False)
    condition_operator = Column(Enum("AND", "OR"), nullable=False, default="AND")
    schedule_start = Column(String(8), nullable=True) # HH:MM:SS
    schedule_end = Column(String(8), nullable=True)
    cooldown_seconds = Column(Integer, nullable=False, default=300)
    auto_resolve = Column(Boolean, nullable=False, default=False)
    
class Alert(Base):
    __tablename__ = "alerts"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    factory_id = Column(String(36), nullable=False)
    rule_id = Column(String(36), ForeignKey("rules.id"), nullable=False)
    device_id = Column(String(36), nullable=False)
    status = Column(Enum("open", "acknowledged", "resolved"), nullable=False, default="open")
    triggered_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    trigger_values = Column(JSON, nullable=True)

class NotificationLog(Base):
    __tablename__ = "notification_logs"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    factory_id = Column(String(36), nullable=False)
    alert_id = Column(String(36), ForeignKey("alerts.id"), nullable=False)
    channel = Column(Enum("email", "whatsapp"), nullable=False)
    status = Column(Enum("pending", "sent", "failed"), nullable=False, default="pending")
    retry_count = Column(Integer, nullable=False, default=0)
