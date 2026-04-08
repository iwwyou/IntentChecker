"""
RQ3: Run NumScout on all 75 cases.
Usage: C:/Users/isjeon/NumScout/venv/Scripts/python.exe run_numscout.py [--case CASE_ID]

NumScout analyzes single .sol files via symbolic execution on bytecode.
- NumScout cases: use original single-file contracts directly
- Web3Bugs cases: flatten via hardhat, then analyze

Requires:
  - NumScout venv: C:/Users/isjeon/NumScout/venv
  - NumScout code: C:/Users/isjeon/NumScout
  - solc binaries: C:/Users/isjeon/.solc-select/artifacts/solc-{version}/solc-{version}.exe
  - Web3Bugs projects: C:/Users/isjeon/Web3Bugs/contracts/{N}/ (with node_modules)
"""

import csv
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent.parent
NUMSCOUT_DIR = Path("C:/Users/isjeon/NumScout")
NUMSCOUT_VENV_PYTHON = NUMSCOUT_DIR / "venv/Scripts/python.exe"
SOLC_ARTIFACTS = Path("C:/Users/isjeon/.solc-select/artifacts")
WEB3BUGS_DIR = Path("C:/Users/isjeon/Web3Bugs/contracts")
CASE_MAPPING = SCRIPT_DIR / "case_mapping.csv"
OUTPUT_DIR = SCRIPT_DIR / "outputs" / "numscout"
WORK_DIR = SCRIPT_DIR / "workdir_numscout"
GLOBAL_TIMEOUT = 1800  # seconds


def switch_solc(version: str):
    """Copy the correct solc binary into the NumScout venv."""
    solc_exe = SOLC_ARTIFACTS / f"solc-{version}" / f"solc-{version}.exe"
    target = NUMSCOUT_DIR / "venv" / "Scripts" / "solc.exe"
    if not solc_exe.exists():
        print(f"  [ERROR] solc {version} not found at {solc_exe}")
        return False
    shutil.copy2(solc_exe, target)
    return True


def flatten_sol(contest_number: str, project_root: str, target_sol: str, solc_version: str) -> str:
    """Flatten a multi-file Solidity project into a single .sol file."""
    web3bugs_project = WEB3BUGS_DIR / project_root
    # Derive relative path of target .sol within the project
    # target_sol format: "45/contracts/market/UToken.sol"
    # project_root format: "45"
    rel_sol = target_sol.replace(f"{contest_number}/", "", 1) if contest_number else target_sol

    flat_file = WORK_DIR / f"{Path(target_sol).stem}_flat.sol"

    env = os.environ.copy()
    env["INFURA_ID"] = "dummy"
    env["MNEMONIC_TEST"] = "test test test test test test test test test test test junk"
    env["ALCHEMY_API_KEY"] = "dummy"
    env["PRIVATE_KEY"] = "0x0000000000000000000000000000000000000000000000000000000000000001"
    env["ETHERSCAN_API_KEY"] = "dummy"
    env["PYTHONUTF8"] = "1"

    # Try hardhat flatten
    try:
        result = subprocess.run(
            ["npx", "hardhat", "flatten", rel_sol],
            cwd=str(web3bugs_project),
            capture_output=True, timeout=120, env=env
        )
        if result.returncode == 0 and len(result.stdout) > 100:
            content = result.stdout.decode("utf-8", errors="replace")
            # Remove duplicate SPDX and pragma
            lines = content.splitlines(keepends=True)
            seen_spdx = False
            seen_pragma = False
            out = []
            for l in lines:
                if "SPDX-License" in l:
                    if seen_spdx:
                        continue
                    seen_spdx = True
                if l.strip().startswith("pragma solidity"):
                    if seen_pragma:
                        continue
                    seen_pragma = True
                out.append(l)
            flat_file.write_text("".join(out), encoding="utf-8")
            return str(flat_file)
    except Exception as e:
        print(f"  [WARN] hardhat flatten failed: {e}")

    return None


