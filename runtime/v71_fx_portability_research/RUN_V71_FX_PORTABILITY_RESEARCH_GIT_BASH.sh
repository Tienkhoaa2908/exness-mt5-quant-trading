#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

EXPECTED_BRANCH="agent/v71-fx-portability-research"
EXPECTED_HEAD="${V71_FX_EXPECTED_HEAD:-}"

BRANCH="$(git branch --show-current)"
HEAD="$(git rev-parse HEAD)"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] V71 FX portability research"
echo "BRANCH=$BRANCH"
echo "HEAD=$HEAD"
echo "EXPECTED_HEAD=$EXPECTED_HEAD"

[[ "$BRANCH" == "$EXPECTED_BRANCH" ]] || {
  echo "FATAL: wrong branch expected=$EXPECTED_BRANCH actual=$BRANCH"
  exit 20
}

[[ -n "$EXPECTED_HEAD" ]] || {
  echo "FATAL: V71_FX_EXPECTED_HEAD is required"
  exit 21
}

[[ "$HEAD" == "$EXPECTED_HEAD" ]] || {
  echo "FATAL: exact HEAD mismatch expected=$EXPECTED_HEAD actual=$HEAD"
  exit 22
}

[[ -z "$(git status --porcelain)" ]] || {
  echo "FATAL: working tree must be clean"
  git status --short
  exit 23
}

PY=""
for candidate in python.exe python3 python; do
  if command -v "$candidate" >/dev/null 2>&1; then
    PY="$candidate"
    break
  fi
done
[[ -n "$PY" ]] || { echo "FATAL: Python not found"; exit 24; }
echo "PYTHON_SELECTED=$PY"

"$PY" runtime/v71_fx_portability_research/RUN_V71_FX_PORTABILITY_RESEARCH.py

echo "V71_FX_PORTABILITY_LAUNCHER=PASS"
echo "V71_SHORT_ENABLED=0"
echo "REAL_MONEY_AUTHORIZED=0"
