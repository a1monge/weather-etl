import logging
import os
from datetime import datetime, timezone
import psycopg2
from psycopg2.extras import execute_values
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Meteo API Documentation: https://open-meteo.com/en/docs
API_BASE_URL = "https://api.open-meteo.com/v1/forecast"

CITIES = {
    "Dallas": {"lat": 32.7767, "lon": -96.7970},
    "Austin": {"lat": 30.2672, "lon": -97.7431},
    "Houston": {"lat": 29.7604, "lon": -95.3698},
    "San Antonio": {"lat": 29.4241, "lon": -98.4936},
}

def extract(cities: dict) -> list[dict]:
    extracted_data = []

    for city_name, coords in cities.items():
        params = {
            "latitude": coords["lat"],
            "longitude": coords["lon"],
            "current": ["temperature_2m", "relative_humidity_2m", "wind_speed_10m", "weather_code"],
            "wind_speed_unit": "mph",
            "timezone": "UTC",
        }
        try:
            response = requests.get(API_BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            payload = response.json()
            payload["_city_name"] = city_name
            extracted_data.append(payload)
        except requests.RequestException as e:
            logger.warning(f"Failed to fetch data for {city_name}: {e}")
            continue

    return extracted_data