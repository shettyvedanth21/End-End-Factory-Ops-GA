from typing import Any, List
from datetime import datetime

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.api import deps
from app.core.database import get_db
from app.models.models import Alert, User
from app.schemas.schemas import AlertResponse, AlertStatus, AlertAcknowledge, AlertResolve

router = APIRouter()

@router.get("/", response_model=List[AlertResponse])
def read_alerts(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    status: AlertStatus = None,
    current_user: User = Depends(deps.get_current_active_user),
    factory_id: str = Depends(deps.get_factory_id)
) -> Any:
    query = db.query(Alert).filter(Alert.factory_id == factory_id)
    if status:
        query = query.filter(Alert.status == status)
    alerts = query.offset(skip).limit(limit).all()
    return alerts

@router.patch("/{alert_id}/acknowledge", response_model=AlertResponse)
def acknowledge_alert(
    *,
    db: Session = Depends(get_db),
    alert_id: str,
    ack_in: AlertAcknowledge,
    current_user: User = Depends(deps.get_current_active_user),
    factory_id: str = Depends(deps.get_factory_id)
) -> Any:
    alert = db.query(Alert).filter(Alert.id == alert_id, Alert.factory_id == factory_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    if alert.status != AlertStatus.OPEN:
        raise HTTPException(status_code=400, detail="Alert must be open to acknowledge")
        
    alert.status = AlertStatus.ACKNOWLEDGED
    alert.acknowledged_at = datetime.utcnow()
    alert.acknowledged_by = current_user.id
    alert.notes = ack_in.notes
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert

@router.patch("/{alert_id}/resolve", response_model=AlertResponse)
def resolve_alert(
    *,
    db: Session = Depends(get_db),
    alert_id: str,
    res_in: AlertResolve,
    current_user: User = Depends(deps.get_current_active_user),
    factory_id: str = Depends(deps.get_factory_id)
) -> Any:
    alert = db.query(Alert).filter(Alert.id == alert_id, Alert.factory_id == factory_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.status = AlertStatus.RESOLVED
    alert.resolved_at = datetime.utcnow()
    if res_in.notes:
        alert.notes = (alert.notes or "") + "\n" + res_in.notes
    
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert
