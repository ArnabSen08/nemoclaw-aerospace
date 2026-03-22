"""
Geospatial Disaster Response Agent
------------------------------------
Monitors NASA EONET for real-time natural events (wildfires, floods, storms,
volcanoes) and generates satellite-backed incident reports with response
recommendations using Nemotron.

APIs used:
  - NASA EONET v3 (free, no key): https://eonet.gsfc.nasa.gov/api/v3
  - NASA GIBS WMS (free, no key): https://gibs.earthdata.nasa.gov

Run inside NemoClaw sandbox:
  python agent.py --days 3 --category wildfires
"""
import argparse
import json
import subprocess
import tempfile
from datetime import datetime, timezone
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
import eonet_fetcher

console = Console()

RISK_LABELS = {3: "[red]HIGH[/red]", 2: "[yellow]MEDIUM[/yellow]", 1: "[green]LOW[/green]"}

def build_incident_prompt(events, category, days):
    return f"""You are a satellite-based disaster response coordinator. 
The following natural events are currently active or occurred in the last {days} days,
sourced from NASA's Earth Observatory Natural Event Tracker (EONET).

Category filter: {category}
Events analyzed: {len(events)}

Event data:
{json.dumps(events, indent=2)}

Generate a structured Incident Response Report including:

1. EXECUTIVE SUMMARY
   - Overall threat level (CRITICAL/HIGH/MEDIUM/LOW)
   - Number of active events by type
   - Geographic hotspots

2. TOP PRIORITY INCIDENTS (top 5 by risk)
   - Event name, location (lat/lon), status
   - Why it's high priority
   - Recommended immediate actions

3. RESPONSE RECOMMENDATIONS
   - Resource deployment suggestions
   - Monitoring frequency recommendations
   - Coordination agencies to notify

4. SATELLITE IMAGERY NOTE
   - Mention that NASA GIBS imagery URLs are included for visual verification

Keep the report actionable for emergency response teams."""

def main():
    parser = argparse.ArgumentParser(description="Geospatial Disaster Response Agent")
    parser.add_argument("--days", type=int, default=7,
                        help="Look back N days for events (default: 7)")
    parser.add_argument("--category", default="all",
                        choices=list(eonet_fetcher.CATEGORIES.keys()),
                        help="Event category to monitor (default: all)")
    parser.add_argument("--status", default="open",
                        choices=["open", "closed", "all"],
                        help="Event status filter (default: open/ongoing)")
    parser.add_argument("--no-agent", action="store_true",
                        help="Skip Nemotron inference")
    args = parser.parse_args()

    console.print(Panel(
        f"[bold cyan]Geospatial Disaster Response Agent[/bold cyan]\n"
        f"Category: [yellow]{args.category}[/yellow] | "
        f"Days: [yellow]{args.days}[/yellow] | "
        f"Status: [yellow]{args.status}[/yellow]",
        expand=False
    ))

    console.print("\n[bold green]Fetching events from NASA EONET...[/bold green]")
    raw_events = eonet_fetcher.fetch_events(
        days=args.days,
        category=args.category,
        status=args.status,
        limit=100
    )
    console.print(f"  Found [cyan]{len(raw_events)}[/cyan] events")

    events = [eonet_fetcher.parse_event(e) for e in raw_events]
    events.sort(key=lambda x: x["risk_score"], reverse=True)

    # Display table
    table = Table(title=f"Active Natural Events (last {args.days} days)", show_lines=True)
    table.add_column("Event", style="cyan", max_width=35)
    table.add_column("Category")
    table.add_column("Risk")
    table.add_column("Status")
    table.add_column("Location")
    table.add_column("Start Date")

    for e in events[:25]:
        risk = RISK_LABELS.get(e["risk_score"], "[white]LOW[/white]")
        loc = f"{e['latitude']}, {e['longitude']}" if e["latitude"] else "Unknown"
        table.add_row(
            e["title"][:35],
            ", ".join(e["categories"]),
            risk,
            e["status"],
            loc,
            e["start_date"]
        )

    console.print(table)

    # Add GIBS imagery URLs to top events
    for e in events[:5]:
        if e["latitude"] and e["longitude"]:
            e["satellite_imagery_url"] = eonet_fetcher.get_gibs_imagery_url(
                e["latitude"], e["longitude"], e["latest_date"]
            )

    # Summary stats
    by_category = {}
    for e in events:
        for cat in e["categories"]:
            by_category[cat] = by_category.get(cat, 0) + 1

    console.print(f"\n[bold]Event breakdown:[/bold] {json.dumps(by_category, indent=2)}")

    if args.no_agent:
        console.print("\n[yellow]--no-agent flag set. Skipping Nemotron inference.[/yellow]")
        return

    console.print("\n[bold green]Generating incident report via Nemotron...[/bold green]\n")
    prompt = build_incident_prompt(events[:15], args.category, args.days)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, dir="/tmp") as f:
        f.write(prompt)
        tmp_path = f.name

    result = subprocess.run(
        ["openclaw", "agent", "--agent", "main", "--local",
         "-m", f"$(cat {tmp_path})", "--session-id", "disaster-response"],
        capture_output=True, text=True, timeout=180
    )
    response = result.stdout or result.stderr
    console.print(Panel(response, title="[bold cyan]Incident Report — Nemotron[/bold cyan]"))

if __name__ == "__main__":
    main()
