"""Hyper-local GPS & precision location live weather tool."""

from __future__ import annotations

import json
import os
import time
import urllib.parse
import urllib.request
from typing import Any, Dict, Optional, Tuple

from app.constants import RiskLevel
from app.tools.base import Tool, ToolResult
from app.utils.logging import get_logger

logger = get_logger("tools.weather")

DEFAULT_USER_LOCATION = "Dhamtour, Abbottabad"


def get_current_gps_location() -> Tuple[str, str, str, str]:
    """Retrieve user's precise configured location (Dhamtour, Abbottabad)."""
    env_loc = os.environ.get("USER_LOCATION", "").strip() or DEFAULT_USER_LOCATION
    return ("Dhamtour, Abbottabad", "Khyber Pakhtunkhwa", "Pakistan", env_loc)


class GetWeatherTool(Tool):
    name = "get_weather"
    description = "Fetches current hyper-local weather conditions, temperature, humidity, wind, and forecast for Dhamtour, Abbottabad or any specified city."
    risk_level = RiskLevel.SAFE
    requires_confirmation = False
    parameters = {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "City or area name (e.g. 'Dhamtour, Abbottabad', 'Lahore', 'Islamabad'). Default is user location 'Dhamtour, Abbottabad'.",
                "default": "Dhamtour, Abbottabad",
            },
        },
    }

    def execute(self, location: str = "auto", **kwargs: Any) -> ToolResult:
        try:
            if not location or location.lower() in ("auto", "current", "", "none", "local"):
                target_loc = os.environ.get("USER_LOCATION", "").strip() or DEFAULT_USER_LOCATION
            else:
                target_loc = location.strip()

            loc_query = urllib.parse.quote(target_loc)
            url = f"https://wttr.in/{loc_query}?format=j1"
            headers = {"User-Agent": "JARVIS-Desktop-Agent/1.0"}
            req = urllib.request.Request(url, headers=headers)

            with urllib.request.urlopen(req, timeout=6) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            current = data.get("current_condition", [{}])[0]
            nearest_area = data.get("nearest_area", [{}])[0]

            city_name = target_loc if target_loc != "auto" else nearest_area.get("areaName", [{}])[0].get("value", "Dhamtour, Abbottabad")
            country_name = nearest_area.get("country", [{}])[0].get("value", "Pakistan")
            temp_c = current.get("temp_C", "N/A")
            temp_f = current.get("temp_F", "N/A")
            feels_like_c = current.get("FeelsLikeC", "N/A")
            desc = current.get("weatherDesc", [{}])[0].get("value", "Clear")
            humidity = current.get("humidity", "N/A")
            wind_kmph = current.get("windspeedKmph", "N/A")
            wind_dir = current.get("winddir16Point", "")

            weather_report = {
                "city": city_name,
                "country": country_name,
                "temperature_c": f"{temp_c}°C",
                "temp_num": temp_c,
                "temperature_f": f"{temp_f}°F",
                "feels_like": f"{feels_like_c}°C",
                "condition": desc,
                "humidity": f"{humidity}%",
                "wind": f"{wind_kmph} km/h {wind_dir}",
                "summary": f"The weather in {city_name}, {country_name} is currently {desc} at {temp_c}°C ({temp_f}°F), feels like {feels_like_c}°C with {humidity}% humidity and wind of {wind_kmph} km/h {wind_dir}."
            }

            return ToolResult(success=True, output=weather_report)
        except Exception as e:
            logger.error(f"Weather fetch failed for '{location}': {e}")
            return ToolResult(
                success=False,
                output="",
                error=f"Unable to retrieve live weather data for '{location}': {e}",
            )
