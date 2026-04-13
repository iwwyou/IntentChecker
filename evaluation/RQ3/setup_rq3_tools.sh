#!/usr/bin/env bash
# RQ3 tool setup: clone GPTScan, NumScout, and ScType at pinned commits,
# apply the patches in evaluation/RQ3/patches/, create a dedicated Python
# virtualenv for each tool, and install each tool's requirements.
#
# Optionally also clones the Web3Bugs dataset (target: web3bugs) — pass it
# explicitly because the dataset is large and only needed to re-run the
# Web3Bugs subset of the experiments.
#
# Requirements on the host:
#   - git
#   - Python 3.10 or newer available on PATH as `python3` or `python`
#   - For any solc-based run: `solc-select` installed and the required
#     versions downloaded (`solc-select install 0.6.12 0.7.6 0.8.3 ...`)
#   - For Web3Bugs runs: Node.js + npm/yarn (per-contest; each project's
#     package.json controls its toolchain)
#
# Usage:
#   bash evaluation/RQ3/setup_rq3_tools.sh                       # all three tools
#   bash evaluation/RQ3/setup_rq3_tools.sh gptscan               # one tool only
#   bash evaluation/RQ3/setup_rq3_tools.sh numscout sctype       # pick a subset
#   bash evaluation/RQ3/setup_rq3_tools.sh web3bugs              # clone dataset only
#   bash evaluation/RQ3/setup_rq3_tools.sh gptscan web3bugs      # tool + dataset
#
# All tools and the Web3Bugs clone are installed under evaluation/RQ3/tools/
# and evaluation/RQ3/web3bugs/ respectively, both of which are gitignored.
# Re-running the script is safe — clone/venv steps are skipped when already
# in place and patches are applied idempotently.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOLS_DIR="$SCRIPT_DIR/tools"
PATCHES_DIR="$SCRIPT_DIR/patches"
WEB3BUGS_DIR="$SCRIPT_DIR/web3bugs"

# Pinned upstream commits (match the versions used for the paper's experiments).
GPTSCAN_REPO="https://github.com/GPTScan/GPTScan.git"
GPTSCAN_COMMIT="29a174773bd526c32ab7d6a8c78a63870330ccc7"

NUMSCOUT_REPO="https://github.com/NumScout/NumScout.git"
NUMSCOUT_COMMIT="3abc0f3b5ab104e68c023b8d2202aa6fdef93d95"

SCTYPE_REPO="https://github.com/NioTheFirst/ScType.git"
SCTYPE_COMMIT="24deb8c165a5fa8a768d625cf96bae64196e4463"

WEB3BUGS_REPO="https://github.com/ZhangZhuoSJTU/Web3Bugs.git"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# All log lines go to stderr so command-substitution captures (e.g.,
# `vpy="$(make_venv ...)"`) only see the actual return value on stdout.
log() { printf '\033[1;34m[setup]\033[0m %s\n' "$*" >&2; }
warn() { printf '\033[1;33m[setup]\033[0m %s\n' "$*" >&2; }
err() { printf '\033[1;31m[setup]\033[0m %s\n' "$*" >&2; }

find_python() {
  # Prefer python3 so we don't accidentally grab Python 2 on ancient systems.
  for cand in python3 python; do
    if command -v "$cand" >/dev/null 2>&1; then
      if "$cand" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
        echo "$cand"
        return 0
      fi
    fi
  done
  return 1
}

PYTHON="$(find_python)" || {
  err "Python 3.10+ is required but was not found on PATH."
  err "Install Python 3.10 or newer and re-run this script."
  exit 1
}
log "Using Python: $($PYTHON -c 'import sys; print(sys.executable, sys.version.split()[0])')"

venv_python() {
  # Cross-platform venv python path. Unix uses bin/python, Windows uses Scripts/python.exe.
  local venv_dir="$1"
  if [ -x "$venv_dir/bin/python" ]; then
    echo "$venv_dir/bin/python"
  elif [ -x "$venv_dir/Scripts/python.exe" ]; then
    echo "$venv_dir/Scripts/python.exe"
  else
    err "Could not locate python executable inside $venv_dir"
    exit 1
  fi
}

