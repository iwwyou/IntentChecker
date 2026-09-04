"""
RQ2-B latency + RQ1-B validation_outcome collection, for the 45 cases that have a
built, executable case JSON (baseline 20 + phase_reviews-expressible 25).

For each case: run main.py 10x, record per-run wall time (from [TIMING]) and the
per-annotation-line outcome (Violated / Warning / Satisfied), then compare the
number of observed output lines against the number of @During/@Post annotations
declared in the case JSON to detect a silently-missing ("Unsupported") annotation.

Outputs:
  - evaluation/RQ2/rq2b_latency.csv       (case, run_1..run_10, mean, median, std, q1, q3, iqr, min, max)
  - evaluation/RQ2/rq2b_cumulative_median.csv   (case, median_1, median_3, median_6, median_10)
  - evaluation/RQ2/rq2b_validation.json   (case -> list of per-annotation outcome dicts + case-level rollup)

Usage:
    .venv/Scripts/python.exe evaluation/RQ2/collect_rq2b.py
    .venv/Scripts/python.exe evaluation/RQ2/collect_rq2b.py --case web3bugs_62_H_03
    .venv/Scripts/python.exe evaluation/RQ2/collect_rq2b.py --runs 10
"""

import argparse
import csv
import json
import os
import re
import statistics
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
RQ1_DIR = PROJECT_ROOT / "evaluation" / "RQ1"
RQ2_DIR = PROJECT_ROOT / "evaluation" / "RQ2"
CASES_DIR = RQ1_DIR / "cases"
MAIN_PY = PROJECT_ROOT / "main.py"

LATENCY_CSV = RQ2_DIR / "rq2b_latency.csv"
CUMMEDIAN_CSV = RQ2_DIR / "rq2b_cumulative_median.csv"
VALIDATION_JSON = RQ2_DIR / "rq2b_validation.json"

# baseline 20 -- canonical subfolder paths only (never the stale root-level duplicates).
# case_id is explicit here (not derived from the filename) so it matches
# evaluation/RQ2/extracted/<case_id>.json exactly -- deriving it from the path
# (e.g. "<category>_<stem>") previously produced wrong/colliding ids for every
# non-web3bugs case (WANGMI/Nokon/SwordCrowdsale/HIT/BoostToken x2).
BASELINE_CASE_JSONS = [
    ("numscout_WANGMI", "div_in_path/WANGMI_input.json"),
    ("numscout_Nokon", "exchange_problem/Nokon_input.json"),
    ("flyinointment_SwordCrowdsale", "greedy_contract/SwordCrowdsale_input.json"),
    ("numscout_BoostToken_operator", "operator_order_issue/BoostToken_input.json"),
    ("numscout_BoostToken_indivisible", "indivisible_amount/BoostToken_input.json"),
    ("numscout_HIT", "profit_opportunity/HIT_input.json"),
    ("web3bugs_5_H_07", "web3bugs_5_H_07/web3bugs_5_H_07.json"),
    ("web3bugs_5_H_08", "web3bugs_5_H_08/web3bugs_5_H_08.json"),
    ("web3bugs_5_H_12", "web3bugs_5_H_12/web3bugs_5_H_12.json"),
    ("web3bugs_45_H_01", "web3bugs_45_H_01/web3bugs_45_H_01.json"),
    ("web3bugs_47_H_02", "web3bugs_47_H_02/web3bugs_47_H_02.json"),
    ("web3bugs_51_H_02", "web3bugs_51_H_02/web3bugs_51_H_02.json"),
    ("web3bugs_56_H_02", "web3bugs_56_H_02/web3bugs_56_H_02.json"),
    ("web3bugs_58_H_02", "web3bugs_58_H_02/web3bugs_58_H_02.json"),
    ("web3bugs_60_H_01", "web3bugs_60_H_01/web3bugs_60_H_01.json"),
    ("web3bugs_62_H_08", "web3bugs_62_H_08/web3bugs_62_H_08.json"),
    ("web3bugs_70_H_10", "web3bugs_70_H_10/web3bugs_70_H_10.json"),
    ("web3bugs_77_H_01", "web3bugs_77_H_01/web3bugs_77_H_01.json"),
    ("web3bugs_78_H_02", "web3bugs_78_H_02/web3bugs_78_H_02.json"),
    ("web3bugs_101_H_01", "web3bugs_101_H_01/web3bugs_101_H_01.json"),
]

