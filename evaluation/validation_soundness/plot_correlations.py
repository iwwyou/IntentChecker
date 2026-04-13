"""
Generate scatter plots of analysis time vs complexity metrics.
Produces a 2x3 subplot figure saved as PDF for LaTeX inclusion.

Usage:
    python plot_correlations.py [--out rq1_scatter.pdf]
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

# Metrics to plot: (csv_column, display_label)
PLOT_METRICS = [
    ("lines",         "Source lines"),
    ("functions",     "Functions"),
    ("branch_count",  "Branches"),
    ("debug_total",   "Debug annotations"),
    ("loop_count",    "Loops"),
    ("external_calls","External calls"),
]


def load_metrics(path):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not row.get("case", "").strip():
                continue
            rows.append(row)
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=os.path.join(SCRIPT_DIR, "rq1_scatter.pdf"))
    args = parser.parse_args()

    rows = load_metrics(METRICS_CSV)
    times = np.array([float(r["analysis_time_mean"]) for r in rows])

    fig, axes = plt.subplots(2, 3, figsize=(7.0, 4.2))
    axes = axes.flatten()

    for idx, (col, label) in enumerate(PLOT_METRICS):
        ax = axes[idx]
        vals = np.array([float(r[col]) for r in rows])

        ax.scatter(vals, times, s=18, color="black", alpha=0.7, zorder=3)

        # Regression line
        if np.std(vals) > 0:
            slope, intercept, r_val, _, _ = stats.linregress(vals, times)
            x_line = np.linspace(vals.min(), vals.max(), 50)
            ax.plot(x_line, slope * x_line + intercept,
                    color="gray", linewidth=1.0, linestyle="--", zorder=2)
            r_text = f"r = {r_val:+.2f}"
        else:
            r_text = "r = N/A"

        ax.set_xlabel(label, fontsize=8)
        if idx % 3 == 0:
            ax.set_ylabel("Analysis time (s)", fontsize=8)
        ax.tick_params(labelsize=7)
        ax.text(0.97, 0.95, r_text, transform=ax.transAxes,
                fontsize=7.5, ha="right", va="top",
                bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="gray",
                          alpha=0.8))
        ax.grid(True, linewidth=0.3, alpha=0.5)

    plt.tight_layout(pad=0.5)
    plt.savefig(args.out, bbox_inches="tight", dpi=300)
    print(f"Saved: {args.out}")


if __name__ == "__main__":
    main()
