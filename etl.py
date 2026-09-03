import logging
from datetime import datetime, timezone
from psycopg2.extras import execute_values
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Meteo API Documentation: https://open-meteo.com/en/docs

# API ENDPOINTS
GEOCODING_API_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"

# Dynamic input list
CITIES_TO_FETCH = ["Dallas", "Austin", "Houston", "San Antonio", "Lubbock"]


def get_coordinates(city_name: str) -> tuple[float, float] | None:
    """Dynamically resolves a city name string to (latitude, longitude)."""
    params = {"name": city_name, "count": 1, "format": "json"}
    try:
        response = requests.get(GEOCODING_API_URL, params=params, timeout=10)
        response.raise_for_status()
        results = response.json().get("results")

        if not results:
            logger.warning(f"Geocoding failed: No coordinates found for '{city_name}'")
            return None

        lat = results[0]["latitude"]
        lon = results[0]["longitude"]
        return lat, lon

    except requests.RequestException as e:
        logger.warning(f"Geocoding API error for '{city_name}': {e}")
        return None


def extract(city_names: list[str]) -> list[dict]:
    # Extracts weather data for a list of city strings.
    extracted_data = []

    for city_name in city_names:
        # Lookup coordinates dynamically
        coords = get_coordinates(city_name)
        if not coords:
            continue  # Skip city if location lookup failed

        lat, lon = coords

        # Fetch weather using the resolved coordinates
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": ["temperature_2m", "relative_humidity_2m", "wind_speed_10m", "weather_code"],
            "wind_speed_unit": "mph",
            "timezone": "UTC",
        }
        
        try:
            response = requests.get(WEATHER_API_URL, params=params, timeout=10)
            response.raise_for_status()
            payload = response.json()
            payload["_city_name"] = city_name  # Attach city name metadata
            extracted_data.append(payload)

        except requests.RequestException as e:
            logger.warning(f"Failed to fetch weather for '{city_name}': {e}")
            continue

    return extracted_data