# phase_reviews-expressible -- directory-scanned, subfolder == case_id.
# (name kept as "_25" for historical continuity even though it's now 26: web3bugs_16_H_04
# was newly case-built and added later.)
PHASE_REVIEWS_EXPRESSIBLE_25 = [
    "web3bugs_112_H_01", "web3bugs_113_H_05", "web3bugs_16_H_04", "web3bugs_16_H_06",
    "web3bugs_192_H_01", "web3bugs_29_H_08", "web3bugs_29_H_11", "web3bugs_31_H_01",
    "web3bugs_35_H_08", "web3bugs_35_H_11", "web3bugs_35_H_12", "web3bugs_3_H_04",
    "web3bugs_3_H_05", "web3bugs_42_H_01", "web3bugs_52_H_04", "web3bugs_52_H_23",
    "web3bugs_52_H_34", "web3bugs_59_H_04", "web3bugs_62_H_03", "web3bugs_62_H_10",
    "web3bugs_65_H_01", "web3bugs_70_H_04", "web3bugs_70_H_05", "web3bugs_79_H_02",
    "web3bugs_83_H_01", "numscout_EthereumGod",
]


def resolve_case_list():
    """Return list of (case_id, absolute_json_path)."""
    out = []
    for case_id, rel in BASELINE_CASE_JSONS:
        out.append((case_id, CASES_DIR / rel))
    for case_id in PHASE_REVIEWS_EXPRESSIBLE_25:
        p = CASES_DIR / case_id / f"{case_id}.json"
        out.append((case_id, p))
    return out


def count_declared_annotations(json_path: Path) -> int:
    recs = json.loads(json_path.read_text(encoding="utf-8"))
    n = 0
    for r in recs:
        if not isinstance(r, dict):
            continue
        code = r.get("code", "").strip()
        if code.startswith("// @During ") or code.startswith("// @Post "):
            n += 1
    return n


LINE_RE = re.compile(
    r"\[(POST )?INTENT (VIOLAT(?:ION|ED)|WARNING|SUCCESS)\]\s*(?:Line (\d+):)?\s*(.*)"
)
TIMING_RE = re.compile(r"\[TIMING\]\s+([0-9.]+)s")
ERROR_RE = re.compile(r"(ValueError|AttributeError|TypeError|KeyError|IndexError):.*")


def parse_output(out: str, err: str):
    """Return (list of per-annotation outcome dicts, analysis_time, error_msg)."""
    outcomes = []
    for m in LINE_RE.finditer(out):
        scope = "Post" if m.group(1) else "During/Post"
        kind = m.group(2)
        line_no = m.group(3)
        rest = m.group(4).strip()
        if kind.startswith("VIOLAT"):
            outcome = "Violated"
        elif kind == "WARNING":
            outcome = "Warning"
        else:
            outcome = "Satisfied"
        risk_m = re.search(r"risk=([0-9.]+)", rest)
        risk = float(risk_m.group(1)) if risk_m else None
        outcomes.append({
            "line": line_no, "scope": scope, "outcome": outcome,
            "risk": risk, "text": rest[:200],
        })

    timing_m = TIMING_RE.search(out)
    analysis_time = float(timing_m.group(1)) if timing_m else 0.0

    err_m = ERROR_RE.search(err + out)
    error_msg = err_m.group(0)[:200] if err_m else ""

    return outcomes, analysis_time, error_msg


