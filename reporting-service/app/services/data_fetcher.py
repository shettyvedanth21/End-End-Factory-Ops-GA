import pandas as pd
from influxdb_client import InfluxDBClient
from sqlalchemy import text
from app.core.config import settings
from app.core import database
import logging

logger = logging.getLogger("data-fetcher")

class DataFetcher:
    def __init__(self):
        self.influx_client = InfluxDBClient(
            url=settings.INFLUX_URL,
            token=f"{settings.INFLUX_ORG}:{settings.INFLUX_BUCKET}", 
            org=settings.INFLUX_ORG
        )

    def get_telemetry_aggregates(self, factory_id, device_ids, start, end):
        # Sample aggregate query
        device_filter = ""
        if device_ids:
            device_filter = " or ".join([f'r.device_id == "{d}"' for d in device_ids])
            device_filter = f'|> filter(fn: (r) => {device_filter})'
            
        query = f'''
        from(bucket: "{settings.INFLUX_BUCKET}")
          |> range(start: {start.isoformat()}Z, stop: {end.isoformat()}Z)
          |> filter(fn: (r) => r.factory_id == "{factory_id}")
          {device_filter}
          |> filter(fn: (r) => r._field == "value")
          |> aggregateWindow(every: 1h, fn: mean)
          |> pivot(rowKey:["_time"], columnKey: ["property_name"], valueColumn: "_value")
        '''
        try:
             df = self.influx_client.query_api().query_data_frame(query=query)
             if isinstance(df, list):
                 df = pd.concat(df)
             return df
        except Exception as e:
            logger.error(f"Influx Query failed: {e}")
            return pd.DataFrame()

    def get_alerts(self, factory_id, device_ids, start, end):
        db = database.SessionLocal()
        try:
            # Need to access Alert model directly or via raw SQL if Model not shared
            # Ideally Reporting Service would have read-only access to Alerts table via shared lib or replicated model
            # For this milestone, we redefine simple Alert model or use raw SQL
            query = text("""
                SELECT * FROM alerts 
                WHERE factory_id = :fid 
                AND triggered_at BETWEEN :start AND :end
            """)
            result = db.execute(query, {"fid": factory_id, "start": start, "end": end}).fetchall()
            # Convert to list of dicts or DF
            return [dict(row._mapping) for row in result]
        finally:
            db.close()
            
data_fetcher = DataFetcher()
