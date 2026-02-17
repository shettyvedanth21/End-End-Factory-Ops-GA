from sqlalchemy import Column, String, DateTime, Enum, JSON, Integer
from datetime import datetime
from app.core.database import Base
import uuid

class Report(Base):
    __tablename__ = "reports"
    
    id = Column(String(36), primary_key=True)
    factory_id = Column(String(36), nullable=False)
    name = Column(String(255), nullable=False)
    status = Column(Enum("queued", "generating", "completed", "failed"), default="queued")
    
    type = Column(Enum("energy", "production", "alerts", "custom"), nullable=False)
    format = Column(Enum("pdf", "excel", "json"), default="pdf")
    
    # Parameters
    time_range_start = Column(DateTime, nullable=False)
    time_range_end = Column(DateTime, nullable=False)
    device_ids = Column(JSON, nullable=True)
    include_analytics = Column(Integer, default=0) # Boolean 0/1, SQL doesn't really have bool sometimes in certain adapters but boolean works in SA
    
    # Result
    s3_key = Column(String(512), nullable=True)
    error_message = Column(String(1024), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    generated_at = Column(DateTime, nullable=True)
