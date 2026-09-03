#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

EXPECTED_BRANCH="agent/v71-fx-portability-research"
EXPECTED_HEAD="${V71_FX_EXPECTED_HEAD:-}"
EVIDENCE_HEAD="${V71_FX_EVIDENCE_HEAD:-}"

BRANCH="$(git branch --show-current)"
HEAD="$(git rev-parse HEAD)"

printf '[%s] V71 FX evidence packaging\n' "$(date '+%Y-%m-%d %H:%M:%S')"
echo "BRANCH=$BRANCH"
echo "HEAD=$HEAD"
echo "EXPECTED_HEAD=$EXPECTED_HEAD"
echo "EVIDENCE_HEAD=$EVIDENCE_HEAD"

[[ "$BRANCH" == "$EXPECTED_BRANCH" ]] || {
  echo "FATAL: wrong branch expected=$EXPECTED_BRANCH actual=$BRANCH"
  exit 20
}
[[ -n "$EXPECTED_HEAD" ]] || {
  echo "FATAL: V71_FX_EXPECTED_HEAD is required"
  exit 21
}
[[ -n "$EVIDENCE_HEAD" ]] || {
  echo "FATAL: V71_FX_EVIDENCE_HEAD is required"
  exit 22
}
[[ "$HEAD" == "$EXPECTED_HEAD" ]] || {
  echo "FATAL: exact HEAD mismatch expected=$EXPECTED_HEAD actual=$HEAD"
  exit 23
}
[[ -z "$(git status --porcelain)" ]] || {
  echo "FATAL: working tree must be clean"
  git status --short
  exit 24
}

PY=""
for candidate in python.exe python3 python; do
  if command -v "$candidate" >/dev/null 2>&1; then
    PY="$candidate"
    break
  fi
done
[[ -n "$PY" ]] || { echo "FATAL: Python not found"; exit 25; }
echo "PYTHON_SELECTED=$PY"

echo "V71_FX_EVIDENCE_REUSES_EXISTING_TESTER_OUTPUT=1"
echo "V71_FX_EVIDENCE_TESTER_RERUN=0"
echo "V71_FX_EVIDENCE_MT5_CLOSE_REQUIRED=0"

"$PY" scripts/package_v71_fx_evidence.py \
  --repo . \
  --output-root runtime/v71_fx_portability_research/OUTPUT_V71_FX \
  --packaging-head "$HEAD" \
  --evidence-head "$EVIDENCE_HEAD"

echo "V71_FX_EVIDENCE_LAUNCHER=PASS"
echo "V71_SHORT_ENABLED=0"
echo "REAL_MONEY_AUTHORIZED=0"