def run_numscout(sol_file: str, contract_name: str, solc_version: str, output_file: str) -> dict:
    """Run NumScout on a single .sol file."""
    work = WORK_DIR / f"run_{contract_name}"
    work.mkdir(parents=True, exist_ok=True)

    # Copy sol file to work dir (NumScout needs to run from sol file's directory)
    sol_basename = Path(sol_file).name
    target = work / sol_basename
    shutil.copy2(sol_file, target)

    start = time.time()
    try:
        result = subprocess.run(
            [str(NUMSCOUT_VENV_PYTHON), str(NUMSCOUT_DIR / "tool.py"),
             "-s", sol_basename, "-cnames", contract_name,
             "-j", "-sv", solc_version, "-glt", str(GLOBAL_TIMEOUT)],
            cwd=str(work),
            capture_output=True, timeout=GLOBAL_TIMEOUT + 60,
            env={**os.environ, "PYTHONUTF8": "1"}
        )
    except subprocess.TimeoutExpired:
        elapsed = time.time() - start
        return {"error": "timeout", "time": elapsed}

    elapsed = time.time() - start

    # Find result JSON (filename uses _ instead of : on Windows)
    result_file = work / f"{sol_basename}_{contract_name}.json"
    if result_file.exists():
        with open(result_file, encoding="utf-8") as f:
            data = json.load(f)
        data["_elapsed_wall"] = elapsed
        # Copy to output
        shutil.copy2(result_file, output_file)
        return data
    else:
        stderr = result.stderr.decode("utf-8", errors="replace")[-500:]
        return {"error": "no_output", "time": elapsed, "stderr": stderr}


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Run NumScout on RQ3 cases")
    parser.add_argument("--case", help="Run single case by ID")
    parser.add_argument("--source", choices=["numscout", "web3bugs", "all"], default="all")
    parser.add_argument("--run", help="Run name (output subdirectory)", default="run1")
    args = parser.parse_args()

    output_dir = SCRIPT_DIR / "outputs" / "numscout" / args.run
    output_dir.mkdir(parents=True, exist_ok=True)
    WORK_DIR.mkdir(parents=True, exist_ok=True)

    with open(CASE_MAPPING, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        cases = list(reader)

    if args.case:
        cases = [c for c in cases if c["case_id"] == args.case]
    elif args.source != "all":
        cases = [c for c in cases if c["source"] == args.source]

    results_summary = []

    for case in cases:
        cid = case["case_id"]
        source = case["source"]
        contract = case["contract_name"]
        solc_ver = case["solc_version"]
        output_file = output_dir / f"{cid}.json"

        if output_file.exists():
            print(f"[SKIP] {cid} — already has result")
            continue

        print(f"[RUN] {cid} (contract={contract}, solc={solc_ver})")

        if not switch_solc(solc_ver):
            results_summary.append({"case_id": cid, "result": "solc_missing"})
            continue

        if source == "numscout":
            sol_file = str(PROJECT_ROOT / case["target_sol_file"])
            if not Path(sol_file).exists():
                print(f"  [ERROR] File not found: {sol_file}")
                results_summary.append({"case_id": cid, "result": "file_not_found"})
                continue
        else:
            # Web3Bugs: need to flatten
            sol_file = flatten_sol(
                case["contest_number"], case["project_root"],
                case["target_sol_file"], solc_ver
            )
            if not sol_file:
                print(f"  [ERROR] Flatten failed for {cid}")
                results_summary.append({"case_id": cid, "result": "flatten_failed"})
                continue

        data = run_numscout(sol_file, contract, solc_ver, str(output_file))

        if "error" in data:
            t = data.get("time", 0)
            print(f"  [ERROR] {data['error']} ({t:.1f}s)")
            entry = {"case_id": cid, "tool": "numscout", "detected": False,
                     "detected_patterns": [], "time": t, "status": data["error"]}
        else:
            defects = [k for k, v in data.get("bool_defect", {}).items() if v]
            detected = len(defects) > 0
            t = float(data.get("time", 0))
            print(f"  [{'DETECTED' if detected else 'NONE'}] patterns={defects} time={t:.1f}s")
            entry = {"case_id": cid, "tool": "numscout", "detected": detected,
                     "detected_patterns": defects, "time": t, "status": "ok"}

        results_summary.append(entry)

        # Write summary after each case (incremental save)
        summary_file = output_dir / "summary.json"
        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump(results_summary, f, indent=2, ensure_ascii=False)

    print(f"\nDone. {len(results_summary)} cases processed.")
    print(f"Summary: {summary_file}")


if __name__ == "__main__":
    main()
