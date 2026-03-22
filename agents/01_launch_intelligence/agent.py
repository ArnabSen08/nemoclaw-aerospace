"""
Launch Intelligence Agent
-------------------------
Fetches real-time space data and generates a structured daily briefing
using the Nemotron model via NemoClaw's OpenClaw agent runtime.

Run inside NemoClaw sandbox:
  nemoclaw my-assistant connect
  python agent.py --nasa-key YOUR_KEY
"""
import argparse
import json
import os
from datetime import datetime, timezone
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
import fetcher

console = Console()

def format_launch(launch, rocket_cache={}):
    """Format a single launch record into a readable dict."""
    rocket_id = launch.get("rocket", "")
    if rocket_id and rocket_id not in rocket_cache:
        try:
            rocket_cache[rocket_id] = fetcher.get_rocket_info(rocket_id).get("name", rocket_id)
        except Exception:
            rocket_cache[rocket_id] = rocket_id

    date_unix = launch.get("date_unix")
    date_str = datetime.fromtimestamp(date_unix, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC") if date_unix else "TBD"

    return {
        "name": launch.get("name", "Unknown"),
        "date": date_str,
        "rocket": rocket_cache.get(rocket_id, rocket_id),
        "success": launch.get("success"),
        "details": (launch.get("details") or "No details available.")[:200],
        "webcast": launch.get("links", {}).get("webcast", "N/A"),
    }

def build_briefing_prompt(data: dict) -> str:
    """Build the prompt sent to the Nemotron agent."""
    return f"""You are an aerospace intelligence analyst. Based on the following real-time space data, 
generate a concise daily briefing report. Include:
1. Upcoming launch highlights and what to watch for
2. Recent launch outcomes summary
3. Current ISS status and crew
4. Space weather advisory (if any solar flares detected)
5. A "Mission of the Day" insight based on the APOD

Keep the tone professional but accessible. Use bullet points where helpful.

--- DATA ---
{json.dumps(data, indent=2)}
--- END DATA ---

Generate the briefing now:"""

def print_raw_data(data: dict):
    """Display raw fetched data in a rich table before agent processing."""
    console.print(Panel("[bold cyan]Launch Intelligence Agent[/bold cyan] — Live Data Feed", expand=False))

    # Upcoming launches table
    table = Table(title="Upcoming SpaceX Launches", show_lines=True)
    table.add_column("Mission", style="cyan")
    table.add_column("Date (UTC)")
    table.add_column("Rocket")
    table.add_column("Webcast")
    for l in data.get("upcoming_launches", []):
        table.add_row(l["name"], l["date"], l["rocket"], l.get("webcast", "N/A")[:40])
    console.print(table)

    # ISS
    iss = data.get("iss_location", {})
    pos = iss.get("iss_position", {})
    console.print(f"\n[bold]ISS Position:[/bold] Lat {pos.get('latitude', '?')} / Lon {pos.get('longitude', '?')}")

    # Crew
    crew = data.get("people_in_space", {})
    console.print(f"[bold]People in Space:[/bold] {crew.get('number', '?')} — " +
                  ", ".join(p["name"] for p in crew.get("people", [])))

    # Space weather
    flares = data.get("space_weather", [])
    console.print(f"[bold]Solar Flares (today):[/bold] {len(flares)} detected")

    # APOD
    apod = data.get("apod", {})
    console.print(f"[bold]APOD:[/bold] {apod.get('title', 'N/A')} — {apod.get('date', '')}")

def run_agent_via_openclaw(prompt: str):
    """
    Send the briefing prompt to the Nemotron agent via OpenClaw CLI.
    This runs inside the NemoClaw sandbox where openclaw is available.
    """
    import subprocess
    import tempfile

    # Write prompt to a temp file to avoid shell escaping issues
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, dir="/tmp") as f:
        f.write(prompt)
        tmp_path = f.name

    result = subprocess.run(
        ["openclaw", "agent", "--agent", "main", "--local",
         "-m", f"$(cat {tmp_path})", "--session-id", "launch-intel"],
        capture_output=True, text=True, timeout=120
    )
    return result.stdout or result.stderr

def main():
    parser = argparse.ArgumentParser(description="Launch Intelligence Agent")
    parser.add_argument("--nasa-key", default=os.getenv("NASA_API_KEY", "DEMO_KEY"),
                        help="NASA API key (get free at api.nasa.gov)")
    parser.add_argument("--no-agent", action="store_true",
                        help="Only fetch and display data, skip agent inference")
    args = parser.parse_args()

    console.print("\n[bold green]Fetching live aerospace data...[/bold green]\n")

    # Fetch all data
    upcoming = [format_launch(l) for l in fetcher.get_upcoming_launches(5)]
    past = [format_launch(l) for l in fetcher.get_past_launches(3)]
    iss = fetcher.get_iss_location()
    crew = fetcher.get_people_in_space()
    weather = fetcher.get_space_weather(args.nasa_key)
    apod = fetcher.get_apod(args.nasa_key)

    data = {
        "report_time": datetime.now(timezone.utc).isoformat(),
        "upcoming_launches": upcoming,
        "recent_launches": past,
        "iss_location": iss,
        "people_in_space": crew,
        "space_weather": weather,
        "apod": {
            "title": apod.get("title"),
            "date": apod.get("date"),
            "explanation": apod.get("explanation", "")[:500],
            "url": apod.get("url"),
        }
    }

    print_raw_data(data)

    if args.no_agent:
        console.print("\n[yellow]--no-agent flag set. Skipping Nemotron inference.[/yellow]")
        console.print("[dim]Run without --no-agent inside NemoClaw sandbox for AI briefing.[/dim]")
        return

    console.print("\n[bold green]Sending to Nemotron agent for briefing...[/bold green]\n")
    prompt = build_briefing_prompt(data)
    response = run_agent_via_openclaw(prompt)

    console.print(Panel(response, title="[bold cyan]AI Briefing — Nemotron[/bold cyan]", expand=True))

if __name__ == "__main__":
    main()
