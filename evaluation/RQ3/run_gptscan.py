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

# Force stdout/stderr to UTF-8 on Windows (avoids cp949 encoding errors)
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

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
    """Copy the correct solc binary into ALL locations where subprocess might find it.

    Python subprocess inherits the parent's PATH, and when run_gptscan.py is invoked
    from a non-activated shell, the GPTScan venv's Scripts/ is not in PATH. We therefore
    overwrite solc.exe in every candidate PATH location so the subprocess always picks
    up the correct version regardless of PATH order.
    """
    solc_exe = SOLC_ARTIFACTS / f"solc-{version}" / f"solc-{version}.exe"
    if not solc_exe.exists():
        print(f"  [ERROR] solc {version} not found at {solc_exe}")
        return False

    targets = [
        Path("C:/Users/isjeon/GPTScan/venv/Scripts/solc.exe"),
        Path("C:/Users/isjeon/AppData/Local/Programs/Python/Python310/Scripts/solc.exe"),
    ]
    for target in targets:
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(solc_exe, target)
        except Exception as e:
            print(f"  [WARN] failed to copy solc to {target}: {e}")
    return True


def disable_foundry_config(project_root: str):
    """Rename foundry.toml so crytic-compile detects the project as Hardhat, not Foundry.

    crytic-compile's framework detection priority is Foundry > Hardhat. If foundry.toml
    exists, crytic-compile looks for `out/build-info/` (Foundry output) instead of
    `artifacts/build-info/` (Hardhat output). Since we use Hardhat to compile all
    projects for consistency, we need to hide foundry.toml so Hardhat wins detection.
    """
    project_dir = WEB3BUGS_DIR / project_root
    foundry_toml = project_dir / "foundry.toml"
    disabled = project_dir / "foundry.toml.disabled"
    if foundry_toml.exists() and not disabled.exists():
        foundry_toml.rename(disabled)
        print(f"  [disable-foundry] {foundry_toml} -> foundry.toml.disabled")


def compile_hardhat(project_root: str) -> bool:
    """Run hardhat compile on a Web3Bugs project."""
    project_dir = WEB3BUGS_DIR / project_root
    # Ensure crytic-compile uses Hardhat (not Foundry) for this project
    disable_foundry_config(project_root)
    artifacts_dir = project_dir / "artifacts"
    if artifacts_dir.exists() and any(artifacts_dir.rglob("*.json")):
        return True  # Already compiled

    env = os.environ.copy()
    # Set common dummy env vars to prevent hardhat config parse errors
    dummy_vars = {
        "INFURA_ID": "dummy", "INFURA_KEY": "dummy", "INFURA_API_KEY": "dummy",
        "ALCHEMY_API_KEY": "dummy", "ALCHEMY_KEY": "dummy", "ALCHEMY_URL": "https://dummy",
        "MNEMONIC": "test test test test test test test test test test test junk",
        "MNEMONIC_TEST": "test test test test test test test test test test test junk",
        "PRIVATE_KEY": "0x0000000000000000000000000000000000000000000000000000000000000001",
        "DEPLOYER_PRIVATE_KEY": "0x0000000000000000000000000000000000000000000000000000000000000001",
        "ETHERSCAN_API_KEY": "dummy", "COINMARKETCAP_API_KEY": "dummy",
        "DEV": "0x0000000000000000000000000000000000000000000000000000000000000001",
        "DEV_BOT": "0x0000000000000000000000000000000000000000000000000000000000000001",
        "REF": "0x0000000000000000000000000000000000000000000000000000000000000001",
        "kovan": "https://kovan.infura.io/v3/dummy",
        "PYTHONUTF8": "1",
    }
    env.update(dummy_vars)

    try:
        result = subprocess.run(
            ["npx.cmd", "hardhat", "compile"],
            cwd=str(project_dir),
            capture_output=True, timeout=180, env=env, shell=True
        )
        if result.returncode != 0:
            stderr = result.stderr.decode("utf-8", errors="replace")[-300:]
            print(f"  [WARN] hardhat compile error: {stderr.strip()}")
        return result.returncode == 0
    except Exception as e:
        print(f"  [WARN] hardhat compile failed: {e}")
        return False


