#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

BRANCH="$(git branch --show-current)"
HEAD="$(git rev-parse HEAD)"
EXPECTED_HEAD="${V70_EXIT_HARVEST_EXPECTED_HEAD:-}"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] V70 exit-harvest research"
echo "BRANCH=$BRANCH"
echo "HEAD=$HEAD"
echo "EXPECTED_HEAD=$EXPECTED_HEAD"

[ "$BRANCH" = "agent/v70-exit-harvest-research" ] || {
  echo "FATAL: wrong branch"
  exit 20
}

[ -n "$EXPECTED_HEAD" ] || {
  echo "FATAL: V70_EXIT_HARVEST_EXPECTED_HEAD is required"
  exit 21
}

[ "$HEAD" = "$EXPECTED_HEAD" ] || {
  echo "FATAL: exact HEAD mismatch"
  exit 22
}

[ -z "$(git status --porcelain)" ] || {
  echo "FATAL: WORKTREE DIRTY"
  git status --short
  exit 23
}

PY=""
for candidate in py.exe python.exe python3 python; do
  if command -v "$candidate" >/dev/null 2>&1; then
    if "$candidate" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)' >/dev/null 2>&1; then
      PY="$candidate"
      break
    fi
  fi
done

[ -n "$PY" ] || {
  echo "FATAL: Python 3.10+ not found"
  exit 24
}

echo "PYTHON_SELECTED=$PY"
"$PY" runtime/v70_exit_harvest_research/RUN_V70_EXIT_HARVEST_RESEARCH.py

echo "V70_EXIT_HARVEST_LAUNCHER=PASS"
echo "REAL_MONEY_AUTHORIZED=0"
