from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # MySQL
    MYSQL_HOST: str
    MYSQL_DB: str
    MYSQL_USER: str
    MYSQL_PASSWORD: str
    
    # Redis
    REDIS_URL: str
    
    # SMTP (Email)
    SMTP_SERVER: str
    SMTP_PORT: int
    SMTP_USER: str
    SMTP_PASSWORD: str
    SMTP_FROM_EMAIL: str
    
    # Twilio (WhatsApp)
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_FROM_NUMBER: str
    
    # Service
    SERVICE_NAME: str = "notification-service"
    PORT: int = 8005
    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: str = "production"

    model_config = {
        "env_file": ".env"
    }

settings = Settings()