def run_gptscan(source_dir: str, output_file: str, api_key: str) -> dict:
    """Run GPTScan on a source directory."""
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    # Ensure GPTScan venv's Scripts dir (with the current solc.exe) is first in PATH
    venv_scripts = str(Path("C:/Users/isjeon/GPTScan/venv/Scripts"))
    env["PATH"] = venv_scripts + os.pathsep + env.get("PATH", "")

    start = time.time()
    # Stream subprocess output line-by-line so GPTScan's internal progress is visible
    try:
        proc = subprocess.Popen(
            [str(GPTSCAN_VENV_PYTHON), "-u", "main.py",
             "-s", source_dir,
             "-o", output_file,
             "-k", api_key],
            cwd=str(GPTSCAN_SRC),
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            env=env, bufsize=1, universal_newlines=True, encoding="utf-8", errors="replace"
        )
    except Exception as e:
        elapsed = time.time() - start
        return {"error": f"spawn_failed: {e}", "time": elapsed}

    # Filter noisy lines; only show key progress events
    import re
    NOISE_PATTERNS = [
        r'^\s*[│┌└├┤┬┴─═║╔╗╚╝╠╣╦╩╬]',  # box drawing
        r'^\s*\|',                         # pipe-bordered content
        r'^\s*[.oO0@*#]{3,}',              # ASCII art
        r'^\s*\[04/\d{2}/\d{2}',           # rich log timestamps (already have ours)
    ]
    noise_re = re.compile('|'.join(NOISE_PATTERNS))
    # Important events to show
    KEEP_PATTERNS = [
        r'Loaded \d+ rules',
        r'Compiling',
        r'Compiled \d+',
        r'Scanning',
        r'Starting',
        r'Summary',
        r'Error',
        r'ERROR',
        r'Exception',
        r'Traceback',
        r'Files\s*\|',
        r'Contracts\s*\|',
        r'Functions\s*\|',
        r'Used Time',
        r'Estimated Cost',
    ]
    keep_re = re.compile('|'.join(KEEP_PATTERNS))

    last_heartbeat = start
    last_activity = start
    collected_lines = []
    try:
        while True:
            line = proc.stdout.readline()
            if not line:
                if proc.poll() is not None:
                    break
                # No output, check heartbeat
                now = time.time()
                if now - last_heartbeat > 30:
                    print(f"    [heartbeat] elapsed={now - start:.0f}s / timeout={TIMEOUT}s / idle={now - last_activity:.0f}s")
                    last_heartbeat = now
                if now - start > TIMEOUT:
                    proc.terminate()
                    try:
                        proc.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                    elapsed = time.time() - start
                    return {"error": "timeout", "time": elapsed}
                time.sleep(0.1)
                continue
            line = line.rstrip()
            last_activity = time.time()
            if line:
                collected_lines.append(line)
                # Only print if it's an important event (not noise)
                if keep_re.search(line) and not noise_re.search(line):
                    print(f"    > {line[:200]}")
            # Periodic heartbeat even when output is flowing
            now = time.time()
            if now - last_heartbeat > 30:
                print(f"    [heartbeat] elapsed={now - start:.0f}s / timeout={TIMEOUT}s")
                last_heartbeat = now
            # Hard timeout
            if now - start > TIMEOUT:
                proc.terminate()
                try:
                    proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    proc.kill()
                elapsed = time.time() - start
                return {"error": "timeout", "time": elapsed}
        proc.wait()
    except Exception as e:
        proc.kill()
        elapsed = time.time() - start
        return {"error": f"stream_failed: {e}", "time": elapsed}

    elapsed = time.time() - start

    if Path(output_file).exists():
        with open(output_file, encoding="utf-8") as f:
            data = json.load(f)
        data["_elapsed_wall"] = elapsed
        return data
    else:
        tail = "\n".join(collected_lines[-10:])
        return {"error": "no_output", "time": elapsed, "tail": tail}


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Run GPTScan on RQ3 cases")
    parser.add_argument("--case", help="Run single case by ID")
    parser.add_argument("--source", choices=["numscout", "web3bugs", "all"], default="all")
    # TODO: Remove this key before committing to public repo
    _DEFAULT_KEY = "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"
    parser.add_argument("--key", help="OpenAI API key", default=os.environ.get("OPENAI_API_KEY", _DEFAULT_KEY))
    parser.add_argument("--run", help="Run name (output subdirectory)", default="run1")
    parser.add_argument("--annotated-only", action="store_true", help="Run only 20 annotated cases")
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
    elif args.annotated_only:
        cases = [c for c in cases if c["status"] == "annotated"]
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

        import datetime
        print(f"[RUN] {cid} (contract={contract}, solc={solc_ver}) @ {datetime.datetime.now().strftime('%H:%M:%S')}")

        print(f"  [1/4] Switching solc to {solc_ver}...")
        if not switch_solc(solc_ver):
            results_summary.append({"case_id": cid, "result": "solc_missing"})
            continue

        if source == "numscout":
            print(f"  [2/4] Preparing single-file input...")
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

            if project_root in compiled_projects:
                print(f"  [2/4] Using pre-compiled {project_root}")
            else:
                print(f"  [2/4] Compiling {project_root} with hardhat...")
                comp_start = time.time()
                if compile_hardhat(project_root):
                    compiled_projects.add(project_root)
                    print(f"  [2/4] Compile OK ({time.time() - comp_start:.1f}s)")
                else:
                    print(f"  [2/4] [WARN] Compile failed, running GPTScan anyway (ANTLR fallback)")

        print(f"  [3/4] Running GPTScan (timeout={TIMEOUT}s)...")
        data = run_gptscan(source_dir, output_file, args.key)
        print(f"  [4/4] GPTScan done")

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
