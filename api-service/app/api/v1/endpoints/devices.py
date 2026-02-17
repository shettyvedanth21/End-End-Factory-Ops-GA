from typing import Any, List

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from influxdb_client.client.query_api import QueryApi

from app.api import deps
from app.core.config import settings
from app.core import influx
from app.core.database import get_db
from app.models.models import Device, DeviceProperty, User
from app.schemas.schemas import DeviceCreate, DeviceResponse, PropertyResponse, TelemetryResponse

router = APIRouter()

@router.get("/", response_model=List[DeviceResponse])
def read_devices(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_user),
    factory_id: str = Depends(deps.get_factory_id)
) -> Any:
    devices = db.query(Device).filter(Device.factory_id == factory_id).offset(skip).limit(limit).all()
    return devices

@router.post("/", response_model=DeviceResponse)
def create_device(
    *,
    db: Session = Depends(get_db),
    device_in: DeviceCreate,
    current_user: User = Depends(deps.get_current_active_user),
    factory_id: str = Depends(deps.get_factory_id)
) -> Any:
    if not current_user.can_write and current_user.role != "super_admin":
        raise HTTPException(status_code=400, detail="Not enough permissions")
        
    device = Device(
        id=device_in.id,
        name=device_in.name,
        type=device_in.type,
        location=device_in.location,
        factory_id=factory_id
    )
    db.add(device)
    db.commit()
    db.refresh(device)
    return device

@router.get("/{device_id}/properties", response_model=List[PropertyResponse])
def read_device_properties(
    device_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
    factory_id: str = Depends(deps.get_factory_id)
) -> Any:
    props = db.query(DeviceProperty).filter(
        DeviceProperty.device_id == device_id,
        DeviceProperty.factory_id == factory_id
    ).all()
    return props

@router.get("/{device_id}/telemetry") # Returns custom dict structure or schema
def read_telemetry(
    device_id: str,
    property: str,
    start: str = "-1h",
    end: str = "now()",
    aggregation: str = "mean", # mean, count, etc.
    window: str = "5m",
    query_api: QueryApi = Depends(influx.get_influx_query_api),
    factory_id: str = Depends(deps.get_factory_id)
) -> Any:
    # Construct Flux query
    # Minimal implementation
    bucket = settings.INFLUX_BUCKET
    query = f"""
    from(bucket: "{bucket}")
      |> range(start: {start}, stop: {end})
      |> filter(fn: (r) => r["_measurement"] == "device_metrics")
      |> filter(fn: (r) => r["factory_id"] == "{factory_id}")
      |> filter(fn: (r) => r["device_id"] == "{device_id}")
      |> filter(fn: (r) => r["property_name"] == "{property}")
      |> aggregateWindow(every: {window}, fn: {aggregation}, createEmpty: false)
      |> yield(name: "{aggregation}")
    """
    # execute query
    # Parsing results to JSON
    # This part needs actual InfluxDB client interaction which returns tables
    # mocking response structure for now or implementing if client available
    return {"device_id": device_id, "property": property, "points": []} 
