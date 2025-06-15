#!/usr/bin/env python3
import requests
import json
import base64
import time
import sys
import logging
import uuid
from datetime import datetime
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('sems_scraper')

class SEMSPortalClient:
    def __init__(self, username: str, password: str, region: str = 'au'):
        self.username = username
        self.password = password
        self.region = region
        self.base_url = f"https://{region}.semsportal.com/api"
        self.session = requests.Session()
        self.token_data = None
        self.power_station_id = None
        self.last_login = None
        self.login_expiry = 3600  # Token expires after 1 hour
        
        # Set initial headers
        initial_token = {"uid": "", "timestamp": 0, "token": "", "client": "web", "version": "", "language": "en"}
        token_base64 = base64.b64encode(json.dumps(initial_token).encode()).decode()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Content-Type": "application/json",
            "Token": token_base64
        })

    def login(self) -> bool:
        """Login to SEMS Portal"""
        # Check if existing token is still valid
        if self.token_data and self.last_login:
            elapsed = (datetime.now() - self.last_login).total_seconds()
            if elapsed < self.login_expiry:
                return True

        url = f"{self.base_url}/v3/Common/CrossLogin"
        data = {
            "account": self.username,
            "pwd": self.password,
            "is_local": True,
            "agreement_agreement": 1
        }
        
        try:
            response = self.session.post(url, json=data)
            result = response.json()
            
            if not result.get("hasError") and result.get("data"):
                token_data = result["data"]
                token_base64 = base64.b64encode(json.dumps(token_data).encode()).decode()
                self.session.headers.update({"Token": token_base64})
                self.token_data = token_data
                self.last_login = datetime.now()
                logger.info("Successfully logged in to SEMS Portal")
                return True
            
            logger.error(f"Login failed: {result.get('msg', 'Unknown error')}")
            return False
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return False

    def get_power_station_id(self) -> bool:
        """Get power station ID"""
        if self.power_station_id:
            return True
            
        url = f"{self.base_url}/v3/PowerStation/List"
        data = {"page": 1, "size": 10}
        
        try:
            response = self.session.post(url, json=data)
            result = response.json()
            
            if not result.get("hasError") and result.get("data"):
                stations = result["data"].get("list", [])
                if stations:
                    self.power_station_id = stations[0].get("id")
                    logger.info(f"Found power station ID: {self.power_station_id}")
                    return True
            
            logger.error("No power stations found")
            return False
        except Exception as e:
            logger.error(f"Failed to get power station ID: {str(e)}")
            return False

    def get_inverter_data(self) -> Optional[Dict[str, Any]]:
        """Get inverter data from SEMS Portal"""
        if not self.power_station_id:
            return None
        
        url = f"{self.base_url}/v3/PowerStation/GetInverterAllPoint"
        data = {"powerStationId": self.power_station_id}
        
        try:
            response = self.session.post(url, json=data)
            result = response.json()
            if not result.get("hasError") and result.get("data"):
                return result["data"]
            logger.error(f"Failed to get inverter data: {result.get('msg', 'Unknown error')}")
            return None
        except Exception as e:
            logger.error(f"Failed to get inverter data: {str(e)}")
            return None

    def collect_data(self) -> Optional[Dict[str, Any]]:
        """Collect all inverter data"""
        if not self.login() or not self.get_power_station_id():
            return None
        
        inverter_data = self.get_inverter_data()
        if not inverter_data or "inverterPoints" not in inverter_data:
            return None
        
        inverter = inverter_data["inverterPoints"][0]
        return {
            "timestamp": datetime.now().isoformat(),
            "inverter": {
                "name": inverter.get("name", ""),
                "sn": inverter.get("sn", ""),
                "status": "Online" if inverter.get("status") == 1 else "Offline",
                "current_power": inverter.get("out_pac", 0),
                "daily_energy": inverter.get("eday", 0),
                "monthly_energy": inverter.get("emonth", 0),
                "total_energy": inverter.get("etotal", 0),
                "total_hours": inverter.get("hTotal", 0),
            }
        }

    def write_to_influxdb(self, data: Dict[str, Any], influx_config: Dict[str, str]) -> bool:
        """Write data to InfluxDB"""
        if not data:
            return False
        
        try:
            client = InfluxDBClient(
                url=influx_config['url'],
                token=influx_config['token'],
                org=influx_config['org']
            )
            write_api = client.write_api(write_options=SYNCHRONOUS)
            
            inverter = data.get("inverter", {})
            collection_id = str(uuid.uuid4())[:8]
            
            point = Point("inverter_status")\
                .tag("inverter_name", inverter.get('name', ''))\
                .tag("inverter_sn", inverter.get('sn', ''))\
                .tag("status", inverter.get('status', 'Unknown'))\
                .tag("collection_id", collection_id)\
                .field("current_power", float(inverter.get('current_power', 0)))\
                .field("daily_energy", float(inverter.get('daily_energy', 0)))\
                .field("monthly_energy", float(inverter.get('monthly_energy', 0)))\
                .field("total_energy", float(inverter.get('total_energy', 0)))\
                .field("total_hours", float(inverter.get('total_hours', 0)))\
                .time(datetime.now())
            
            write_api.write(bucket=influx_config['bucket'], org=influx_config['org'], record=point)
            client.close()
            logger.info("Data written to InfluxDB successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to write to InfluxDB: {str(e)}")
            return False

def load_config() -> Optional[Dict[str, Any]]:
    """Load configuration from file"""
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load config: {str(e)}")
        return None

def main():
    """Main function"""
    config = load_config()
    if not config:
        logger.error("Failed to load configuration")
        sys.exit(1)
    
    client = SEMSPortalClient(
        config['sems']['username'],
        config['sems']['password'],
        config['sems']['region']
    )
    
    interval = config.get('settings', {}).get('interval', 300)
    logger.info(f"Starting data collection, interval: {interval}s")
    
    while True:
        try:
            data = client.collect_data()
            if data:
                if client.write_to_influxdb(data, config['influxdb']):
                    logger.info("✅ Data collection successful")
                else:
                    logger.error("❌ Failed to write to InfluxDB")
            else:
                logger.error("❌ Failed to collect data")
            
            time.sleep(interval)
        except KeyboardInterrupt:
            logger.info("🛑 Stopping data collection...")
            break
        except Exception as e:
            logger.error(f"❌ Error: {str(e)}")
            time.sleep(30)  # Wait before retrying on error

if __name__ == "__main__":
    main()