clone_at_commit() {
  # Args: repo url, commit hash, destination dir, [path...]
  # If extra path args are passed, the function uses `git archive` to
  # extract only those paths from the pinned commit instead of running
  # `git checkout`. This is required for NumScout, whose Experiment/
  # and test/ trees contain files with ':' in their names — illegal on
  # Windows/NTFS — which would otherwise break any checkout attempt
  # regardless of sparse-checkout configuration.
  local repo="$1" commit="$2" dest="$3"
  shift 3
  local archive_paths=("$@")

  if [ -d "$dest/.git" ]; then
    log "$(basename "$dest"): already populated, skipping clone"
    return 0
  fi

  log "$(basename "$dest"): cloning from $repo"
  if [ "${#archive_paths[@]}" -gt 0 ]; then
    log "$(basename "$dest"): selective extract of: ${archive_paths[*]}"
    # Disable NTFS / HFS path protections at every git invocation so the
    # bad ':' paths under Experiment/ and test/ don't fail the archive
    # (git archive still validates tree entries even though it writes
    # to stdout).
    local GIT_OPTS="-c core.protectNTFS=false -c core.protectHFS=false -c core.longpaths=true"
    # Step 1: clone metadata only, no working tree, no checkout
    git $GIT_OPTS clone --quiet --no-checkout "$repo" "$dest"
    # Step 2: make sure the pinned commit is in the local object store
    git $GIT_OPTS -C "$dest" fetch --quiet origin "$commit" || true
    # Step 3: extract just the requested paths via git archive | tar.
    #         git archive never touches the working tree or index, so
    #         the bad ':' paths under Experiment/ and test/ are not
    #         produced — but we still need protectNTFS=false so the
    #         tree walk itself doesn't reject them.
    git $GIT_OPTS -C "$dest" archive --format=tar "$commit" "${archive_paths[@]}" \
      | tar -x -C "$dest"
    # Step 4: detach HEAD to the pinned commit so subsequent calls of
    #         the script see the right SHA without invoking checkout.
    git $GIT_OPTS -C "$dest" update-ref --no-deref HEAD "$commit"
  else
    git clone --quiet "$repo" "$dest"
    git -C "$dest" fetch --quiet origin "$commit" || true
    git -C "$dest" checkout --quiet "$commit"
  fi
}

