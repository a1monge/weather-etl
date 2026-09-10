"""
Unit tests for etl.transform()

Run:
    pytest test_etl.py -v
"""

from datetime import datetime, timezone

import pytest

from etl import transform


# Helpers
def make_payload(city="Dallas", current=None):
    """Build a fake Open-Meteo API response shaped like the real one."""
    payload = {"_city_name": city}
    if current is not None:
        payload["current"] = current
    return payload


VALID_CURRENT = {
    "temperature_2m": 37.0,  # Celsius
    "time": "2026-09-08T21:45",
    "relative_humidity_2m": 36,
    "wind_speed_10m": 9.2,
    "weather_code": 0,
}



# Happy path
def test_valid_record_is_transformed_correctly():
    payload = make_payload("Dallas", VALID_CURRENT)

    result = transform([payload])

    assert len(result) == 1
    city, observed_at, temp_f, humidity, wind_speed, weather_code, fetched_at = result[0]

    assert city == "Dallas"
    # 37.0 C -> 98.6 F
    assert temp_f == 98.6
    assert humidity == 36
    assert wind_speed == 9.2
    assert weather_code == 0
    assert observed_at.tzinfo == timezone.utc
    assert isinstance(fetched_at, datetime)


def test_celsius_to_fahrenheit_conversion_is_correct():
    # 0 C should convert to 32 F
    current = {**VALID_CURRENT, "temperature_2m": 0.0}
    payload = make_payload("Austin", current)

    result = transform([payload])

    assert result[0][2] == 32.0


def test_multiple_cities_one_batch_all_valid():
    payloads = [
        make_payload("Dallas", VALID_CURRENT),
        make_payload("Houston", {**VALID_CURRENT, "temperature_2m": 30.0}),
    ]

    result = transform(payloads)

    assert len(result) == 2
    cities = {record[0] for record in result}
    assert cities == {"Dallas", "Houston"}



# Missing / malformed data - should be skipped, not crash the whole run
def test_missing_current_block_is_skipped():
    payload = make_payload("Dallas", current=None)

    result = transform([payload])

    assert result == []


def test_missing_temperature_is_skipped():
    current = {k: v for k, v in VALID_CURRENT.items() if k != "temperature_2m"}
    payload = make_payload("Dallas", current)

    result = transform([payload])

    assert result == []


def test_missing_timestamp_is_skipped():
    current = {k: v for k, v in VALID_CURRENT.items() if k != "time"}
    payload = make_payload("Dallas", current)

    result = transform([payload])

    assert result == []


def test_one_bad_city_does_not_block_the_others():
    """A single malformed record should be skipped, not crash the batch."""
    payloads = [
        make_payload("Dallas", VALID_CURRENT),           # valid
        make_payload("Houston", current=None),            # missing current block
        make_payload("Austin", {**VALID_CURRENT, "temperature_2m": 25.0}),  # valid
    ]

    result = transform(payloads)

    assert len(result) == 2
    cities = {record[0] for record in result}
    assert cities == {"Dallas", "Austin"}


def test_optional_fields_can_be_none_without_crashing():
    """humidity/wind_speed/weather_code are optional - missing shouldn't skip the record."""
    current = {
        "temperature_2m": 20.0,
        "time": "2026-09-08T21:45",
        # no relative_humidity_2m, wind_speed_10m, or weather_code
    }
    payload = make_payload("Dallas", current)

    result = transform([payload])

    assert len(result) == 1
    _, _, _, humidity, wind_speed, weather_code, _ = result[0]
    assert humidity is None
    assert wind_speed is None
    assert weather_code is None


def test_empty_input_returns_empty_list():
    assert transform([]) == []