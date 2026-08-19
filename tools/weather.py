"""
Weather Tool: Weather lookup using Open-Meteo API with geocoding.
No API key required.
"""

import logging
from typing import Dict, Any, Optional
import requests

logger = logging.getLogger("WeatherTool")

# WMO Weather interpretation codes (WW) mapping
WMO_WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


def geocode_location(location_name: str) -> Optional[Dict[str, Any]]:
    """
    Lookup latitude, longitude, and country for a given location name.
    """
    if not location_name or not location_name.strip():
        return None

    geocode_url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {
        "name": location_name.strip(),
        "count": 1,
        "language": "en",
        "format": "json"
    }

    try:
        response = requests.get(geocode_url, params=params, timeout=10)
        logger.debug(f"Geocoding API response: {response.text}")

        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])
            if results:
                top_result = results[0]
                return {
                    "name": top_result.get("name"),
                    "latitude": top_result.get("latitude"),
                    "longitude": top_result.get("longitude"),
                    "country": top_result.get("country", ""),
                    "admin1": top_result.get("admin1", ""),
                    "timezone": top_result.get("timezone", "UTC"),
                }
    except requests.exceptions.RequestException as e:
        logger.error(f"Geocoding request failed: {e}")

    return None


def get_weather(location: str, latitude: Optional[float] = None, longitude: Optional[float] = None) -> Dict[str, Any]:
    """
    Fetch current weather for a city or coordinates using Open-Meteo API.

    Args:
        location (str): Name of city or place (e.g. "Mumbai", "Delhi", "London", "Tokyo").
        latitude (Optional[float]): Optional latitude coordinate.
        longitude (Optional[float]): Optional longitude coordinate.

    Returns:
        Dict[str, Any]: Structured weather report.
    """
    if not location and (latitude is None or longitude is None):
        return {
            "success": False,
            "error": "Please provide a location name (e.g. 'Mumbai') or latitude and longitude.",
            "data": None
        }

    city_name = location
    country_name = ""

    # If coordinates not supplied, geocode the location name
    if latitude is None or longitude is None:
        geo_info = geocode_location(location)
        if not geo_info:
            return {
                "success": False,
                "error": f"Could not find coordinates for location '{location}'. Please verify the city name.",
                "data": None
            }
        latitude = geo_info["latitude"]
        longitude = geo_info["longitude"]
        city_name = geo_info["name"]
        country_name = geo_info["country"]

    forecast_url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current_weather": "true"
    }

    try:
        response = requests.get(forecast_url, params=params, timeout=10)
        logger.debug(f"Open-Meteo API raw response: {response.text}")

        if response.status_code != 200:
            return {
                "success": False,
                "error": f"Open-Meteo API returned status code {response.status_code}.",
                "data": None
            }

        data = response.json()
        current = data.get("current_weather")
        if not current:
            return {
                "success": False,
                "error": "No current weather data in Open-Meteo response.",
                "data": None
            }

        temp_c = current.get("temperature")
        wind_speed = current.get("windspeed")
        wind_direction = current.get("winddirection")
        weather_code = current.get("weathercode", 0)
        condition_desc = WMO_WEATHER_CODES.get(weather_code, f"Code {weather_code}")
        time_obs = current.get("time")

        # Human-readable formatted string
        loc_display = f"{city_name}, {country_name}" if country_name else city_name
        formatted_summary = (
            f"Weather in {loc_display}: {condition_desc}, Temperature: {temp_c}°C, "
            f"Wind: {wind_speed} km/h (Direction: {wind_direction}°)."
        )

        return {
            "success": True,
            "location": loc_display,
            "latitude": latitude,
            "longitude": longitude,
            "temperature_c": temp_c,
            "condition": condition_desc,
            "weather_code": weather_code,
            "windspeed_kmh": wind_speed,
            "wind_direction_deg": wind_direction,
            "time": time_obs,
            "formatted": formatted_summary,
            "error": None
        }

    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": "Open-Meteo API request timed out. Please try again.",
            "data": None
        }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"Network error fetching weather: {str(e)}",
            "data": None
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error in weather lookup: {str(e)}",
            "data": None
        }


# Tool specification for LLM tool calling
WEATHER_TOOL_DEFINITION = {
    "name": "get_weather",
    "description": "Fetches real-time weather information and temperature for any city, region, or coordinates using the Open-Meteo API. Use this tool whenever the user asks about current weather, temperature, or forecasts.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "location": {
                "type": "STRING",
                "description": "The city or location name, e.g., 'Mumbai', 'Delhi', 'New York', 'Tokyo', 'London'"
            }
        },
        "required": ["location"]
    }
}
