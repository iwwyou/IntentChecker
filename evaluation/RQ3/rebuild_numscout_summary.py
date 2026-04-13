"""Rebuild summary.json for NumScout run1 from existing output files.

Does NOT run NumScout. Reads all *.json files in outputs/numscout/<run>/ and
produces a consolidated summary.json. Supports both regular and patched results.
"""
import csv
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
CASE_MAPPING = SCRIPT_DIR / "case_mapping.csv"


def entry_from_json(cid, json_path, patched=False):
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)
    defects = [k for k, v in data.get("bool_defect", {}).items() if v]
    return {
        "case_id": cid, "tool": "numscout",
        "detected": len(defects) > 0,
        "detected_patterns": defects,
        "time": float(data.get("time", 0)),
        "evm_coverage": float(data.get("evm_code_coverage", 0)),
        "status": "ok_patched" if patched else "ok",
        "patched": patched,
    }


def main():
    run = sys.argv[1] if len(sys.argv) > 1 else "run1"
    output_dir = SCRIPT_DIR / "outputs" / "numscout" / run

    with open(CASE_MAPPING, encoding="utf-8") as f:
        all_cases = list(csv.DictReader(f))
    annotated = [c for c in all_cases if c["status"] == "annotated"]

    results = []
    for case in annotated:
        cid = case["case_id"]
        regular = output_dir / f"{cid}.json"
        patched = output_dir / f"{cid}_patched.json"
        if regular.exists():
            results.append(entry_from_json(cid, regular, patched=False))
        elif patched.exists():
            results.append(entry_from_json(cid, patched, patched=True))
        else:
            results.append({
                "case_id": cid, "tool": "numscout",
                "detected": False, "detected_patterns": [],
                "time": 0, "status": "no_result", "patched": False,
            })

    summary_file = output_dir / "summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    total = len(results)
    ok = sum(1 for r in results if r["status"] in ("ok", "ok_patched"))
    detected = sum(1 for r in results if r["detected"])
    patched_count = sum(1 for r in results if r.get("patched"))
    no_result = sum(1 for r in results if r["status"] == "no_result")
    print(f"Wrote {summary_file}")
    print(f"Total: {total}, OK: {ok} (patched: {patched_count}), Detected: {detected}, Missing: {no_result}")
    for r in results:
        marker = "[P]" if r.get("patched") else "   "
        det = "Y" if r["detected"] else "N"
        t = r.get("time", 0)
        cov = r.get("evm_coverage", 0)
        status = r["status"]
        pats = ",".join(r.get("detected_patterns", []))
        print(f"  {marker} {r['case_id']:35} det={det} t={t:7.1f}s cov={cov:5.1f}% {status:12} {pats}")


if __name__ == "__main__":
    main()
