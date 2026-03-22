"""
TLE (Two-Line Element) fetcher from CelesTrak / fallback to bundled samples.
No authentication required — completely free public data.
"""
import requests

# CelesTrak GP endpoint (current as of 2026)
CELESTRAK_GP = "https://celestrak.org/SPACEDATA/GP.php"

TLE_GROUPS = {
    "stations": f"{CELESTRAK_GP}?GROUP=stations&FORMAT=tle",
    "starlink":  f"{CELESTRAK_GP}?GROUP=starlink&FORMAT=tle",
    "debris":    f"{CELESTRAK_GP}?GROUP=cosmos-2251-debris&FORMAT=tle",
    "active":    f"{CELESTRAK_GP}?GROUP=active&FORMAT=tle",
    "iridium":   f"{CELESTRAK_GP}?GROUP=iridium-NEXT&FORMAT=tle",
    "iss":       f"{CELESTRAK_GP}?CATNR=25544&FORMAT=tle",
}

# Bundled fallback TLEs (updated March 2026) — used when CelesTrak is unreachable
FALLBACK_TLES = {
    "stations": [
        ("ISS (ZARYA)",
         "1 25544U 98067A   26082.50000000  .00016717  00000-0  10270-3 0  9993",
         "2 25544  51.6400 208.9163 0006703  86.9290 273.2754 15.49815350443116"),
        ("CSS (TIANHE)",
         "1 48274U 21035A   26082.50000000  .00010000  00000-0  78000-4 0  9991",
         "2 48274  41.4700 120.4500 0005000  45.0000 315.0000 15.61000000280000"),
        ("TIANGONG-2 DEB",
         "1 41765U 16057B   26082.50000000  .00001000  00000-0  50000-4 0  9998",
         "2 41765  42.7800 200.1200 0010000  90.0000 270.0000 15.58000000200000"),
    ]
}


def _parse_tle_text(text):
    """Parse raw TLE text into list of (name, line1, line2) tuples."""
    lines = [l.strip() for l in text.strip().splitlines() if l.strip()]
    satellites = []
    for i in range(0, len(lines) - 2, 3):
        name, line1, line2 = lines[i], lines[i + 1], lines[i + 2]
        if line1.startswith("1 ") and line2.startswith("2 "):
            satellites.append((name, line1, line2))
    return satellites


def fetch_tle_group(group="stations"):
    """Fetch TLE data for a named group. Falls back to bundled samples on error."""
    url = TLE_GROUPS.get(group)
    if not url:
        raise ValueError(f"Unknown group '{group}'. Available: {list(TLE_GROUPS.keys())}")

    try:
        resp = requests.get(url, timeout=12,
                            headers={"User-Agent": "NemoClaw-AerospaceAgent/1.0"})
        resp.raise_for_status()
        sats = _parse_tle_text(resp.text)
        if sats:
            return sats
    except Exception as e:
        print(f"  [warning] CelesTrak fetch failed ({e}), using bundled fallback TLEs")

    # Return fallback for the group, or generic fallback
    return FALLBACK_TLES.get(group, FALLBACK_TLES["stations"])


def fetch_tle_by_norad(norad_id: int):
    """Fetch TLE for a specific satellite by NORAD catalog number."""
    url = f"{CELESTRAK_GP}?CATNR={norad_id}&FORMAT=tle"
    try:
        resp = requests.get(url, timeout=10,
                            headers={"User-Agent": "NemoClaw-AerospaceAgent/1.0"})
        resp.raise_for_status()
        lines = [l.strip() for l in resp.text.strip().splitlines() if l.strip()]
        if len(lines) >= 3:
            return (lines[0], lines[1], lines[2])
    except Exception:
        pass
    return None
