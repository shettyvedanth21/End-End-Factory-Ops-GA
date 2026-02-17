from app.core import database
from app.models.models import Report
from app.services.minio_client import minio_service
from app.services.data_fetcher import DataFetcher
from app.services.renderer import generate_pdf, generate_excel, generate_json
from sqlalchemy.orm import Session
import logging
import datetime
import traceback
import pandas as pd

logger = logging.getLogger("report-worker")

def process_report(factory_id: str, report_id: str):
    db: Session = database.SessionLocal()
    fetcher = DataFetcher()
    
    try:
        report = db.query(Report).filter(Report.id == report_id, Report.factory_id == factory_id).first()
        if not report:
            logger.error(f"Report not found: {report_id}")
            return
            
        # 1. Update status
        report.status = "generating"
        db.commit()
        
        # 2. Data Assembly
        start = report.time_range_start
        end = report.time_range_end
        
        # Fetch Metrics
        metrics_df = fetcher.get_telemetry_aggregates(factory_id, report.device_ids, start, end)
        
        # Fetch Alerts
        alerts_list = fetcher.get_alerts(factory_id, report.device_ids, start, end)
        
        # Prepare Data Dict for Rendering
        render_data = {
            "report_name": report.name,
            "start": start.isoformat(),
            "end": end.isoformat(),
            "metrics_html": metrics_df.to_html() if not metrics_df.empty else "<p>No Data</p>",
            "alerts": alerts_list
        }
        
        # 3. Render
        output_data = b""
        extension = "pdf"
        content_type = "application/pdf"
        
        if report.format == "pdf":
            output_data = generate_pdf(render_data)
        elif report.format == "excel":
            output_data = generate_excel(metrics_df, alerts_list)
            extension = "xlsx"
            content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        elif report.format == "json":
            output_data = generate_json(render_data)
            extension = "json"
            content_type = "application/json"
            
        # 4. Upload to MinIO
        s3_key = f"factoryops/{factory_id}/reports/{report_id}/report.{extension}"
        if minio_service.upload_bytes(s3_key, output_data, content_type):
            report.s3_key = s3_key
            report.status = "completed"
            report.generated_at = datetime.datetime.utcnow()
        else:
            raise Exception("Upload failed")
            
        db.commit()
        logger.info(f"Report {report_id} generated successfully")
        
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        logger.error(traceback.format_exc())
        report.status = "failed"
        report.error_message = str(e)
        db.commit()
        
    finally:
        db.close()
