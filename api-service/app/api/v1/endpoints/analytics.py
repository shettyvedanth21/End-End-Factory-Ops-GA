from typing import Any, List
from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.api import deps
from app.core.database import get_db
from app.models.models import AnalyticsJob, AnalyticsModel, User
from app.schemas.schemas import JobCreate, JobResponse, ModelResponse, JobStatus

router = APIRouter()

@router.get("/jobs", response_model=List[JobResponse])
def read_jobs(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_user),
    factory_id: str = Depends(deps.get_factory_id)
) -> Any:
    jobs = db.query(AnalyticsJob).filter(AnalyticsJob.factory_id == factory_id).offset(skip).limit(limit).all()
    return jobs

@router.post("/jobs", response_model=JobResponse)
def create_job(
    *,
    db: Session = Depends(get_db),
    job_in: JobCreate,
    current_user: User = Depends(deps.get_current_active_user),
    factory_id: str = Depends(deps.get_factory_id)
) -> Any:
    job = AnalyticsJob(
        factory_id=factory_id,
        name=job_in.name,
        mode=job_in.mode,
        analysis_type=job_in.analysis_type,
        status=JobStatus.QUEUED,
        model_name=job_in.model_name,
        hyperparameters=job_in.hyperparameters,
        created_by=current_user.id
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    
    # Publish to queue
    from app.core.queue import analytics_queue
    analytics_queue.enqueue({"job_id": job.id, "factory_id": job.factory_id})
    
    return job

@router.get("/jobs/{job_id}", response_model=JobResponse)
def read_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
    factory_id: str = Depends(deps.get_factory_id)
) -> Any:
    job = db.query(AnalyticsJob).filter(AnalyticsJob.id == job_id, AnalyticsJob.factory_id == factory_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.get("/models", response_model=List[ModelResponse])
def read_models(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_user),
    factory_id: str = Depends(deps.get_factory_id)
) -> Any:
    models = db.query(AnalyticsModel).filter(AnalyticsModel.factory_id == factory_id, AnalyticsModel.is_active == True).offset(skip).limit(limit).all()
    return models
