from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
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
    
    # Security
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 * 60

    # Redis
    REDIS_URL: str
    
    # Service
    SERVICE_NAME: str = "api-service"
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: str = "production"

    model_config = {
        "env_file": ".env"
    }

settings = Settings()
