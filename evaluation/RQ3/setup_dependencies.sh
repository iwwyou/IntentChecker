#!/bin/bash
# RQ3 Setup: Install npm dependencies for Web3Bugs projects
# Run from any directory - uses absolute paths

WEB3BUGS="C:/Users/isjeon/Web3Bugs/contracts"
LOG="C:/Users/isjeon/PycharmProjects/pythonProject/SolidityGuardian/evaluation/RQ3/setup_log.txt"

echo "=== RQ3 dependency setup started at $(date) ===" > "$LOG"

install_project() {
  local contest=$1
  local subdir=$2
  local pkg_mgr=$3
  local project_dir="$WEB3BUGS/$contest/$subdir"

  echo "[$contest] Installing in $project_dir ($pkg_mgr)..."
  echo "[$contest] $project_dir ($pkg_mgr)" >> "$LOG"

  cd "$project_dir" || { echo "[$contest] FAIL: dir not found" >> "$LOG"; return 1; }

  if [ "$pkg_mgr" = "yarn" ]; then
    yarn install --frozen-lockfile 2>&1 | tail -3 >> "$LOG"
    if [ $? -ne 0 ]; then
      yarn install 2>&1 | tail -3 >> "$LOG"
    fi
  else
    npm install 2>&1 | tail -3 >> "$LOG"
  fi

  if [ $? -eq 0 ]; then
    echo "[$contest] OK" >> "$LOG"
  else
    echo "[$contest] FAIL" >> "$LOG"
  fi
}

# Projects with package.json at root level
install_project 5 "." "npm"
install_project 17 "." "yarn"
install_project 25 "." "yarn"
install_project 44 "." "yarn"
install_project 45 "." "yarn"
install_project 47 "." "yarn"
install_project 52 "." "npm"
install_project 56 "." "yarn"
install_project 61 "." "npm"
install_project 70 "." "npm"
install_project 71 "." "npm"
install_project 78 "." "yarn"
install_project 79 "." "yarn"
install_project 83 "." "npm"
install_project 110 "." "npm"
install_project 113 "." "yarn"
install_project 192 "." "npm"

# Projects with nested package.json
install_project 8 "nftx-protocol-v2" "yarn"
install_project 16 "src" "npm"
install_project 29 "trident" "yarn"
install_project 31 "veCVX" "npm"
install_project 34 "v4-core" "yarn"
install_project 35 "trident" "yarn"
install_project 36 "contracts" "npm"
install_project 42 "projects/mochi-core" "npm"
install_project 51 "customswap" "npm"
install_project 58 "mellow-vaults" "npm"
install_project 59 "src" "yarn"
install_project 60 "protocol" "yarn"
install_project 62 "Streaming" "npm"
install_project 65 "contracts" "npm"
install_project 77 "elasticswap" "yarn"
install_project 101 "sublime-v1" "npm"
install_project 112 "backd" "yarn"

# Projects without package.json (3, 39) - skip, may need manual handling
echo "[3] NO package.json - manual check needed" >> "$LOG"
echo "[39] NO package.json - manual check needed" >> "$LOG"

echo "=== Setup completed at $(date) ===" >> "$LOG"
echo "Done. Check $LOG for results."
