"""
RQ1 per-case metrics collection for the 20 mitigated cases.

For each case, collects:
  - Analysis time (mean over N runs of run_all.py)
  - Source complexity: total lines, contract count, function count
  - Control-flow complexity: loop count, branch count
  - Dependency metrics: inheritance count, using-directive count, external-call count
  - Annotation metrics: @StateVar/@LocalVar/@GlobalVar/@IReturn, @During/@Post

Outputs:
  - evaluation/validation_soundness/rq1_metrics.csv                 (merged per-case metrics)
  - evaluation/validation_soundness/rq1_correlations.csv            (Pearson correlation with mean time)
  - evaluation/validation_soundness/rq2_run{i}.csv                  (snapshot of each run)
  - evaluation/validation_soundness/plots/analysis_time_factors.png (scatter plots, optional)

Usage:
    .venv/Scripts/python.exe evaluation/validation_soundness/collect_metrics.py             # use existing CSV
    .venv/Scripts/python.exe evaluation/validation_soundness/collect_metrics.py --runs 3    # run 3 times, average
    .venv/Scripts/python.exe evaluation/validation_soundness/collect_metrics.py --runs 1    # single run
"""

import argparse
import csv
import json
import re
import shutil
import statistics
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
MAIN_EVAL_DIR = PROJECT_ROOT / "evaluation" / "RQ1"
MAIN_RESULTS = MAIN_EVAL_DIR / "rq2_results.csv"
SOUNDNESS_DIR = PROJECT_ROOT / "evaluation" / "validation_soundness"
OUT_CSV = SOUNDNESS_DIR / "rq1_metrics.csv"
CORR_CSV = SOUNDNESS_DIR / "rq1_correlations.csv"
PLOTS_DIR = SOUNDNESS_DIR / "plots"

# Same 20 cases as run_all.py
CASE_JSONS = [
    "cases/div_in_path/WANGMI_input.json",
    "cases/exchange_problem/Nokon_input.json",
    "cases/greedy_contract/SwordCrowdsale_input.json",
    "cases/operator_order_issue/BoostToken_input.json",
    "cases/indivisible_amount/BoostToken_input.json",
    "cases/profit_opportunity/HIT_input.json",
    "cases/web3bugs_5_H_07/web3bugs_5_H_07.json",
    "cases/web3bugs_5_H_08/web3bugs_5_H_08.json",
    "cases/web3bugs_5_H_12/web3bugs_5_H_12.json",
    "cases/web3bugs_45_H_01/web3bugs_45_H_01.json",
    "cases/web3bugs_47_H_02/web3bugs_47_H_02.json",
    "cases/web3bugs_51_H_02/web3bugs_51_H_02.json",
    "cases/web3bugs_56_H_02/web3bugs_56_H_02.json",
    "cases/web3bugs_58_H_02/web3bugs_58_H_02.json",
    "cases/web3bugs_60_H_01/web3bugs_60_H_01.json",
    "cases/web3bugs_62_H_08/web3bugs_62_H_08.json",
    "cases/web3bugs_70_H_10/web3bugs_70_H_10.json",
    "cases/web3bugs_77_H_01/web3bugs_77_H_01.json",
    "cases/web3bugs_78_H_02/web3bugs_78_H_02.json",
    "cases/web3bugs_101_H_01/web3bugs_101_H_01.json",
]


# ─────────────────────────────────────────────────────────────
# Source-level metric extraction
# ─────────────────────────────────────────────────────────────

ANNOTATION_PREFIXES = (
    "// @StateVar", "// @LocalVar", "// @GlobalVar", "// @IReturn",
    "// @During", "// @Post", "// @Debugging",
)


def _is_annotation(code: str) -> bool:
    return any(code.startswith(p) for p in ANNOTATION_PREFIXES)


