#!/usr/bin/env bash
# IntentChecker — root install script.
#
# Creates a Python 3.10+ virtualenv at ./.venv and installs the runtime
# dependencies listed in requirements.txt. Re-run is safe.
#
# Usage:
#   bash install.sh                         # default — uses ./.venv
#   PYTHON=python3.11 bash install.sh       # pick a specific interpreter
#   IC_VENV=.venv311 bash install.sh        # pick a different venv path

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${IC_VENV:-$REPO_ROOT/.venv}"

find_python() {
  if [ -n "${PYTHON:-}" ]; then
    if "$PYTHON" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
      echo "$PYTHON"
      return 0
    fi
    echo "[install] \$PYTHON ($PYTHON) is not >= 3.10" >&2
    exit 1
  fi
  for cand in python3.12 python3.11 python3.10 python3 python; do
    if command -v "$cand" >/dev/null 2>&1; then
      if "$cand" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
        echo "$cand"
        return 0
      fi
    fi
  done
  return 1
}

PY="$(find_python)" || {
  echo "[install] Python 3.10+ is required but was not found on PATH." >&2
  echo "[install] Install Python 3.10 or newer and re-run." >&2
  exit 1
}

echo "[install] Using $($PY -c 'import sys; print(sys.executable, sys.version.split()[0])')"

if [ ! -f "$VENV_DIR/pyvenv.cfg" ]; then
  echo "[install] Creating virtualenv at $VENV_DIR"
  "$PY" -m venv "$VENV_DIR"
else
  echo "[install] Virtualenv already exists at $VENV_DIR"
fi

if [ -x "$VENV_DIR/bin/python" ]; then
  VPY="$VENV_DIR/bin/python"
elif [ -x "$VENV_DIR/Scripts/python.exe" ]; then
  VPY="$VENV_DIR/Scripts/python.exe"
else
  echo "[install] Could not locate python inside $VENV_DIR" >&2
  exit 1
fi

"$VPY" -m pip install --quiet --upgrade pip
"$VPY" -m pip install -r "$REPO_ROOT/requirements.txt"

echo "[install] IntentChecker dependencies installed."
echo "[install] Activate the venv and run:"
if [ -x "$VENV_DIR/bin/python" ]; then
  echo "    source $VENV_DIR/bin/activate"
else
  echo "    $VENV_DIR/Scripts/activate"
fi
echo "    python main.py <case.json>"
echo ""
echo "[install] To set up the RQ3 baseline tools (GPTScan, NumScout, ScType):"
echo "    bash evaluation/RQ3/setup_rq3_tools.sh"
