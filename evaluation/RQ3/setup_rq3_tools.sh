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

log() { printf '\033[1;34m[setup]\033[0m %s\n' "$*"; }
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
  local repo="$1" commit="$2" dest="$3"
  if [ -d "$dest/.git" ]; then
    log "$(basename "$dest"): already cloned, fetching pinned commit"
    git -C "$dest" fetch --quiet origin "$commit" || git -C "$dest" fetch --quiet origin
  else
    log "$(basename "$dest"): cloning from $repo"
    git clone --quiet "$repo" "$dest"
    git -C "$dest" fetch --quiet origin "$commit" || true
  fi
  git -C "$dest" checkout --quiet "$commit"
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
  local dest="$1"
  if [ -f "$dest/pyvenv.cfg" ]; then
    log "venv already exists at $dest"
  else
    log "creating venv at $dest"
    "$PYTHON" -m venv "$dest"
  fi
  local vpy
  vpy="$(venv_python "$dest")"
  "$vpy" -m pip install --quiet --upgrade pip
  echo "$vpy"
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
  local req="$dest/requirements_win.txt"
  [ -f "$req" ] || req="$dest/requirements.txt"
  if [ -f "$req" ]; then
    log "gptscan: installing $(basename "$req")"
    "$vpy" -m pip install -r "$req"
  else
    warn "gptscan: no requirements file found, skipping pip install"
  fi
  log "gptscan: ready at $dest"
}

install_numscout() {
  local dest="$TOOLS_DIR/numscout"
  mkdir -p "$TOOLS_DIR"
  clone_at_commit "$NUMSCOUT_REPO" "$NUMSCOUT_COMMIT" "$dest"
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
