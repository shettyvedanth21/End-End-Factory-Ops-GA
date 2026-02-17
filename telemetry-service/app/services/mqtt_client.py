import paho.mqtt.client as mqtt
import logging
import time
import json
from app.core.config import settings
from app.services.processor import process_message

logger = logging.getLogger("mqtt-client")

class MQTTClient:
    def __init__(self):
        self.client = mqtt.Client()
        if settings.MQTT_ADMIN_USER:
            self.client.username_pw_set(settings.MQTT_ADMIN_USER, settings.MQTT_ADMIN_PASSWORD)
            
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info("Connected to EMQX Broker!")
            # Subscribe to all telemetry topics
            self.client.subscribe("factories/+/devices/+/telemetry", qos=1)
        else:
            logger.error(f"Failed to connect, return code {rc}")

    def on_message(self, client, userdata, msg):
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            # Parse topic factories/{factory_id}/devices/{device_id}/telemetry
            parts = topic.split("/")
            if len(parts) >= 5 and parts[0] == "factories" and parts[2] == "devices" and parts[4] == "telemetry":
                factory_id = parts[1]
                device_id = parts[3]
                process_message(factory_id, device_id, payload)
            else:
                logger.warning(f"Invalid topic format: {topic}")
        except json.JSONDecodeError:
            logger.error("Failed to decode JSON payload")
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    def on_disconnect(self, client, userdata, rc):
        logger.warning(f"Disconnected with result code {rc}. Reconnection handled by loop_start()")
        
    def start(self):
        try:
            self.client.connect(settings.MQTT_BROKER_HOST, settings.MQTT_BROKER_PORT, 60)
            self.client.loop_start()
        except Exception as e:
            logger.error(f"Failed to start MQTT client: {e}")

mqtt_app = MQTTClient()
