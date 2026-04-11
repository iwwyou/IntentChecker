"""Analyze GPTScan run1 results with function-level matching."""
import json, os, csv, sys

sys.stdout.reconfigure(encoding="utf-8")

cases = {}
with open("evaluation/RQ3/case_mapping.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        if row["case_id"]:
            cases[row["case_id"]] = row

output_dir = "evaluation/RQ3/outputs/gptscan/run1"
results = []

for fname in sorted(os.listdir(output_dir)):
    if not fname.endswith(".json") or fname.endswith(".metadata.json") or fname == "summary.json":
        continue
    case_id = fname.replace(".json", "")

    meta_path = os.path.join(output_dir, case_id + ".json.metadata.json")
    meta = {}
    if os.path.exists(meta_path):
        with open(meta_path, encoding="utf-8") as mf:
            meta = json.load(mf)

    with open(os.path.join(output_dir, fname), encoding="utf-8") as jf:
        data = json.load(jf)

    findings = data.get("results", []) if isinstance(data, dict) else []

    case_info = cases.get(case_id, {})
    target_sol = case_info.get("target_sol_file", "").split("/")[-1] if case_info.get("target_sol_file") else ""
    target_funcs = [fn.strip() for fn in case_info.get("function_name", "").split(";")]

    file_matched = False
    file_matched_codes = []
    func_details = []

    for finding in findings:
        code = finding.get("code", "")
        title = finding.get("title", "")
        for af in finding.get("affectedFiles", []):
            fp = af.get("filePath", "")
            start_line = af.get("range", {}).get("start", {}).get("line", 0)
            end_line = af.get("range", {}).get("end", {}).get("line", 0)

            if target_sol and target_sol in fp:
                file_matched = True
                file_matched_codes.append(code)
                # Extract just the filename
                short_fp = fp.replace("\\", "/").split("/")[-1]
                func_details.append({
                    "code": code,
                    "title": title,
                    "file": short_fp,
                    "lines": f"{start_line}-{end_line}",
                })

    results.append({
        "case_id": case_id,
        "annotated": case_info.get("status", "") == "annotated",
        "target_sol": target_sol,
        "target_funcs": target_funcs,
        "time": meta.get("used_time", 0),
        "has_finding": len(findings) > 0,
        "n_findings": len(findings),
        "file_matched": file_matched,
        "file_matched_codes": sorted(set(file_matched_codes)),
        "func_details": func_details,
        "all_patterns": sorted(set(r.get("code", "") for r in findings)),
    })

# ============ ANNOTATED 20: Detailed =============
print("=== ANNOTATED 20: Function-level matching ===\n")
for r in sorted(results, key=lambda x: x["case_id"]):
    if not r["annotated"]:
        continue

    cid = r["case_id"]
    tgt = f"{r['target_sol']}::{';'.join(r['target_funcs'])}"
    t = f"{r['time']:.0f}s" if r["time"] > 0 else "-"

    if not r["has_finding"]:
        label = "NO_FINDING"
    elif not r["file_matched"]:
        label = "OTHER_FILE_ONLY"
    else:
        label = "FILE_MATCH"

    print(f"[{label}] {cid}")
    print(f"  Target: {tgt} | Time: {t} | Total findings: {r['n_findings']}")

    if r["file_matched"]:
        print(f"  File-level codes: {r['file_matched_codes']}")
        seen = set()
        for d in r["func_details"]:
            key = f"{d['code']}@{d['lines']}"
            if key not in seen:
                seen.add(key)
                print(f"    -> {d['code']}: {d['file']} L{d['lines']}")
    elif r["has_finding"]:
        print(f"  Findings in OTHER files: {r['all_patterns']}")
    print()

# ============ ALL 74: Summary table =============
print("\n=== ALL 74 CASES ===")
print(f"{'case_id':<35} {'ann':<4} {'#find':<5} {'file?':<6} {'#tgt':<5} {'time':<7} {'codes_on_target'}")
print("-" * 120)

stats = {"NO_FINDING": 0, "OTHER_FILE": 0, "FILE_MATCH": 0}
ann_stats = {"NO_FINDING": 0, "OTHER_FILE": 0, "FILE_MATCH": 0}

for r in sorted(results, key=lambda x: x["case_id"]):
    n_on_tgt = len(set(f"{d['code']}@{d['lines']}" for d in r["func_details"]))
    t = f"{r['time']:.0f}" if r["time"] > 0 else "-"
    codes = r["file_matched_codes"] if r["file_matched"] else []
    a = "Y" if r["annotated"] else ""

    if not r["has_finding"]:
        cat = "NO_FINDING"
    elif not r["file_matched"]:
        cat = "OTHER_FILE"
    else:
        cat = "FILE_MATCH"

    stats[cat] += 1
    if r["annotated"]:
        ann_stats[cat] += 1

    print(f"{r['case_id']:<35} {a:<4} {r['n_findings']:<5} {str(r['file_matched']):<6} {n_on_tgt:<5} {t:<7} {codes}")

print(f"\nOverall 74: NO_FINDING={stats['NO_FINDING']}, OTHER_FILE={stats['OTHER_FILE']}, FILE_MATCH={stats['FILE_MATCH']}")
print(f"Annotated 20: NO_FINDING={ann_stats['NO_FINDING']}, OTHER_FILE={ann_stats['OTHER_FILE']}, FILE_MATCH={ann_stats['FILE_MATCH']}")
