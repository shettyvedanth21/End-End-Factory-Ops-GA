import logging
import sys
import threading
import json
import redis
import time
from fastapi import FastAPI
from app.api.api import api_router, health_check
from app.core.config import settings
from app.services.processor import process_event

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

# Background Worker Thread for Redis Queue
def worker_loop():
    logger.info("Starting Rule Engine Worker Loop")
    r = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
    while True:
        try:
            # BLPOP blocks until item available
            # Queue name from Telemetry Service: "events_queue"
            msg = r.blpop("events_queue", timeout=5) 
            if msg:
                queue, payload = msg
                event = json.loads(payload)
                process_event(event) # Async processing usually, here sync for simplicity
                
        except redis.ConnectionError:
            logger.error("Redis connection lost, retrying...")
            time.sleep(5)
        except Exception as e:
            logger.error(f"Error in worker loop: {e}")
            time.sleep(1)

@app.on_event("startup")
async def startup_event():
    # Start worker thread
    t = threading.Thread(target=worker_loop, daemon=True)
    t.start()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.PORT)
