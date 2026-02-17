from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.api.v1.api import api_router
from app.models.models import User, Factory, Device
from app.core import security
from app.main import app

def test_login_access_token(client: TestClient, db: Session, user_one):
    login_data = {
        "factory_slug": user_one.factory.slug,
        "email": user_one.email,
        "password": "password"
    }
    r = client.post(f"/api/v1/auth/login", json=login_data)
    tokens = r.json()
    assert r.status_code == 200
    assert "access_token" in tokens
    assert tokens["access_token"]

def test_read_devices_success(client: TestClient, db: Session, user_one, normal_user_token_headers):
    # Setup data
    device = Device(name="Test Device", type="test", factory_id=user_one.factory_id)
    db.add(device)
    db.commit()
    
    r = client.get(f"/api/v1/devices/", headers=normal_user_token_headers)
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 1
    assert data[0]["name"] == "Test Device"

def test_invalid_token(client: TestClient):
    r = client.get(f"/api/v1/devices/", headers={"Authorization": "Bearer invalid_token"})
    assert r.status_code == 401

def test_tenant_isolation(client: TestClient, db: Session, user_one, normal_user_token_headers):
    # Create factory 2 and user 2
    factory2 = Factory(name="Factory Two", slug="factory-two")
    db.add(factory2)
    db.commit()
    
    user2 = User(
        email="user2@example.com",
        password_hash=security.get_password_hash("password"),
        role="admin",
        factory_id=factory2.id,
        is_active=True
    )
    db.add(user2)
    
    # User 2 create device
    device2 = Device(name="Factory 2 Device", type="test", factory_id=factory2.id)
    db.add(device2)
    db.commit()
    
    # User 1 tries to list devices. Should not see device2
    r = client.get(f"/api/v1/devices/", headers=normal_user_token_headers)
    assert r.status_code == 200
    data = r.json()
    device_names = [d["name"] for d in data]
    assert "Factory 2 Device" not in device_names
    
    # If user 1 tries to access device 2 directly? Not explicitly covered in LLD API spec, but general endpoint is list.
    # LLD has /devices/{id}/properties but not /devices/{id} explicitly in detail section, maybe I missed it.
    # LLD has GET /devices/{device_id}/telemetry.
    # If endpoint exists to get single device, it should 404.