apply_patches_for() {
  local tool="$1" dest="$2"
  local pdir="$PATCHES_DIR/$tool"
  if [ ! -d "$pdir" ]; then
    return 0
  fi
  shopt -s nullglob
  local patches=("$pdir"/*.patch)
  shopt -u nullglob
  if [ "${#patches[@]}" -eq 0 ]; then
    return 0
  fi
  for p in "${patches[@]}"; do
    if git -C "$dest" apply --check "$p" 2>/dev/null; then
      log "$tool: applying $(basename "$p")"
      git -C "$dest" apply "$p"
    elif git -C "$dest" apply --check --reverse "$p" 2>/dev/null; then
      log "$tool: $(basename "$p") already applied, skipping"
    else
      err "$tool: patch $(basename "$p") does not apply cleanly against the pinned commit"
      exit 1
    fi
  done
}

make_venv() {
  # Returns the venv's python executable path on stdout. All other output
  # (log lines, `python -m venv`, `pip install`) is redirected to stderr so
  # callers using $(make_venv ...) capture only the path.
  local dest="$1"
  if [ -f "$dest/pyvenv.cfg" ]; then
    log "venv already exists at $dest"
  else
    log "creating venv at $dest"
    "$PYTHON" -m venv "$dest" >&2
  fi
  local vpy
  vpy="$(venv_python "$dest")"
  "$vpy" -m pip install --quiet --upgrade pip >&2
  printf '%s\n' "$vpy"
}

# ---------------------------------------------------------------------------
# Per-tool installers
# ---------------------------------------------------------------------------

install_gptscan() {
  local dest="$TOOLS_DIR/gptscan"
  mkdir -p "$TOOLS_DIR"
  clone_at_commit "$GPTSCAN_REPO" "$GPTSCAN_COMMIT" "$dest"
  apply_patches_for gptscan "$dest"
  local vpy
  vpy="$(make_venv "$dest/venv")"

  # GPTScan ships requirements.txt that lists `dbus-python`, which is a
  # Linux-only build (depends on dbus headers + glib). Filter it out on
  # any non-Linux host so pip doesn't try to compile it. We also strip any
  # obviously Linux-only packages picked up from a `pip freeze`.
  local req="$dest/requirements.txt"
  if [ ! -f "$req" ]; then
    warn "gptscan: no requirements file found, skipping pip install"
    log "gptscan: ready at $dest"
    return 0
  fi

  local platform_req="$req"
  case "$(uname -s 2>/dev/null || echo unknown)" in
    Linux*) ;;
    *)
      platform_req="$dest/requirements.platform.txt"
      log "gptscan: filtering Linux-only packages out of requirements.txt"
      grep -v -E '^(dbus-python|distro)[<=>~!]' "$req" > "$platform_req" || true
      ;;
  esac

  log "gptscan: installing $(basename "$platform_req")"
  "$vpy" -m pip install -r "$platform_req"

  # falcon-analyzer (a GPTScan dependency) imports FastChildWatcher
  # unconditionally at module top level, which fails on Windows and on
  # Python 3.12+ where the symbol no longer exists. The import is
  # vestigial — the module never actually uses it — so we strip the
  # import line in the installed package.
  local falcon_version_py
  for cand in \
    "$dest/venv/Lib/site-packages/falcon/utils/version.py" \
    "$dest/venv/lib/python3.10/site-packages/falcon/utils/version.py" \
    "$dest/venv/lib/python3.11/site-packages/falcon/utils/version.py" \
    "$dest/venv/lib/python3.12/site-packages/falcon/utils/version.py"; do
    if [ -f "$cand" ]; then
      falcon_version_py="$cand"
      break
    fi
  done
  if [ -n "${falcon_version_py:-}" ]; then
    if grep -q "^from asyncio import FastChildWatcher" "$falcon_version_py"; then
      log "gptscan: removing FastChildWatcher import from $falcon_version_py"
      sed -i '/^from asyncio import FastChildWatcher$/d' "$falcon_version_py"
    fi
  fi

  log "gptscan: ready at $dest"
}

install_numscout() {
  local dest="$TOOLS_DIR/numscout"
  mkdir -p "$TOOLS_DIR"
  # Whitelist only the paths NumScout's tool.py actually needs. Excludes
  # the bundled Experiment/ and test/ trees which contain file names with
  # ':' (illegal on Windows/NTFS) and which the RQ3 drivers don't use.
  clone_at_commit "$NUMSCOUT_REPO" "$NUMSCOUT_COMMIT" "$dest" \
    tool.py global_params.py requirements.txt README.md LICENSE \
    cfg_builder defect_identifier feature_detector inputter GPT-Pruning
  apply_patches_for numscout "$dest"
  local vpy
  vpy="$(make_venv "$dest/venv")"
  if [ -f "$dest/requirements.txt" ]; then
    log "numscout: installing requirements.txt"
    "$vpy" -m pip install -r "$dest/requirements.txt"
  else
    warn "numscout: no requirements.txt, skipping pip install"
  fi
  log "numscout: ready at $dest"
}

install_sctype() {
  local dest="$TOOLS_DIR/sctype"
  mkdir -p "$TOOLS_DIR"
  clone_at_commit "$SCTYPE_REPO" "$SCTYPE_COMMIT" "$dest"
  apply_patches_for sctype "$dest"
  local vpy
  vpy="$(make_venv "$dest/venv")"
  log "sctype: installing via editable setup.py"
  "$vpy" -m pip install -e "$dest"
  log "sctype: ready at $dest"
  log "sctype: type files are committed under $SCRIPT_DIR/sctype_typefiles/"
  log "        (run_sctype.py picks them up automatically)"
}

install_web3bugs() {
  if [ -d "$WEB3BUGS_DIR/.git" ]; then
    log "web3bugs: already cloned at $WEB3BUGS_DIR, pulling latest"
    git -C "$WEB3BUGS_DIR" pull --quiet || warn "web3bugs: pull failed (continuing)"
  else
    log "web3bugs: cloning $WEB3BUGS_REPO (this takes a while)"
    git clone --quiet "$WEB3BUGS_REPO" "$WEB3BUGS_DIR"
  fi
  if [ ! -d "$WEB3BUGS_DIR/contracts" ]; then
    warn "web3bugs: expected contracts/ not found in clone"
    return 1
  fi
  log "web3bugs: ready at $WEB3BUGS_DIR/contracts"
  log "          set WEB3BUGS_CONTRACTS=$WEB3BUGS_DIR/contracts (or leave unset;"
  log "          run_*.py auto-detects this path)"
  log "          per-project npm/yarn install: bash $SCRIPT_DIR/setup_dependencies.sh"
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

targets=("$@")
if [ "${#targets[@]}" -eq 0 ]; then
  targets=(gptscan numscout sctype)
fi

for t in "${targets[@]}"; do
  case "$t" in
    gptscan)  install_gptscan ;;
    numscout) install_numscout ;;
    sctype)   install_sctype ;;
    web3bugs) install_web3bugs ;;
    *) err "unknown target: $t (expected gptscan | numscout | sctype | web3bugs)"; exit 2 ;;
  esac
done

log "done"
