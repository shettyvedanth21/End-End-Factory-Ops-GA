from datetime import datetime, timedelta
from app.core.database import SessionLocal
from app.models.models import Rule, Alert, NotificationLog
from app.services.evaluator import evaluate_rule
import logging

logger = logging.getLogger("rule-engine")

def process_event(event: dict):
    factory_id = event.get("factory_id")
    device_id = event.get("device_id")
    payload = event.get("properties", {})
    
    db = SessionLocal()
    try:
        # 1. Fetch active rules
        rules = db.query(Rule).filter(
            Rule.factory_id == factory_id,
            Rule.device_id == device_id,
            Rule.is_active == True
        ).all()
        
        for rule in rules:
            try:
                # 2. Evaluate
                triggered = evaluate_rule(rule, payload)
                
                if triggered:
                    # Check Cooldown
                    last_alert = db.query(Alert).filter(
                        Alert.rule_id == rule.id,
                        Alert.status == "open",
                        Alert.triggered_at > datetime.utcnow() - timedelta(seconds=rule.cooldown_seconds)
                    ).first()
                    
                    if not last_alert:
                        # Create Alert
                        new_alert = Alert(
                            factory_id=factory_id,
                            rule_id=rule.id,
                            device_id=device_id,
                            status="open",
                            trigger_values=payload
                        )
                        db.add(new_alert)
                        db.commit() # Commit to get ID
                        
                        logger.info(f"Alert created: {new_alert.id} for rule {rule.id}")
                        
                        # Publish Notification (Mock - Insert Log which Notification Service would pick up)
                        # Here we just insert into NotificationLog or publish to another queue
                        # LLD 4.2 -> Publish to Notification Queue: { alert_id, rule, ... }
                        
                        # Minimal implementation: Insert NotificationLog directly if Worker is same process or separate
                        # LLD 4.3 says Notification Worker consumes from Notification Queue.
                        # We will simulate publishing by just logging for now, or use Redis queue if implemented.
                        pass
                
                elif rule.auto_resolve:
                    # Check if open alert exists to resolve
                    open_alert = db.query(Alert).filter(
                        Alert.rule_id == rule.id,
                        Alert.status == "open"
                    ).order_by(Alert.triggered_at.desc()).first()
                    
                    if open_alert:
                        open_alert.status = "resolved"
                        open_alert.resolved_at = datetime.utcnow()
                        db.commit()
                        logger.info(f"Alert resolved: {open_alert.id}")

            except Exception as e:
                logger.error(f"Error evaluating rule {rule.id}: {e}")
                
    except Exception as e:
        logger.error(f"Error processing event: {e}")
    finally:
        db.close()
