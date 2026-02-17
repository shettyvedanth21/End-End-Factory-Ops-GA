from sqlalchemy import Column, String, DateTime, Enum, JSON, Integer, ForeignKey
from datetime import datetime
from app.core.database import Base
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class AnalyticsJob(Base):
    __tablename__ = "analytics_jobs"
    
    id = Column(String(36), primary_key=True) # ID sent from API service
    factory_id = Column(String(36), nullable=False)
    name = Column(String(255), nullable=False)
    status = Column(Enum("queued", "running", "completed", "failed"), default="queued")
    
    # Configuration
    job_type = Column(Enum("training", "inference"), nullable=False)
    model_name = Column(String(255), nullable=True) # Used for inference or output of training
    target_variable = Column(String(255), nullable=True)
    features = Column(JSON, nullable=True)
    algorithm = Column(String(50), nullable=True) # e.g., 'random_forest', 'linear_regression'
    hyperparameters = Column(JSON, nullable=True)
    
    # Dataset references
    data_range_start = Column(DateTime, nullable=True)
    data_range_end = Column(DateTime, nullable=True)
    device_ids = Column(JSON, nullable=True) 
    dataset_s3_key = Column(String(512), nullable=True)
    
    # Results
    artifact_s3_prefix = Column(String(512), nullable=True)
    metrics = Column(JSON, nullable=True)
    error_message = Column(String(1024), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

class AnalyticsModel(Base):
    __tablename__ = "analytics_models"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    factory_id = Column(String(36), nullable=False)
    name = Column(String(255), nullable=False)
    version = Column(Integer, nullable=False, default=1)
    description = Column(String(1024), nullable=True)
    
    algorithm = Column(String(50), nullable=False)
    hyperparameters = Column(JSON, nullable=True)
    training_metrics = Column(JSON, nullable=True)
    
    s3_key = Column(String(512), nullable=False) # Location of the .pkl or .h5
    created_at = Column(DateTime, default=datetime.utcnow)
    job_id = Column(String(36), ForeignKey("analytics_jobs.id"), nullable=True)
