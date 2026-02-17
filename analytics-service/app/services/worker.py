from app.core import database
from app.models.models import AnalyticsJob, AnalyticsModel
from app.services.minio_client import minio_service
from app.services.influx_client import influx_service
from app.services.trainer import train_model
from sqlalchemy.orm import Session
import json
import logging
import datetime
import traceback
import pandas as pd
import io

logger = logging.getLogger("analytics-worker")

def process_job(factory_id: str, job_id: str):
    db: Session = database.SessionLocal()
    try:
        job = db.query(AnalyticsJob).filter(AnalyticsJob.id == job_id, AnalyticsJob.factory_id == factory_id).first()
        if not job:
            logger.error(f"Job not found: {job_id}")
            return
            
        # 1. Update status = 'running'
        job.status = "running"
        job.started_at = datetime.datetime.utcnow()
        db.commit()
        
        # 2. Data Export (Influx -> Pandas -> Parquet -> MinIO)
        logger.info(f"Fetching data for job {job_id}")
        start_ts = job.data_range_start.isoformat()
        end_ts = job.data_range_end.isoformat()
        properties = job.features if job.features else []
        if job.target_variable and job.target_variable not in properties:
            properties.append(job.target_variable)

        df = influx_service.query_dataset(
            factory_id, 
            job.device_ids, 
            properties, 
            start_ts, 
            end_ts
        )
        
        if df.empty:
            raise ValueError("Empty dataset returned from InfluxDB")
            
        # Serialize to Parquet
        parquet_buffer = io.BytesIO()
        df.to_parquet(parquet_buffer, index=False)
        parquet_bytes = parquet_buffer.getvalue()
        
        # Upload Dataset to MinIO
        dataset_key = f"factoryops/{factory_id}/datasets/{job_id}/dataset.parquet"
        minio_service.upload_bytes(dataset_key, parquet_bytes)
        job.dataset_s3_key = dataset_key
        db.commit()
        
        # 3. Model Training
        model_bytes, metrics = train_model(
            df, 
            job.target_variable, 
            algorithm=job.algorithm,
            task_type="regression" # Assume regression for simplicity, or infer from job type
        )
        
        # 4. Upload Artifacts (Model + Results)
        model_key = f"factoryops/{factory_id}/analytics/{job_id}/model.pkl"
        results_key = f"factoryops/{factory_id}/analytics/{job_id}/results.json"
        
        minio_service.upload_bytes(model_key, model_bytes)
        minio_service.upload_bytes(results_key, json.dumps(metrics).encode())
        
        job.artifact_s3_prefix = f"factoryops/{factory_id}/analytics/{job_id}/"
        job.metrics = metrics
        
        # 5. Registry Update (Create AnalyticsModel entry)
        model_entry = AnalyticsModel(
            factory_id=factory_id,
            name=job.model_name or f"model-{job_id}",
            version=1, # Simple versioning logic: query max version and increment? omitted for simplicity
            algorithm=job.algorithm or "random_forest",
            hyperparameters=job.hyperparameters,
            training_metrics=metrics,
            s3_key=model_key,
            job_id=job_id
        )
        db.add(model_entry)
        
        # 6. Update Job Status
        job.status = "completed"
        job.completed_at = datetime.datetime.utcnow()
        db.commit()
        logger.info(f"Job {job_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Job failed: {e}")
        logger.error(traceback.format_exc())
        job.status = "failed"
        job.error_message = str(e)
        db.commit()
        
    finally:
        db.close()
