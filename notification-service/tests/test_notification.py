from datetime import datetime
from app.models.models import NotificationLog, User
from app.services.worker import process_notification
import pytest

def test_process_notification_success(db_session, monkeypatch):
    import app.services.worker as worker_module
    
    class MockSMTP:
        def send_email(self, *args, **kwargs):
            return True
            
    class MockWhatsApp:
        def send_whatsapp(self, *args, **kwargs):
            return True
            
    monkeypatch.setattr(worker_module, "email_service", MockSMTP())
    monkeypatch.setattr(worker_module, "whatsapp_service", MockWhatsApp())

    factory_id = "fct-001"
    alert = {"id": "alert-001", "device_id": "dev-001", "triggered_at": str(datetime.utcnow()), "trigger_values": {"temp": 101}}
    rule = {"name": "High Temp Rule"}
    
    # 1. Create recipient user
    user = User(
        id="usr-admin",
        factory_id=factory_id,
        email="admin@factory.com",
        phone_number="+1234567890",
        role="admin"
    )
    db_session.add(user)
    db_session.commit()
    
    # Run
    process_notification(alert, rule, factory_id)
    
    # Verify Logs
    logs = db_session.query(NotificationLog).filter(NotificationLog.factory_id==factory_id).all()
    # Should be 2 (Email + WA)
    assert len(logs) == 2
    
    email_log = next((l for l in logs if l.channel == "email"), None)
    assert email_log.status == "sent"
    
    wa_log = next((l for l in logs if l.channel == "whatsapp"), None)
    assert wa_log.status == "sent"

def test_process_notification_failure(db_session, monkeypatch):
    import app.services.worker as worker_module
    
    class FailingSMTP:
        def send_email(self, *args, **kwargs):
            return False 
            
    monkeypatch.setattr(worker_module, "email_service", FailingSMTP())
    
    factory_id = "fct-002"
    alert = {"id": "alert-002", "device_id": "dev-002"}
    rule = {"name": "Test Rule"}
    
    user = User(
        id="usr-admin-2",
        factory_id=factory_id,
        email="admin2@factory.com",
        role="admin"
    )
    db_session.add(user)
    db_session.commit()
    
    process_notification(alert, rule, factory_id)
    
    logs = db_session.query(NotificationLog).filter(NotificationLog.factory_id==factory_id).all()
    assert len(logs) == 1
    assert logs[0].status == "failed"
    assert logs[0].retry_count == 1