def extract_source_metrics(json_path: Path) -> dict:
    """Parse the case JSON and compute source + annotation metrics."""
    recs = json.loads(json_path.read_text(encoding="utf-8"))

    # Annotation counts
    ann = {
        "debug_statevar": 0,
        "debug_localvar": 0,
        "debug_globalvar": 0,
        "debug_ireturn": 0,
        "intent_during": 0,
        "intent_post": 0,
    }

    # Source complexity counters
    contracts: set[str] = set()
    functions: set[str] = set()
    inheritance_count = 0
    using_directives = 0
    loop_count = 0
    branch_count = 0  # if statements
    external_calls = 0

    covered_lines: set[int] = set()

    for r in recs:
        if not isinstance(r, dict):
            continue
        code = r.get("code", "").strip()
        start = r.get("startLine", 0) or 0
        end = r.get("endLine", start) or start

        if not code or code == "\n":
            continue

        # Annotation records: count and skip
        if code.startswith("// @StateVar"):
            ann["debug_statevar"] += 1
            continue
        if code.startswith("// @LocalVar"):
            ann["debug_localvar"] += 1
            continue
        if code.startswith("// @GlobalVar"):
            ann["debug_globalvar"] += 1
            continue
        if code.startswith("// @IReturn"):
            ann["debug_ireturn"] += 1
            continue
        if code.startswith("// @During"):
            ann["intent_during"] += 1
            continue
        if code.startswith("// @Post"):
            ann["intent_post"] += 1
            continue
        if code.startswith("// @Debugging"):
            continue
        if code.startswith("//"):
            continue

        # Count real source lines
        for ln in range(start, end + 1):
            covered_lines.add(ln)

        # Contract declaration
        m = re.match(r"(?:abstract\s+)?(?:contract|library|interface)\s+(\w+)(?:\s+is\s+([^{]+))?", code)
        if m:
            contracts.add(m.group(1))
            if m.group(2):
                parents = [p.strip() for p in m.group(2).split(",") if p.strip()]
                inheritance_count += len(parents)
            continue

        # Function declaration
        fm = re.match(r"function\s+(\w+)", code)
        if fm:
            functions.add(fm.group(1))

        # Control flow: loops and branches
        if re.search(r"\bfor\s*\(", code):
            loop_count += 1
        if re.search(r"\bwhile\s*\(", code):
            loop_count += 1
        if re.search(r"\bif\s*\(", code):
            branch_count += 1

        # Using directive
        if re.match(r"using\s+\w+\s+for", code):
            using_directives += 1

        # External call pattern — rough heuristic:
        #   CapName(expr).method(...) or InterfaceVar.method(...)
        #   counts each CapName(...).ident( occurrence
        external_calls += len(re.findall(r"[A-Z]\w*\([^)]*\)\s*\.\s*\w+\s*\(", code))

    total_records = sum(
        1 for r in recs
        if isinstance(r, dict) and r.get("code", "").strip()
    )

    return {
        "num_records": total_records,
        "lines": len(covered_lines),
        "contracts": len(contracts),
        "functions": len(functions),
        "inheritance_count": inheritance_count,
        "using_directives": using_directives,
        "loop_count": loop_count,
        "branch_count": branch_count,
        "external_calls": external_calls,
        **ann,
        "debug_total": (
            ann["debug_statevar"] + ann["debug_localvar"]
            + ann["debug_globalvar"] + ann["debug_ireturn"]
        ),
        "intent_total": ann["intent_during"] + ann["intent_post"],
    }


# ─────────────────────────────────────────────────────────────
# run_all.py result loading
# ─────────────────────────────────────────────────────────────

