from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # MySQL
    MYSQL_HOST: str
    MYSQL_DB: str
    MYSQL_USER: str
    MYSQL_PASSWORD: str

    # Redis
    REDIS_URL: str
    
    # Service
    SERVICE_NAME: str = "rule-engine-service"
    PORT: int = 8002
    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: str = "production"

    model_config = {
        "env_file": ".env"
    }

settings = Settings()
