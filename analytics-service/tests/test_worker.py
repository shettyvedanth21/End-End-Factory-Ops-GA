from datetime import datetime, timedelta
# Need to import job/model from app.models.models
from app.models.models import AnalyticsJob, AnalyticsModel
from app.services.worker import process_job
import pytest
import pandas as pd

def test_process_job_success(db_session, monkeypatch):
    import app.services.worker as worker_module
    
    # Mock Influx
    class MockInflux:
        def query_dataset(self, *args, **kwargs):
            return pd.DataFrame({
                "feature1": [1.0, 2.0, 3.0, 4.0, 5.0], 
                "feature2": [10, 20, 30, 40, 50],
                "target": [1, 2, 3, 4, 5]
            })
            
    # Mock MinIO
    class MockMinio:
        def upload_bytes(self, key, data):
            # Assert key format if needed
            return True
            
    monkeypatch.setattr(worker_module, "influx_service", MockInflux())
    monkeypatch.setattr(worker_module, "minio_service", MockMinio())
    
    factory_id = "fct-001"
    job_id = "job-001"
    
    # Create Job
    job = AnalyticsJob(
        id=job_id,
        factory_id=factory_id,
        name="Test Job",
        status="queued",
        job_type="training", 
        target_variable="target", # MUST match column in mock dataframe
        device_ids=["dev-1"],
        data_range_start=datetime.utcnow() - timedelta(days=1),
        data_range_end=datetime.utcnow(),
    )
    db_session.add(job)
    db_session.commit()
    
    # Run
    process_job(factory_id, job_id)
    
    # Verify
    db_session.refresh(job)
    assert job.status == "completed"
    assert job.dataset_s3_key is not None
    assert job.metrics is not None
    
    model = db_session.query(AnalyticsModel).filter(AnalyticsModel.job_id == job_id).first()
    assert model is not None
    assert model.name == "model-job-001"

def test_process_job_failure_empty_data(db_session, monkeypatch):
    import app.services.worker as worker_module
    
    class MockEmptyInflux:
        def query_dataset(self, *args, **kwargs):
            return pd.DataFrame() # Empty
    
    monkeypatch.setattr(worker_module, "influx_service", MockEmptyInflux())
    
    factory_id = "fct-001"
    job_id = "job-fail"
    
    job = AnalyticsJob(
        id=job_id,
        factory_id=factory_id,
        name="Fail Job",
        status="queued",
        job_type="training",
        target_variable="target",
        device_ids=["dev-1"],
        data_range_start=datetime.utcnow() - timedelta(days=1),
        data_range_end=datetime.utcnow(),
    )
    db_session.add(job)
    db_session.commit()
    
    process_job(factory_id, job_id)
    
    db_session.refresh(job)
    assert job.status == "failed"
