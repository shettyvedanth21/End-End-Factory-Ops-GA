from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, UniqueConstraint
from datetime import datetime
from app.core.database import Base
import uuid

def generate_uuid():
    return str(uuid.uuid4())

# We only need minimal models to support auto-discovery and validation

class Factory(Base):
    __tablename__ = "factories"
    id = Column(String(36), primary_key=True)
    # Other fields omitted as we don't query them in telemetry

class Device(Base):
    __tablename__ = "devices"
    id = Column(String(36), primary_key=True)
    factory_id = Column(String(36), nullable=False)
    status = Column(Enum("active", "inactive", "maintenance"), nullable=False, default="active")
    last_seen_at = Column(DateTime, nullable=True)

class DeviceProperty(Base):
    __tablename__ = "device_properties"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    factory_id = Column(String(36), nullable=False)
    device_id = Column(String(36), nullable=False)
    property_name = Column(String(255), nullable=False)
    data_type = Column(Enum("float", "integer", "boolean", "string"), nullable=False, default="float")
    first_seen_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_seen_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (UniqueConstraint('device_id', 'property_name', name='uq_dp_device_property'),)
