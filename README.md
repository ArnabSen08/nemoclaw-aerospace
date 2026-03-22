# NemoClaw Aerospace Projects

Four sandboxed AI agent projects built on NVIDIA NemoClaw + Nemotron-120B.

## APIs Used (All Free)

| API | Auth | Used In |
|-----|------|---------|
| SpaceX API v4 `api.spacexdata.com/v4` | None | Project 1 |
| Open-Notify ISS `api.open-notify.org` | None | Project 1 |
| NASA APOD `api.nasa.gov/planetary/apod` | Free key (api.nasa.gov) | Project 1 |
| NASA DONKI `api.nasa.gov/DONKI` | Free key (api.nasa.gov) | Project 1 |
| CelesTrak TLE `celestrak.org/SOCRATES` | None | Project 2 |
| CelesTrak GP Data `celestrak.org/SPACEDATA` | None | Project 2 |
| NASA EONET `eonet.gsfc.nasa.gov/api/v3` | None | Project 3 |
| NASA GIBS WMS `gibs.earthdata.nasa.gov` | None | Project 3 |
| NASA Telemanom Dataset (GitHub) | None | Project 4 |
| NASA Open Data Portal `data.nasa.gov` | None | Project 4 |

## Get Your Free NASA API Key
Visit https://api.nasa.gov — takes 30 seconds, no credit card.
Use `DEMO_KEY` for testing (30 req/hour limit).

## Projects

1. **Launch Intelligence Agent** — Daily briefing on rocket launches, ISS, space weather
2. **Satellite Conjunction Analyst** — Orbital debris & collision risk analysis
3. **Geospatial Disaster Response Agent** — Real-time natural event monitoring from satellite data
4. **Flight Anomaly Detection Agent** — AI-powered spacecraft telemetry anomaly analysis

## Prerequisites
- NemoClaw installed (Windows: download from https://github.com/nvidia-nemoclaw/NemoClaw)
- NVIDIA API key from https://build.nvidia.com
- NASA API key from https://api.nasa.gov (or use DEMO_KEY)
- Python 3.10+

## Quick Start
```bash
# Install NemoClaw (Windows)
# Download .exe from https://github.com/nvidia-nemoclaw/NemoClaw/releases

# Onboard your first agent
nemoclaw onboard

# Then run any project
cd agents/01_launch_intelligence
pip install -r requirements.txt
python agent.py
```
