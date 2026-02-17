from fastapi import FastAPI
from app.api.api import api_router, health_check
from app.core.config import settings
from app.services.worker import process_notification
import logging
import sys
import threading
import redis
import json
import time

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
app.add_api_route("/health", health_check, methods=["GET"])

# Background Worker Thread
def worker_loop():
    logger.info("Starting Notification Worker Loop")
    r = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
    while True:
        msg = r.blpop("notifications_queue", timeout=5)
        if msg:
            queue, payload = msg
            data = json.loads(payload)
            logger.info(f"Processing notification: {data}")
            process_notification(data["alert"], data["rule"], data["factory_id"])
            
if __name__ == "__main__":
    t = threading.Thread(target=worker_loop, daemon=True)
    t.start()
    
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.PORT)
