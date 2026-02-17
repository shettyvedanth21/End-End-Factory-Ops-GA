from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS, ASYNCHRONOUS
from app.core.config import settings

class InfluxService:
    def __init__(self):
        self.client = InfluxDBClient(
            url=settings.INFLUX_URL,
            token=f"{settings.INFLUX_ORG}:{settings.INFLUX_BUCKET}", 
            org=settings.INFLUX_ORG
        )
        self.write_api = self.client.write_api(write_options=ASYNCHRONOUS)

    def write_point(self, factory_id: str, device_id: str, data: dict, timestamp: str = None):
        """
        Write multiple fields for a device.
        """
        p = Point("device_metrics") \
            .tag("factory_id", factory_id) \
            .tag("device_id", device_id)
        
        for k, v in data.items():
            if isinstance(v, (int, float, bool)):
                p = p.field(k, v)
                # Also add property_name tag as per HLD 5.2? 
                # HLD 5.2 says: Tags: factory_id, device_id, property_name. Field: value.
                # If we follow HLD strictly, we need one point per property?
                # "Tags: - factory_id - device_id - property_name. Field: - value"
                # This approach (one point per property) allows filtering by property_name easily in Flux.
                # If we put all properties as fields in one measurement, filtering by property becomes `r._field == "temp"`.
                # HLD explicitly says "Tag: property_name". So we should write one point per property.
                pass

        points = []
        for k, v in data.items():
            if isinstance(v, (int, float, bool)):
                point = Point("device_metrics") \
                    .tag("factory_id", factory_id) \
                    .tag("device_id", device_id) \
                    .tag("property_name", k) \
                    .field("value", v)
                if timestamp:
                    point = point.time(timestamp) # standard datetime or localized
                points.append(point)
        
        if points:
            self.write_api.write(bucket=settings.INFLUX_BUCKET, org=settings.INFLUX_ORG, record=points)

influx_service = InfluxService()
