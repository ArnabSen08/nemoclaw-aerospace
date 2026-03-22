"""Data fetchers for Launch Intelligence Agent — with graceful fallbacks."""
import requests
from datetime import datetime, timezone

SPACEX_BASE = "https://api.spacexdata.com/v4"
ISS_BASE    = "https://api.open-notify.org"
NASA_BASE   = "https://api.nasa.gov"

# Fallback ISS APIs if open-notify is down
ISS_FALLBACKS = [
    "https://api.wheretheiss.at/v1/satellites/25544",
]

def _get(url, timeout=10):
    """GET with timeout; returns None on any error."""
    try:
        r = requests.get(url, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None

def get_upcoming_launches(limit=5):
    data = _get(f"{SPACEX_BASE}/launches/upcoming")
    if not data:
        return []
    data = [l for l in data if l.get("date_unix")]
    data.sort(key=lambda x: x["date_unix"])
    return data[:limit]

def get_past_launches(limit=3):
    data = _get(f"{SPACEX_BASE}/launches/past")
    if not data:
        return []
    data = [l for l in data if l.get("date_unix")]
    data.sort(key=lambda x: x["date_unix"], reverse=True)
    return data[:limit]

def get_iss_location():
    """Try open-notify first, fall back to wheretheiss.at."""
    data = _get(f"{ISS_BASE}/iss-now.json")
    if data:
        return data
    # Fallback: wheretheiss.at returns {latitude, longitude, ...}
    fb = _get(ISS_FALLBACKS[0])
    if fb:
        return {"iss_position": {"latitude": str(fb["latitude"]), "longitude": str(fb["longitude"])},
                "message": "success", "timestamp": fb.get("timestamp", 0)}
    return {"iss_position": {"latitude": "N/A", "longitude": "N/A"}, "message": "unavailable"}

def get_people_in_space():
    """Try open-notify; return placeholder if down."""
    data = _get(f"{ISS_BASE}/astros.json")
    if data:
        return data
    return {"number": 7, "people": [{"name": "Data unavailable — open-notify offline", "craft": "ISS"}],
            "message": "fallback"}

def get_space_weather(nasa_key="DEMO_KEY"):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    data = _get(f"{NASA_BASE}/DONKI/FLR?startDate={today}&api_key={nasa_key}")
    return data if data is not None else []

def get_apod(nasa_key="DEMO_KEY"):
    data = _get(f"{NASA_BASE}/planetary/apod?api_key={nasa_key}")
    return data if data else {"title": "Unavailable", "date": "", "explanation": "", "url": ""}

def get_rocket_info(rocket_id):
    data = _get(f"{SPACEX_BASE}/rockets/{rocket_id}")
    return data if data else {"name": rocket_id}
