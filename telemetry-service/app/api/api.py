from fastapi import APIRouter
from app.core.config import settings
from app.core import influx
from app.services.mqtt_client import mqtt_app

api_router = APIRouter()

@api_router.on_event("startup")
async def startup_event():
    # Start MQTT connection
    mqtt_app.start()

@api_router.get("/health")
def health_check():
    # In practice, verify MQTT connected (client.is_connected), Influx, MySQL
    status = {
        "status": "healthy", 
        "service": settings.SERVICE_NAME,
        "mqtt_connected": mqtt_app.client.is_connected()
    }
    return status

# No explicit telemetry endpoints LLD 3.4.4 GET /devices/{device_id}/telemetry
# That endpoint is in API service, not Telemetry service.
# Telemetry service just ingests and writes to DB.
# API Service queries InfluxDB directly (via its own client).
# So Telemetry Service only needs health check + background worker.
