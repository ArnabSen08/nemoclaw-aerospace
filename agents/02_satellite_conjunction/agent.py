"""
Satellite Conjunction & Debris Analyst
---------------------------------------
Fetches live TLE data from CelesTrak (free, no auth), propagates orbits
using SGP4, and identifies close approach events. Sends findings to
Nemotron for risk assessment and plain-English report.

Run inside NemoClaw sandbox:
  python agent.py --group stations --threshold 50
"""
import argparse
import json
import os
import subprocess
import tempfile
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
import tle_fetcher
import orbital_math

console = Console()

def build_analysis_prompt(conjunctions, group, threshold, satellite_count):
    return f"""You are an orbital safety analyst. The following conjunction analysis was performed on 
{satellite_count} satellites from the '{group}' group using live TLE data from CelesTrak.

Analysis parameters:
- Close approach threshold: {threshold} km
- Lookahead window: 24 hours
- Propagation model: SGP4

Conjunction events found (sorted by minimum distance):
{json.dumps(conjunctions, indent=2)}

Please provide:
1. A risk assessment summary (HIGH/MEDIUM/LOW overall risk level)
2. The top 3 most concerning conjunction events and why
3. Recommended monitoring actions for operators
4. Brief explanation of what conjunction events mean for non-experts

Be concise and actionable."""

def main():
    parser = argparse.ArgumentParser(description="Satellite Conjunction Analyst")
    parser.add_argument("--group", default="stations",
                        choices=list(tle_fetcher.TLE_GROUPS.keys()),
                        help="Satellite group to analyze")
    parser.add_argument("--threshold", type=float, default=50.0,
                        help="Close approach threshold in km (default: 50)")
    parser.add_argument("--hours", type=int, default=24,
                        help="Hours to look ahead (default: 24)")
    parser.add_argument("--no-agent", action="store_true",
                        help="Skip Nemotron inference, show raw analysis only")
    args = parser.parse_args()

    console.print(Panel(
        f"[bold cyan]Satellite Conjunction Analyst[/bold cyan]\n"
        f"Group: [yellow]{args.group}[/yellow] | "
        f"Threshold: [yellow]{args.threshold} km[/yellow] | "
        f"Lookahead: [yellow]{args.hours}h[/yellow]",
        expand=False
    ))

    console.print("\n[bold green]Fetching TLE data from CelesTrak...[/bold green]")
    satellites = tle_fetcher.fetch_tle_group(args.group)
    console.print(f"  Loaded [cyan]{len(satellites)}[/cyan] satellites")

    console.print("\n[bold green]Running conjunction analysis (SGP4 propagation)...[/bold green]")
    conjunctions = orbital_math.find_conjunctions(
        satellites,
        threshold_km=args.threshold,
        hours_ahead=args.hours
    )

    # Display results table
    table = Table(title=f"Conjunction Events (< {args.threshold} km)", show_lines=True)
    table.add_column("Satellite 1", style="cyan")
    table.add_column("Satellite 2", style="cyan")
    table.add_column("Min Distance (km)", style="red")
    table.add_column("Time (UTC)")

    for c in conjunctions[:20]:  # show top 20
        dist = c["min_distance_km"]
        color = "red" if dist < 5 else "yellow" if dist < 20 else "white"
        table.add_row(
            c["sat1"], c["sat2"],
            f"[{color}]{dist}[/{color}]",
            c["time_utc"]
        )

    console.print(table)
    console.print(f"\nTotal events found: [bold]{len(conjunctions)}[/bold]")

    if not conjunctions:
        console.print("[green]No conjunction events detected within threshold.[/green]")

    if args.no_agent:
        console.print("\n[yellow]--no-agent flag set. Skipping Nemotron inference.[/yellow]")
        return

    console.print("\n[bold green]Sending to Nemotron for risk assessment...[/bold green]\n")
    prompt = build_analysis_prompt(conjunctions[:10], args.group, args.threshold, len(satellites))

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, dir="/tmp") as f:
        f.write(prompt)
        tmp_path = f.name

    result = subprocess.run(
        ["openclaw", "agent", "--agent", "main", "--local",
         "-m", f"$(cat {tmp_path})", "--session-id", "conjunction-analysis"],
        capture_output=True, text=True, timeout=180
    )
    response = result.stdout or result.stderr
    console.print(Panel(response, title="[bold cyan]Risk Assessment — Nemotron[/bold cyan]"))

if __name__ == "__main__":
    main()
