# ============================================
#  KPI Dashboard for War Room
#  --------------------------------------------
#  Version: 0.1 (Standalone Analytics Module)
#  Author: Aj & ChatGPT System Ops
#
#  PURPOSE:
#     - Visualize performance trends from /logs/kpi_log.csv
#     - Create simple line and bar charts
#     - Save charts to /logs/charts/
#
#  SAFETY:
#     - Read-only. Does not modify War Room data.
#     - Auto-creates /logs/charts/ if missing.
#
#  USAGE:
#     python dashboard.py
# ============================================

import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from pathlib import Path

LOG_FILE = Path("logs/kpi_log.csv")
CHART_DIR = Path("logs/charts")

def load_data():
    """Load KPI data safely."""
    if not LOG_FILE.exists():
        print("⚠️  No KPI log found at", LOG_FILE)
        return None
    df = pd.read_csv(LOG_FILE)
    if df.empty:
        print("⚠️  KPI log is empty.")
        return None
    return df

def clean_columns(df):
    """Normalize columns for easy plotting."""
    df.columns = [c.strip().lower() for c in df.columns]
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    if "revenue" in df.columns:
        df["revenue"] = pd.to_numeric(df["revenue"], errors="coerce")
    return df

def plot_metric(df, metric, agg_func="sum"):
    """Create and save a chart for one metric."""
    if metric not in df.columns:
        print(f"⚠️  '{metric}' column not found.")
        return

    # Aggregate by date
    df["date"] = df["timestamp"].dt.date
    grouped = df.groupby("date")[metric].agg(agg_func)

    plt.figure(figsize=(8, 4))
    grouped.plot(kind="bar", color="#2E86C1", edgecolor="black")
    plt.title(f"{metric.capitalize()} over Time")
    plt.xlabel("Date")
    plt.ylabel(metric.capitalize())
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()

    CHART_DIR.mkdir(parents=True, exist_ok=True)
    filename = CHART_DIR / f"{metric}_trend_{datetime.now().strftime('%Y%m%d_%H%M')}.png"
    plt.savefig(filename)
    plt.close()
    print(f"📊 Saved chart: {filename}")

def main():
    print("Running KPI Dashboard...\n")
    df = load_data()
    if df is None:
        return

    df = clean_columns(df)

    # Show available columns for context
    print("Columns:", list(df.columns), "\n")

    metrics = ["leads", "booked", "revenue"]
    for metric in metrics:
        if metric in df.columns:
            plot_metric(df, metric)
        else:
            print(f"Skipping missing metric: {metric}")

    print("\n✅ Charts generated in /logs/charts/")

if __name__ == "__main__":
    main()