import pytest
from app.services.processor import process_message, CACHE_PROPERTIES
from app.models.models import Device, DeviceProperty

def test_auto_discovery(db_session, monkeypatch):
    factory_id = "fct-001"
    device_id = "dev-001"
    payload = {"temperature": 25.5, "pressure": 10}
    
    # Ensure cache is clean for test
    if device_id in CACHE_PROPERTIES:
        del CACHE_PROPERTIES[device_id]
        
    # Process
    process_message(factory_id, device_id, payload)
    
    # Check DB
    props = db_session.query(DeviceProperty).filter(
        DeviceProperty.device_id == device_id,
        DeviceProperty.factory_id == factory_id
    ).all()
    
    assert len(props) == 2
    prop_names = {p.property_name for p in props}
    assert "temperature" in prop_names
    assert "pressure" in prop_names

def test_invalid_payload_handling(db_session):
    # String values should be ignored as per LLD 6.2 (numeric/bool only)
    factory_id = "fct-002"
    device_id = "dev-002"
    payload = {"valid": 100, "invalid": "text"}
    
    if device_id in CACHE_PROPERTIES:
        del CACHE_PROPERTIES[device_id]
        
    process_message(factory_id, device_id, payload)
    
    props = db_session.query(DeviceProperty).filter(DeviceProperty.device_id == device_id).all()
    assert len(props) == 1
    assert props[0].property_name == "valid"
