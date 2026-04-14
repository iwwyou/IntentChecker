"""
RQ3: Run GPTScan on all 75 cases.

GPTScan analyzes source directories using GPT + static analysis.
- NumScout cases: single .sol file in a temp folder
- Web3Bugs cases: full project directory (needs hardhat compile first)

Requires (installed by setup_rq3_tools.sh):
  - GPTScan tree at evaluation/RQ3/tools/gptscan/ with its own venv
Requires on the host:
  - solc binaries installed via solc-select (default: ~/.solc-select/artifacts,
    override with $SOLC_ARTIFACTS)
  - Web3Bugs contracts dir (default: evaluation/RQ3/web3bugs/contracts if the
    setup script was run with the ``web3bugs`` target, otherwise ~/Web3Bugs/contracts;
    override with $WEB3BUGS_CONTRACTS)
  - OpenAI API key: resolved from (in order) the ``--key`` flag, the
    ``OPENAI_API_KEY`` environment variable, or an interactive
    ``getpass()`` prompt. No hardcoded default is shipped.
"""

import csv
import json
import os
import platform
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
IS_WINDOWS = platform.system() == "Windows"


def _tool_venv_python(tool_dir: Path) -> Path:
    """Return the python executable inside a tool's venv on either Unix or Windows."""
    candidates = [
        tool_dir / "venv" / "Scripts" / "python.exe",
        tool_dir / "venv" / "bin" / "python",
    ]
    for c in candidates:
        if c.exists():
            return c
    return candidates[0]  # best guess; we'll surface a clear error at invocation


def _default_solc_artifacts() -> Path:
    return Path.home() / ".solc-select" / "artifacts"


def _default_web3bugs_contracts() -> Path:
    in_repo = SCRIPT_DIR / "web3bugs" / "contracts"
    if in_repo.exists():
        return in_repo
    return Path.home() / "Web3Bugs" / "contracts"


def _which(name: str) -> str:
    hit = shutil.which(name)
    if hit:
        return hit
    if IS_WINDOWS:
        hit = shutil.which(name + ".cmd")
        if hit:
            return hit
    return name


GPTSCAN_DIR = SCRIPT_DIR / "tools" / "gptscan"
GPTSCAN_SRC = GPTSCAN_DIR / "src"
GPTSCAN_VENV_PYTHON = _tool_venv_python(GPTSCAN_DIR)
GPTSCAN_VENV_DIR = GPTSCAN_DIR / "venv"
SOLC_ARTIFACTS = Path(os.environ.get("SOLC_ARTIFACTS", str(_default_solc_artifacts())))
WEB3BUGS_DIR = Path(os.environ.get("WEB3BUGS_CONTRACTS", str(_default_web3bugs_contracts())))
NPX = _which("npx")
CASE_MAPPING = SCRIPT_DIR / "case_mapping.csv"
OUTPUT_DIR = SCRIPT_DIR / "outputs" / "gptscan"
WORK_DIR = SCRIPT_DIR / "workdir_gptscan"
TIMEOUT = 1800  # seconds per case


def _find_solc_binary(version: str) -> Path | None:
    root = SOLC_ARTIFACTS / f"solc-{version}"
    for c in [root / f"solc-{version}.exe", root / f"solc-{version}"]:
        if c.exists():
            return c
    return None


def switch_solc(version: str):
    """Mirror the versioned solc binary into the GPTScan venv so the subprocess picks
    it up regardless of the caller's PATH. Also tries ``solc-select use`` for
    portability on hosts where it's installed.

    SOLC_COPY_TARGETS (pathsep-separated) can be set to copy solc into extra
    locations, e.g. when a site-wide Python Scripts dir is on PATH.
    """
    solc_bin = _find_solc_binary(version)
    if solc_bin is None:
        print(
            f"  [ERROR] solc {version} not found under {SOLC_ARTIFACTS}. "
            f"Run `solc-select install {version}` or set SOLC_ARTIFACTS."
        )
        return False

    solc_select = shutil.which("solc-select")
    if solc_select:
        try:
            subprocess.run(
                [solc_select, "use", version], check=False, capture_output=True
            )
        except Exception as e:
            print(f"  [WARN] solc-select use {version} failed: {e}")

    if IS_WINDOWS:
        targets = [GPTSCAN_VENV_DIR / "Scripts" / "solc.exe"]
    else:
        targets = [GPTSCAN_VENV_DIR / "bin" / "solc"]
    extra = os.environ.get("SOLC_COPY_TARGETS", "")
    if extra:
        for p in extra.split(os.pathsep):
            p = p.strip()
            if p:
                targets.append(Path(p))

    for target in targets:
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(solc_bin, target)
            if not IS_WINDOWS:
                target.chmod(0o755)
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
            [NPX, "hardhat", "compile"],
            cwd=str(project_dir),
            capture_output=True, timeout=180, env=env, shell=IS_WINDOWS
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
    # Ensure the GPTScan venv's bin/Scripts dir (with the current solc) is first in PATH
    if IS_WINDOWS:
        venv_bin = str(GPTSCAN_VENV_DIR / "Scripts")
    else:
        venv_bin = str(GPTSCAN_VENV_DIR / "bin")
    env["PATH"] = venv_bin + os.pathsep + env.get("PATH", "")

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


def _resolve_api_key(cli_key: str | None) -> str:
    """Resolve the OpenAI API key from (in priority order):
      1. the ``--key`` CLI flag
      2. the ``OPENAI_API_KEY`` environment variable
      3. an interactive getpass() prompt (stdin must be a TTY)

    Never falls back to a hardcoded default.
    """
    key = cli_key or os.environ.get("OPENAI_API_KEY", "")
    if key:
        return key.strip()
    if not sys.stdin.isatty():
        print(
            "ERROR: OpenAI API key required.\n"
            "       Pass it with --key sk-... or export OPENAI_API_KEY before running.\n"
            "       (stdin is not a TTY, so an interactive prompt is unavailable.)",
            file=sys.stderr,
        )
        sys.exit(1)
    try:
        import getpass
        key = getpass.getpass("Enter your OpenAI API key (input hidden): ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\nCancelled.", file=sys.stderr)
        sys.exit(1)
    if not key:
        print("ERROR: no OpenAI API key provided.", file=sys.stderr)
        sys.exit(1)
    return key


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Run GPTScan on RQ3 cases")
    parser.add_argument("--case", help="Run single case by ID")
    parser.add_argument("--source", choices=["numscout", "web3bugs", "all"], default="all")
    parser.add_argument(
        "--key",
        help="OpenAI API key (falls back to $OPENAI_API_KEY, then an interactive prompt)",
        default=None,
    )
    parser.add_argument("--run", help="Run name (output subdirectory)", default="run1")
    parser.add_argument("--annotated-only", action="store_true", help="Run only 20 annotated cases")
    args = parser.parse_args()

    args.key = _resolve_api_key(args.key)

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
