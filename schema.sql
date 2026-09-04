-- PostgreSQL Schema for Weather ETL Pipeline

CREATE TABLE IF NOT EXISTS weather_readings (
    city VARCHAR(50) NOT NULL,
    observed_at TIMESTAMP WITH TIME ZONE NOT NULL,
    temp_f NUMERIC(5, 2) NOT NULL,
    humidity INT,
    wind_speed_mph NUMERIC(5, 2),
    weather_code INT,
    fetched_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (city, observed_at)
);

-- Index to optimize time-series analytical queries by city
CREATE INDEX IF NOT EXISTS idx_weather_city_observed 
ON weather_readings (city, observed_at DESC);