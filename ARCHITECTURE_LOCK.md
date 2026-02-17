# ARCHITECTURE LOCK
# This file is authoritative. No service may redefine credentials.
# No service may hardcode secrets.

MYSQL_HOST=mysql
MYSQL_DB=factoryops
MYSQL_USER=factoryops_user
MYSQL_PASSWORD=factoryops_password
INFLUX_URL=http://influxdb:8086
INFLUX_ORG=factoryops
INFLUX_BUCKET=factoryops
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minio_access_key
MINIO_SECRET_KEY=minio_secret_key
JWT_SECRET=super_secret_jwt_key_please_change_in_prod
REDIS_URL=redis://redis:6379/0
# MQTT
MQTT_BROKER_HOST=emqx
MQTT_BROKER_PORT=1883
MQTT_ADMIN_USER=admin
MQTT_ADMIN_PASSWORD=public
SERVICE_PORTS={"api": 8000, "telemetry": 8001, "rule_engine": 8002, "analytics": 8003, "reporting": 8004}
INTERNAL_SERVICE_URLS={"api": "http://api-service:8000", "telemetry": "http://telemetry-service:8001", "rule_engine": "http://rule-engine:8002", "analytics": "http://analytics-service:8003", "reporting": "http://reporting-service:8004"}