def load_rq2_results(csv_path: Path = MAIN_RESULTS) -> dict:
    """Return {(case_name, category): {analysis_time_sec, result}} from a results CSV.

    Uses (case, category) as the key because some target contracts (e.g., BoostToken)
    appear in multiple NumScout pattern subdirectories with distinct annotations.
    """
    if not csv_path.exists():
        return {}
    out = {}
    with open(csv_path, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            key = (row["case"], row.get("category", ""))
            out[key] = {
                "analysis_time_sec": float(row.get("analysis_time_sec", 0) or 0),
                "result": row.get("result", ""),
            }
    return out


def run_rq2_evaluation() -> None:
    """Invoke run_all.py to regenerate rq2_results.csv."""
    runner = MAIN_EVAL_DIR / "run_all.py"
    print(f"[info] Running {runner} ...")
    subprocess.run([sys.executable, str(runner)], check=False)


def run_rq2_n_times(n: int) -> dict:
    """Run run_all.py n times, snapshot each result, return aggregated timings.

    Returns {(case, category): {mean, stdev, min, max, n_runs, result, all_times}}.
    """
    timings = defaultdict(list)
    last_results = {}

    for i in range(1, n + 1):
        print(f"\n========== run {i}/{n} ==========")
        run_rq2_evaluation()

        if not MAIN_RESULTS.exists():
            print(f"[error] {MAIN_RESULTS} not produced after run {i}")
            continue

        # Snapshot
        snapshot = SOUNDNESS_DIR / f"rq2_run{i}.csv"
        snapshot.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(MAIN_RESULTS, snapshot)
        print(f"[ok] snapshot → {snapshot}")

        # Collect timings
        rq2 = load_rq2_results()
        for key, data in rq2.items():
            timings[key].append(data["analysis_time_sec"])
            last_results[key] = data["result"]

    # Aggregate
    out = {}
    for key, times in timings.items():
        if not times:
            continue
        out[key] = {
            "analysis_time_mean": statistics.mean(times),
            "analysis_time_stdev": statistics.stdev(times) if len(times) > 1 else 0.0,
            "analysis_time_min": min(times),
            "analysis_time_max": max(times),
            "n_runs": len(times),
            "all_times": times,
            "result": last_results.get(key, ""),
        }
    return out


# ─────────────────────────────────────────────────────────────
# Analysis
# ─────────────────────────────────────────────────────────────

def collect_rows(case_jsons: list[str], rq2_agg: dict) -> list[dict]:
    """Build per-case rows. rq2_agg may be from a single run or aggregated over N."""
    rows = []
    for rel in case_jsons:
        path = MAIN_EVAL_DIR / rel
        case_name = path.stem.replace("_input", "")
        category = path.parent.name
        # Display name disambiguates collisions like BoostToken (operator vs indivisible)
        display = (
            case_name
            if case_name.startswith("web3bugs_")
            else f"{category}_{case_name}"
        )
        metrics = extract_source_metrics(path)
        agg = rq2_agg.get((case_name, category), {})

        # Support both shapes: single-run {analysis_time_sec, result}
        # or aggregated {analysis_time_mean, ...}
        if "analysis_time_mean" in agg:
            time_fields = {
                "analysis_time_mean": round(agg["analysis_time_mean"], 4),
                "analysis_time_stdev": round(agg["analysis_time_stdev"], 4),
                "analysis_time_min": round(agg["analysis_time_min"], 4),
                "analysis_time_max": round(agg["analysis_time_max"], 4),
                "n_runs": agg["n_runs"],
            }
        else:
            t = agg.get("analysis_time_sec", 0.0)
            time_fields = {
                "analysis_time_mean": round(t, 4),
                "analysis_time_stdev": 0.0,
                "analysis_time_min": round(t, 4),
                "analysis_time_max": round(t, 4),
                "n_runs": 1 if t > 0 else 0,
            }

        rows.append({
            "case": display,
            **time_fields,
            "result": agg.get("result", ""),
            **metrics,
        })
    return rows


def write_csv(rows: list[dict], path: Path) -> None:
    fieldnames = [
        "case",
        "analysis_time_mean", "analysis_time_stdev",
        "analysis_time_min", "analysis_time_max", "n_runs",
        "result",
        "num_records", "lines", "contracts", "functions",
        "inheritance_count", "using_directives",
        "loop_count", "branch_count", "external_calls",
        "debug_statevar", "debug_localvar", "debug_globalvar", "debug_ireturn",
        "debug_total",
        "intent_during", "intent_post", "intent_total",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def pearson(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n == 0:
        return 0.0
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = sum((x - mx) ** 2 for x in xs) ** 0.5
    dy = sum((y - my) ** 2 for y in ys) ** 0.5
    if dx == 0 or dy == 0:
        return 0.0
    return num / (dx * dy)


def compute_correlations(rows: list[dict]) -> list[tuple[str, float]]:
    numeric_keys = [
        "num_records", "lines", "contracts", "functions",
        "inheritance_count", "using_directives",
        "loop_count", "branch_count", "external_calls",
        "debug_statevar", "debug_localvar", "debug_globalvar", "debug_ireturn",
        "debug_total", "intent_during", "intent_post", "intent_total",
    ]
    ys = [r["analysis_time_mean"] for r in rows]
    corrs = []
    for k in numeric_keys:
        xs = [r.get(k, 0) for r in rows]
        corrs.append((k, pearson(xs, ys)))
    corrs.sort(key=lambda t: abs(t[1]), reverse=True)
    return corrs


def write_correlations(corrs: list[tuple[str, float]], path: Path) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "pearson_r_with_analysis_time"])
        for k, v in corrs:
            writer.writerow([k, f"{v:+.4f}"])


def print_correlations(corrs: list[tuple[str, float]]) -> None:
    print("\n=== Pearson correlation with analysis_time_sec ===")
    for k, v in corrs:
        bar_width = int(abs(v) * 20)
        bar = "#" * bar_width
        print(f"  {k:22s}: {v:+.3f}  {bar}")


def try_plot(rows: list[dict]) -> None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("[info] matplotlib not installed, skipping scatter plots")
        return

    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    factors = [
        "lines", "loop_count", "external_calls",
        "debug_total", "intent_total", "branch_count",
    ]
    ys = [r["analysis_time_mean"] for r in rows]
    yerrs = [r.get("analysis_time_stdev", 0) for r in rows]

    fig, axes = plt.subplots(2, 3, figsize=(13, 8))
    for ax, factor in zip(axes.flatten(), factors):
        xs = [r.get(factor, 0) for r in rows]
        ax.errorbar(xs, ys, yerr=yerrs, fmt='o', alpha=0.75,
                    markersize=6, capsize=3)
        ax.set_xlabel(factor)
        ax.set_ylabel("analysis time (s)")
        r_val = pearson(xs, ys)
        ax.set_title(f"{factor}  (r={r_val:+.2f})")
        ax.grid(alpha=0.3)
    fig.suptitle("Analysis time vs complexity factors (20 mitigated cases)")
    plt.tight_layout()
    out = PLOTS_DIR / "analysis_time_factors.png"
    plt.savefig(out, dpi=150)
    plt.close()
    print(f"[ok] Scatter plots → {out}")


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="RQ1 metrics collection")
    parser.add_argument(
        "--runs", type=int, default=0,
        help="Run run_all.py N times and average. 0 = use existing rq2_results.csv.",
    )
    args = parser.parse_args()

    if args.runs > 0:
        rq2_agg = run_rq2_n_times(args.runs)
        if not rq2_agg:
            print("[error] No timings collected. Aborting.")
            sys.exit(1)
    else:
        if not MAIN_RESULTS.exists():
            print(f"[info] {MAIN_RESULTS} not found. Running run_all.py once ...")
            run_rq2_evaluation()
        rq2_agg = load_rq2_results()
        if not rq2_agg:
            print(f"[error] {MAIN_RESULTS} still missing. Aborting.")
            sys.exit(1)

    missing = []
    for rel in CASE_JSONS:
        p = Path(rel)
        key = (p.stem.replace("_input", ""), p.parent.name)
        if key not in rq2_agg:
            missing.append(f"{key[1]}/{key[0]}")
    if missing:
        print(f"[warn] {len(missing)} cases missing from RQ2 data: {missing}")

    rows = collect_rows(CASE_JSONS, rq2_agg)
    write_csv(rows, OUT_CSV)
    n_runs = rows[0].get("n_runs", 1) if rows else 0
    print(f"\n[ok] Per-case metrics → {OUT_CSV}  ({len(rows)} cases, {n_runs} runs each)")

    corrs = compute_correlations(rows)
    write_correlations(corrs, CORR_CSV)
    print(f"[ok] Correlations → {CORR_CSV}")
    print_correlations(corrs)

    try_plot(rows)


if __name__ == "__main__":
    main()
