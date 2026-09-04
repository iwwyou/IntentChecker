"""
RQ1 structural metrics (lines, internal/external calls, control flow, debug/intent
annotation counts) for the 45 case-built cases (baseline 20 + phase_reviews-expressible
25), re-derived from the CURRENT case JSON (post this-session engine/annotation edits).

Pure text parsing only -- does not invoke main.py, so this is safe to run alongside a
concurrent latency measurement without any CPU contention.

Output: evaluation/RQ2/rq1_structural.csv

Usage:
    .venv/Scripts/python.exe evaluation/RQ2/collect_rq1_structural.py
"""

import csv
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "evaluation" / "RQ1"))

from collect_metrics import extract_source_metrics  # noqa: E402

RQ1_DIR = PROJECT_ROOT / "evaluation" / "RQ1"
RQ2_DIR = PROJECT_ROOT / "evaluation" / "RQ2"
CASES_DIR = RQ1_DIR / "cases"
OUT_CSV = RQ2_DIR / "rq1_structural.csv"

BASELINE_CASE_JSONS = [
    "div_in_path/WANGMI_input.json", "exchange_problem/Nokon_input.json",
    "greedy_contract/SwordCrowdsale_input.json", "operator_order_issue/BoostToken_input.json",
    "indivisible_amount/BoostToken_input.json", "profit_opportunity/HIT_input.json",
    "web3bugs_5_H_07/web3bugs_5_H_07.json", "web3bugs_5_H_08/web3bugs_5_H_08.json",
    "web3bugs_5_H_12/web3bugs_5_H_12.json", "web3bugs_45_H_01/web3bugs_45_H_01.json",
    "web3bugs_47_H_02/web3bugs_47_H_02.json", "web3bugs_51_H_02/web3bugs_51_H_02.json",
    "web3bugs_56_H_02/web3bugs_56_H_02.json", "web3bugs_58_H_02/web3bugs_58_H_02.json",
    "web3bugs_60_H_01/web3bugs_60_H_01.json", "web3bugs_62_H_08/web3bugs_62_H_08.json",
    "web3bugs_70_H_10/web3bugs_70_H_10.json", "web3bugs_77_H_01/web3bugs_77_H_01.json",
    "web3bugs_78_H_02/web3bugs_78_H_02.json", "web3bugs_101_H_01/web3bugs_101_H_01.json",
]

PHASE_REVIEWS_EXPRESSIBLE_25 = [
    "web3bugs_112_H_01", "web3bugs_113_H_05", "web3bugs_16_H_06", "web3bugs_192_H_01",
    "web3bugs_29_H_08", "web3bugs_29_H_11", "web3bugs_31_H_01", "web3bugs_35_H_08",
    "web3bugs_35_H_11", "web3bugs_35_H_12", "web3bugs_3_H_04", "web3bugs_3_H_05",
    "web3bugs_42_H_01", "web3bugs_52_H_04", "web3bugs_52_H_23", "web3bugs_52_H_34",
    "web3bugs_59_H_04", "web3bugs_62_H_03", "web3bugs_62_H_10", "web3bugs_65_H_01",
    "web3bugs_70_H_04", "web3bugs_70_H_05", "web3bugs_79_H_02", "web3bugs_83_H_01",
    "numscout_EthereumGod",
]


def main():
    rows = []
    for rel in BASELINE_CASE_JSONS:
        p = CASES_DIR / rel
        case_id = p.stem.replace("_input", "")
        group = "baseline20"
        metrics = extract_source_metrics(p)
        rows.append({"case_id": case_id, "group": group, **metrics})

    for case_id in PHASE_REVIEWS_EXPRESSIBLE_25:
        p = CASES_DIR / case_id / f"{case_id}.json"
        if not p.exists():
            print(f"[warn] missing {p}")
            continue
        metrics = extract_source_metrics(p)
        rows.append({"case_id": case_id, "group": "phase_reviews_expressible", **metrics})

    fieldnames = [
        "case_id", "group",
        "lines", "internal_calls", "external_calls", "control_flow", "debug_total",
        "num_records", "using_directives",
        "loop_count", "branch_count", "guard_count",
        "debug_statevar", "debug_localvar", "debug_globalvar", "debug_ireturn",
        "intent_during", "intent_post", "intent_total",
    ]
    RQ2_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"[ok] {len(rows)} cases -> {OUT_CSV}")


if __name__ == "__main__":
    main()
