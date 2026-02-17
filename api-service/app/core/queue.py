import redis
import json
from app.core.config import settings

class RedisQueue:
    def __init__(self, key: str):
        self.key = key
        self.redis_client = redis.Redis.from_url(settings.REDIS_URL)

    def enqueue(self, item: dict):
        self.redis_client.lpush(self.key, json.dumps(item))

    def dequeue(self) -> dict:
        item = self.redis_client.rpop(self.key)
        if item:
            return json.loads(item)
        return None

analytics_queue = RedisQueue("analytics_queue")
reports_queue = RedisQueue("reports_queue")
notifications_queue = RedisQueue("notifications_queue")
events_queue = RedisQueue("events_queue") 
