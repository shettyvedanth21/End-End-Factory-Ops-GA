from influxdb_client import InfluxDBClient
from app.core.config import settings

class InfluxClient:
    def __init__(self):
        self.client = InfluxDBClient(
            url=settings.INFLUX_URL,
            token=f"{settings.INFLUX_ORG}:{settings.INFLUX_BUCKET}", # Token handled differently in v2 usually, but here simulating v1 or standard token
            org=settings.INFLUX_ORG
        )
        self.query_api = self.client.query_api()

influx_db = InfluxDBClient(url=settings.INFLUX_URL, token=settings.INFLUX_BUCKET, org=settings.INFLUX_ORG) # Placeholder. Real auth usually token.

def get_influx_query_api():
    # In a real app, use dependency injection or a singleton properly initialized
    # For now, return a client created on demand or global
    client = InfluxDBClient(url=settings.INFLUX_URL, token=settings.INFLUX_BUCKET, org=settings.INFLUX_ORG) # Insecure token usage
    return client.query_api()
