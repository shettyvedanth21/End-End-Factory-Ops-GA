from datetime import datetime, timedelta
from app.services.processor import process_event
from app.models.models import Rule, Alert
from sqlalchemy import text

# Helper to create rule
def create_rule(session, rid, fid, did, conds, cooldown=300, resolve=False):
    rule = Rule(
        id=rid,
        factory_id=fid,
        device_id=did,
        name="Test Rule",
        is_active=True,
        conditions=conds,
        condition_operator="AND",
        cooldown_seconds=cooldown,
        auto_resolve=resolve
    )
    session.add(rule)
    session.commit()
    return rule

def test_alert_creation_integration(db_session):
    # This tests the full flow inside process_event
    fid, did = "fct-001", "dev-001"
    
    # Create rule
    create_rule(db_session, "r1", fid, did, [{"property": "temp", "operator": "GT", "threshold": 100}])
    
    # Process event
    process_event({"factory_id": fid, "device_id": did, "properties": {"temp": 101}})
    
    # Verify
    alert = db_session.query(Alert).filter(Alert.rule_id == "r1").first()
    assert alert is not None
    assert alert.status == "open"

def test_cooldown_integration(db_session):
    fid, did = "fct-001", "dev-001"
    create_rule(db_session, "r2", fid, did, [{"property": "temp", "operator": "GT", "threshold": 100}], cooldown=60)
    
    # Trigger 1
    process_event({"factory_id": fid, "device_id": did, "properties": {"temp": 101}})
    assert db_session.query(Alert).count() == 1
    
    # Trigger 2 (immediate)
    process_event({"factory_id": fid, "device_id": did, "properties": {"temp": 102}})
    assert db_session.query(Alert).count() == 1 # Cooldown active

def test_auto_resolve_integration(db_session):
    fid, did = "fct-001", "dev-001"
    create_rule(db_session, "r3", fid, did, [{"property": "temp", "operator": "GT", "threshold": 100}], resolve=True)
    
    # Trigger OPEN
    process_event({"factory_id": fid, "device_id": did, "properties": {"temp": 101}})
    alert = db_session.query(Alert).filter(Alert.rule_id == "r3").first()
    assert alert.status == "open"
    
    # Trigger NORMAL
    process_event({"factory_id": fid, "device_id": did, "properties": {"temp": 90}})
    
    # Refresh
    db_session.refresh(alert)
    assert alert.status == "resolved"
    assert alert.resolved_at is not None
