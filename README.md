# Dynamic Weather ETL Pipeline

A production-grade, idempotent ETL (Extract, Transform, Load) pipeline built with Python and PostgreSQL (Supabase) that ingests live weather data via Open-Meteo REST APIs.

## Key Features

- **Dynamic Extraction**: Geocodes city names with HTTP timeouts and fault isolation.
- **Data Transformation**: Converts Celsius to Fahrenheit, validates schema integrity, and standardizes all timestamps to timezone-aware UTC objects.
- **Idempotent Loading**: Bulk inserts records into PostgreSQL using `psycopg2.extras.execute_values` with an `ON CONFLICT (city, observed_at) DO UPDATE` strategy to prevent duplicates.
- **Secure Credentials**: Uses `python-dotenv` and `.gitignore` to keep credentials safe.

## Project Structure

```text
weather-etl/
├── etl.py              # Main ETL pipeline logic
├── requirements.txt    # Third-party dependencies
├── .env                # Database credentials (git-ignored)
├── .gitignore          # Git exclusion rules
└── README.md           # Project documentation
```
