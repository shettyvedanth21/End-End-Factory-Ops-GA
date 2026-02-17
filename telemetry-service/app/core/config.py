from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # MQTT
    MQTT_BROKER_HOST: str
    MQTT_BROKER_PORT: int
    MQTT_ADMIN_USER: str
    MQTT_ADMIN_PASSWORD: str
    
    # InfluxDB
    INFLUX_URL: str
    INFLUX_ORG: str
    INFLUX_BUCKET: str
    
    # MySQL
    MYSQL_HOST: str
    MYSQL_DB: str
    MYSQL_USER: str
    MYSQL_PASSWORD: str

    # Redis
    REDIS_URL: str
    
    # Service
    SERVICE_NAME: str = "telemetry-service"
    PORT: int = 8001
    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: str = "production"

    model_config = {
        "env_file": ".env",
        "extra": "ignore"
    }

settings = Settings()
