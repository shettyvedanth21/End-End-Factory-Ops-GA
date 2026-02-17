import logging
import sys
from fastapi import FastAPI
from app.api.api import api_router, startup_event, health_check
from app.core.config import settings

logging.basicConfig(
    stream=sys.stdout,
    level=settings.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.SERVICE_NAME,
    openapi_url=f"/api/v1/openapi.json",
    docs_url=f"/api/v1/docs",
    redoc_url=f"/api/v1/redoc",
)

app.include_router(api_router, prefix="/api/v1")
app.add_event_handler("startup", startup_event)
app.add_api_route("/health", health_check, methods=["GET"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.PORT)
