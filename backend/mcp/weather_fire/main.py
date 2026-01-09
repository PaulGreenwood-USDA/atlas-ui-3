#!/usr/bin/env python3
"""
Weather & Fire Conditions MCP Server for USDA Forest Service.

Provides tools to fetch weather forecasts, fire weather alerts, fire danger ratings,
and active wildfire incidents. Designed for the Southern Region (R8) with focus on
Western North Carolina (Pisgah and Nantahala National Forests).

APIs used:
- National Weather Service (NWS) API - Free, no API key required
- InciWeb/NIFC GeoMAC - Active fire incidents
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional
from dataclasses import dataclass

import httpx
from fastmcp import FastMCP

logger = logging.getLogger(__name__)

mcp = FastMCP("WeatherFire")

# Common locations for the Forest Service Supervisor Office in Asheville
PRESET_LOCATIONS = {
    "asheville": {"lat": 35.5951, "lon": -82.5515, "name": "Asheville, NC (Supervisor Office)"},
    "pisgah_ranger": {"lat": 35.2687, "lon": -82.7104, "name": "Pisgah Ranger District"},
    "pisgah": {"lat": 35.2687, "lon": -82.7104, "name": "Pisgah National Forest"},
    "grandfather_ranger": {"lat": 36.0998, "lon": -81.8288, "name": "Grandfather Ranger District"},
    "appalachian_ranger": {"lat": 35.7796, "lon": -82.5702, "name": "Appalachian Ranger District"},
    "nantahala_ranger": {"lat": 35.1873, "lon": -83.5594, "name": "Nantahala Ranger District"},
    "nantahala": {"lat": 35.1873, "lon": -83.5594, "name": "Nantahala National Forest"},
    "cheoah_ranger": {"lat": 35.4506, "lon": -83.9278, "name": "Cheoah Ranger District"},
    "tusquitee_ranger": {"lat": 35.0607, "lon": -83.9023, "name": "Tusquitee Ranger District"},
    "highlands_ranger": {"lat": 35.0526, "lon": -83.1968, "name": "Highlands Ranger District"},
}

# Fire danger rating levels (NFDRS)
FIRE_DANGER_LEVELS = {
    1: {"level": "Low", "color": "Green", "description": "Fuels do not ignite readily. Fires starting are slow to spread."},
    2: {"level": "Moderate", "color": "Blue", "description": "Fires start easily and spread at a moderate rate."},
    3: {"level": "High", "color": "Yellow", "description": "Fires start easily and spread rapidly. Unattended campfires may escape."},
    4: {"level": "Very High", "color": "Orange", "description": "Fires start very easily and spread rapidly. Extreme caution advised."},
    5: {"level": "Extreme", "color": "Red", "description": "Fires start immediately and spread furiously. All activities restricted."},
}


@dataclass
class WeatherAlert:
    """Represents a weather alert from NWS."""
    event: str
    headline: str
    description: str
    severity: str
    urgency: str
    areas: str
    onset: Optional[str]
    expires: Optional[str]


async def _fetch_nws_data(url: str) -> Optional[Dict[str, Any]]:
    """Fetch data from NWS API with proper headers."""
    headers = {
        "User-Agent": "(USDA Forest Service Atlas UI, contact@fs.usda.gov)",
        "Accept": "application/geo+json",
    }
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        logger.error(f"NWS API error: {e}")
        return None
    except Exception as e:
        logger.error(f"Error fetching NWS data: {e}")
        return None


async def _get_nws_gridpoint(lat: float, lon: float) -> Optional[Dict[str, str]]:
    """Get NWS grid point info for coordinates."""
    url = f"https://api.weather.gov/points/{lat},{lon}"
    data = await _fetch_nws_data(url)
    if data and "properties" in data:
        props = data["properties"]
        return {
            "forecast_url": props.get("forecast"),
            "forecast_hourly_url": props.get("forecastHourly"),
            "forecast_grid_url": props.get("forecastGridData"),
            "office": props.get("gridId"),
            "grid_x": props.get("gridX"),
            "grid_y": props.get("gridY"),
            "county": props.get("county"),
            "fire_weather_zone": props.get("fireWeatherZone"),
        }
    return None


def _resolve_location(location: str) -> Optional[Dict[str, Any]]:
    """Resolve a location string to coordinates."""
    location_lower = location.lower().replace(" ", "_").replace("-", "_")
    
    # Check preset locations
    if location_lower in PRESET_LOCATIONS:
        return PRESET_LOCATIONS[location_lower]
    
    # Check for partial matches
    for key, value in PRESET_LOCATIONS.items():
        if location_lower in key or key in location_lower:
            return value
    
    return None


# ============================================================================
# Internal implementation functions
# ============================================================================

async def _impl_get_weather_forecast(location: str = "asheville", detailed: bool = False) -> Dict[str, Any]:
    """Internal: Get weather forecast."""
    loc_data = _resolve_location(location)
    if loc_data:
        lat, lon = loc_data["lat"], loc_data["lon"]
        location_name = loc_data["name"]
    elif "," in location:
        try:
            lat, lon = map(float, location.split(","))
            location_name = f"Custom Location ({lat}, {lon})"
        except ValueError:
            return {"error": f"Invalid coordinates format. Use 'lat,lon' (e.g., '35.5951,-82.5515')"}
    else:
        return {"error": f"Unknown location: {location}", "available_locations": list(PRESET_LOCATIONS.keys())}

    grid_info = await _get_nws_gridpoint(lat, lon)
    if not grid_info:
        return {"error": "Could not retrieve NWS grid point. Check coordinates."}

    forecast_data = await _fetch_nws_data(grid_info["forecast_url"])
    if not forecast_data:
        return {"error": "Could not retrieve forecast data from NWS."}

    periods = forecast_data.get("properties", {}).get("periods", [])
    
    result = {
        "location": location_name,
        "coordinates": {"lat": lat, "lon": lon},
        "nws_office": grid_info["office"],
        "generated_at": datetime.now().isoformat(),
        "forecast_periods": [],
    }

    for period in periods[:7]:
        result["forecast_periods"].append({
            "name": period.get("name"),
            "temperature": period.get("temperature"),
            "temperature_unit": period.get("temperatureUnit"),
            "wind_speed": period.get("windSpeed"),
            "wind_direction": period.get("windDirection"),
            "short_forecast": period.get("shortForecast"),
            "detailed_forecast": period.get("detailedForecast") if detailed else None,
            "precipitation_probability": period.get("probabilityOfPrecipitation", {}).get("value"),
            "is_daytime": period.get("isDaytime"),
        })

    if detailed and grid_info.get("forecast_hourly_url"):
        hourly_data = await _fetch_nws_data(grid_info["forecast_hourly_url"])
        if hourly_data:
            hourly_periods = hourly_data.get("properties", {}).get("periods", [])[:24]
            result["hourly_forecast"] = [
                {
                    "time": p.get("startTime"),
                    "temperature": p.get("temperature"),
                    "wind_speed": p.get("windSpeed"),
                    "wind_direction": p.get("windDirection"),
                    "short_forecast": p.get("shortForecast"),
                    "precipitation_probability": p.get("probabilityOfPrecipitation", {}).get("value"),
                }
                for p in hourly_periods
            ]

    return result


async def _impl_get_fire_weather_alerts(state: str = "NC", include_all_hazards: bool = False) -> Dict[str, Any]:
    """Internal: Get fire weather alerts."""
    url = f"https://api.weather.gov/alerts/active?area={state.upper()}"
    data = await _fetch_nws_data(url)
    
    if not data:
        return {"error": f"Could not retrieve alerts for {state}"}

    features = data.get("features", [])
    
    fire_events = {"Red Flag Warning", "Fire Weather Watch", "Extreme Fire Danger", "Fire Warning"}
    related_events = {"Heat Advisory", "Excessive Heat Warning", "Wind Advisory", "High Wind Warning", "Dense Smoke Advisory"}

    alerts = []
    for feature in features:
        props = feature.get("properties", {})
        event = props.get("event", "")
        
        if not include_all_hazards:
            if event not in fire_events and event not in related_events:
                continue
        
        desc = props.get("description", "")
        alert = WeatherAlert(
            event=event,
            headline=props.get("headline", ""),
            description=desc[:500] + "..." if len(desc) > 500 else desc,
            severity=props.get("severity", ""),
            urgency=props.get("urgency", ""),
            areas=props.get("areaDesc", ""),
            onset=props.get("onset"),
            expires=props.get("expires"),
        )
        
        alerts.append({
            "event": alert.event,
            "headline": alert.headline,
            "severity": alert.severity,
            "urgency": alert.urgency,
            "areas_affected": alert.areas,
            "onset": alert.onset,
            "expires": alert.expires,
            "description": alert.description,
            "is_fire_related": event in fire_events,
        })

    severity_order = {"Extreme": 0, "Severe": 1, "Moderate": 2, "Minor": 3, "Unknown": 4}
    alerts.sort(key=lambda x: severity_order.get(x["severity"], 4))

    result = {
        "state": state.upper(),
        "generated_at": datetime.now().isoformat(),
        "total_alerts": len(alerts),
        "fire_alerts_count": sum(1 for a in alerts if a["is_fire_related"]),
        "alerts": alerts,
    }

    if not alerts:
        result["message"] = f"No active fire weather alerts for {state.upper()}"

    return result


async def _get_fires_from_nifc(state: str) -> Dict[str, Any]:
    """Fallback to NIFC data if ArcGIS is unavailable."""
    url = "https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/Current_WildlandFire_Locations/FeatureServer/0/query"
    
    params = {
        "where": f"POOState = '{state.upper()}'",
        "outFields": "IncidentName,POOState,POOCounty,DailyAcres,PercentContained,FireDiscoveryDateTime,IncidentTypeCategory",
        "returnGeometry": "false",
        "f": "json",
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
    except Exception as e:
        logger.error(f"NIFC fallback also failed: {e}")
        return {"state": state.upper(), "error": "Unable to retrieve fire data.", "fires": []}

    features = data.get("features", [])
    fires = []
    
    for feature in features:
        attrs = feature.get("attributes", {})
        fires.append({
            "name": attrs.get("IncidentName", "Unknown"),
            "state": attrs.get("POOState", state.upper()),
            "county": attrs.get("POOCounty", "Unknown"),
            "acres": attrs.get("DailyAcres"),
            "percent_contained": attrs.get("PercentContained"),
            "incident_type": attrs.get("IncidentTypeCategory", "Wildfire"),
        })

    return {
        "state": state.upper(),
        "generated_at": datetime.now().isoformat(),
        "total_active_fires": len(fires),
        "fires": fires,
        "source": "NIFC Wildland Fire Locations",
    }


async def _impl_get_active_fires(state: str = "NC", radius_miles: int = 100) -> Dict[str, Any]:
    """Internal: Get active fires."""
    url = "https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/Current_WildlandFire_Perimeters/FeatureServer/0/query"
    
    params = {
        "where": f"POOState = '{state.upper()}' OR poly_IncidentName LIKE '%{state.upper()}%'",
        "outFields": "*",
        "returnGeometry": "false",
        "f": "json",
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
    except Exception as e:
        logger.error(f"Error fetching fire data: {e}")
        return await _get_fires_from_nifc(state)

    features = data.get("features", [])
    
    fires = []
    for feature in features:
        attrs = feature.get("attributes", {})
        
        discovery_date = attrs.get("FireDiscoveryDateTime")
        days_burning = None
        if discovery_date:
            try:
                disc_dt = datetime.fromtimestamp(discovery_date / 1000)
                days_burning = (datetime.now() - disc_dt).days
            except Exception:
                pass

        fires.append({
            "name": attrs.get("poly_IncidentName") or attrs.get("IncidentName", "Unknown"),
            "state": attrs.get("POOState", state.upper()),
            "county": attrs.get("POOCounty", "Unknown"),
            "acres": attrs.get("GISAcres") or attrs.get("DailyAcres"),
            "percent_contained": attrs.get("PercentContained"),
            "incident_type": attrs.get("IncidentTypeCategory", "Wildfire"),
            "discovery_date": datetime.fromtimestamp(discovery_date / 1000).isoformat() if discovery_date else None,
            "days_burning": days_burning,
            "cause": attrs.get("FireCause"),
            "irwin_id": attrs.get("IRWINID"),
        })

    fires.sort(key=lambda x: x.get("acres") or 0, reverse=True)

    return {
        "state": state.upper(),
        "generated_at": datetime.now().isoformat(),
        "total_active_fires": len(fires),
        "fires": fires,
        "message": f"No active fires reported in {state.upper()}" if not fires else None,
    }


async def _impl_get_fire_danger_rating(location: str = "asheville") -> Dict[str, Any]:
    """Internal: Get fire danger rating."""
    loc_data = _resolve_location(location)
    if loc_data:
        lat, lon = loc_data["lat"], loc_data["lon"]
        location_name = loc_data["name"]
    elif "," in location:
        try:
            lat, lon = map(float, location.split(","))
            location_name = f"Custom Location ({lat}, {lon})"
        except ValueError:
            return {"error": "Invalid coordinates format"}
    else:
        return {"error": f"Unknown location: {location}"}

    grid_info = await _get_nws_gridpoint(lat, lon)
    if not grid_info:
        return {"error": "Could not retrieve grid point data"}

    grid_url = grid_info.get("forecast_grid_url")
    if not grid_url:
        return {"error": "Could not retrieve forecast grid URL"}

    grid_data = await _fetch_nws_data(grid_url)
    if not grid_data:
        return {"error": "Could not retrieve detailed forecast data"}

    props = grid_data.get("properties", {})
    
    def get_first_value(data_array):
        if data_array and "values" in data_array and data_array["values"]:
            return data_array["values"][0].get("value")
        return None

    temperature = get_first_value(props.get("temperature"))
    relative_humidity = get_first_value(props.get("relativeHumidity"))
    wind_speed = get_first_value(props.get("windSpeed"))
    precip_prob = get_first_value(props.get("probabilityOfPrecipitation"))

    temp_f = temperature
    if temperature is not None:
        temp_f = (temperature * 9/5) + 32

    danger_score = 0
    factors = []

    if temp_f is not None:
        if temp_f > 90:
            danger_score += 2
            factors.append(f"High temperature ({temp_f:.0f}F)")
        elif temp_f > 80:
            danger_score += 1
            factors.append(f"Warm temperature ({temp_f:.0f}F)")

    if relative_humidity is not None:
        if relative_humidity < 15:
            danger_score += 3
            factors.append(f"Very low humidity ({relative_humidity:.0f}%)")
        elif relative_humidity < 25:
            danger_score += 2
            factors.append(f"Low humidity ({relative_humidity:.0f}%)")
        elif relative_humidity < 35:
            danger_score += 1
            factors.append(f"Below-average humidity ({relative_humidity:.0f}%)")

    if wind_speed is not None:
        wind_mph = wind_speed * 0.621371
        if wind_mph > 25:
            danger_score += 2
            factors.append(f"High winds ({wind_mph:.0f} mph)")
        elif wind_mph > 15:
            danger_score += 1
            factors.append(f"Moderate winds ({wind_mph:.0f} mph)")

    if precip_prob is not None and precip_prob > 50:
        danger_score -= 1
        factors.append(f"Precipitation likely ({precip_prob:.0f}%)")

    if danger_score <= 1:
        level = 1
    elif danger_score <= 3:
        level = 2
    elif danger_score <= 5:
        level = 3
    elif danger_score <= 7:
        level = 4
    else:
        level = 5

    danger_info = FIRE_DANGER_LEVELS[level]

    return {
        "location": location_name,
        "coordinates": {"lat": lat, "lon": lon},
        "generated_at": datetime.now().isoformat(),
        "fire_danger": {
            "level": level,
            "rating": danger_info["level"],
            "color": danger_info["color"],
            "description": danger_info["description"],
        },
        "conditions": {
            "temperature_f": round(temp_f, 1) if temp_f else None,
            "relative_humidity_pct": round(relative_humidity, 1) if relative_humidity else None,
            "wind_speed_mph": round(wind_speed * 0.621371, 1) if wind_speed else None,
            "precipitation_probability_pct": precip_prob,
        },
        "contributing_factors": factors,
        "note": "This is an estimate based on NWS forecast data. For official fire danger ratings, consult your local Fire Management Officer.",
    }


async def _impl_get_forest_conditions_summary(include_all_districts: bool = False) -> Dict[str, Any]:
    """Internal: Get forest conditions summary."""
    summary = {
        "generated_at": datetime.now().isoformat(),
        "forest": "Pisgah and Nantahala National Forests",
        "supervisor_office": "Asheville, NC",
    }

    weather = await _impl_get_weather_forecast("asheville", detailed=False)
    if "error" not in weather:
        current_period = weather.get("forecast_periods", [{}])[0]
        summary["current_weather"] = {
            "location": weather.get("location"),
            "temperature": f"{current_period.get('temperature')}F",
            "conditions": current_period.get("short_forecast"),
            "wind": f"{current_period.get('wind_speed')} {current_period.get('wind_direction')}",
        }

    alerts = await _impl_get_fire_weather_alerts("NC", include_all_hazards=False)
    summary["fire_weather_alerts"] = {
        "total": alerts.get("total_alerts", 0),
        "fire_related": alerts.get("fire_alerts_count", 0),
        "alerts": alerts.get("alerts", [])[:3],
    }

    if include_all_districts:
        districts_danger = {}
        for district_key, district_info in PRESET_LOCATIONS.items():
            if "_ranger" in district_key:
                danger = await _impl_get_fire_danger_rating(district_key)
                if "error" not in danger:
                    districts_danger[district_info["name"]] = {
                        "rating": danger["fire_danger"]["rating"],
                        "level": danger["fire_danger"]["level"],
                        "color": danger["fire_danger"]["color"],
                    }
        summary["fire_danger_by_district"] = districts_danger
    else:
        danger = await _impl_get_fire_danger_rating("asheville")
        if "error" not in danger:
            summary["fire_danger"] = danger["fire_danger"]

    nc_fires = await _impl_get_active_fires("NC")
    summary["active_fires"] = {
        "north_carolina": {
            "count": nc_fires.get("total_active_fires", 0),
            "fires": nc_fires.get("fires", [])[:5],
        }
    }

    recommendations = []
    
    if alerts.get("fire_alerts_count", 0) > 0:
        recommendations.append("ALERT: Active fire weather alerts in effect. Review alerts for details.")
    
    fire_danger = summary.get("fire_danger", {})
    if fire_danger.get("level", 0) >= 4:
        recommendations.append("CAUTION: Very High to Extreme fire danger. Consider restricting fire activities.")
    elif fire_danger.get("level", 0) >= 3:
        recommendations.append("NOTE: High fire danger. Monitor conditions and ensure compliance with burn permits.")

    if nc_fires.get("total_active_fires", 0) > 0:
        recommendations.append(f"INFO: {nc_fires.get('total_active_fires')} active fire(s) in North Carolina.")

    summary["recommendations"] = recommendations if recommendations else ["Conditions are favorable for normal operations."]

    return summary


# ============================================================================
# MCP Tool Definitions - MUST USE THESE FOR REAL-TIME DATA
# ============================================================================

@mcp.tool
async def get_weather_forecast(location: str = "asheville", detailed: bool = False) -> Dict[str, Any]:
    """
    ALWAYS USE THIS TOOL to get current weather forecasts. Returns LIVE DATA from NWS.

    YOU MUST CALL THIS TOOL when users ask about:
    - Current weather conditions
    - Weather forecast for any location
    - Temperature, wind, precipitation predictions
    - Weather in Pisgah, Nantahala, Asheville, or NC mountains

    This tool fetches REAL-TIME data from the National Weather Service API.
    Do NOT answer weather questions from your training data - use this tool.

    Available locations: asheville, pisgah, pisgah_ranger, nantahala, nantahala_ranger,
    grandfather_ranger, appalachian_ranger, cheoah_ranger, tusquitee_ranger, highlands_ranger

    Args:
        location: Location name (e.g., "pisgah", "asheville") or "lat,lon" coordinates
        detailed: If True, include hourly forecast data

    Returns:
        LIVE weather data: temperature, wind, precipitation, forecast periods
    """
    return await _impl_get_weather_forecast(location, detailed)


@mcp.tool
async def get_fire_weather_alerts(state: str = "NC", include_all_hazards: bool = False) -> Dict[str, Any]:
    """
    ALWAYS USE THIS TOOL to check for fire weather alerts. Returns LIVE DATA from NWS.

    YOU MUST CALL THIS TOOL when users ask about:
    - Red Flag Warnings
    - Fire weather alerts or watches
    - Current fire-related weather hazards
    - Whether there are any fire warnings in effect

    This tool fetches REAL-TIME active alerts from the National Weather Service.
    Do NOT guess about alerts - use this tool to get current data.

    Args:
        state: Two-letter state code (default: NC)
        include_all_hazards: Include all weather hazards, not just fire-related

    Returns:
        LIVE alert data: Red Flag Warnings, Fire Weather Watches, Heat/Wind Advisories
    """
    return await _impl_get_fire_weather_alerts(state, include_all_hazards)


@mcp.tool
async def get_active_fires(state: str = "NC", radius_miles: int = 100) -> Dict[str, Any]:
    """
    ALWAYS USE THIS TOOL to check for active wildfires. Returns LIVE DATA from NIFC.

    YOU MUST CALL THIS TOOL when users ask about:
    - Active fires or wildfires
    - Current fire incidents
    - Fires burning in NC or nearby states
    - Fire containment status

    This tool fetches REAL-TIME wildfire data from the National Interagency Fire Center.
    Do NOT make up fire information - use this tool.

    Args:
        state: Two-letter state code (default: NC)
        radius_miles: Search radius (for future use)

    Returns:
        LIVE fire data: fire names, acres burned, containment percentage, locations
    """
    return await _impl_get_active_fires(state, radius_miles)


@mcp.tool
async def get_fire_danger_rating(location: str = "asheville") -> Dict[str, Any]:
    """
    ALWAYS USE THIS TOOL to get fire danger ratings. Returns LIVE DATA calculated from NWS.

    YOU MUST CALL THIS TOOL when users ask about:
    - Fire danger level or rating
    - Is it safe to have a campfire?
    - Current fire risk
    - Fire danger for Pisgah, Nantahala, or any forest location

    This tool calculates REAL-TIME fire danger from live NWS weather data including
    temperature, humidity, wind speed, and precipitation probability.

    Fire Danger Levels: Low (Green), Moderate (Blue), High (Yellow), 
                        Very High (Orange), Extreme (Red)

    Available locations: pisgah, nantahala, asheville, pisgah_ranger, nantahala_ranger,
    grandfather_ranger, appalachian_ranger, cheoah_ranger, tusquitee_ranger, highlands_ranger

    Args:
        location: Location name (e.g., "pisgah", "nantahala") or "lat,lon" coordinates

    Returns:
        LIVE fire danger: rating level, color code, current conditions, contributing factors
    """
    return await _impl_get_fire_danger_rating(location)


@mcp.tool
async def get_forest_conditions_summary(include_all_districts: bool = False) -> Dict[str, Any]:
    """
    ALWAYS USE THIS TOOL for comprehensive forest conditions. Returns LIVE DATA.

    YOU MUST CALL THIS TOOL when users ask about:
    - Overall forest conditions
    - Morning briefing or situation report
    - Combined weather, fire danger, and alerts
    - General "what's happening" in the forest

    This tool provides a REAL-TIME comprehensive summary combining:
    - Current weather conditions
    - Active fire weather alerts
    - Fire danger ratings
    - Active wildfires in the region

    Ideal for morning briefings or situational awareness.

    Args:
        include_all_districts: If True, show fire danger for all 8 ranger districts

    Returns:
        LIVE comprehensive summary with weather, alerts, fire danger, and recommendations
    """
    return await _impl_get_forest_conditions_summary(include_all_districts)


@mcp.tool
def list_monitoring_locations() -> Dict[str, Any]:
    """
    List all available monitoring locations for Pisgah and Nantahala National Forests.

    Returns location IDs that can be used with other weather_fire tools:
    - pisgah / pisgah_ranger: Pisgah National Forest / Ranger District
    - nantahala / nantahala_ranger: Nantahala National Forest / Ranger District  
    - asheville: Supervisor Office
    - grandfather_ranger, appalachian_ranger, cheoah_ranger, tusquitee_ranger, highlands_ranger

    Returns:
        Dictionary of available locations with coordinates
    """
    locations = []
    for key, value in PRESET_LOCATIONS.items():
        locations.append({
            "id": key,
            "name": value["name"],
            "latitude": value["lat"],
            "longitude": value["lon"],
        })

    return {
        "forest": "Pisgah and Nantahala National Forests",
        "supervisor_office": "Asheville, NC",
        "locations": locations,
        "usage": "Use the 'id' field as the 'location' parameter in other tools",
    }


if __name__ == "__main__":
    mcp.run()
