"""
Orbital propagation and conjunction analysis using SGP4.
Computes satellite positions and finds close approaches.
"""
import numpy as np
from datetime import datetime, timezone, timedelta
from sgp4.api import Satrec, jday

EARTH_RADIUS_KM = 6371.0

def propagate_satellite(name, line1, line2, dt: datetime):
    """Propagate a satellite to a given datetime. Returns (x, y, z) in km."""
    sat = Satrec.twoline2rv(line1, line2)
    jd, fr = jday(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second + dt.microsecond / 1e6)
    e, r, v = sat.sgp4(jd, fr)
    if e != 0:
        return None  # propagation error
    return np.array(r)  # ECI position in km

def distance_km(pos1, pos2):
    """Euclidean distance between two ECI position vectors."""
    return float(np.linalg.norm(pos1 - pos2))

def find_conjunctions(satellites, threshold_km=10.0, hours_ahead=24, step_minutes=5):
    """
    Scan forward in time and find pairs of satellites that come within
    threshold_km of each other.

    Returns list of conjunction events:
    {sat1, sat2, min_distance_km, time_utc}
    """
    now = datetime.now(timezone.utc)
    steps = int((hours_ahead * 60) / step_minutes)
    conjunctions = []

    # Pre-parse all satellites
    parsed = []
    for name, l1, l2 in satellites:
        try:
            sat = Satrec.twoline2rv(l1, l2)
            parsed.append((name, sat))
        except Exception:
            continue

    n = len(parsed)
    print(f"  Scanning {n} satellites over {hours_ahead}h ({steps} time steps)...")

    # Track minimum distances per pair to avoid duplicate events
    pair_min = {}

    for step in range(steps):
        t = now + timedelta(minutes=step * step_minutes)
        jd, fr = jday(t.year, t.month, t.day, t.hour, t.minute, t.second)

        positions = []
        for name, sat in parsed:
            e, r, _ = sat.sgp4(jd, fr)
            positions.append(np.array(r) if e == 0 else None)

        for i in range(n):
            if positions[i] is None:
                continue
            for j in range(i + 1, n):
                if positions[j] is None:
                    continue
                dist = distance_km(positions[i], positions[j])
                if dist < threshold_km:
                    key = (parsed[i][0], parsed[j][0])
                    if key not in pair_min or dist < pair_min[key]["min_distance_km"]:
                        pair_min[key] = {
                            "sat1": parsed[i][0],
                            "sat2": parsed[j][0],
                            "min_distance_km": round(dist, 3),
                            "time_utc": t.strftime("%Y-%m-%d %H:%M UTC"),
                        }

    conjunctions = list(pair_min.values())
    conjunctions.sort(key=lambda x: x["min_distance_km"])
    return conjunctions

def altitude_km(pos_eci):
    """Compute altitude above Earth's surface from ECI position."""
    return float(np.linalg.norm(pos_eci)) - EARTH_RADIUS_KM
