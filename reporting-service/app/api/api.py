from fastapi import APIRouter
from app.core.config import settings

api_router = APIRouter()

@api_router.get("/health")
def health_check():
    return {"status": "healthy", "service": settings.SERVICE_NAME}
