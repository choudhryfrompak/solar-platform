import json
import os

def load_influx_config():
    try:
        config_path = os.path.join(os.path.dirname(__file__), 'influx_config.json')
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "url": "http://influxdb:8086",
            "token": "your-super-secret-token",
            "org": "solar",
            "bucket": "solar-bucket"
        }

INFLUX_CONFIG = load_influx_config() 