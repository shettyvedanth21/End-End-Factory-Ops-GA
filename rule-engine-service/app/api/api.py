from fastapi import APIRouter
from app.core.config import settings
import redis

api_router = APIRouter()

@api_router.get("/health")
def health_check():
    # Check dependencies (Redis, MySQL)
    status = {"status": "healthy", "service": settings.SERVICE_NAME}
    
    try:
        r = redis.Redis.from_url(settings.REDIS_URL)
        r.ping()
        status["redis"] = "ok"
    except Exception as e:
        status["redis"] = f"error: {str(e)}"
        
    return status

# No explicit API endpoints for rule engine, it's a background worker.
# Rules are managed via API Service.
# Rule Engine just consumes events.
