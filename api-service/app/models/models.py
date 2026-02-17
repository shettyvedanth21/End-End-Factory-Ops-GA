from sqlalchemy import Column, String, Boolean, DateTime, Enum, ForeignKey, Integer, Float, Text, JSON, UniqueConstraint, func
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class Factory(Base):
    __tablename__ = "factories"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), nullable=False, unique=True)
    timezone = Column(String(64), nullable=False, default="UTC")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    users = relationship("User", back_populates="factory")
    devices = relationship("Device", back_populates="factory")

class User(Base):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    factory_id = Column(String(36), ForeignKey("factories.id"), nullable=True) # Null for Platform Root
    email = Column(String(255), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum("platform_root", "super_admin", "admin"), nullable=False)
    can_write = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
    last_login_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    factory = relationship("Factory", back_populates="users")

class Device(Base):
    __tablename__ = "devices"
    
    id = Column(String(36), primary_key=True, default=generate_uuid) # Often provided by external system, but we can generate if needed. LLD says "id ... PRIMARY KEY". API POST allows providing ID.
    factory_id = Column(String(36), ForeignKey("factories.id"), nullable=False)
    name = Column(String(255), nullable=False)
    type = Column(String(100), nullable=False)
    location = Column(String(255), nullable=True)
    status = Column(Enum("active", "inactive", "maintenance"), nullable=False, default="active")
    last_seen_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    factory = relationship("Factory", back_populates="devices")
    properties = relationship("DeviceProperty", back_populates="device")
    rules = relationship("Rule", back_populates="device")

class DeviceProperty(Base):
    __tablename__ = "device_properties"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    factory_id = Column(String(36), ForeignKey("factories.id"), nullable=False)
    device_id = Column(String(36), ForeignKey("devices.id"), nullable=False)
    property_name = Column(String(255), nullable=False)
    unit = Column(String(50), nullable=True)
    data_type = Column(Enum("float", "integer", "boolean", "string"), nullable=False, default="float") # Using specific enums might need imports
    first_seen_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_seen_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    device = relationship("Device", back_populates="properties")
    __table_args__ = (UniqueConstraint('device_id', 'property_name', name='uq_dp_device_property'),)

class Rule(Base):
    __tablename__ = "rules"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    factory_id = Column(String(36), ForeignKey("factories.id"), nullable=False)
    device_id = Column(String(36), ForeignKey("devices.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    conditions = Column(JSON, nullable=False)
    condition_operator = Column(Enum("AND", "OR"), nullable=False, default="AND")
    schedule_start = Column(String(8), nullable=True) # Time type in SQL, String in Python/SQLAlchemy often used for simple time storage unless using Time type explicitly. LLD says TIME. I'll use String for simplicity or standard Time type. SQLAlchemy has Time.
    schedule_end = Column(String(8), nullable=True)
    cooldown_seconds = Column(Integer, nullable=False, default=300)
    auto_resolve = Column(Boolean, nullable=False, default=False)
    created_by = Column(String(36), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    device = relationship("Device", back_populates="rules")

class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    factory_id = Column(String(36), ForeignKey("factories.id"), nullable=False)
    rule_id = Column(String(36), ForeignKey("rules.id"), nullable=False)
    device_id = Column(String(36), ForeignKey("devices.id"), nullable=False)
    status = Column(Enum("open", "acknowledged", "resolved"), nullable=False, default="open")
    triggered_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    acknowledged_at = Column(DateTime, nullable=True)
    acknowledged_by = Column(String(36), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    trigger_values = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)

class NotificationLog(Base):
    __tablename__ = "notification_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    factory_id = Column(String(36), ForeignKey("factories.id"), nullable=False)
    alert_id = Column(String(36), ForeignKey("alerts.id"), nullable=False)
    channel = Column(Enum("email", "whatsapp"), nullable=False)
    recipient = Column(String(255), nullable=False)
    status = Column(Enum("sent", "failed", "pending"), nullable=False, default="pending")
    sent_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

class AnalyticsJob(Base):
    __tablename__ = "analytics_jobs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    factory_id = Column(String(36), ForeignKey("factories.id"), nullable=False)
    name = Column(String(255), nullable=False)
    mode = Column(Enum("standard", "ai_copilot"), nullable=False)
    analysis_type = Column(String(100), nullable=False)
    status = Column(Enum("queued", "running", "completed", "failed"), nullable=False, default="queued")
    model_name = Column(String(255), nullable=True)
    model_version = Column(String(50), nullable=True)
    dataset_s3_key = Column(String(512), nullable=True)
    artifact_s3_prefix = Column(String(512), nullable=True)
    hyperparameters = Column(JSON, nullable=True)
    metrics = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_by = Column(String(36), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

class AnalyticsModel(Base):
    __tablename__ = "analytics_models"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    factory_id = Column(String(36), ForeignKey("factories.id"), nullable=False)
    name = Column(String(255), nullable=False)
    version = Column(String(50), nullable=False)
    analysis_type = Column(String(100), nullable=False)
    source_job_id = Column(String(36), nullable=False) # LLD says source_job_id, not FK? "Constraint fk_jobs..." wait, LLD doesn't list FK for source_job_id in CREATE TABLE block, but implies relationship. I'll stick to LLD exactly: just a string field.
    artifact_s3_key = Column(String(512), nullable=False)
    hyperparameters = Column(JSON, nullable=True)
    metrics = Column(JSON, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    __table_args__ = (UniqueConstraint('factory_id', 'name', 'version', name='uq_model_version'),)

class Report(Base):
    __tablename__ = "reports"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    factory_id = Column(String(36), ForeignKey("factories.id"), nullable=False)
    name = Column(String(255), nullable=False)
    type = Column(Enum("energy", "alerts", "analytics", "custom"), nullable=False)
    format = Column(Enum("pdf", "excel", "json"), nullable=False)
    status = Column(Enum("queued", "generating", "completed", "failed"), nullable=False, default="queued")
    s3_key = Column(String(512), nullable=True)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    parameters = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    generated_at = Column(DateTime, nullable=True)
    created_by = Column(String(36), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True) # BIGINT in LLD
    factory_id = Column(String(36), nullable=True)
    user_id = Column(String(36), nullable=True)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(100), nullable=True)
    entity_id = Column(String(36), nullable=True)
    payload = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
