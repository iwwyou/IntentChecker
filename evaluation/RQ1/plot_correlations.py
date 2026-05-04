"""
Generate scatter plots of analysis time vs complexity metrics.
3+2 layout (3 on top, 2 centered on bottom), saved as PDF for LaTeX inclusion.

Usage:
    python plot_correlations.py [--out <path.pdf>]
"""

import argparse
import csv
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
METRICS_CSV = os.path.join(SCRIPT_DIR, "rq1_metrics.csv")
DEFAULT_OUT = os.path.abspath(
    os.path.join(SCRIPT_DIR, "..", "..", "paper", "figure", "rq1_scatter.pdf")
)

# (csv_column, display_label) — order = plot order
PLOT_METRICS = [
    ("lines",           "Source lines"),
    ("internal_calls",  "Internal calls"),
    ("external_calls",  "External calls"),
    ("control_flow",    "Control flow"),
    ("debug_total",     "Debug annotations"),
]


def load_metrics(path):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if not row.get("case", "").strip():
                continue
            rows.append(row)
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=DEFAULT_OUT)
    args = parser.parse_args()

    rows = load_metrics(METRICS_CSV)
    times = np.array([float(r["analysis_time_mean"]) for r in rows])

    # 3+2 layout: 2 rows × 6 columns grid; each subplot spans 2 columns.
    # Bottom row shifts by 1 column to center 2 subplots.
    mosaic = [
        ["A", "A", "B", "B", "C", "C"],
        [".", "D", "D", "E", "E", "."],
    ]
    fig, axd = plt.subplot_mosaic(mosaic, figsize=(7.2, 4.6))
    panel_ids = ["A", "B", "C", "D", "E"]

    for pid, (col, label) in zip(panel_ids, PLOT_METRICS):
        ax = axd[pid]
        vals = np.array([float(r[col]) for r in rows])

        ax.scatter(vals, times, s=18, color="black", alpha=0.7, zorder=3)

        if np.std(vals) > 0:
            slope, intercept, r_val, _, _ = stats.linregress(vals, times)
            x_line = np.linspace(vals.min(), vals.max(), 50)
            ax.plot(x_line, slope * x_line + intercept,
                    color="gray", linewidth=1.0, linestyle="--", zorder=2)
            r_text = f"r = {r_val:+.2f}"
        else:
            r_text = "r = N/A"

        ax.set_xlabel(label, fontsize=8)
        ax.set_ylabel("Analysis time (s)", fontsize=8)
        ax.tick_params(labelsize=7)
        ax.text(0.97, 0.95, r_text, transform=ax.transAxes,
                fontsize=7.5, ha="right", va="top",
                bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="gray",
                          alpha=0.8))
        ax.grid(True, linewidth=0.3, alpha=0.5)

    plt.tight_layout(pad=0.6)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    plt.savefig(args.out, bbox_inches="tight", dpi=300)
    print(f"Saved: {args.out}")


if __name__ == "__main__":
    main()
