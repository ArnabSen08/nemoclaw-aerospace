"""Data fetchers for Launch Intelligence Agent."""
import requests
from datetime import datetime, timezone

SPACEX_BASE = "https://api.spacexdata.com/v4"
ISS_BASE = "https://api.open-notify.org"
NASA_BASE = "https://api.nasa.gov"

def get_upcoming_launches(limit=5):
    """Fetch upcoming SpaceX launches."""
    resp = requests.get(f"{SPACEX_BASE}/launches/upcoming", timeout=10)
    resp.raise_for_status()
    launches = resp.json()
    # Sort by date_unix, filter out None dates
    launches = [l for l in launches if l.get("date_unix")]
    launches.sort(key=lambda x: x["date_unix"])
    return launches[:limit]

def get_past_launches(limit=3):
    """Fetch most recent past SpaceX launches."""
    resp = requests.get(f"{SPACEX_BASE}/launches/past", timeout=10)
    resp.raise_for_status()
    launches = resp.json()
    launches = [l for l in launches if l.get("date_unix")]
    launches.sort(key=lambda x: x["date_unix"], reverse=True)
    return launches[:limit]

def get_iss_location():
    """Fetch current ISS position."""
    resp = requests.get(f"{ISS_BASE}/iss-now.json", timeout=10)
    resp.raise_for_status()
    return resp.json()

def get_people_in_space():
    """Fetch current crew in space."""
    resp = requests.get(f"{ISS_BASE}/astros.json", timeout=10)
    resp.raise_for_status()
    return resp.json()

def get_space_weather(nasa_key="DEMO_KEY"):
    """Fetch solar flare events from NASA DONKI (last 7 days)."""
    today = datetime.now(timezone.utc)
    start = today.strftime("%Y-%m-%d")
    url = f"{NASA_BASE}/DONKI/FLR?startDate={start}&api_key={nasa_key}"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    return resp.json()

def get_apod(nasa_key="DEMO_KEY"):
    """Fetch NASA Astronomy Picture of the Day."""
    url = f"{NASA_BASE}/planetary/apod?api_key={nasa_key}"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    return resp.json()

def get_rocket_info(rocket_id):
    """Fetch rocket details by ID."""
    resp = requests.get(f"{SPACEX_BASE}/rockets/{rocket_id}", timeout=10)
    resp.raise_for_status()
    return resp.json()
