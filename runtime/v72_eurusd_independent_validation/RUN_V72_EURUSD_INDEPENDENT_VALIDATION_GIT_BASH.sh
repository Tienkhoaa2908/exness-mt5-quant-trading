#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

EXPECTED_BRANCH="agent/v72-eurusd-independent-validation"
EXPECTED_HEAD="${V72_EURUSD_EXPECTED_HEAD:-}"
BRANCH="$(git branch --show-current)"
HEAD="$(git rev-parse HEAD)"

printf '[%s] V72 EURUSD independent validation\n' "$(date '+%Y-%m-%d %H:%M:%S')"
echo "BRANCH=$BRANCH"
echo "HEAD=$HEAD"
echo "EXPECTED_HEAD=$EXPECTED_HEAD"

[[ "$BRANCH" == "$EXPECTED_BRANCH" ]] || { echo "FATAL: wrong branch expected=$EXPECTED_BRANCH actual=$BRANCH"; exit 20; }
[[ -n "$EXPECTED_HEAD" ]] || { echo "FATAL: V72_EURUSD_EXPECTED_HEAD is required"; exit 21; }
[[ "$HEAD" == "$EXPECTED_HEAD" ]] || { echo "FATAL: exact HEAD mismatch expected=$EXPECTED_HEAD actual=$HEAD"; exit 22; }
[[ -z "$(git status --porcelain)" ]] || { echo "FATAL: working tree must be clean"; git status --short; exit 23; }

PY=""
for candidate in python.exe python3 python; do
  if command -v "$candidate" >/dev/null 2>&1; then PY="$candidate"; break; fi
done
[[ -n "$PY" ]] || { echo "FATAL: Python not found"; exit 24; }
echo "PYTHON_SELECTED=$PY"

echo "V72_EURUSD_TESTER_RUNS=1"
echo "V72_EURUSD_UNTOUCHED_PERIOD=2024.09.01,2025.09.01"
echo "V72_EURUSD_ENTRY_RETUNE=0"
echo "V72_EURUSD_EXIT_RETUNE=0"
echo "V72_SHORT_ENABLED=0"
echo "REAL_MONEY_AUTHORIZED=0"

"$PY" runtime/v72_eurusd_independent_validation/RUN_V72_EURUSD_INDEPENDENT_VALIDATION.py

echo "V72_EURUSD_VALIDATION_LAUNCHER=PASS"
echo "V72_SHORT_ENABLED=0"
echo "REAL_MONEY_AUTHORIZED=0"
