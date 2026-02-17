from sqlalchemy import Column, String, DateTime, Enum, JSON, Integer, ForeignKey, Text
from datetime import datetime
from app.core.database import Base
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    factory_id = Column(String(36), nullable=True) # Platform root has no factory
    email = Column(String(255), unique=True, nullable=False)
    phone_number = Column(String(50), nullable=True)
    role = Column(String(50), nullable=False)
    
class Device(Base):
    __tablename__ = "devices"
    id = Column(String(36), primary_key=True)
    factory_id = Column(String(36), nullable=False)
    name = Column(String(255), nullable=False)
    type = Column(String(100), nullable=False)
    location = Column(String(255), nullable=True)
    status = Column(Enum('active', 'inactive', 'maintenance'), default='active')
    last_seen_at = Column(DateTime, nullable=True)

class Rule(Base):
    __tablename__ = "rules"
    id = Column(String(36), primary_key=True)
    factory_id = Column(String(36), nullable=False)
    device_id = Column(String(36))
    name = Column(String(255))
    is_active = Column(Integer) # Boolean
    conditions = Column(JSON)

class Alert(Base):
    __tablename__ = "alerts"
    id = Column(String(36), primary_key=True)
    factory_id = Column(String(36))
    rule_id = Column(String(36))
    device_id = Column(String(36))
    status = Column(String(50))
    triggered_at = Column(DateTime)
    trigger_values = Column(JSON)
