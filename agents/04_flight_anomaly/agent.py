"""
Flight Anomaly Detection Agent
--------------------------------
Downloads real NASA spacecraft telemetry (MSL Curiosity Rover + SMAP satellite)
from the Telemanom dataset, runs statistical anomaly detection, and sends
findings to Nemotron for engineering-level analysis and plain-English reporting.

Dataset: github.com/khundman/telemanom (Apache 2.0)
Missions: Mars Science Laboratory (MSL) & SMAP satellite

Run inside NemoClaw sandbox:
  python agent.py --channel P-1
  python agent.py --channel S-2 --z-threshold 2.5
"""
import argparse
import json
import subprocess
import tempfile
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
import telemetry_loader

console = Console()

def build_anomaly_prompt(channel_id, mission, stats, anomalies, labeled):
    labeled_str = json.dumps(labeled, indent=2) if labeled else "No labeled anomalies found for this channel."
    return f"""You are a spacecraft systems engineer analyzing telemetry data.

Mission: {mission}
Channel ID: {channel_id}
Data source: NASA Telemanom dataset (real spacecraft telemetry)

Telemetry Statistics:
{json.dumps(stats, indent=2)}

Detected Anomalies (z-score method, threshold=3σ):
{json.dumps(anomalies[:20], indent=2)}

Known Labeled Anomalies from NASA engineers:
{labeled_str}

Please provide a Flight Anomaly Report including:

1. ANOMALY SUMMARY
   - Total anomalies detected vs labeled
   - Severity assessment (CRITICAL/WARNING/NOMINAL)
   - Detection accuracy commentary

2. ANOMALY ANALYSIS
   - Pattern description (clustered? isolated? gradual drift?)
   - Possible root causes (sensor fault, environmental, mechanical, software)
   - Comparison with labeled ground truth

3. ENGINEERING RECOMMENDATIONS
   - Immediate actions for mission controllers
   - Suggested follow-up diagnostics
   - Risk to mission if unaddressed

4. PLAIN ENGLISH SUMMARY
   - Explain what this means for a non-engineer stakeholder

Be precise and use aerospace engineering terminology where appropriate."""

def main():
    parser = argparse.ArgumentParser(description="Flight Anomaly Detection Agent")
    parser.add_argument("--channel", default="P-1",
                        choices=list(telemetry_loader.ANOMALY_CHANNELS.keys()),
                        help="Telemetry channel to analyze")
    parser.add_argument("--z-threshold", type=float, default=3.0,
                        help="Z-score threshold for anomaly detection (default: 3.0)")
    parser.add_argument("--no-agent", action="store_true",
                        help="Skip Nemotron inference")
    args = parser.parse_args()

    mission = telemetry_loader.ANOMALY_CHANNELS[args.channel]

    console.print(Panel(
        f"[bold cyan]Flight Anomaly Detection Agent[/bold cyan]\n"
        f"Channel: [yellow]{args.channel}[/yellow] | "
        f"Mission: [yellow]{mission}[/yellow] | "
        f"Z-threshold: [yellow]{args.z_threshold}σ[/yellow]",
        expand=False
    ))

    # Fetch labeled anomalies index
    console.print("\n[bold green]Fetching labeled anomaly index from NASA Telemanom...[/bold green]")
    try:
        all_labeled = telemetry_loader.fetch_labeled_anomalies()
        labeled = [r for r in all_labeled if r.get("chan_id", "").strip() == args.channel]
        console.print(f"  Found [cyan]{len(labeled)}[/cyan] labeled anomaly records for {args.channel}")
    except Exception as e:
        console.print(f"  [yellow]Warning: Could not fetch labels: {e}[/yellow]")
        labeled = []

    # Fetch telemetry data
    console.print(f"\n[bold green]Downloading telemetry data for channel {args.channel}...[/bold green]")
    try:
        data = telemetry_loader.fetch_channel_data(args.channel, split="test")
        console.print(f"  Loaded [cyan]{data.shape}[/cyan] telemetry array")
    except Exception as e:
        console.print(f"[red]Error fetching telemetry: {e}[/red]")
        return

    # Compute stats
    stats = telemetry_loader.compute_basic_stats(data)
    anomalies = telemetry_loader.detect_threshold_anomalies(data, z_threshold=args.z_threshold)

    # Display stats
    stats_table = Table(title=f"Telemetry Statistics — {args.channel} ({mission})")
    stats_table.add_column("Metric", style="cyan")
    stats_table.add_column("Value")
    for k, v in stats.items():
        stats_table.add_row(k, str(v))
    console.print(stats_table)

    # Display anomalies
    if anomalies:
        anom_table = Table(title=f"Detected Anomalies (z > {args.z_threshold}σ) — Top 15")
        anom_table.add_column("Time Step", style="cyan")
        anom_table.add_column("Value")
        anom_table.add_column("Z-Score", style="red")
        for a in anomalies[:15]:
            z = a["z_score"]
            color = "red" if z > 5 else "yellow" if z > 4 else "white"
            anom_table.add_row(str(a["time_step"]), str(a["value"]), f"[{color}]{z}[/{color}]")
        console.print(anom_table)
    else:
        console.print(f"\n[green]No anomalies detected above {args.z_threshold}σ threshold.[/green]")

    console.print(f"\n[bold]Total anomalies detected:[/bold] {len(anomalies)}")
    if labeled:
        console.print(f"[bold]NASA labeled anomalies:[/bold] {len(labeled)}")

    if args.no_agent:
        console.print("\n[yellow]--no-agent flag set. Skipping Nemotron inference.[/yellow]")
        return

    console.print("\n[bold green]Sending to Nemotron for engineering analysis...[/bold green]\n")
    prompt = build_anomaly_prompt(args.channel, mission, stats, anomalies, labeled)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, dir="/tmp") as f:
        f.write(prompt)
        tmp_path = f.name

    result = subprocess.run(
        ["openclaw", "agent", "--agent", "main", "--local",
         "-m", f"$(cat {tmp_path})", "--session-id", "anomaly-detection"],
        capture_output=True, text=True, timeout=180
    )
    response = result.stdout or result.stderr
    console.print(Panel(response, title="[bold cyan]Engineering Report — Nemotron[/bold cyan]"))

if __name__ == "__main__":
    main()
