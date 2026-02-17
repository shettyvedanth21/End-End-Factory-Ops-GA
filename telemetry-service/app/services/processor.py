from app.core.influx import influx_service
from app.core.database import SessionLocal
from app.models.models import Device, DeviceProperty
from app.services.redis_service import rule_engine_queue
import json
import logging
import datetime

logger = logging.getLogger("telemetry-processor")

CACHE_PROPERTIES = {} # In-memory cache for simplicity in this artifact, real prod would use Redis for HA

def process_message(factory_id: str, device_id: str, payload: dict, timestamp: datetime.datetime = None):
    # 1. Validate payload
    valid_data = {}
    for k, v in payload.items():
        if isinstance(v, (int, float, bool)):
            valid_data[k] = v
        else:
            logger.warning(f"Invalid data type for {k}: {type(v)} in device {device_id}")

    if not valid_data:
        return

    # 2. Auto-discovery
    db = SessionLocal()
    try:
        if device_id not in CACHE_PROPERTIES:
            # Load known properties for device
            props = db.query(DeviceProperty.property_name).filter(
                DeviceProperty.device_id == device_id,
                DeviceProperty.factory_id == factory_id
            ).all()
            CACHE_PROPERTIES[device_id] = {p[0] for p in props}
        
        known_props = CACHE_PROPERTIES[device_id]
        new_props = []
        
        for k in valid_data.keys():
            if k not in known_props:
                new_props.append(k)
        
        if new_props:
            logger.info(f"New properties discovered for {device_id}: {new_props}")
            for prop_name in new_props:
                # Add to DB
                # Check if exists first (concurrency)
                existing = db.query(DeviceProperty).filter(
                    DeviceProperty.device_id == device_id,
                    DeviceProperty.property_name == prop_name
                ).first()
                
                if not existing:
                    new_prop = DeviceProperty(
                        factory_id=factory_id,
                        device_id=device_id,
                        property_name=prop_name,
                        data_type="float" # Defaulting for now as per minimal impl
                    )
                    db.add(new_prop)
                    # Add to cache immediately
                    known_props.add(prop_name)
            
            db.commit()
            
    except Exception as e:
        logger.error(f"Error in auto-discovery: {e}")
        db.rollback()
    finally:
        db.close()

    # 3. Write to InfluxDB
    try:
        influx_service.write_point(factory_id, device_id, valid_data, timestamp)
    except Exception as e:
        logger.error(f"Error writing to InfluxDB: {e}")

    # 4. Update Device Last Seen (Async/Debounced? For now direct synchronous update or skip for performance)
    # LLD 4.1 Step 4: async debounced. We'll skip for high throughput prototype or do simple update
    try:
         # Update Last Seen
         pass 
    except:
         pass

    # 5. Publish to Rule Engine
    try:
        event = {
            "factory_id": factory_id,
            "device_id": device_id,
            "properties": valid_data,
            "timestamp": timestamp.isoformat() if timestamp else datetime.datetime.utcnow().isoformat()
        }
        rule_engine_queue.publish(event)
    except Exception as e:
        logger.error(f"Error publishing to Rule Engine: {e}")
