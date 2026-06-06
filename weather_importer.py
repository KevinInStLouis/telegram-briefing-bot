# weather_importer.py
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from memories import Memory, create_memory


OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


WEATHER_CODES = {
    0: "clear",
    1: "mainly clear",
    2: "partly cloudy",
    3: "overcast",
    45: "foggy",
    48: "rime fog",
    51: "light drizzle",
    53: "moderate drizzle",
    55: "dense drizzle",
    56: "light freezing drizzle",
    57: "dense freezing drizzle",
    61: "slight rain",
    63: "moderate rain",
    65: "heavy rain",
    66: "light freezing rain",
    67: "heavy freezing rain",
    71: "slight snow",
    73: "moderate snow",
    75: "heavy snow",
    77: "snow grains",
    80: "slight showers",
    81: "moderate showers",
    82: "violent showers",
    85: "slight snow showers",
    86: "heavy snow showers",
    95: "thunderstorms",
    96: "thunderstorms with slight hail",
    99: "thunderstorms with heavy hail",
}


@dataclass(frozen=True)
class WeatherForecast:
    date: str
    summary: str
    high_f: float | None
    low_f: float | None
    precipitation_probability: int | None
    precipitation_sum_in: float | None
    weather_code: int | None


def _env_float(*names: str) -> float | None:
    for name in names:
        value = os.getenv(name)
        if value:
            return float(value)
    return None


def _env_str(*names: str, default: str | None = None) -> str | None:
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    return default


def get_weather_config() -> tuple[float, float, str]:
    latitude = _env_float("STEVENS_WEATHER_LATITUDE", "WEATHER_LATITUDE")
    longitude = _env_float("STEVENS_WEATHER_LONGITUDE", "WEATHER_LONGITUDE")
    timezone = _env_str("STEVENS_TIMEZONE", "WEATHER_TIMEZONE", default="America/Chicago")

    if latitude is None or longitude is None:
        raise RuntimeError(
            "Weather importer requires STEVENS_WEATHER_LATITUDE and "
            "STEVENS_WEATHER_LONGITUDE in the environment."
        )

    return latitude, longitude, timezone or "America/Chicago"


def fetch_open_meteo_forecast(
    *,
    latitude: float,
    longitude: float,
    timezone: str,
    timeout_seconds: int = 20,
) -> dict[str, Any]:
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "timezone": timezone,
        "forecast_days": 1,
        "temperature_unit": "fahrenheit",
        "wind_speed_unit": "mph",
        "precipitation_unit": "inch",
        "current": "temperature_2m,weather_code,wind_speed_10m",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,precipitation_sum",
    }
    url = f"{OPEN_METEO_FORECAST_URL}?{urlencode(params)}"
    request = Request(url, headers={"User-Agent": "Stevens/0.1 telegram-briefing-bot"})
    with urlopen(request, timeout=timeout_seconds) as response:
        return json.loads(response.read().decode("utf-8"))


def _first(values: list[Any] | None) -> Any | None:
    if not values:
        return None
    return values[0]


def _round_temp(value: float | int | None) -> int | None:
    if value is None:
        return None
    return int(round(float(value)))


def _format_summary(forecast: WeatherForecast) -> str:
    parts: list[str] = []
    if forecast.high_f is not None and forecast.low_f is not None:
        parts.append(f"High of {_round_temp(forecast.high_f)}, low of {_round_temp(forecast.low_f)}")
    elif forecast.high_f is not None:
        parts.append(f"High of {_round_temp(forecast.high_f)}")
    elif forecast.low_f is not None:
        parts.append(f"Low of {_round_temp(forecast.low_f)}")

    if forecast.summary:
        parts.append(forecast.summary)

    if forecast.precipitation_probability is not None:
        parts.append(f"precipitation chance {forecast.precipitation_probability}%")
    elif forecast.precipitation_sum_in is not None and forecast.precipitation_sum_in > 0:
        parts.append(f"precipitation around {forecast.precipitation_sum_in:.2f} in")

    if not parts:
        return "weather forecast: Forecast data was fetched, but no concise daily summary was available."

    return "weather forecast: " + ", ".join(parts) + "."


def parse_daily_forecast(payload: dict[str, Any]) -> WeatherForecast:
    daily = payload.get("daily") or {}
    date = _first(daily.get("time")) or datetime.now().date().isoformat()
    weather_code = _first(daily.get("weather_code"))
    weather_code_int = int(weather_code) if weather_code is not None else None
    high_f = _first(daily.get("temperature_2m_max"))
    low_f = _first(daily.get("temperature_2m_min"))
    precipitation_probability = _first(daily.get("precipitation_probability_max"))
    precipitation_sum_in = _first(daily.get("precipitation_sum"))

    forecast = WeatherForecast(
        date=str(date),
        summary=WEATHER_CODES.get(weather_code_int, "weather code unknown"),
        high_f=float(high_f) if high_f is not None else None,
        low_f=float(low_f) if low_f is not None else None,
        precipitation_probability=int(precipitation_probability) if precipitation_probability is not None else None,
        precipitation_sum_in=float(precipitation_sum_in) if precipitation_sum_in is not None else None,
        weather_code=weather_code_int,
    )

    return WeatherForecast(
        date=forecast.date,
        summary=_format_summary(forecast),
        high_f=forecast.high_f,
        low_f=forecast.low_f,
        precipitation_probability=forecast.precipitation_probability,
        precipitation_sum_in=forecast.precipitation_sum_in,
        weather_code=forecast.weather_code,
    )


def import_weather_memory(
    *,
    latitude: float | None = None,
    longitude: float | None = None,
    timezone: str | None = None,
) -> Memory:
    if latitude is None or longitude is None:
        env_latitude, env_longitude, env_timezone = get_weather_config()
        latitude = env_latitude if latitude is None else latitude
        longitude = env_longitude if longitude is None else longitude
        timezone = timezone or env_timezone

    payload = fetch_open_meteo_forecast(
        latitude=float(latitude),
        longitude=float(longitude),
        timezone=timezone or "America/Chicago",
    )
    forecast = parse_daily_forecast(payload)
    return create_memory(
        forecast.summary,
        date=forecast.date,
        tags="weather,briefing",
        created_by="weather",
    )


def main() -> None:
    memory = import_weather_memory()
    print(f"Imported weather memory: {memory.id}")
    print(memory.text)


if __name__ == "__main__":
    main()
