"""
NASA EONET (Earth Observatory Natural Event Tracker) fetcher.
Completely free, no API key required.
Docs: https://eonet.gsfc.nasa.gov/docs/v3
"""
import requests
from datetime import datetime, timezone, timedelta

EONET_BASE = "https://eonet.gsfc.nasa.gov/api/v3"

# EONET category IDs
CATEGORIES = {
    "wildfires":    "wildfires",
    "floods":       "floods",
    "storms":       "severeStorms",
    "volcanoes":    "volcanoes",
    "earthquakes":  "earthquakes",
    "drought":      "drought",
    "landslides":   "landslides",
    "snow":         "snow",
    "all":          None,
}

RISK_WEIGHTS = {
    "wildfires": 3,
    "floods": 3,
    "severeStorms": 2,
    "volcanoes": 3,
    "earthquakes": 2,
    "drought": 1,
    "landslides": 2,
    "snow": 1,
}

def fetch_events(days=7, category=None, status="open", limit=50):
    """
    Fetch natural events from NASA EONET.
    
    Args:
        days: Look back this many days
        category: Filter by category slug (see CATEGORIES dict)
        status: 'open' (ongoing), 'closed' (ended), or 'all'
        limit: Max events to return
    """
    params = {
        "days": days,
        "status": status,
        "limit": limit,
    }
    if category and category != "all":
        params["category"] = CATEGORIES.get(category, category)

    resp = requests.get(f"{EONET_BASE}/events", params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    return data.get("events", [])

def fetch_categories():
    """Fetch all available EONET categories."""
    resp = requests.get(f"{EONET_BASE}/categories", timeout=10)
    resp.raise_for_status()
    return resp.json().get("categories", [])

def parse_event(event):
    """Extract key fields from an EONET event."""
    geometries = event.get("geometries", [])
    latest_geo = geometries[-1] if geometries else {}
    coords = latest_geo.get("coordinates", [])

    # Coordinates can be [lon, lat] or [[lon, lat], ...]
    if coords and isinstance(coords[0], list):
        lon, lat = coords[0][0], coords[0][1]
    elif len(coords) == 2:
        lon, lat = coords[0], coords[1]
    else:
        lon, lat = None, None

    categories = [c.get("id", "") for c in event.get("categories", [])]
    risk_score = sum(RISK_WEIGHTS.get(c, 1) for c in categories)

    return {
        "id": event.get("id"),
        "title": event.get("title"),
        "categories": categories,
        "status": "ongoing" if not event.get("closed") else "closed",
        "start_date": (event.get("geometries") or [{}])[0].get("date", "Unknown")[:10],
        "latest_date": latest_geo.get("date", "Unknown")[:10],
        "latitude": round(lat, 4) if lat is not None else None,
        "longitude": round(lon, 4) if lon is not None else None,
        "risk_score": risk_score,
        "sources": [s.get("url", "") for s in event.get("sources", [])][:2],
    }

def get_gibs_imagery_url(lat, lon, date, layer="MODIS_Terra_CorrectedReflectance_TrueColor"):
    """
    Generate a NASA GIBS WMS URL for satellite imagery at a given location.
    Free, no auth required.
    """
    # 1-degree bounding box around the event
    bbox = f"{lon-0.5},{lat-0.5},{lon+0.5},{lat+0.5}"
    return (
        f"https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi"
        f"?SERVICE=WMS&REQUEST=GetMap&VERSION=1.3.0"
        f"&LAYERS={layer}&CRS=EPSG:4326"
        f"&BBOX={bbox}&WIDTH=512&HEIGHT=512"
        f"&FORMAT=image/png&TIME={date}"
    )
