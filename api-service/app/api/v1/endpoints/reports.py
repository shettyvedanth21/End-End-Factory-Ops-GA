from typing import Any, List
from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.api import deps
from app.core.database import get_db
from app.models.models import Report, User
from app.schemas.schemas import ReportCreate, ReportResponse, ReportStatus

router = APIRouter()

@router.get("/{report_id}", response_model=ReportResponse)
def read_report(
    report_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
    factory_id: str = Depends(deps.get_factory_id)
) -> Any:
    report = db.query(Report).filter(Report.id == report_id, Report.factory_id == factory_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    # For download URL, we'd normally generate a presigned URL here if not stored or expired
    # Mock download_url logic for now as S3 integration is complex
    return report

@router.post("/", response_model=ReportResponse)
def create_report(
    *,
    db: Session = Depends(get_db),
    report_in: ReportCreate,
    current_user: User = Depends(deps.get_current_active_user),
    factory_id: str = Depends(deps.get_factory_id)
) -> Any:
    report = Report(
        factory_id=factory_id,
        name=report_in.name,
        type=report_in.type,
        format=report_in.format,
        period_start=report_in.period_start,
        period_end=report_in.period_end,
        parameters=report_in.parameters,
        created_by=current_user.id,
        status=ReportStatus.QUEUED
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    
    # Publish to queue
    from app.core.queue import reports_queue
    reports_queue.enqueue({"report_id": report.id, "factory_id": report.factory_id})
    
    return report
