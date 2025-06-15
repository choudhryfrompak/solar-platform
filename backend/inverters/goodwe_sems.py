import requests
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class GoodWeSEMSClient:
    LOGIN_URL = "https://www.semsportal.com/api/v2/Common/CrossLogin"
    POWER_STATION_URL = "/v2/PowerStation/GetMonitorDetailByPowerstationId"
    POWER_CONTROL_URL = "https://www.semsportal.com/api/PowerStation/SaveRemoteControlInverter"
    REQUEST_TIMEOUT = 30

    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.token = None
        self.api_url = None

    def _get_default_headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Token": json.dumps({
                "version": "v2.1.0",
                "client": "ios",
                "language": "en"
            })
        }

    def _get_auth_headers(self) -> Dict[str, str]:
        if not self.token:
            raise ValueError("Not authenticated. Call login() first.")
        
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Token": json.dumps({
                "version": "v2.1.0",
                "client": "ios",
                "language": "en",
                "timestamp": self.token["timestamp"],
                "uid": self.token["uid"],
                "token": self.token["token"]
            })
        }

    def login(self) -> bool:
        """Login to SEMS Portal and get authentication token"""
        try:
            login_data = {
                "account": self.username,
                "pwd": self.password
            }

            response = requests.post(
                self.LOGIN_URL,
                headers=self._get_default_headers(),
                json=login_data,
                timeout=self.REQUEST_TIMEOUT
            )
            response.raise_for_status()

            data = response.json()
            if data["msg"] != "Successful":
                logger.error(f"Login failed: {data['msg']}")
                return False

            self.token = data["data"]
            self.api_url = data["api"]
            return True

        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return False

    def get_power_station_data(self, power_station_id: str, max_retries: int = 2) -> Optional[Dict[str, Any]]:
        """Get power station data"""
        if max_retries <= 0:
            logger.error("Maximum retries reached")
            return None

        try:
            if not self.token:
                if not self.login():
                    return None

            url = f"{self.api_url}{self.POWER_STATION_URL}"
            response = requests.post(
                url,
                headers=self._get_auth_headers(),
                json={"powerStationId": power_station_id},
                timeout=self.REQUEST_TIMEOUT
            )
            response.raise_for_status()

            data = response.json()
            if data["msg"] != "success" or not data["data"]:
                # Token might be expired, try to login again
                if self.login():
                    return self.get_power_station_data(power_station_id, max_retries - 1)
                return None

            return data["data"]

        except Exception as e:
            logger.error(f"Error getting power station data: {str(e)}")
            return None

    def control_inverter(self, inverter_sn: str, status: bool, max_retries: int = 2) -> bool:
        """Control inverter status (on/off)"""
        if max_retries <= 0:
            logger.error("Maximum retries reached")
            return False

        try:
            if not self.token:
                if not self.login():
                    return False

            data = {
                "InverterSN": inverter_sn,
                "InverterStatusSettingMark": "1",
                "InverterStatus": "1" if status else "0"
            }

            response = requests.post(
                self.POWER_CONTROL_URL,
                headers=self._get_auth_headers(),
                json=data,
                timeout=self.REQUEST_TIMEOUT
            )
            response.raise_for_status()

            if response.status_code != 200:
                if self.login():
                    return self.control_inverter(inverter_sn, status, max_retries - 1)
                return False

            return True

        except Exception as e:
            logger.error(f"Error controlling inverter: {str(e)}")
            return False

    def transform_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform raw SEMS data into standardized format"""
        try:
            # Extract relevant data from the raw response
            # This will need to be adjusted based on the actual SEMS API response structure
            return {
                "power_generation": float(raw_data.get("power", 0)),
                "earning": float(raw_data.get("money", 0)),
                "used": float(raw_data.get("used", 0)),
                "producing": float(raw_data.get("current_power", 0)),
                "consuming": float(raw_data.get("home_consumption", 0)),
                "charging": float(raw_data.get("battery_charging", 0)),
                "exporting": float(raw_data.get("grid_export", 0)),
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            logger.error(f"Error transforming data: {str(e)}")
            return None 