"""Run ScType on RQ3 cases.

The ScType tree and its venv are installed by evaluation/RQ3/setup_rq3_tools.sh
into evaluation/RQ3/tools/sctype/. Type-annotation files are committed under
evaluation/RQ3/sctype_typefiles/ (copied from ScType's Benchmark_subset/).

Env vars:
  SOLC_ARTIFACTS       — solc-select artifacts dir (default: ~/.solc-select/artifacts)
  WEB3BUGS_CONTRACTS   — Web3Bugs contracts dir (default: evaluation/RQ3/web3bugs/contracts
                         if present, else ~/Web3Bugs/contracts)
"""
import csv
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

# ── Paths ──────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
IS_WINDOWS = platform.system() == "Windows"


def _default_solc_artifacts() -> Path:
    return Path.home() / ".solc-select" / "artifacts"


def _default_web3bugs_contracts() -> Path:
    in_repo = SCRIPT_DIR / "web3bugs" / "contracts"
    if in_repo.exists():
        return in_repo
    return Path.home() / "Web3Bugs" / "contracts"


def _venv_bin_dir(tool_dir: Path) -> Path:
    """Return the venv's bin/Scripts directory (platform-aware)."""
    if IS_WINDOWS:
        return tool_dir / "venv" / "Scripts"
    return tool_dir / "venv" / "bin"


SCTYPE_DIR = SCRIPT_DIR / "tools" / "sctype"
SCTYPE_VENV = _venv_bin_dir(SCTYPE_DIR)
SCTYPE_SLITHER = SCTYPE_VENV / ("slither.exe" if IS_WINDOWS else "slither")
TYPEFILE_ROOT = SCRIPT_DIR / "sctype_typefiles"
SOLC_DIR = Path(os.environ.get("SOLC_ARTIFACTS", str(_default_solc_artifacts())))
WEB3BUGS_ROOT = Path(os.environ.get("WEB3BUGS_CONTRACTS", str(_default_web3bugs_contracts())))

OUTPUT_BASE = SCRIPT_DIR / "outputs" / "sctype"
CASE_MAPPING_CSV = SCRIPT_DIR / "case_mapping.csv"

# ── ScType case mapping ────────────────────────────────────────────
# Each case maps to its ScType configuration.
# hardhat_root: directory containing hardhat.config.js (CWD for slither)
# typefile_dir: relative path under TYPEFILE_ROOT where type files are
# solc: solc version required
#
# NOTE: web3bugs_45_H_01 removed -- ScType benchmark's PoolTogether
# (IdleYieldSource) does NOT overlap with Web3Bugs contest 45 (Union Finance / UToken).
SCTYPE_CASES = {
    "web3bugs_5_H_07": {
        "typefile_dir": "Vader_Protocol_p1/vader-protocol/contracts",
        "hardhat_root": "5/vader-protocol",
        "solc": "0.8.3",
    },
    "web3bugs_5_H_08": {
        "typefile_dir": "Vader_Protocol_p1/vader-protocol/contracts",
        "hardhat_root": "5/vader-protocol",
        "solc": "0.8.3",
    },
    "web3bugs_47_H_02": {
        "typefile_dir": "Badger_Dao_p2/contracts",
        "hardhat_root": "47",
        "solc": "0.6.12",
    },
    "web3bugs_56_H_02": {
        "typefile_dir": "yAxis_p2/contracts/v3/alchemix/libraries/alchemist",
        "hardhat_root": "56",
        "solc": "0.6.12",
    },
    "web3bugs_60_H_01": {
        "typefile_dir": "Perennial/protocol/contracts/collateral/types",
        "hardhat_root": "60/protocol",
        "solc": "0.8.10",
    },
    "web3bugs_70_H_10": {
        "typefile_dir": "Vader_Protocol_p3/contracts/lbt",
        "hardhat_root": "70",
        "solc": "0.8.9",
    },
    "web3bugs_101_H_01": {
        "typefile_dir": "Sublime_p2/sublime-v1/contracts/PooledCreditLine",
        "hardhat_root": "101/sublime-v1",
        "solc": "0.7.6",
    },
}


