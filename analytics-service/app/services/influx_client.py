from influxdb_client import InfluxDBClient
from app.core.config import settings
import pandas as pd
import logging

logger = logging.getLogger("influx-service")

class InfluxService:
    def __init__(self):
        self.client = InfluxDBClient(
            url=settings.INFLUX_URL,
            token=f"{settings.INFLUX_ORG}:{settings.INFLUX_BUCKET}", 
            org=settings.INFLUX_ORG
        )

    def query_dataset(self, factory_id: str, device_ids: list, properties: list, start: str, end: str) -> pd.DataFrame:
        """
        Query InfluxDB and return Pandas DataFrame.
        """
        
        # Flux query construction
        # filtering by factory_id, device_id in list, property_name in list
        
        range_filter = f'|> range(start: {start}, stop: {end})'
        
        # Filter Device IDs
        device_filter = ' or '.join([f'r.device_id == "{d}"' for d in device_ids])
        if not device_ids:
            device_filter = 'r.device_id != ""' # Catch all if empty or handle error
            
        # Filter Properties
        prop_filter = ' or '.join([f'r.property_name == "{p}"' for p in properties])
        if not properties:
            prop_filter = 'r.property_name != ""'

        query = f'''
        from(bucket: "{settings.INFLUX_BUCKET}")
          {range_filter}
          |> filter(fn: (r) => r.factory_id == "{factory_id}")
          |> filter(fn: (r) => {device_filter})
          |> filter(fn: (r) => {prop_filter})
          |> pivot(rowKey:["_time"], columnKey: ["property_name"], valueColumn: "_value")
          |> keep(columns: ["_time", "device_id"] + {str(properties).replace("'", '"')})
        '''
        
        try:
            df = self.client.query_api().query_data_frame(query=query)
            if isinstance(df, list):
                # If multiple tables returned, concat them
                df = pd.concat(df)
            return df
        except Exception as e:
            logger.error(f"Influx Query Failed: {e}")
            return pd.DataFrame()

influx_service = InfluxService()
