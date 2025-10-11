"""Weather and marine tools using Open-Meteo API."""
import httpx
from typing import Dict, Optional
from ..config import settings

async def get_weather(lat: float, lon: float, days: int = 3) -> Dict:
    """
    Get weather forecast from Open-Meteo.
    
    Args:
        lat: Latitude
        lon: Longitude
        days: Number of forecast days (default 3)
    
    Returns:
        {
            "location": {"lat": float, "lon": float},
            "current": {"temp": float, "wind_speed": float, ...},
            "forecast": [{"date": str, "temp_max": float, "temp_min": float, ...}, ...]
        }
    """
    # CI stub
    if settings.ci:
        return {
            "location": {"lat": lat, "lon": lon},
            "current": {
                "temp": 22.5,
                "wind_speed": 15.0,
                "condition": "partly_cloudy"
            },
            "forecast": [
                {"date": "2025-10-12", "temp_max": 25, "temp_min": 18, "precip": 0.5},
                {"date": "2025-10-13", "temp_max": 24, "temp_min": 17, "precip": 1.2},
                {"date": "2025-10-14", "temp_max": 23, "temp_min": 16, "precip": 0.0}
            ]
        }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            params = {
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,wind_speed_10m,weather_code",
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max",
                "forecast_days": days,
                "timezone": "auto"
            }
            
            resp = await client.get("https://api.open-meteo.com/v1/forecast", params=params)
            
            if resp.status_code == 200:
                data = resp.json()
                
                # Parse current conditions
                current = {}
                if "current" in data:
                    current = {
                        "temp": data["current"].get("temperature_2m"),
                        "wind_speed": data["current"].get("wind_speed_10m"),
                        "weather_code": data["current"].get("weather_code")
                    }
                
                # Parse daily forecast
                forecast = []
                if "daily" in data:
                    daily = data["daily"]
                    for i in range(len(daily.get("time", []))):
                        forecast.append({
                            "date": daily["time"][i],
                            "temp_max": daily["temperature_2m_max"][i],
                            "temp_min": daily["temperature_2m_min"][i],
                            "precip": daily["precipitation_sum"][i],
                            "wind_max": daily["wind_speed_10m_max"][i]
                        })
                
                return {
                    "location": {"lat": lat, "lon": lon},
                    "current": current,
                    "forecast": forecast
                }
            else:
                return {"error": f"Weather API returned {resp.status_code}"}
    
    except Exception as e:
        return {"error": str(e)}

async def get_marine(lat: float, lon: float, days: int = 3) -> Dict:
    """
    Get marine forecast from Open-Meteo Marine API.
    
    Args:
        lat: Latitude
        lon: Longitude
        days: Number of forecast days (default 3)
    
    Returns:
        {
            "location": {"lat": float, "lon": float},
            "current": {"wave_height": float, "wave_direction": float, ...},
            "forecast": [{"date": str, "wave_height_max": float, ...}, ...]
        }
    """
    # CI stub
    if settings.ci:
        return {
            "location": {"lat": lat, "lon": lon},
            "current": {
                "wave_height": 1.2,
                "wave_direction": 90,
                "wave_period": 8
            },
            "forecast": [
                {"date": "2025-10-12", "wave_height_max": 1.5, "swell_height": 1.0},
                {"date": "2025-10-13", "wave_height_max": 1.8, "swell_height": 1.2},
                {"date": "2025-10-14", "wave_height_max": 1.3, "swell_height": 0.9}
            ]
        }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            params = {
                "latitude": lat,
                "longitude": lon,
                "current": "wave_height,wave_direction,wave_period",
                "daily": "wave_height_max,wave_direction_dominant,wave_period_max",
                "forecast_days": days,
                "timezone": "auto"
            }
            
            resp = await client.get("https://marine-api.open-meteo.com/v1/marine", params=params)
            
            if resp.status_code == 200:
                data = resp.json()
                
                # Parse current marine conditions
                current = {}
                if "current" in data:
                    current = {
                        "wave_height": data["current"].get("wave_height"),
                        "wave_direction": data["current"].get("wave_direction"),
                        "wave_period": data["current"].get("wave_period")
                    }
                
                # Parse daily marine forecast
                forecast = []
                if "daily" in data:
                    daily = data["daily"]
                    for i in range(len(daily.get("time", []))):
                        forecast.append({
                            "date": daily["time"][i],
                            "wave_height_max": daily["wave_height_max"][i],
                            "wave_direction": daily["wave_direction_dominant"][i],
                            "wave_period_max": daily["wave_period_max"][i]
                        })
                
                return {
                    "location": {"lat": lat, "lon": lon},
                    "current": current,
                    "forecast": forecast
                }
            else:
                return {"error": f"Marine API returned {resp.status_code}"}
    
    except Exception as e:
        return {"error": str(e)}

async def geocode(place: str) -> Optional[Dict]:
    """
    Simple geocoding using Open-Meteo geocoding API.
    
    Args:
        place: Place name (e.g., "Clarence River, NSW")
    
    Returns:
        {"lat": float, "lon": float, "name": str} or None
    """
    if settings.ci:
        return {"lat": -29.43, "lon": 153.03, "name": "Clarence River"}
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            params = {"name": place, "count": 1, "language": "en", "format": "json"}
            resp = await client.get("https://geocoding-api.open-meteo.com/v1/search", params=params)
            
            if resp.status_code == 200:
                data = resp.json()
                if data.get("results"):
                    result = data["results"][0]
                    return {
                        "lat": result["latitude"],
                        "lon": result["longitude"],
                        "name": result["name"]
                    }
        return None
    except Exception:
        return None