def run_once(json_path: Path):
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    try:
        proc = subprocess.run(
            [sys.executable, str(MAIN_PY), str(json_path)],
            capture_output=True, timeout=180, env=env, cwd=str(PROJECT_ROOT),
        )
        out = proc.stdout.decode("utf-8", errors="replace")
        err = proc.stderr.decode("utf-8", errors="replace")
        return parse_output(out, err)
    except subprocess.TimeoutExpired:
        return [], 180.0, "TIMEOUT"


def quartiles(sorted_vals):
    n = len(sorted_vals)
    if n == 0:
        return 0.0, 0.0
    def median_of(vals):
        m = len(vals)
        if m == 0:
            return 0.0
        mid = m // 2
        if m % 2 == 1:
            return vals[mid]
        return (vals[mid - 1] + vals[mid]) / 2
    mid = n // 2
    lower = sorted_vals[:mid]
    upper = sorted_vals[mid + (n % 2):]
    return median_of(lower), median_of(upper)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", help="substring filter on case_id")
    parser.add_argument("--runs", type=int, default=10)
    args = parser.parse_args()

    cases = resolve_case_list()
    if args.case:
        cases = [(cid, p) for cid, p in cases if args.case.lower() in cid.lower()]

    print(f"=== RQ2-B: {len(cases)} cases x {args.runs} runs ===\n")

    latency_rows = []
    cummedian_rows = []
    validation = {}

    for idx, (case_id, json_path) in enumerate(cases, 1):
        if not json_path.exists():
            print(f"[{idx}/{len(cases)}] {case_id} ... MISSING JSON at {json_path}, skipping")
            continue

        declared = count_declared_annotations(json_path)
        times = []
        last_outcomes = None
        last_error = ""
        print(f"[{idx}/{len(cases)}] {case_id} (declared annotations={declared}) ", end="", flush=True)

        for run_i in range(1, args.runs + 1):
            outcomes, t, err = run_once(json_path)
            times.append(t)
            last_outcomes = outcomes
            last_error = err
            print(".", end="", flush=True)

        sorted_times = sorted(times)
        n = len(sorted_times)
        mean_t = statistics.mean(sorted_times) if n else 0.0
        median_t = statistics.median(sorted_times) if n else 0.0
        std_t = statistics.stdev(sorted_times) if n > 1 else 0.0
        q1, q3 = quartiles(sorted_times)
        iqr = q3 - q1
        min_t = min(sorted_times) if n else 0.0
        max_t = max(sorted_times) if n else 0.0

        row = {"case_id": case_id}
        for i, t in enumerate(times, 1):
            row[f"run_{i}"] = round(t, 4)
        row.update({
            "mean": round(mean_t, 4), "median": round(median_t, 4),
            "std": round(std_t, 4), "q1": round(q1, 4), "q3": round(q3, 4),
            "iqr": round(iqr, 4), "min": round(min_t, 4), "max": round(max_t, 4),
        })
        latency_rows.append(row)

        cum = {}
        for k in (1, 3, 6, 10):
            sub = times[:k] if k <= len(times) else times
            cum[f"median_{k}"] = round(statistics.median(sub), 4) if sub else 0.0
        cummedian_rows.append({"case_id": case_id, **cum})

        # ---- validation outcome rollup ----
        observed = len(last_outcomes) if last_outcomes else 0
        missing = max(0, declared - observed)
        case_outcome = "ERROR" if last_error and last_error != "" else None
        if case_outcome is None:
            kinds = {o["outcome"] for o in (last_outcomes or [])}
            if "Violated" in kinds:
                case_outcome = "Violated"
            elif "Warning" in kinds:
                case_outcome = "Warning"
            elif missing > 0:
                case_outcome = "Unsupported"
            elif "Satisfied" in kinds:
                case_outcome = "Satisfied"
            else:
                case_outcome = "Unsupported"  # nothing printed at all

        validation[case_id] = {
            "declared_annotations": declared,
            "observed_output_lines": observed,
            "missing_lines": missing,
            "case_level_outcome": case_outcome,
            "per_line_outcomes": last_outcomes or [],
            "error": last_error,
        }

        print(f" median={median_t:.3f}s iqr=[{q1:.3f},{q3:.3f}] outcome={case_outcome}"
              + (f" (missing={missing} silent lines!)" if missing else ""))

    # ---- merge with any existing output rather than clobbering it ----
    # (important when --case narrows this run to a subset of cases: a plain overwrite
    # would silently delete every other case's already-collected data)
    cum_fieldnames = ["case_id", "median_1", "median_3", "median_6", "median_10"]

    existing_latency = {}
    if LATENCY_CSV.exists():
        with open(LATENCY_CSV, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                existing_latency[row["case_id"]] = row
    for row in latency_rows:
        existing_latency[row["case_id"]] = row

    existing_cum = {}
    if CUMMEDIAN_CSV.exists():
        with open(CUMMEDIAN_CSV, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                existing_cum[row["case_id"]] = row
    for row in cummedian_rows:
        existing_cum[row["case_id"]] = row

    existing_validation = {}
    if VALIDATION_JSON.exists():
        existing_validation = json.loads(VALIDATION_JSON.read_text(encoding="utf-8"))
    existing_validation.update(validation)

    n_merged_in = len(existing_latency) - len(latency_rows)
    if n_merged_in > 0:
        print(f"\n[info] merged {len(latency_rows)} case(s) from this run into "
              f"{n_merged_in} pre-existing case(s) -- total {len(existing_latency)}")

    # ---- write outputs (merged) ----
    RQ2_DIR.mkdir(parents=True, exist_ok=True)

    # Field list = union of run_N columns actually present across ALL merged rows (existing
    # rows may have more/fewer runs than this invocation's --runs), so a --case-filtered
    # re-run with a different --runs count never drops columns from untouched rows.
    max_runs = 0
    for row in existing_latency.values():
        run_ns = [int(k.split("_")[1]) for k in row.keys() if k.startswith("run_") and k.split("_")[1].isdigit()]
        if run_ns:
            max_runs = max(max_runs, max(run_ns))
    lat_fieldnames = ["case_id"] + [f"run_{i}" for i in range(1, max_runs + 1)] + \
        ["mean", "median", "std", "q1", "q3", "iqr", "min", "max"]

    with open(LATENCY_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=lat_fieldnames, restval="")
        writer.writeheader()
        writer.writerows(existing_latency.values())
    print(f"[ok] latency -> {LATENCY_CSV}")

    with open(CUMMEDIAN_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=cum_fieldnames)
        writer.writeheader()
        writer.writerows(existing_cum.values())
    print(f"[ok] cumulative median -> {CUMMEDIAN_CSV}")

    with open(VALIDATION_JSON, "w", encoding="utf-8") as f:
        json.dump(existing_validation, f, indent=2)
    print(f"[ok] validation outcomes -> {VALIDATION_JSON}")

    # overall summary -- over the full merged set, not just this run's (possibly --case-filtered) subset
    all_medians = [float(r["median"]) for r in existing_latency.values()]
    if all_medians:
        overall_median = statistics.median(all_medians)
        oq1, oq3 = quartiles(sorted(all_medians))
        print(f"\n=== Overall (case-median) median={overall_median:.3f}s IQR=[{oq1:.3f},{oq3:.3f}] over {len(all_medians)} cases (full merged set) ===")

    outcome_counts = {}
    for v in existing_validation.values():
        outcome_counts[v["case_level_outcome"]] = outcome_counts.get(v["case_level_outcome"], 0) + 1
    print(f"Outcome distribution (full merged set): {outcome_counts}")


if __name__ == "__main__":
    main()
