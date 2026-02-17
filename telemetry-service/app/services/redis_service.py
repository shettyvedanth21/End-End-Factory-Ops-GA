import redis
import json
from app.core.config import settings

class RedisService:
    def __init__(self):
        try:
            self.redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
            self.redis_client.ping()
        except redis.ConnectionError:
            print("Redis connection failed")
            # Should retry or exit, for now simple fail log

    def publish(self, message: dict):
        self.redis_client.lpush("events_queue", json.dumps(message))

    def get_client(self):
        return self.redis_client

rule_engine_queue = RedisService()
