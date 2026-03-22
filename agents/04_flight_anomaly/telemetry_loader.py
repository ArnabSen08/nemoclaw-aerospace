"""
Telemetry data loader.
Downloads NASA spacecraft anomaly datasets from the Telemanom project
(Mars Science Laboratory + SMAP missions) — free, no auth required.

Dataset: https://github.com/khundman/telemanom
Paper: Detecting Spacecraft Anomalies Using LSTMs and Nonparametric Dynamic Thresholding
"""
import requests
import numpy as np
import os
import json

TELEMANOM_BASE = "https://raw.githubusercontent.com/khundman/telemanom/master"

# Known channels with labeled anomalies from MSL and SMAP missions
ANOMALY_CHANNELS = {
    # MSL (Mars Science Laboratory / Curiosity Rover)
    "P-1":  "MSL",
    "P-2":  "MSL",
    "P-3":  "MSL",
    "P-4":  "MSL",
    "P-7":  "MSL",
    # SMAP (Soil Moisture Active Passive satellite)
    "S-1":  "SMAP",
    "S-2":  "SMAP",
    "S-3":  "SMAP",
    "A-1":  "SMAP",
    "A-2":  "SMAP",
}

LABELED_ANOMALIES_URL = f"{TELEMANOM_BASE}/labeled_anomalies.csv"

def fetch_labeled_anomalies():
    """Download the labeled anomaly index CSV."""
    resp = requests.get(LABELED_ANOMALIES_URL, timeout=15)
    resp.raise_for_status()
    lines = resp.text.strip().splitlines()
    header = lines[0].split(",")
    records = []
    for line in lines[1:]:
        parts = line.split(",")
        if len(parts) >= len(header):
            records.append(dict(zip(header, parts)))
    return records

def fetch_channel_data(channel_id: str, split="test"):
    """
    Download telemetry numpy array for a specific channel.
    split: 'train' or 'test'
    """
    url = f"{TELEMANOM_BASE}/data/{split}/{channel_id}.npy"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()

    # Save to /tmp and load
    tmp_path = f"/tmp/{channel_id}_{split}.npy"
    with open(tmp_path, "wb") as f:
        f.write(resp.content)
    return np.load(tmp_path)

def compute_basic_stats(data: np.ndarray):
    """Compute basic telemetry statistics for the first channel dimension."""
    channel = data[:, 0] if data.ndim > 1 else data
    return {
        "length": len(channel),
        "mean": round(float(np.mean(channel)), 4),
        "std": round(float(np.std(channel)), 4),
        "min": round(float(np.min(channel)), 4),
        "max": round(float(np.max(channel)), 4),
        "range": round(float(np.max(channel) - np.min(channel)), 4),
    }

def detect_threshold_anomalies(data: np.ndarray, z_threshold=3.0):
    """
    Simple z-score based anomaly detection.
    Returns list of anomalous time indices and their z-scores.
    """
    channel = data[:, 0] if data.ndim > 1 else data
    mean = np.mean(channel)
    std = np.std(channel)
    if std == 0:
        return []

    z_scores = np.abs((channel - mean) / std)
    anomaly_indices = np.where(z_scores > z_threshold)[0]

    anomalies = []
    for idx in anomaly_indices[:50]:  # cap at 50
        anomalies.append({
            "time_step": int(idx),
            "value": round(float(channel[idx]), 4),
            "z_score": round(float(z_scores[idx]), 3),
        })
    return anomalies
