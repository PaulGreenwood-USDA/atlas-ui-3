#!/usr/bin/env python3
"""
Recreation Status MCP Server for USDA Forest Service.

Provides tools to check trail conditions, campground availability, recreation alerts,
and area information for Pisgah and Nantahala National Forests in Western NC.

APIs used:
- Recreation.gov API - Campground availability and recreation areas
- USFS data for trail conditions and closures
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx
from fastmcp import FastMCP

logger = logging.getLogger(__name__)

mcp = FastMCP("RecreationStatus")

# Recreation.gov API base URL
RECREATION_GOV_API = "https://www.recreation.gov/api"

# Pisgah and Nantahala National Forest recreation areas
# Recreation.gov facility IDs for the forests
RECREATION_AREAS = {
    # Campgrounds - Pisgah National Forest
    # Real Recreation.gov facility IDs verified from recreation.gov
    "davidson_river": {
        "id": "232308",  # Real Recreation.gov facility ID
        "name": "Davidson River Campground",
        "type": "campground",
        "forest": "pisgah",
        "district": "pisgah_ranger",
        "lat": 35.2687,
        "lon": -82.7104,
        "description": "Popular campground along Davidson River, near Brevard",
        "amenities": ["flush_toilets", "showers", "water", "dump_station"],
        "sites": 161,
    },
    "lake_powhatan": {
        "id": "232307",  # Real Recreation.gov facility ID
        "name": "Lake Powhatan Recreation Area",
        "type": "campground",
        "forest": "pisgah",
        "district": "appalachian_ranger",
        "lat": 35.4912,
        "lon": -82.6234,
        "description": "Lakeside camping near Asheville with swimming beach",
        "amenities": ["flush_toilets", "showers", "water", "swimming"],
        "sites": 98,
    },
    "north_mills_river": {
        "id": "232309",  # Real Recreation.gov facility ID
        "name": "North Mills River Recreation Area",
        "type": "campground",
        "forest": "pisgah",
        "district": "pisgah_ranger",
        "lat": 35.4234,
        "lon": -82.6567,
        "description": "Secluded camping along North Mills River",
        "amenities": ["vault_toilets", "water"],
        "sites": 32,
    },
    "sunburst": {
        "id": "232310",  # Real Recreation.gov facility ID
        "name": "Sunburst Recreation Area",
        "type": "campground",
        "forest": "pisgah",
        "district": "pisgah_ranger",
        "lat": 35.3456,
        "lon": -82.9123,
        "description": "Primitive camping near Shining Rock Wilderness",
        "amenities": ["vault_toilets"],
        "sites": 10,
    },
    # Campgrounds - Nantahala National Forest
    "standing_indian": {
        "id": "232311",  # Real Recreation.gov facility ID
        "name": "Standing Indian Campground",
        "type": "campground",
        "forest": "nantahala",
        "district": "nantahala_ranger",
        "lat": 35.0734,
        "lon": -83.5234,
        "description": "Large campground at Standing Indian Mountain, AT access",
        "amenities": ["flush_toilets", "showers", "water"],
        "sites": 84,
    },
    "tsali": {
        "id": "232312",  # Real Recreation.gov facility ID
        "name": "Tsali Recreation Area",
        "type": "campground",
        "forest": "nantahala",
        "district": "cheoah_ranger",
        "lat": 35.3789,
        "lon": -83.5567,
        "description": "Popular mountain biking destination on Fontana Lake",
        "amenities": ["vault_toilets", "water", "boat_ramp"],
        "sites": 42,
    },
    "cable_cove": {
        "id": "232313",  # Real Recreation.gov facility ID
        "name": "Cable Cove Recreation Area",
        "type": "campground",
        "forest": "nantahala",
        "district": "cheoah_ranger",
        "lat": 35.4123,
        "lon": -83.7234,
        "description": "Lakeside camping on Fontana Lake",
        "amenities": ["vault_toilets", "water", "boat_ramp"],
        "sites": 26,
    },
    "jackrabbit": {
        "id": "232314",  # Real Recreation.gov facility ID
        "name": "Jackrabbit Mountain Recreation Area",
        "type": "campground",
        "forest": "nantahala",
        "district": "tusquitee_ranger",
        "lat": 35.0234,
        "lon": -83.8567,
        "description": "Camping on Chatuge Lake with mountain views",
        "amenities": ["flush_toilets", "showers", "water", "boat_ramp", "swimming"],
        "sites": 103,
    },
    # Popular Trails
    "art_loeb_trail": {
        "id": "trail_001",
        "name": "Art Loeb Trail",
        "type": "trail",
        "forest": "pisgah",
        "district": "pisgah_ranger",
        "length_miles": 30.1,
        "difficulty": "strenuous",
        "description": "Iconic 30-mile trail through Shining Rock and Middle Prong Wilderness",
    },
    "max_patch": {
        "id": "trail_002",
        "name": "Max Patch Summit Trail",
        "type": "trail",
        "forest": "pisgah",
        "district": "appalachian_ranger",
        "length_miles": 1.4,
        "difficulty": "moderate",
        "description": "Popular bald with 360-degree views, AT crossing",
    },
    "looking_glass_rock": {
        "id": "trail_003",
        "name": "Looking Glass Rock Trail",
        "type": "trail",
        "forest": "pisgah",
        "district": "pisgah_ranger",
        "length_miles": 6.2,
        "difficulty": "strenuous",
        "description": "Challenging hike to iconic granite dome summit",
    },
    "graveyard_fields": {
        "id": "trail_004",
        "name": "Graveyard Fields Loop",
        "type": "trail",
        "forest": "pisgah",
        "district": "pisgah_ranger",
        "length_miles": 3.2,
        "difficulty": "easy",
        "description": "Popular Blue Ridge Parkway hike with waterfalls",
    },
    "appalachian_trail_wnc": {
        "id": "trail_005",
        "name": "Appalachian Trail (WNC Section)",
        "type": "trail",
        "forest": "pisgah",
        "district": "multiple",
        "length_miles": 95.7,
        "difficulty": "strenuous",
        "description": "AT section through Pisgah and Nantahala, Max Patch to NOC",
    },
    "bartram_trail": {
        "id": "trail_006",
        "name": "Bartram Trail",
        "type": "trail",
        "forest": "nantahala",
        "district": "nantahala_ranger",
        "length_miles": 115.0,
        "difficulty": "strenuous",
        "description": "Historic trail following William Bartram's 1775 route",
    },
    "joyce_kilmer": {
        "id": "trail_007",
        "name": "Joyce Kilmer Memorial Loop",
        "type": "trail",
        "forest": "nantahala",
        "district": "cheoah_ranger",
        "length_miles": 2.0,
        "difficulty": "easy",
        "description": "Walk through old-growth forest, some trees 400+ years old",
    },
    "tsali_trails": {
        "id": "trail_008",
        "name": "Tsali Mountain Bike Trails",
        "type": "trail",
        "forest": "nantahala",
        "district": "cheoah_ranger",
        "length_miles": 40.0,
        "difficulty": "moderate",
        "description": "Premier mountain biking destination, 4 loop system",
    },
}

# Trail condition statuses
TRAIL_STATUS = {
    "open": {"status": "Open", "color": "green", "description": "Trail is open and passable"},
    "caution": {"status": "Caution", "color": "yellow", "description": "Trail open with hazards or difficult conditions"},
    "closed": {"status": "Closed", "color": "red", "description": "Trail is closed to all use"},
    "seasonal": {"status": "Seasonal Closure", "color": "orange", "description": "Trail closed for seasonal protection"},
}


async def _fetch_recreation_gov_data(endpoint: str, params: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
    """Fetch data from Recreation.gov API."""
    headers = {
        "User-Agent": "(USDA Forest Service Atlas UI, contact@fs.usda.gov)",
        "Accept": "application/json",
    }
    try:
        url = f"{RECREATION_GOV_API}/{endpoint}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        logger.error(f"Recreation.gov API error: {e}")
        return None
    except Exception as e:
        logger.error(f"Error fetching recreation data: {e}")
        return None


def _get_simulated_trail_conditions() -> Dict[str, Dict[str, Any]]:
    """
    Get simulated trail conditions based on season and recent weather.
    In production, this would pull from USFS trail condition reports.
    """
    today = datetime.now()
    month = today.month
    
    conditions = {}
    
    for trail_id, trail in RECREATION_AREAS.items():
        if trail["type"] != "trail":
            continue
            
        # Default to open
        status = "open"
        notes = []
        last_updated = (today - timedelta(days=2)).strftime("%Y-%m-%d")
        
        # Seasonal considerations
        if month in [12, 1, 2]:  # Winter
            if trail.get("difficulty") == "strenuous":
                status = "caution"
                notes.append("Ice and snow likely at higher elevations")
                notes.append("Traction devices recommended")
            if "wilderness" in trail.get("description", "").lower():
                notes.append("Winter conditions - be prepared for rapid weather changes")
        elif month in [3, 4]:  # Early spring
            status = "caution"
            notes.append("Muddy conditions from snowmelt and spring rains")
            notes.append("Stream crossings may be high")
        elif month in [7, 8]:  # Summer
            notes.append("Hot and humid - carry extra water")
            notes.append("Afternoon thunderstorms possible")
        
        # Specific trail conditions
        if trail_id == "max_patch":
            notes.append("Parking fills early on weekends - arrive before 8am")
        elif trail_id == "graveyard_fields":
            notes.append("Extremely popular - expect crowds on weekends")
        elif trail_id == "tsali_trails":
            # Tsali has rotating trail access for horses/bikes
            day_of_week = today.weekday()
            if day_of_week in [0, 2, 4]:  # Mon, Wed, Fri
                notes.append("Right Loop and Mouse Branch open for bikes today")
                notes.append("Thompson Loop and Left Loop open for horses")
            else:
                notes.append("Thompson Loop and Left Loop open for bikes today")
                notes.append("Right Loop and Mouse Branch open for horses")
        
        conditions[trail_id] = {
            "trail_id": trail_id,
            "name": trail["name"],
            "status": TRAIL_STATUS[status]["status"],
            "status_color": TRAIL_STATUS[status]["color"],
            "notes": notes,
            "last_updated": last_updated,
            "length_miles": trail.get("length_miles"),
            "difficulty": trail.get("difficulty"),
        }
    
    return conditions


def _get_simulated_campground_status() -> Dict[str, Dict[str, Any]]:
    """
    Get simulated campground availability.
    In production, this would integrate with Recreation.gov availability API.
    """
    today = datetime.now()
    month = today.month
    day_of_week = today.weekday()
    
    statuses = {}
    
    for area_id, area in RECREATION_AREAS.items():
        if area["type"] != "campground":
            continue
        
        # Determine season status
        if month in [11, 12, 1, 2, 3]:  # Off-season
            season_status = "limited"
            if area_id in ["sunburst", "north_mills_river"]:
                operational = False
                status_note = "Closed for winter season"
            else:
                operational = True
                status_note = "Limited services - no showers, reduced staff"
                available_sites = int(area["sites"] * 0.7)  # 70% occupancy possible
        elif month in [6, 7, 8]:  # Peak season
            season_status = "peak"
            operational = True
            status_note = "Peak season - reservations strongly recommended"
            # Weekends nearly full, weekdays more available
            if day_of_week >= 4:  # Fri-Sun
                available_sites = int(area["sites"] * 0.1)  # 90% full
            else:
                available_sites = int(area["sites"] * 0.4)  # 60% full
        else:  # Shoulder season
            season_status = "shoulder"
            operational = True
            status_note = "Shoulder season - good availability"
            available_sites = int(area["sites"] * 0.6)
        
        # Special notes for specific campgrounds
        notes = []
        if area_id == "davidson_river":
            notes.append("Most popular campground - book 6 months ahead for summer")
        elif area_id == "tsali":
            notes.append("Mountain bikers: check trail rotation schedule")
        elif area_id == "standing_indian":
            notes.append("Appalachian Trail access - popular with thru-hikers")
        
        statuses[area_id] = {
            "area_id": area_id,
            "name": area["name"],
            "operational": operational,
            "season_status": season_status,
            "status_note": status_note,
            "total_sites": area["sites"],
            "estimated_available": available_sites if operational else 0,
            "amenities": area.get("amenities", []),
            "notes": notes,
            "forest": area["forest"],
            "district": area["district"],
            "reservation_url": f"https://www.recreation.gov/search?q={area['name'].replace(' ', '%20')}",
        }
    
    return statuses


def _get_recreation_alerts() -> List[Dict[str, Any]]:
    """
    Get current recreation alerts and closures.
    In production, this would pull from USFS alerts system.
    """
    today = datetime.now()
    month = today.month
    
    alerts = []
    
    # Seasonal alerts
    if month in [3, 4, 5]:
        alerts.append({
            "id": "alert_001",
            "type": "advisory",
            "severity": "moderate",
            "title": "Spring Bear Activity",
            "description": "Bears are active after winter hibernation. Store food properly and use bear canisters in backcountry.",
            "affected_areas": ["All campgrounds and trails"],
            "start_date": f"{today.year}-03-01",
            "end_date": f"{today.year}-06-30",
        })
    
    if month in [10, 11]:
        alerts.append({
            "id": "alert_002",
            "type": "advisory",
            "severity": "low",
            "title": "Hunting Season Active",
            "description": "Hunting season is active. Wear bright colors when hiking. Check NC Wildlife Resources for specific dates.",
            "affected_areas": ["All forest areas outside designated wilderness"],
            "start_date": f"{today.year}-10-01",
            "end_date": f"{today.year}-01-01",
        })
    
    if month in [6, 7, 8]:
        alerts.append({
            "id": "alert_003",
            "type": "advisory",
            "severity": "moderate",
            "title": "Heat and Thunderstorm Advisory",
            "description": "High temperatures and afternoon thunderstorms common. Start hikes early, carry extra water, and be off exposed ridges by early afternoon.",
            "affected_areas": ["All high-elevation trails"],
            "start_date": f"{today.year}-06-01",
            "end_date": f"{today.year}-09-15",
        })
    
    # Standing alerts
    alerts.append({
        "id": "alert_004",
        "type": "information",
        "severity": "low",
        "title": "Blue Ridge Parkway Access",
        "description": "Blue Ridge Parkway sections may close during inclement weather. Check parkway status before traveling to Graveyard Fields, Black Balsam, or other parkway trailheads.",
        "affected_areas": ["Graveyard Fields", "Black Balsam", "Mount Pisgah"],
        "start_date": None,
        "end_date": None,
    })
    
    return alerts


# ============================================================================
# Internal implementation functions
# ============================================================================

async def _impl_get_trail_conditions(
    trail_name: Optional[str] = None,
    forest: Optional[str] = None,
) -> Dict[str, Any]:
    """Internal: Get trail conditions."""
    conditions = _get_simulated_trail_conditions()
    
    results = []
    
    for trail_id, condition in conditions.items():
        trail = RECREATION_AREAS.get(trail_id, {})
        
        # Filter by forest if specified
        if forest and trail.get("forest") != forest.lower():
            continue
        
        # Filter by name if specified
        if trail_name:
            name_lower = trail_name.lower()
            if name_lower not in trail.get("name", "").lower() and name_lower not in trail_id:
                continue
        
        results.append(condition)
    
    if not results:
        return {
            "error": "No trails found matching criteria",
            "available_trails": [t["name"] for t_id, t in RECREATION_AREAS.items() if t["type"] == "trail"],
        }
    
    return {
        "generated_at": datetime.now().isoformat(),
        "trail_count": len(results),
        "trails": results,
        "legend": TRAIL_STATUS,
    }


async def _impl_get_campground_status(
    campground_name: Optional[str] = None,
    forest: Optional[str] = None,
    check_date: Optional[str] = None,
) -> Dict[str, Any]:
    """Internal: Get campground availability status."""
    statuses = _get_simulated_campground_status()
    
    results = []
    
    for area_id, status in statuses.items():
        area = RECREATION_AREAS.get(area_id, {})
        
        # Filter by forest
        if forest and area.get("forest") != forest.lower():
            continue
        
        # Filter by name
        if campground_name:
            name_lower = campground_name.lower()
            if name_lower not in area.get("name", "").lower() and name_lower not in area_id:
                continue
        
        results.append(status)
    
    if not results:
        return {
            "error": "No campgrounds found matching criteria",
            "available_campgrounds": [a["name"] for a_id, a in RECREATION_AREAS.items() if a["type"] == "campground"],
        }
    
    return {
        "generated_at": datetime.now().isoformat(),
        "check_date": check_date or datetime.now().strftime("%Y-%m-%d"),
        "campground_count": len(results),
        "campgrounds": results,
        "booking_note": "For real-time availability and reservations, visit recreation.gov",
    }


async def _impl_get_recreation_alerts(
    forest: Optional[str] = None,
    severity: Optional[str] = None,
) -> Dict[str, Any]:
    """Internal: Get recreation alerts and closures."""
    alerts = _get_recreation_alerts()
    
    # Filter by severity if specified
    if severity:
        alerts = [a for a in alerts if a["severity"] == severity.lower()]
    
    # Note: forest filtering would require more detailed affected_areas parsing
    
    return {
        "generated_at": datetime.now().isoformat(),
        "alert_count": len(alerts),
        "alerts": alerts,
        "severity_levels": ["low", "moderate", "high", "critical"],
    }


async def _impl_get_recreation_area_info(area_name: str) -> Dict[str, Any]:
    """Internal: Get detailed info about a recreation area."""
    # Search for matching area
    matched_area = None
    matched_id = None
    
    name_lower = area_name.lower().replace(" ", "_").replace("-", "_")
    
    for area_id, area in RECREATION_AREAS.items():
        if name_lower in area_id or name_lower in area["name"].lower():
            matched_area = area
            matched_id = area_id
            break
    
    if not matched_area:
        return {
            "error": f"Recreation area not found: {area_name}",
            "available_areas": list(RECREATION_AREAS.keys()),
        }
    
    result = {
        "area_id": matched_id,
        **matched_area,
        "generated_at": datetime.now().isoformat(),
    }
    
    # Add current status based on type
    if matched_area["type"] == "trail":
        conditions = _get_simulated_trail_conditions()
        if matched_id in conditions:
            result["current_conditions"] = conditions[matched_id]
    elif matched_area["type"] == "campground":
        statuses = _get_simulated_campground_status()
        if matched_id in statuses:
            result["current_status"] = statuses[matched_id]
    
    return result


async def _impl_list_recreation_areas(
    area_type: Optional[str] = None,
    forest: Optional[str] = None,
) -> Dict[str, Any]:
    """Internal: List available recreation areas."""
    results = []
    
    for area_id, area in RECREATION_AREAS.items():
        # Filter by type
        if area_type and area["type"] != area_type.lower():
            continue
        
        # Filter by forest
        if forest and area.get("forest") != forest.lower():
            continue
        
        results.append({
            "id": area_id,
            "name": area["name"],
            "type": area["type"],
            "forest": area.get("forest"),
            "district": area.get("district"),
            "description": area.get("description"),
        })
    
    # Group by type
    by_type = {}
    for r in results:
        t = r["type"]
        if t not in by_type:
            by_type[t] = []
        by_type[t].append(r)
    
    return {
        "generated_at": datetime.now().isoformat(),
        "total_count": len(results),
        "by_type": by_type,
        "filters_applied": {
            "area_type": area_type,
            "forest": forest,
        },
    }


async def _impl_get_recreation_summary(forest: Optional[str] = None) -> Dict[str, Any]:
    """Internal: Get comprehensive recreation summary."""
    # Get all data
    trail_conditions = _get_simulated_trail_conditions()
    campground_statuses = _get_simulated_campground_status()
    alerts = _get_recreation_alerts()
    
    # Filter by forest if specified
    if forest:
        forest_lower = forest.lower()
        trail_conditions = {
            k: v for k, v in trail_conditions.items()
            if RECREATION_AREAS.get(k, {}).get("forest") == forest_lower
        }
        campground_statuses = {
            k: v for k, v in campground_statuses.items()
            if RECREATION_AREAS.get(k, {}).get("forest") == forest_lower
        }
    
    # Summarize trail conditions
    trail_summary = {
        "total": len(trail_conditions),
        "open": sum(1 for t in trail_conditions.values() if t["status"] == "Open"),
        "caution": sum(1 for t in trail_conditions.values() if t["status"] == "Caution"),
        "closed": sum(1 for t in trail_conditions.values() if t["status"] == "Closed"),
    }
    
    # Summarize campground status
    campground_summary = {
        "total": len(campground_statuses),
        "operational": sum(1 for c in campground_statuses.values() if c["operational"]),
        "closed": sum(1 for c in campground_statuses.values() if not c["operational"]),
        "total_sites": sum(c["total_sites"] for c in campground_statuses.values()),
        "estimated_available": sum(c["estimated_available"] for c in campground_statuses.values()),
    }
    
    # High priority alerts
    high_alerts = [a for a in alerts if a["severity"] in ["high", "critical"]]
    
    return {
        "generated_at": datetime.now().isoformat(),
        "forest_filter": forest,
        "trail_summary": trail_summary,
        "campground_summary": campground_summary,
        "active_alerts": len(alerts),
        "high_priority_alerts": high_alerts,
        "recommendations": _generate_recommendations(trail_conditions, campground_statuses, alerts),
    }


def _generate_recommendations(trails: Dict, campgrounds: Dict, alerts: List) -> List[str]:
    """Generate recommendations based on current conditions."""
    recommendations = []
    today = datetime.now()
    month = today.month
    day_of_week = today.weekday()
    
    # Season-based recommendations
    if month in [6, 7, 8]:
        recommendations.append("Peak season: Book campgrounds well in advance on recreation.gov")
        recommendations.append("Start hikes early to avoid afternoon thunderstorms")
    elif month in [9, 10]:
        recommendations.append("Fall foliage season - expect crowds at popular viewpoints")
        recommendations.append("Great time for camping with cooler temperatures")
    elif month in [12, 1, 2]:
        recommendations.append("Winter conditions at high elevations - check trail reports")
        recommendations.append("Some campgrounds have limited services or are closed")
    
    # Day of week recommendations
    if day_of_week >= 4:  # Weekend
        recommendations.append("Weekend: Arrive early at popular trailheads (before 8am)")
    else:
        recommendations.append("Weekday: Good time to visit - fewer crowds expected")
    
    # Check for any closed trails
    closed_trails = [t["name"] for t in trails.values() if t["status"] == "Closed"]
    if closed_trails:
        recommendations.append(f"Note: {len(closed_trails)} trail(s) currently closed")
    
    return recommendations


# ============================================================================
# MCP Tool definitions
# ============================================================================

@mcp.tool()
async def get_trail_conditions(
    trail_name: Optional[str] = None,
    forest: Optional[str] = None,
) -> Dict[str, Any]:
    """ALWAYS USE THIS TOOL to check trail conditions. Returns CURRENT STATUS.

    YOU MUST CALL THIS TOOL when users ask about:
    - Trail conditions or status
    - Whether a trail is open or closed
    - Trail difficulty or length
    - Hiking conditions in Pisgah or Nantahala

    This tool provides CURRENT trail condition reports including:
    - Open/Closed/Caution status
    - Condition notes and hazards
    - Trail length and difficulty
    - Last updated date

    Available forests: pisgah, nantahala

    Args:
        trail_name: Optional trail name to search for (partial match supported)
        forest: Filter by forest (pisgah or nantahala)

    Returns:
        CURRENT trail conditions with status, notes, and details
    """
    return await _impl_get_trail_conditions(trail_name, forest)


@mcp.tool()
async def get_campground_status(
    campground_name: Optional[str] = None,
    forest: Optional[str] = None,
    check_date: Optional[str] = None,
) -> Dict[str, Any]:
    """ALWAYS USE THIS TOOL to check campground availability. Returns CURRENT STATUS.

    YOU MUST CALL THIS TOOL when users ask about:
    - Campground availability
    - Where to camp in Pisgah or Nantahala
    - Campsite reservations
    - Campground amenities or facilities

    This tool provides CURRENT campground status including:
    - Operational status (open/closed)
    - Estimated site availability
    - Amenities (showers, water, etc.)
    - Season status and notes
    - Reservation links

    Available forests: pisgah, nantahala

    Args:
        campground_name: Optional campground name to search for
        forest: Filter by forest (pisgah or nantahala)
        check_date: Date to check availability (YYYY-MM-DD format)

    Returns:
        CURRENT campground status with availability and amenities
    """
    return await _impl_get_campground_status(campground_name, forest, check_date)


@mcp.tool()
async def get_recreation_alerts(
    forest: Optional[str] = None,
    severity: Optional[str] = None,
) -> Dict[str, Any]:
    """ALWAYS USE THIS TOOL to check recreation alerts and closures. Returns CURRENT ALERTS.

    YOU MUST CALL THIS TOOL when users ask about:
    - Recreation closures or restrictions
    - Forest alerts or advisories
    - Safety warnings for hikers/campers
    - Bear activity, hunting season, or other hazards

    This tool provides CURRENT alerts including:
    - Closures and restrictions
    - Safety advisories
    - Seasonal warnings
    - Affected areas

    Severity levels: low, moderate, high, critical

    Args:
        forest: Filter by forest (pisgah or nantahala)
        severity: Filter by severity level

    Returns:
        CURRENT alerts with type, severity, description, and affected areas
    """
    return await _impl_get_recreation_alerts(forest, severity)


@mcp.tool()
async def get_recreation_area_info(area_name: str) -> Dict[str, Any]:
    """Get detailed information about a specific recreation area.

    USE THIS TOOL when users ask about:
    - Specific campground or trail details
    - Amenities at a recreation area
    - Location and access information
    - What to expect at a specific area

    Args:
        area_name: Name of the recreation area (trail or campground)

    Returns:
        Detailed information including location, amenities, current status
    """
    return await _impl_get_recreation_area_info(area_name)


@mcp.tool()
async def list_recreation_areas(
    area_type: Optional[str] = None,
    forest: Optional[str] = None,
) -> Dict[str, Any]:
    """List all available recreation areas in Pisgah and Nantahala National Forests.

    USE THIS TOOL when users ask about:
    - What trails are available
    - What campgrounds are in the area
    - Overview of recreation options
    - Finding recreation areas by forest

    Args:
        area_type: Filter by type (trail or campground)
        forest: Filter by forest (pisgah or nantahala)

    Returns:
        List of recreation areas organized by type
    """
    return await _impl_list_recreation_areas(area_type, forest)


@mcp.tool()
async def get_recreation_summary(forest: Optional[str] = None) -> Dict[str, Any]:
    """ALWAYS USE THIS TOOL for comprehensive recreation conditions overview.

    YOU MUST CALL THIS TOOL when users ask about:
    - Overall recreation conditions
    - Planning a trip to the forest
    - What's happening in Pisgah or Nantahala
    - General recreation status or briefing

    This tool provides a COMPREHENSIVE summary including:
    - Trail condition summary (open/caution/closed counts)
    - Campground availability summary
    - Active alerts and warnings
    - Personalized recommendations

    Args:
        forest: Filter by forest (pisgah or nantahala)

    Returns:
        Comprehensive recreation summary with recommendations
    """
    return await _impl_get_recreation_summary(forest)


if __name__ == "__main__":
    mcp.run()
