"""
RQ3: Run GPTScan on all 75 cases.
Usage: C:/Users/isjeon/GPTScan/venv/Scripts/python.exe run_gptscan.py [--case CASE_ID]

GPTScan analyzes source directories using GPT + static analysis.
- NumScout cases: single .sol file in a temp folder
- Web3Bugs cases: full project directory (needs hardhat compile first)

Requires:
  - GPTScan venv: C:/Users/isjeon/GPTScan/venv
  - GPTScan code: C:/Users/isjeon/GPTScan/src
  - solc binaries: C:/Users/isjeon/.solc-select/artifacts/solc-{version}/solc-{version}.exe
  - Web3Bugs projects: C:/Users/isjeon/Web3Bugs/contracts/{N}/ (with node_modules)
  - OpenAI API key (passed via --key or OPENAI_API_KEY env var)
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
GPTSCAN_SRC = Path("C:/Users/isjeon/GPTScan/src")
GPTSCAN_VENV_PYTHON = Path("C:/Users/isjeon/GPTScan/venv/Scripts/python.exe")
SOLC_ARTIFACTS = Path("C:/Users/isjeon/.solc-select/artifacts")
WEB3BUGS_DIR = Path("C:/Users/isjeon/Web3Bugs/contracts")
CASE_MAPPING = SCRIPT_DIR / "case_mapping.csv"
OUTPUT_DIR = SCRIPT_DIR / "outputs" / "gptscan"
WORK_DIR = SCRIPT_DIR / "workdir_gptscan"
TIMEOUT = 1800  # seconds per case


def switch_solc(version: str):
    """Copy the correct solc binary into the GPTScan venv."""
    solc_exe = SOLC_ARTIFACTS / f"solc-{version}" / f"solc-{version}.exe"
    target = Path("C:/Users/isjeon/GPTScan/venv/Scripts/solc.exe")
    if not solc_exe.exists():
        print(f"  [ERROR] solc {version} not found at {solc_exe}")
        return False
    shutil.copy2(solc_exe, target)
    return True


def compile_hardhat(project_root: str) -> bool:
    """Run hardhat compile on a Web3Bugs project."""
    project_dir = WEB3BUGS_DIR / project_root
    artifacts_dir = project_dir / "artifacts"
    if artifacts_dir.exists() and any(artifacts_dir.rglob("*.json")):
        return True  # Already compiled

    env = os.environ.copy()
    env["INFURA_ID"] = "dummy"
    env["MNEMONIC_TEST"] = "test test test test test test test test test test test junk"
    env["ALCHEMY_API_KEY"] = "dummy"
    env["PRIVATE_KEY"] = "0x0000000000000000000000000000000000000000000000000000000000000001"
    env["ETHERSCAN_API_KEY"] = "dummy"
    env["PYTHONUTF8"] = "1"

    try:
        result = subprocess.run(
            ["npx", "hardhat", "compile"],
            cwd=str(project_dir),
            capture_output=True, timeout=120, env=env
        )
        return result.returncode == 0
    except Exception as e:
        print(f"  [WARN] hardhat compile failed: {e}")
        return False


def run_gptscan(source_dir: str, output_file: str, api_key: str) -> dict:
    """Run GPTScan on a source directory."""
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"

    start = time.time()
    try:
        result = subprocess.run(
            [str(GPTSCAN_VENV_PYTHON), "main.py",
             "-s", source_dir,
             "-o", output_file,
             "-k", api_key],
            cwd=str(GPTSCAN_SRC),
            capture_output=True, timeout=TIMEOUT, env=env
        )
    except subprocess.TimeoutExpired:
        elapsed = time.time() - start
        return {"error": "timeout", "time": elapsed}

    elapsed = time.time() - start

    if Path(output_file).exists():
        with open(output_file, encoding="utf-8") as f:
            data = json.load(f)
        data["_elapsed_wall"] = elapsed
        return data
    else:
        stderr = result.stderr.decode("utf-8", errors="replace")[-500:]
        stdout = result.stdout.decode("utf-8", errors="replace")[-500:]
        return {"error": "no_output", "time": elapsed, "stderr": stderr, "stdout": stdout}


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Run GPTScan on RQ3 cases")
    parser.add_argument("--case", help="Run single case by ID")
    parser.add_argument("--source", choices=["numscout", "web3bugs", "all"], default="all")
    parser.add_argument("--key", help="OpenAI API key", default=os.environ.get("OPENAI_API_KEY", ""))
    parser.add_argument("--run", help="Run name (output subdirectory)", default="run1")
    args = parser.parse_args()

    if not args.key:
        print("ERROR: OpenAI API key required. Use --key or set OPENAI_API_KEY env var.")
        sys.exit(1)

    output_dir = SCRIPT_DIR / "outputs" / "gptscan" / args.run
    output_dir.mkdir(parents=True, exist_ok=True)
    WORK_DIR.mkdir(parents=True, exist_ok=True)

    with open(CASE_MAPPING, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        cases = list(reader)

    if args.case:
        cases = [c for c in cases if c["case_id"] == args.case]
    elif args.source != "all":
        cases = [c for c in cases if c["source"] == args.source]

    # Group web3bugs cases by contest to avoid redundant compilation
    compiled_projects = set()
    results_summary = []

    for case in cases:
        cid = case["case_id"]
        source = case["source"]
        contract = case["contract_name"]
        solc_ver = case["solc_version"]
        output_file = str(output_dir / f"{cid}.json")

        if Path(output_file).exists():
            print(f"[SKIP] {cid} — already has result")
            continue

        print(f"[RUN] {cid} (contract={contract}, solc={solc_ver})")

        if not switch_solc(solc_ver):
            results_summary.append({"case_id": cid, "result": "solc_missing"})
            continue

        if source == "numscout":
            # Single file -> put in a temp folder
            sol_file = PROJECT_ROOT / case["target_sol_file"]
            if not sol_file.exists():
                print(f"  [ERROR] File not found: {sol_file}")
                results_summary.append({"case_id": cid, "result": "file_not_found"})
                continue
            case_dir = WORK_DIR / cid
            case_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(sol_file, case_dir / sol_file.name)
            source_dir = str(case_dir)
        else:
            # Web3Bugs: use project directory, compile if needed
            project_root = case["project_root"]
            source_dir = str(WEB3BUGS_DIR / project_root)

            if project_root not in compiled_projects:
                print(f"  Compiling {project_root}...")
                if compile_hardhat(project_root):
                    compiled_projects.add(project_root)
                else:
                    print(f"  [WARN] Compile failed, running GPTScan anyway (ANTLR fallback)")

        data = run_gptscan(source_dir, output_file, args.key)

        if "error" in data:
            t = data.get("time", 0)
            print(f"  [ERROR] {data['error']} ({t:.1f}s)")
            entry = {"case_id": cid, "tool": "gptscan", "detected": False,
                     "detected_patterns": [], "time": t, "status": data["error"]}
        else:
            findings = data.get("results", [])
            patterns = [f.get("code", "unknown") for f in findings] if isinstance(findings, list) else []
            detected = len(patterns) > 0
            t = data.get("_elapsed_wall", 0)
            print(f"  [{'DETECTED' if detected else 'NONE'}] patterns={patterns} time={t:.1f}s")
            entry = {"case_id": cid, "tool": "gptscan", "detected": detected,
                     "detected_patterns": patterns, "time": t, "status": "ok"}

        results_summary.append(entry)

        # Write summary after each case (incremental save)
        summary_file = output_dir / "summary.json"
        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump(results_summary, f, indent=2, ensure_ascii=False)

    print(f"\nDone. {len(results_summary)} cases processed.")
    print(f"Summary: {summary_file}")


if __name__ == "__main__":
    main()
