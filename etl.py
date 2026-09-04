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

def transform(raw_payloads: list[dict]) -> list[tuple]:
    transformed_records = []
    fetched_at = datetime.now(timezone.utc)
    
    for payload in raw_payloads:
        city = payload.get("_city_name", "Unknown")
        current = payload.get("current")

        if not current:
            logger.warning(f"Skipping {city}: Missing 'current' data block.")
            continue
        
        temp_c = current.get("temperature_2m")
        observed_at_str = current.get("time")

        if temp_c is None or not observed_at_str:
            logger.warning(f"Skipping {city}: Missing required fields.")
            continue
        
        try:
            # Business Logic 1: Unit Conversion (Celsius to Fahrenheit)
            temp_f = round((temp_c * 9 / 5) + 32, 2)

            # Business Logic 2: Standardize timestamp to UTC datetime object
            observed_at = datetime.fromisoformat(observed_at_str).replace(tzinfo=timezone.utc)

            humidity = current.get("relative_humidity_2m")
            wind_speed = current.get("wind_speed_10m")
            weather_code = current.get("weather_code")

            record = (city, observed_at, temp_f, humidity, wind_speed, weather_code, fetched_at)
            transformed_records.append(record)

        except Exception as e:
            logger.warning(f"Error parsing record for {city}: {e}")
            continue

    return transformed_records