def load_case_mapping():
    """Load case_mapping.csv to get target function info per case."""
    mapping = {}
    with open(CASE_MAPPING_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            mapping[row["case_id"]] = row
    return mapping


def _find_solc_binary(version: str):
    root = SOLC_DIR / f"solc-{version}"
    for c in [root / f"solc-{version}.exe", root / f"solc-{version}", root / "solc.exe", root / "solc"]:
        if c.exists():
            return c
    return None


def switch_solc(version: str):
    """Copy the right solc binary into the ScType venv so slither picks it up.

    Also tries ``solc-select use`` for hosts where solc-select is on PATH.
    """
    solc_bin = _find_solc_binary(version)
    if solc_bin is None:
        print(
            f"  [WARN] solc {version} not found under {SOLC_DIR}. "
            f"Run `solc-select install {version}` or set SOLC_ARTIFACTS."
        )
        return False

    solc_select = shutil.which("solc-select")
    if solc_select:
        try:
            subprocess.run([solc_select, "use", version], check=False, capture_output=True)
        except Exception as e:
            print(f"  [WARN] solc-select use {version} failed: {e}")

    target = SCTYPE_VENV / ("solc.exe" if IS_WINDOWS else "solc")
    extra = os.environ.get("SOLC_COPY_TARGETS", "")
    targets = [target]
    if extra:
        for p in extra.split(os.pathsep):
            p = p.strip()
            if p:
                targets.append(Path(p))
    for t in targets:
        try:
            t.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(solc_bin, t)
            if not IS_WINDOWS:
                t.chmod(0o755)
        except Exception as e:
            print(f"  [WARN] Failed to copy solc to {t}: {e}")
    print(f"  solc switched to {version}")
    return True


def copy_type_files(typefile_dir: str, target_dir: Path):
    """Copy type files from Benchmark_subset to the target directory."""
    src_dir = TYPEFILE_ROOT / typefile_dir
    copied = []
    if not src_dir.exists():
        print(f"  [WARN] Type file dir not found: {src_dir}")
        return copied
    for f in src_dir.iterdir():
        if f.name.endswith("_types.txt") or f.name.endswith("_ftypes.txt"):
            dst = target_dir / f.name
            shutil.copy2(f, dst)
            copied.append(f.name)
    return copied


def remove_type_files(target_dir: Path):
    """Clean up type files after run."""
    if not target_dir.exists():
        return
    for f in target_dir.iterdir():
        if f.name.endswith("_types.txt") or f.name.endswith("_ftypes.txt"):
            f.unlink()


def parse_warnings(output: str):
    """Parse ScType warning lines from combined stdout+stderr."""
    warnings = []
    func_count = 0
    annotation_count = 0
    for line in output.split("\n"):
        stripped = line.strip()
        if "typecheck error" in stripped.lower():
            warnings.append(stripped)
        if "Function count:" in stripped:
            try:
                func_count = int(stripped.split(":")[-1].strip())
            except ValueError:
                pass
        if "Annotation count:" in stripped:
            try:
                annotation_count = int(stripped.split(":")[-1].strip())
            except ValueError:
                pass
    return warnings, func_count, annotation_count


def warning_to_finding(warning_line: str, sol_file: str):
    """Convert a ScType warning line into a GPTScan-like finding dict.

    Example warning:
      typecheck error: Var name: TMP_1066 Func name: calcAsymmetricShare
        in NEW VARIABLE numerator = ((part1 * part2) - part3) + part4
    """
    # Extract function name
    func_match = re.search(r"Func name:\s*(\w+)", warning_line)
    func_name = func_match.group(1) if func_match else "unknown"

    # Extract the expression / context after "in ..."
    expr_match = re.search(r"\bin\s+(.+)$", warning_line, re.IGNORECASE)
    expression = expr_match.group(1).strip() if expr_match else warning_line

    return {
        "code": "typecheck-error",
        "severity": "HIGH",
        "title": f"ScType typecheck error in {func_name}",
        "description": warning_line,
        "recommendation": "Review the arithmetic expression for potential type inconsistency.",
        "affectedFiles": [
            {
                "filePath": sol_file,
                "function": func_name,
                "expression": expression,
                "range": {"start": {"line": 0}, "end": {"line": 0}},
                "highlights": [],
            }
        ],
    }


def check_detection(warnings, target_functions):
    """Check if any warning mentions the target function(s).

    target_functions may contain semicolons for multiple functions.
    Returns (detected: bool, matching_warnings: list).
    """
    if not target_functions:
        return False, []
    funcs = [f.strip() for f in target_functions.split(";")]
    matching = []
    for w in warnings:
        for func in funcs:
            if func.lower() in w.lower():
                matching.append(w)
                break
    return len(matching) > 0, matching


def run_sctype(case_id: str, case_cfg: dict, case_meta: dict, output_dir: Path):
    """Run ScType on a single case and produce GPTScan-compatible output."""
    print(f"\n{'='*60}")
    print(f"[ScType] {case_id}")
    print(f"{'='*60}")

    result_path = output_dir / f"{case_id}.json"
    meta_path = output_dir / f"{case_id}.json.metadata.json"
    if result_path.exists():
        print(f"  Already done, skipping.")
        return

    hardhat_root = WEB3BUGS_ROOT / case_cfg["hardhat_root"]
    solc_ver = case_cfg["solc"]
    target_sol = case_meta.get("target_sol_file", "")
    target_func = case_meta.get("function_name", "")

    if not hardhat_root.exists():
        print(f"  [ERROR] Hardhat root not found: {hardhat_root}")
        json_save(result_path, {
            "version": "1.0.0", "success": False,
            "message": f"Hardhat root not found: {hardhat_root}",
            "results": [],
        })
        json_save(meta_path, {"used_time": 0, "error": "hardhat_root_not_found"})
        return

    # Switch solc
    switch_solc(solc_ver)

    # Ensure hardhat compile has been done
    artifacts_dir = hardhat_root / "artifacts" / "build-info"
    if not artifacts_dir.exists():
        print(f"  Compiling with hardhat...")
        npx_cmd = shutil.which("npx") or (shutil.which("npx.cmd") if IS_WINDOWS else None) or "npx"
        compile_proc = subprocess.run(
            [npx_cmd, "hardhat", "compile"],
            cwd=str(hardhat_root),
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=300,
            env={**os.environ, "HARDHAT_NETWORK": "hardhat"},
            shell=IS_WINDOWS,
        )
        if compile_proc.returncode != 0:
            print(f"  [WARN] Hardhat compile issue: {compile_proc.stderr[-200:]}")

    # Copy type files to hardhat_root (CWD for slither)
    # ScType looks for type files in CWD
    copied = copy_type_files(case_cfg["typefile_dir"], hardhat_root)
    print(f"  Type files copied to {hardhat_root}: {copied}")

    # Run slither --detect tcheck from hardhat_root with "." as target
    cmd = [
        str(SCTYPE_SLITHER),
        "--detect", "tcheck",
        "--compile-force-framework", "hardhat",
        "--hardhat-ignore-compile",
        ".",
    ]
    env = os.environ.copy()
    env["PATH"] = str(SCTYPE_VENV) + os.pathsep + env.get("PATH", "")

    print(f"  Running: {' '.join(cmd)}")
    print(f"  CWD: {hardhat_root}")
    print(f"  Target function: {target_func}")

    start = time.time()
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(hardhat_root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=600,
            env=env,
        )
        elapsed = time.time() - start
        combined = (proc.stdout or "") + "\n" + (proc.stderr or "")

        warnings, func_count, annotation_count = parse_warnings(combined)

        # Resolve full path for the target .sol file
        full_sol = str(WEB3BUGS_ROOT / target_sol) if target_sol else ""

        # Build GPTScan-like individual JSON
        findings = [warning_to_finding(w, full_sol) for w in warnings]
        detected, matching = check_detection(warnings, target_func)

        individual_json = {
            "version": "1.0.0",
            "success": True,
            "message": None,
            "results": findings,
        }

        metadata_json = {
            "used_time": round(elapsed, 2),
            "annotation_count": annotation_count,
            "function_count": func_count,
            "n_warnings": len(warnings),
            "returncode": proc.returncode,
        }

        json_save(result_path, individual_json)
        json_save(meta_path, metadata_json)

        print(f"  Done in {elapsed:.1f}s | Warnings: {len(warnings)} | "
              f"Funcs: {func_count} | Annotations: {annotation_count}")
        print(f"  Detected target ({target_func}): {detected}")
        for w in warnings[:10]:
            print(f"    {w}")

    except subprocess.TimeoutExpired:
        elapsed = time.time() - start
        json_save(result_path, {
            "version": "1.0.0", "success": False,
            "message": "Timeout", "results": [],
        })
        json_save(meta_path, {"used_time": round(elapsed, 2), "error": "timeout"})
        print(f"  TIMEOUT after {elapsed:.1f}s")
    except Exception as e:
        elapsed = time.time() - start
        json_save(result_path, {
            "version": "1.0.0", "success": False,
            "message": str(e), "results": [],
        })
        json_save(meta_path, {"used_time": round(elapsed, 2), "error": str(e)})
        print(f"  ERROR: {e}")
    finally:
        # Clean up type files from hardhat_root
        try:
            remove_type_files(hardhat_root)
        except Exception:
            pass


def build_summary(output_dir: Path, case_mapping: dict):
    """Build unified summary.json from individual result files."""
    summary = []
    for case_id in SCTYPE_CASES:
        result_path = output_dir / f"{case_id}.json"
        meta_path = output_dir / f"{case_id}.json.metadata.json"
        if not result_path.exists():
            continue

        with open(result_path, encoding="utf-8") as f:
            result = json.load(f)
        meta = {}
        if meta_path.exists():
            with open(meta_path, encoding="utf-8") as f:
                meta = json.load(f)

        target_func = case_mapping.get(case_id, {}).get("function_name", "")
        warnings = [r["description"] for r in result.get("results", [])]
        detected, _ = check_detection(warnings, target_func)

        # Collect all pattern codes from findings
        detected_patterns = []
        if detected:
            detected_patterns = [r["code"] for r in result.get("results", [])
                                 if any(fn.strip().lower() in r.get("description", "").lower()
                                        for fn in target_func.split(";") if fn.strip())]

        entry = {
            "case_id": case_id,
            "tool": "sctype",
            "detected": detected,
            "detected_patterns": detected_patterns if detected_patterns else
                                 (["typecheck-error"] if detected else []),
            "findings": warnings,
            "time": meta.get("used_time", 0),
            "status": "ok" if result.get("success") else
                      meta.get("error", "error"),
        }
        summary.append(entry)

    json_save(output_dir / "summary.json", summary)
    return summary


def json_save(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Run ScType on RQ3 cases")
    parser.add_argument("--run", help="Run name (output subdirectory)", default="run1")
    parser.add_argument("--case", help="Run a single case by case_id")
    parser.add_argument("--force", action="store_true",
                        help="Re-run even if output already exists")
    args = parser.parse_args()

    output_dir = OUTPUT_BASE / args.run
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load case mapping for target function info
    case_mapping = load_case_mapping()

    if args.force:
        # Remove existing outputs so they get re-run
        cases_to_clear = [args.case] if args.case else list(SCTYPE_CASES.keys())
        for cid in cases_to_clear:
            for suffix in [".json", ".json.metadata.json"]:
                p = output_dir / f"{cid}{suffix}"
                if p.exists():
                    p.unlink()

    if args.case:
        if args.case in SCTYPE_CASES:
            run_sctype(args.case, SCTYPE_CASES[args.case],
                       case_mapping.get(args.case, {}), output_dir)
        else:
            print(f"Case {args.case} not in ScType mapping. "
                  f"Available: {list(SCTYPE_CASES.keys())}")
    else:
        for case_id, case_cfg in SCTYPE_CASES.items():
            run_sctype(case_id, case_cfg,
                       case_mapping.get(case_id, {}), output_dir)

    # Build summary
    summary = build_summary(output_dir, case_mapping)

    print(f"\n{'='*60}")
    print("=== ScType run complete ===")
    print(f"{'='*60}")
    print(f"Total cases: {len(summary)}")
    for entry in summary:
        det = "DETECTED" if entry["detected"] else "not_detected"
        t = entry.get("time", "?")
        n = len(entry.get("findings", []))
        print(f"  {entry['case_id']:<25} {det:<15} warnings={n:<4} time={t}s")


if __name__ == "__main__":
    main()
