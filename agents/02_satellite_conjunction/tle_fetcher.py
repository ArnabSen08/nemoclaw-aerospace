"""
TLE (Two-Line Element) fetcher from CelesTrak.
No authentication required — completely free public data.
"""
import requests

CELESTRAK_BASE = "https://celestrak.org/SOCRATES/query.php"
CELESTRAK_GP = "https://celestrak.org/SPACEDATA/GP.php"

# Curated groups available from CelesTrak (no auth)
TLE_GROUPS = {
    "stations":     "https://celestrak.org/SOCRATES/query.php?GROUP=stations&FORMAT=tle",
    "starlink":     "https://celestrak.org/SPACEDATA/GP.php?GROUP=starlink&FORMAT=tle",
    "debris":       "https://celestrak.org/SPACEDATA/GP.php?GROUP=cosmos-2251-debris&FORMAT=tle",
    "active":       "https://celestrak.org/SPACEDATA/GP.php?GROUP=active&FORMAT=tle",
    "iridium":      "https://celestrak.org/SPACEDATA/GP.php?GROUP=iridium&FORMAT=tle",
    "iss":          "https://celestrak.org/SPACEDATA/GP.php?CATNR=25544&FORMAT=tle",
}

def fetch_tle_group(group="stations"):
    """Fetch TLE data for a named group. Returns list of (name, line1, line2) tuples."""
    url = TLE_GROUPS.get(group)
    if not url:
        raise ValueError(f"Unknown group '{group}'. Available: {list(TLE_GROUPS.keys())}")

    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    lines = [l.strip() for l in resp.text.strip().splitlines() if l.strip()]

    satellites = []
    for i in range(0, len(lines) - 2, 3):
        name = lines[i]
        line1 = lines[i + 1]
        line2 = lines[i + 2]
        if line1.startswith("1 ") and line2.startswith("2 "):
            satellites.append((name, line1, line2))
    return satellites

def fetch_tle_by_norad(norad_id: int):
    """Fetch TLE for a specific satellite by NORAD catalog number."""
    url = f"https://celestrak.org/SPACEDATA/GP.php?CATNR={norad_id}&FORMAT=tle"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    lines = [l.strip() for l in resp.text.strip().splitlines() if l.strip()]
    if len(lines) >= 3:
        return (lines[0], lines[1], lines[2])
    return None
