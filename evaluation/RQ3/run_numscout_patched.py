"""
Re-run NumScout on the library-inlined variants of 51_H_02 and 77_H_01.

The original .sol files for these two cases call ``public``/``external``
library functions that compile to unresolved library placeholders
(``__$<hash>$__``) in the bytecode, on which NumScout's bytecode parser
raises an ``incomplete push instruction`` error before analysis starts.
The variants under ``workdir_numscout_patched/`` rewrite the library
functions as ``internal`` so that solc inlines them into the caller's
bytecode, avoiding the placeholder.

Outputs are written as ``<run>/web3bugs_51_H_02_patched.json`` and
``<run>/web3bugs_77_H_01_patched.json``, mirroring the layout run1
already uses.

Usage:
    .venv/Scripts/python.exe evaluation/RQ3/run_numscout_patched.py --run run2
    .venv/Scripts/python.exe evaluation/RQ3/run_numscout_patched.py --run run3
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from run_numscout import (
    NUMSCOUT_DIR, NUMSCOUT_VENV_PYTHON, GLOBAL_TIMEOUT,
    IS_WINDOWS, switch_solc,
)

BASE = Path(__file__).parent.resolve()
PATCHED_WORKDIR = BASE / "workdir_numscout_patched"

# (case_id, contract_name, solc_version, workdir_subdir, sol_basename)
PATCHED_CASES = [
    ("web3bugs_51_H_02", "Swap",     "0.6.12", "run_Swap",     "Swap_patched.sol"),
    ("web3bugs_77_H_01", "Exchange", "0.8.4",  "run_Exchange", "Exchange_patched.sol"),
]


def run_one(case_id, contract, solc_ver, workdir_name, sol_name, output_file):
    work = PATCHED_WORKDIR / workdir_name
    target = work / sol_name
    if not target.exists():
        print(f"  [ERROR] patched sol not found: {target}")
        return False

    if not switch_solc(solc_ver):
        return False

    venv_bin = NUMSCOUT_DIR / "venv" / ("Scripts" if IS_WINDOWS else "bin")
    env = {**os.environ, "PYTHONUTF8": "1"}
    env["PATH"] = str(venv_bin) + os.pathsep + env.get("PATH", "")

    result_file = work / f"{sol_name}_{contract}.json"
    if result_file.exists():
        result_file.unlink()

    cmd = [str(NUMSCOUT_VENV_PYTHON), str(NUMSCOUT_DIR / "tool.py"),
           "-s", sol_name, "-cnames", contract, "-j",
           "-sv", solc_ver, "-glt", str(GLOBAL_TIMEOUT)]

    start = time.time()
    try:
        subprocess.run(
            cmd, cwd=str(work), env=env,
            timeout=GLOBAL_TIMEOUT + 600, capture_output=True,
        )
    except subprocess.TimeoutExpired:
        print(f"  [TIMEOUT] {case_id} ({time.time() - start:.0f}s)")
        return False
    elapsed = time.time() - start

    if not result_file.exists():
        print(f"  [ERROR] no output for {case_id} ({elapsed:.0f}s)")
        return False

    with open(result_file, encoding="utf-8") as f:
        data = json.load(f)
    data["_elapsed_wall"] = elapsed
    data["_run_tag"] = "patched"

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print(f"  [OK] {case_id} -> {output_file.name} ({elapsed:.0f}s)")
    return True


def main():
    parser = argparse.ArgumentParser(description="Re-run NumScout on patched 51/77")
    parser.add_argument("--run", required=True, help="Run name (e.g., run2, run3)")
    args = parser.parse_args()

    output_dir = BASE / "outputs" / "numscout" / args.run
    output_dir.mkdir(parents=True, exist_ok=True)

    for case_id, contract, solc_ver, workdir, sol_name in PATCHED_CASES:
        output_file = output_dir / f"{case_id}_patched.json"
        print(f"[RUN] {case_id} (contract={contract}, solc={solc_ver})")
        run_one(case_id, contract, solc_ver, workdir, sol_name, output_file)


if __name__ == "__main__":
    main()
