from datetime import datetime, timedelta
from app.models.models import Report
from app.services.worker import process_report
import pytest

def test_process_report_success(db_session):
    factory_id = "fct-001"
    report_id = "report-001"
    
    # 1. Create Report in DB
    report = Report(
        id=report_id,
        factory_id=factory_id,
        name="Test Report",
        status="queued",
        type="energy",
        format="pdf",
        time_range_start=datetime.utcnow() - timedelta(days=1),
        time_range_end=datetime.utcnow(),
        device_ids=["dev-1"]
    )
    db_session.add(report)
    db_session.commit()
    
    # Run
    process_report(factory_id, report_id)
    
    # Verify
    db_session.expire(report)
    db_session.refresh(report)
    assert report.status == "completed"
    assert report.s3_key == f"factoryops/{factory_id}/reports/{report_id}/report.pdf"

def test_process_report_failure_on_upload(db_session, monkeypatch):
    import app.services.worker as worker_module
    
    class FailingMinio:
        def upload_bytes(self, *args, **kwargs):
            return False 
            
    monkeypatch.setattr(worker_module, "minio_service", FailingMinio())
    
    factory_id = "fct-001"
    report_id = "report-fail"
    
    report = Report(
        id=report_id,
        factory_id=factory_id,
        name="Fail Report",
        status="queued",
        type="energy",
        format="pdf",
        time_range_start=datetime.utcnow(),
        time_range_end=datetime.utcnow(),
    )
    db_session.add(report)
    db_session.commit()
    
    process_report(factory_id, report_id)
    
    db_session.expire(report)
    db_session.refresh(report)
    
    assert report.status == "failed"
    assert "Upload failed" in str(report.error_message)
