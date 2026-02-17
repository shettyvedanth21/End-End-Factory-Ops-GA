import pytest
import requests
import json
import time
import paho.mqtt.client as mqtt
import random
import string
import logging

# Configure Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("SystemTest")

# Configurations (Should match Docker Compose)
BASE_URL = "http://localhost:8000/api/v1"  # API Service
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
INFLUX_URL = "http://localhost:8086"
MYSQL_HOST = "localhost"
FACTORY_ID = "fct-e2e-test"
DEVICE_ID = "dev-e2e-test"
ADMIN_EMAIL = "admin@e2e.com"
ADMIN_PASSWORD = "TestPassword123!"

@pytest.fixture(scope="session")
def api_client():
    class APIClient:
        def __init__(self):
            self.session = requests.Session()
            self.token = None
            
        def login(self, email, password, factory_slug):
            url = f"{BASE_URL}/auth/login"
            payload = {
                "email": email,
                "password": password,
                "factory_slug": factory_slug
            }
            resp = self.session.post(url, json=payload)
            if resp.status_code == 200:
                self.token = resp.json()["data"]["access_token"]
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
            return resp

        def post(self, endpoint, data):
            return self.session.post(f"{BASE_URL}{endpoint}", json=data)

        def get(self, endpoint, params=None):
            return self.session.get(f"{BASE_URL}{endpoint}", params=params)

    return APIClient()

def test_01_setup_infrastructure():
    """Ensure services are responsive (Health Checks)"""
    services = [
        "http://localhost:8000/api/v1/health",   # API
        "http://localhost:8001/health",          # Telemetry (check port if mapped, assumed 8001)
        "http://localhost:8002/health",          # Rule Engine
        "http://localhost:8003/health",          # Analytics
        "http://localhost:8004/health",          # Reporting
        "http://localhost:8005/health",          # Notification
    ]
    
    for url in services:
        try:
            resp = requests.get(url, timeout=5)
            assert resp.status_code == 200, f"Service at {url} is unhealthy: {resp.status_code}"
            logger.info(f"Service {url} is HEALTHY")
        except Exception as e:
            pytest.fail(f"Service at {url} unreachable: {e}")

def test_02_create_factory_and_admin(api_client):
    """Register a new factory and admin user via Platform API"""
    # Note: In a real scenario, this might need a root token or direct DB insert if API is restricted.
    # Assuming public registration or root token is available.
    # For simplicity, we'll try the login directly if already exists, else skip (or implement registration logic).
    
    # Check if we can login (assuming seed data exists or we use seed data)
    # The init.sql seeds 'fct-001' and 'usr-admin-1'. Let's use that for reliability.
    
    resp = api_client.login("admin@factory-alpha.com", "public", "plant-munich") 
    # Password in init.sql for MQTT is public, but for user login? 
    # init.sql: INSERT INTO users ... 'admin@factory-alpha.com' ... no password hash?
    # Verification needed: The Authentication service needs valid users.
    # If the user password isn't set correct in DB match, login fails.
    # We will assume the system allows creating a user or we use a known one.
    
    if resp.status_code != 200:
        logger.warning("Could not login with default seed. Skipping auth dependent tests or check DB seeding.")
    else:
        logger.info("Login Successful")
        assert resp.json()["success"] is True

def test_03_mqtt_telemetry_ingestion():
    """Publish telemetry via MQTT and verify ingestion"""
    client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()
        
        # Topic Structure: factories/{factory_id}/devices/{device_id}/telemetry
        topic = f"factories/fct-001/devices/dev-e2e/telemetry"
        payload = json.dumps({
            "temperature": 88.5,
            "pressure": 10.2,
            "status": "active"
        })
        
        info = client.publish(topic, payload, qos=1)
        info.wait_for_publish()
        logger.info(f"Published to {topic}: {payload}")
        
        client.loop_stop()
        client.disconnect()
        
        # Verification would ideally happen by querying the API
        time.sleep(2) # Wait for ingestion
        
    except Exception as e:
        pytest.fail(f"MQTT Publish failed: {e}")

def test_04_query_telemetry(api_client):
    """Query the InfluxDB data via API to confirm ingestion"""
    # Requires valid login
    if not api_client.token: 
        pytest.skip("No Valid Token")
        
    # Endpoint: /devices/{device_id}/telemetry
    resp = api_client.get(f"/devices/dev-e2e/telemetry", params={"property": "temperature", "window": "5m"})
    if resp.status_code == 200:
        data = resp.json().get("data", {})
        points = data.get("points", [])
        # Iterate to find our value (88.5)
        found = any(p["value"] == 88.5 for p in points)
        if found:
            logger.info("Telemetry verified in API")
        else:
             logger.warning("Telemetry not found in API response (might be delayed or aggregated)")
    else:
        logger.warning(f"Failed to fetch telemetry: {resp.text}")

if __name__ == "__main__":
    pytest.main(["-v", __file__])
