from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # MySQL
    MYSQL_HOST: str
    MYSQL_DB: str
    MYSQL_USER: str
    MYSQL_PASSWORD: str
    
    # InfluxDB
    INFLUX_URL: str
    INFLUX_ORG: str
    INFLUX_BUCKET: str

    # MinIO
    MINIO_ENDPOINT: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_SECURE: bool = False # Usually False for localhost
    
    # Redis
    REDIS_URL: str
    
    # Service
    SERVICE_NAME: str = "analytics-service"
    PORT: int = 8003
    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: str = "production"

    model_config = {
        "env_file": ".env"
    }

settings = Settings()
