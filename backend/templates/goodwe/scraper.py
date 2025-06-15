#!/usr/bin/env python3
import requests
import json
import base64
import time
import os
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
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('sems_scraper.log')
    ]
)
logger = logging.getLogger('sems_scraper')

class SEMSPortalClient:
    def __init__(self, username: str, password: str, region: str = 'au'):
        self.username = username
        self.password = password
        self.region = region
        self.base_url = f"https://{region}.semsportal.com/api"
        self.session = requests.Session()
        self.session.last_response_error = None
        self.initial_token = {
            "uid": "",
            "timestamp": 0,
            "token": "",
            "client": "web",
            "version": "",
            "language": "en"
        }
        self.token_base64 = base64.b64encode(json.dumps(self.initial_token).encode()).decode()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Content-Type": "application/json",
            "Token": self.token_base64
        })
        self.token_data = None
        self.power_station_id = None
        self.inverter_sn = None
        self.last_login_time = None

    def login(self) -> bool:
        """Login to SEMS Portal"""
        login_url = f"{self.base_url}/v2/Common/CrossLogin"
        login_data = {
            "account": self.username,
            "pwd": self.password,
            "agreement_agreement": 0,
            "is_local": False
        }
        try:
            logger.info(f"Logging in to SEMS Portal ({self.region})...")
            response = self.session.post(login_url, json=login_data)
            logger.debug(f"Login response status: {response.status_code}")
            result = response.json()
            logger.debug(f"Login response: {json.dumps(result, indent=2)}")
            if not result.get("hasError") and result.get("data") is not None:
                self.token_data = result["data"]
                self.last_login_time = datetime.now()
                token_base64 = base64.b64encode(json.dumps(self.token_data).encode()).decode()
                self.session.headers.update({"Token": token_base64})
                logger.info("Login successful!")
                return True
            else:
                self.session.last_response_error = result.get('msg', 'Unknown error')
                logger.error(f"Login failed: {self.session.last_response_error}")
                return False
        except Exception as e:
            self.session.last_response_error = str(e)
            logger.error(f"Login request failed: {e}")
            return False

    def get_power_station_id(self) -> bool:
        """Get power station ID"""
        url = f"{self.base_url}/PowerStation/GetPowerStationIdByOwner"
        try:
            logger.info("Getting power station ID...")
            response = self.session.post(url, json={})
            logger.debug(f"Power station response status: {response.status_code}")
            result = response.json()
            # Log the full response for debugging
            logger.error(f"Full response from GetPowerStationIdByOwner: {json.dumps(result, indent=2)}")
            if not result.get("hasError") and result.get("data") is not None:
                self.power_station_id = result["data"]
                logger.info(f"Power station ID: {self.power_station_id}")
                return self.power_station_id
            else:
                self.session.last_response_error = result.get('msg', 'Unknown error')
                logger.error(f"Failed to get power station ID: {self.session.last_response_error}")
                return None
        except Exception as e:
            self.session.last_response_error = str(e)
            logger.error(f"Power station ID request failed: {e}")
            return None

    def get_inverter_data(self) -> Optional[Dict[str, Any]]:
        """Get inverter data from SEMS Portal"""
        if not self.power_station_id:
            logger.error("No power station ID available. Call get_power_station_id() first.")
            return None
        url = f"{self.base_url}/v3/PowerStation/GetInverterAllPoint"
        data = {"powerStationId": self.power_station_id}
        try:
            logger.info("Getting inverter data...")
            response = self.session.post(url, json=data)
            logger.debug(f"Inverter data response status: {response.status_code}")
            result = response.json()
            logger.debug(f"Inverter data response: {json.dumps(result, indent=2)}")
            if not result.get("hasError") and result.get("data") is not None:
                inverters = result["data"].get("inverterPoints", [])
                if inverters:
                    self.inverter_sn = inverters[0]["sn"]
                    logger.info(f"Found inverter SN: {self.inverter_sn}")
                return result["data"]
            else:
                self.session.last_response_error = result.get('msg', 'Unknown error')
                logger.error(f"Failed to get inverter data: {self.session.last_response_error}")
                return None
        except Exception as e:
            self.session.last_response_error = str(e)
            logger.error(f"Inverter data request failed: {e}")
            return None

    def collect_data(self) -> Optional[Dict[str, Any]]:
        """Collect all inverter data"""
        if not self.login():
            logger.error("Failed to login to SEMS Portal")
            return None
        if not self.get_power_station_id():
            logger.error("Failed to get power station ID")
            return None
        inverter_data = self.get_inverter_data()
        if not inverter_data:
            logger.error("Failed to get inverter data")
            return None
        return inverter_data

    def write_to_influxdb(self, data: Dict[str, Any], influx_config: Dict[str, str]) -> bool:
        """Write data to InfluxDB"""
        if not data:
            logger.error("No data available to write to InfluxDB.")
            return False
        
        try:
            logger.info(f"Connecting to InfluxDB at {influx_config['url']}...")
            client = InfluxDBClient(
                url=influx_config['url'],
                token=influx_config['token'],
                org=influx_config['org']
            )
            write_api = client.write_api(write_options=SYNCHRONOUS)
            inverters = data.get("inverterPoints", [])
            for inverter in inverters:
                point = Point("inverter_status")\
                    .tag("inverter_name", inverter.get('name', ''))\
                    .tag("inverter_sn", inverter.get('sn', ''))\
                    .tag("status", "Online" if inverter.get('status') == 1 else "Offline")\
                    .field("current_power", float(inverter.get('out_pac', 0)))\
                    .field("daily_energy", float(inverter.get('eday', 0)))\
                    .field("monthly_energy", float(inverter.get('emonth', 0)))\
                    .field("total_energy", float(inverter.get('etotal', 0)))\
                    .field("total_hours", float(inverter.get('hTotal', 0)))\
                    .time(datetime.now())
                write_api.write(bucket=influx_config['bucket'], org=influx_config['org'], record=point)
            client.close()
            logger.info("Successfully wrote inverter data to InfluxDB")
            return True
        except Exception as e:
            logger.error(f"Failed to write to InfluxDB: {e}")
            return False

def load_config(config_file='config.json') -> Optional[Dict[str, Any]]:
    """Load configuration from file"""
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        logger.error(f"Configuration file '{config_file}' not found.")
        return None
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in configuration file '{config_file}'.")
        return None
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        return None

def main():
    """Main function"""
    config = load_config()
    if not config:
        logger.error("Failed to load configuration. Exiting.")
        sys.exit(1)
    sems_config = config.get('sems', {})
    username = sems_config.get('username')
    password = sems_config.get('password')
    region = sems_config.get('region', 'au')
    if not username or not password:
        logger.error("SEMS username or password not found in configuration.")
        sys.exit(1)
    influx_config = config.get('influxdb', {})
    if not all(k in influx_config for k in ['url', 'token', 'org', 'bucket']):
        logger.error("Missing required InfluxDB configuration.")
        sys.exit(1)
    client = SEMSPortalClient(username, password, region)
    interval = config.get('settings', {}).get('interval', 300)
    logger.info(f"Starting data collection, interval: {interval}s")
    while True:
        data = client.collect_data()
        if data:
            client.write_to_influxdb(data, influx_config)
        else:
            logger.error("❌ Failed to collect data")
        logger.info(f"Sleeping for {interval} seconds before next collection")
        time.sleep(interval)

if __name__ == "__main__":
    main() 