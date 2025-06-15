from influxdb_client import InfluxDBClient, Point
from datetime import datetime
from typing import Dict, Any

class InfluxManager:
    def __init__(self, url: str, token: str, org: str, bucket: str):
        self.client = InfluxDBClient(url=url, token=token, org=org)
        self.write_api = self.client.write_api()
        self.query_api = self.client.query_api()
        self.bucket = bucket
        self.org = org

    def write_power_generation(self, data: Dict[str, Any]):
        """
        Write power generation data to InfluxDB
        
        Expected data format:
        {
            "power_generation": float,
            "earning": float,
            "used": float,
            "property_id": int,
            "user_id": int,
            "device_id": str
        }
        """
        point = Point("power_generation") \
            .field("power_generation", data["power_generation"]) \
            .field("earning", data["earning"]) \
            .field("used", data["used"]) \
            .tag("property_id", str(data["property_id"])) \
            .tag("user_id", str(data["user_id"])) \
            .tag("device_id", data["device_id"]) \
            .time(datetime.utcnow())
        
        self.write_api.write(bucket=self.bucket, record=point)

    def write_home_metrics(self, data: Dict[str, Any]):
        """
        Write home metrics data to InfluxDB
        
        Expected data format:
        {
            "producing": float,
            "consuming": float,
            "charging": float,
            "exporting": float,
            "climate": str,
            "rain_percentage": float,
            "property_id": int,
            "user_id": int
        }
        """
        point = Point("home_metrics") \
            .field("producing", data["producing"]) \
            .field("consuming", data["consuming"]) \
            .field("charging", data["charging"]) \
            .field("exporting", data["exporting"]) \
            .field("climate", data["climate"]) \
            .field("rain_percentage", data["rain_percentage"]) \
            .tag("property_id", str(data["property_id"])) \
            .tag("user_id", str(data["user_id"])) \
            .time(datetime.utcnow())
        
        self.write_api.write(bucket=self.bucket, record=point)

    def get_daily_power_generation(self, property_id: int, start_time: datetime, end_time: datetime = None):
        """Get daily power generation data for a property"""
        if end_time is None:
            end_time = datetime.utcnow()

        query = f'''
        from(bucket: "{self.bucket}")
            |> range(start: {start_time.isoformat()}, stop: {end_time.isoformat()})
            |> filter(fn: (r) => r["_measurement"] == "power_generation")
            |> filter(fn: (r) => r["property_id"] == "{str(property_id)}")
            |> aggregateWindow(every: 1d, fn: sum)
        '''
        
        return self.query_api.query(query, org=self.org)

    def get_home_metrics(self, property_id: int, start_time: datetime, end_time: datetime = None):
        """Get home metrics data for a property"""
        if end_time is None:
            end_time = datetime.utcnow()

        query = f'''
        from(bucket: "{self.bucket}")
            |> range(start: {start_time.isoformat()}, stop: {end_time.isoformat()})
            |> filter(fn: (r) => r["_measurement"] == "home_metrics")
            |> filter(fn: (r) => r["property_id"] == "{str(property_id)}")
        '''
        
        return self.query_api.query(query, org=self.org)

    def get_device_metrics(self, device_id: str, start_time: datetime, end_time: datetime = None):
        """Get device-specific metrics"""
        if end_time is None:
            end_time = datetime.utcnow()

        query = f'''
        from(bucket: "{self.bucket}")
            |> range(start: {start_time.isoformat()}, stop: {end_time.isoformat()})
            |> filter(fn: (r) => r["_measurement"] == "power_generation")
            |> filter(fn: (r) => r["device_id"] == "{device_id}")
        '''
        
        return self.query_api.query(query, org=self.org) 