from datetime import datetime, timedelta
from app.core import database
from app.models.models import NotificationLog, User
from app.services.email_service import email_service
from app.services.whatsapp_service import whatsapp_service
from sqlalchemy.orm import Session
import logging
import json
import traceback

logger = logging.getLogger("notification-worker")

def process_notification(alert: dict, rule: dict, factory_id: str):
    db: Session = database.SessionLocal()
    try:
        # 1. Determine Recipients (Factory Admins)
        admins = db.query(User).filter(
            User.factory_id == factory_id,
            User.role.in_(["admin", "super_admin"])
        ).all()
        
        if not admins:
            logger.warning(f"No admins found for factory {factory_id}")
            return
            
        # 2. Prepare Message
        subject = f"Alert: {rule.get('name')} triggered on {alert.get('device_id')}"
        body = f"""
        Alert ID: {alert.get('id')}
        Rule: {rule.get('name')}
        Device: {alert.get('device_id')}
        Time: {alert.get('triggered_at')}
        Values: {json.dumps(alert.get('trigger_values', {}), indent=2)}
        """
        
        # 3. Dispatch
        for admin in admins:
            # Email
            log_email = NotificationLog(
                factory_id=factory_id,
                alert_id=alert.get("id"),
                channel="email",
                recipient=admin.email,
                subject=subject,
                message_body=body,
                status="pending"
            )
            db.add(log_email)
            db.commit() # Get ID
            
            if email_service.send_email(admin.email, subject, body):
                log_email.status = "sent"
                log_email.sent_at = datetime.utcnow()
            else:
                log_email.status = "failed"
                log_email.retry_count += 1
                
            db.commit()
            
            # WhatsApp (if phone number exists)
            if admin.phone_number:
                log_wa = NotificationLog(
                    factory_id=factory_id,
                    alert_id=alert.get("id"),
                    channel="whatsapp",
                    recipient=admin.phone_number,
                    message_body=body, # Subject ignored for WA
                    status="pending"
                )
                db.add(log_wa)
                db.commit()
                
                if whatsapp_service.send_whatsapp(admin.phone_number, body):
                    log_wa.status = "sent"
                    log_wa.sent_at = datetime.utcnow()
                else:
                    log_wa.status = "failed"
                    log_wa.retry_count += 1
                db.commit()
                
    except Exception as e:
        logger.error(f"Notification processing failed: {e}")
        traceback.print_exc()
    finally:
        db.close()
