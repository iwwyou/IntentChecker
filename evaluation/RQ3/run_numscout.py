"""
RQ3: Run NumScout on all 75 cases.

NumScout analyzes single .sol files via symbolic execution on bytecode.
- NumScout cases: use original single-file contracts directly
- Web3Bugs cases: flatten via hardhat, then analyze

Requires (installed by setup_rq3_tools.sh):
  - NumScout tree at evaluation/RQ3/tools/numscout/ with its own venv
Requires on the host:
  - solc binaries installed via solc-select (default: ~/.solc-select/artifacts,
    override with $SOLC_ARTIFACTS)
  - Web3Bugs contracts dir (default: evaluation/RQ3/web3bugs/contracts if the
    setup script was run with the ``web3bugs`` target, otherwise ~/Web3Bugs/contracts;
    override with $WEB3BUGS_CONTRACTS)
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

SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent.parent
IS_WINDOWS = platform.system() == "Windows"


def _tool_venv_python(tool_dir: Path) -> Path:
    candidates = [
        tool_dir / "venv" / "Scripts" / "python.exe",
        tool_dir / "venv" / "bin" / "python",
    ]
    for c in candidates:
        if c.exists():
            return c
    return candidates[0]


def _default_solc_artifacts() -> Path:
    """Return the conventional solc-select artifacts directory for the host."""
    return Path.home() / ".solc-select" / "artifacts"


def _default_web3bugs_contracts() -> Path:
    """Prefer the in-repo Web3Bugs clone (installed by setup_rq3_tools.sh web3bugs)."""
    in_repo = SCRIPT_DIR / "web3bugs" / "contracts"
    if in_repo.exists():
        return in_repo
    return Path.home() / "Web3Bugs" / "contracts"


def _which(name: str) -> str:
    """Cross-platform executable lookup. On Windows, also tries the .cmd variant
    (npm installs npx as npx.cmd). Returns a command string suitable for subprocess."""
    hit = shutil.which(name)
    if hit:
        return hit
    if IS_WINDOWS:
        hit = shutil.which(name + ".cmd")
        if hit:
            return hit
    return name  # fall through; subprocess will error with a clear message


NUMSCOUT_DIR = SCRIPT_DIR / "tools" / "numscout"
NUMSCOUT_VENV_PYTHON = _tool_venv_python(NUMSCOUT_DIR)
SOLC_ARTIFACTS = Path(os.environ.get("SOLC_ARTIFACTS", str(_default_solc_artifacts())))
WEB3BUGS_DIR = Path(os.environ.get("WEB3BUGS_CONTRACTS", str(_default_web3bugs_contracts())))
NPX = _which("npx")
CASE_MAPPING = SCRIPT_DIR / "case_mapping.csv"
OUTPUT_DIR = SCRIPT_DIR / "outputs" / "numscout"
WORK_DIR = SCRIPT_DIR / "workdir_numscout"
GLOBAL_TIMEOUT = 1800  # seconds


def _find_solc_binary(version: str) -> Path | None:
    """Locate the versioned solc binary inside $SOLC_ARTIFACTS/solc-<version>/.

    solc-select stores the binary with different naming conventions per OS:
      Linux/Mac: solc-<version>
      Windows:   solc-<version>.exe
    """
    root = SOLC_ARTIFACTS / f"solc-{version}"
    candidates = [root / f"solc-{version}.exe", root / f"solc-{version}"]
    for c in candidates:
        if c.exists():
            return c
    return None


def switch_solc(version: str):
    """Make NumScout pick up the requested solc version.

    Strategy:
      1. Try `solc-select use <version>` (preferred, portable).
      2. Mirror the solc binary from $SOLC_ARTIFACTS into the NumScout venv so
         any direct ``solc`` invocation inside NumScout's subprocess finds it.
    """
    solc_bin = _find_solc_binary(version)
    if solc_bin is None:
        print(
            f"  [ERROR] solc {version} not found under {SOLC_ARTIFACTS}. "
            f"Run `solc-select install {version}` or set SOLC_ARTIFACTS."
        )
        return False

    # (1) solc-select use — portable and what NumScout expects.
    solc_select = shutil.which("solc-select")
    if solc_select:
        try:
            subprocess.run(
                [solc_select, "use", version], check=False, capture_output=True
            )
        except Exception as e:
            print(f"  [WARN] solc-select use {version} failed: {e}")

    # (2) Mirror into the tool venv's bin/Scripts directory.
    venv_root = NUMSCOUT_DIR / "venv"
    if IS_WINDOWS:
        targets = [venv_root / "Scripts" / "solc.exe"]
    else:
        targets = [venv_root / "bin" / "solc"]
    extra = os.environ.get("SOLC_COPY_TARGETS", "")
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
    print(f"  solc -> {version}")
    return True


def flatten_sol(contest_number: str, project_root: str, target_sol: str, solc_version: str) -> str:
    """Flatten a multi-file Solidity project into a single .sol file."""
    web3bugs_project = WEB3BUGS_DIR / project_root
    # Derive relative path of target .sol within the project
    # target_sol format: "45/contracts/market/UToken.sol"
    # project_root format: "45"
    # Remove project_root prefix (not just contest_number) to get the path relative to CWD
    if project_root and target_sol.startswith(project_root + "/"):
        rel_sol = target_sol[len(project_root) + 1:]
    elif contest_number and target_sol.startswith(contest_number + "/"):
        rel_sol = target_sol[len(contest_number) + 1:]
    else:
        rel_sol = target_sol

    flat_file = WORK_DIR / f"{Path(target_sol).stem}_flat.sol"

    env = os.environ.copy()
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

    def _dedupe(content: str) -> str:
        """Remove duplicate SPDX/pragma lines and duplicate top-level declarations."""
        import re
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
        text = "".join(out)

        # Dedupe top-level contract/library/interface/abstract contract definitions
        # by tracking brace depth and removing repeat blocks with the same name+kind.
        decl_re = re.compile(
            r'^(abstract\s+contract|contract|library|interface)\s+(\w+)',
            re.MULTILINE,
        )
        seen_decls = set()
        result_chars = []
        i = 0
        n = len(text)
        while i < n:
            m = decl_re.search(text, i)
            if not m:
                result_chars.append(text[i:])
                break
            result_chars.append(text[i:m.start()])
            kind = m.group(1).replace("abstract contract", "contract").strip()
            name = m.group(2)
            key = (kind, name)
            # Find the matching open brace then walk to close
            j = text.find("{", m.end())
            if j == -1:
                result_chars.append(text[m.start():])
                break
            depth = 1
            k = j + 1
            while k < n and depth > 0:
                ch = text[k]
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                k += 1
            block_end = k
            if key in seen_decls:
                # Skip duplicate block
                pass
            else:
                seen_decls.add(key)
                result_chars.append(text[m.start():block_end])
            i = block_end
        return "".join(result_chars)

    # Try hardhat flatten first
    try:
        result = subprocess.run(
            [NPX, "hardhat", "flatten", rel_sol],
            cwd=str(web3bugs_project),
            capture_output=True, timeout=180, env=env, shell=True
        )
        if result.returncode == 0 and len(result.stdout) > 100:
            content = result.stdout.decode("utf-8", errors="replace")
            flat_file.write_text(_dedupe(content), encoding="utf-8")
            return str(flat_file)
        stderr = result.stderr.decode("utf-8", errors="replace")
        if "HH603" in stderr or "circular" in stderr.lower():
            print(f"  [INFO] hardhat flatten hit cyclic dependency, trying sol-merger")
        else:
            print(f"  [WARN] hardhat flatten returncode={result.returncode}")
    except Exception as e:
        print(f"  [WARN] hardhat flatten exception: {e}")

    # Fallback: sol-merger (handles cyclic dependencies)
    try:
        target_path = web3bugs_project / rel_sol
        if not target_path.exists():
            print(f"  [ERROR] target file not found: {target_path}")
            return None
        result = subprocess.run(
            [NPX, "sol-merger", str(target_path), str(WORK_DIR)],
            capture_output=True, timeout=180, env=env, shell=True
        )
        # sol-merger writes to {outputDir}/{basename}
        merged_file = WORK_DIR / Path(rel_sol).name
        if merged_file.exists() and merged_file.stat().st_size > 100:
            content = merged_file.read_text(encoding="utf-8")
            flat_file.write_text(_dedupe(content), encoding="utf-8")
            if merged_file != flat_file:
                merged_file.unlink()
            print(f"  [OK] sol-merger produced {flat_file.name}")
            return str(flat_file)
        stderr = result.stderr.decode("utf-8", errors="replace")[-300:]
        print(f"  [WARN] sol-merger failed: {stderr}")
    except Exception as e:
        print(f"  [WARN] sol-merger exception: {e}")

    return None


def _invoke_numscout(work: Path, sol_basename: str, contract_name: str,
                     solc_version: str, extra_args=None) -> tuple:
    """Run NumScout once. Returns (result, elapsed, timed_out)."""
    cmd = [str(NUMSCOUT_VENV_PYTHON), str(NUMSCOUT_DIR / "tool.py"),
           "-s", sol_basename, "-cnames", contract_name,
           "-j", "-sv", solc_version, "-glt", str(GLOBAL_TIMEOUT)]
    if extra_args:
        cmd.extend(extra_args)
    start = time.time()
    try:
        result = subprocess.run(
            cmd,
            cwd=str(work),
            capture_output=True, timeout=GLOBAL_TIMEOUT + 600,
            env={**os.environ, "PYTHONUTF8": "1"}
        )
        return result, time.time() - start, False
    except subprocess.TimeoutExpired:
        return None, time.time() - start, True


def run_numscout(sol_file: str, contract_name: str, solc_version: str, output_file: str) -> dict:
    """Run NumScout on a single .sol file. On timeout, retry with tight path limits."""
    work = WORK_DIR / f"run_{contract_name}"
    work.mkdir(parents=True, exist_ok=True)

    # Copy sol file to work dir (NumScout needs to run from sol file's directory)
    sol_basename = Path(sol_file).name
    target = work / sol_basename
    shutil.copy2(sol_file, target)
    result_file = work / f"{sol_basename}_{contract_name}.json"

    def _load_and_copy(elapsed, tag=""):
        with open(result_file, encoding="utf-8") as f:
            data = json.load(f)
        data["_elapsed_wall"] = elapsed
        if tag:
            data["_run_tag"] = tag
        shutil.copy2(result_file, output_file)
        return data

    # Attempt 1: default settings
    # Remove any stale result from previous runs so we can detect fresh output.
    if result_file.exists():
        result_file.unlink()
    result, elapsed, timed_out = _invoke_numscout(work, sol_basename, contract_name, solc_version)
    if result_file.exists():
        return _load_and_copy(elapsed)
    if timed_out:
        print(f"  [WARN] default run timed out ({elapsed:.0f}s), retrying with -ll 2 -dl 100")
    else:
        stderr = result.stderr.decode("utf-8", errors="replace")
        if "encoding/hex: invalid byte" in stderr or "incomplete push instruction" in stderr:
            return {"error": "external_library_linking", "time": elapsed, "stderr": stderr[-500:]}
        if "Solidity compilation failed" in stderr or "compilation failed" in stderr.lower():
            return {"error": "compile_error", "time": elapsed, "stderr": stderr[-500:]}
        # No result and not a known compile/linking failure — try tight limits too
        print(f"  [WARN] no output ({elapsed:.0f}s), retrying with -ll 2 -dl 100")

    # Attempt 2: tight symbolic-execution limits (loop limit 2, depth limit 100)
    result2, elapsed2, timed_out2 = _invoke_numscout(
        work, sol_basename, contract_name, solc_version,
        extra_args=["-ll", "2", "-dl", "100"],
    )
    if result_file.exists():
        return _load_and_copy(elapsed2, tag="ll2_dl100")
    if timed_out2:
        return {"error": "timeout", "time": elapsed + elapsed2}
    stderr2 = result2.stderr.decode("utf-8", errors="replace")
    return {"error": "no_output", "time": elapsed + elapsed2, "stderr": stderr2[-500:]}


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Run NumScout on RQ3 cases")
    parser.add_argument("--case", help="Run single case by ID")
    parser.add_argument("--source", choices=["numscout", "web3bugs", "all"], default="all")
    parser.add_argument("--run", help="Run name (output subdirectory)", default="run1")
    parser.add_argument("--annotated-only", action="store_true", help="Run only 20 annotated cases")
    args = parser.parse_args()

    output_dir = SCRIPT_DIR / "outputs" / "numscout" / args.run
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

    results_summary = []

    def _entry_from_json(cid, json_path, patched=False):
        """Build a summary entry from an existing result JSON."""
        try:
            with open(json_path, encoding="utf-8") as f:
                data = json.load(f)
            defects = [k for k, v in data.get("bool_defect", {}).items() if v]
            return {
                "case_id": cid, "tool": "numscout",
                "detected": len(defects) > 0,
                "detected_patterns": defects,
                "time": float(data.get("time", 0)),
                "status": "ok_patched" if patched else "ok",
                "patched": patched,
            }
        except Exception as e:
            return {"case_id": cid, "tool": "numscout", "detected": False,
                    "detected_patterns": [], "time": 0,
                    "status": f"json_read_error: {e}"}

    for case in cases:
        cid = case["case_id"]
        source = case["source"]
        contract = case["contract_name"]
        solc_ver = case["solc_version"]
        output_file = output_dir / f"{cid}.json"

        patched_file = output_dir / f"{cid}_patched.json"
        if output_file.exists():
            print(f"[SKIP] {cid} - already has result")
            results_summary.append(_entry_from_json(cid, output_file))
            continue
        if patched_file.exists():
            print(f"[SKIP] {cid} - has patched result (external library workaround)")
            results_summary.append(_entry_from_json(cid, patched_file, patched=True))
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
