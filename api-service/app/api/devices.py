from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import Device

router = APIRouter()

@router.get("/devices")
def list_devices(factory_id: str = "fct-001", db: Session = Depends(get_db)):
    # Factory ID normally from token
    devices = db.query(Device).filter(Device.factory_id == factory_id).all()
    
    return {
        "success": True,
        "data": {
            "items": devices,
            "pagination": {"page": 1, "per_page": 100, "total": len(devices)}
        }
    }
