"""
Master runner — test all 4 aerospace agents in --no-agent mode
(data fetch + analysis only, no NemoClaw sandbox required).

Usage:
  python run_all.py                    # run all with DEMO_KEY
  python run_all.py --nasa-key YOUR_KEY
"""
import argparse
import subprocess
import sys

def run(label, cmd):
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    result = subprocess.run(cmd, capture_output=False)
    return result.returncode

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--nasa-key", default="DEMO_KEY")
    args = parser.parse_args()

    py = sys.executable

    results = []
    results.append(run(
        "Project 1: Launch Intelligence Agent",
        [py, "agents/01_launch_intelligence/agent.py",
         "--nasa-key", args.nasa_key, "--no-agent"]
    ))
    results.append(run(
        "Project 2: Satellite Conjunction Analyst",
        [py, "agents/02_satellite_conjunction/agent.py",
         "--group", "stations", "--threshold", "100", "--no-agent"]
    ))
    results.append(run(
        "Project 3: Geospatial Disaster Response Agent",
        [py, "agents/03_geospatial_disaster/agent.py",
         "--days", "3", "--no-agent"]
    ))
    results.append(run(
        "Project 4: Flight Anomaly Detection Agent",
        [py, "agents/04_flight_anomaly/agent.py",
         "--channel", "P-1", "--no-agent"]
    ))

    print(f"\n{'='*60}")
    print(f"  All done. Exit codes: {results}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
