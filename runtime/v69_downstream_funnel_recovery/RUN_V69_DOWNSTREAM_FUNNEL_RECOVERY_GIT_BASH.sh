#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

EXPECTED="${V69_DOWNSTREAM_FUNNEL_EXPECTED_HEAD:-}"
if [ -z "$EXPECTED" ]; then
    echo "FATAL: V69_DOWNSTREAM_FUNNEL_EXPECTED_HEAD is required"
    exit 20
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] V69 downstream LONG funnel recovery"
echo "BRANCH=$(git branch --show-current)"
echo "HEAD=$(git rev-parse HEAD)"
echo "EXPECTED_HEAD=$EXPECTED"

[ "$(git rev-parse HEAD)" = "$EXPECTED" ] || { echo "FATAL: HEAD MISMATCH"; exit 21; }
[ -z "$(git status --porcelain)" ] || {
    echo "FATAL: WORKTREE DIRTY"
    git status --short
    exit 22
}

PYTHON=""
for candidate in "python.exe" "python" "py.exe -3"; do
    if $candidate -c 'import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)' >/dev/null 2>&1; then
        PYTHON="$candidate"
        break
    else
        echo "PYTHON_REJECTED=$candidate"
    fi
done
[ -n "$PYTHON" ] || { echo "FATAL: Python 3.10+ not found"; exit 23; }

echo "PYTHON_SELECTED=$PYTHON"
$PYTHON -m py_compile \
    scripts/analyze_v69_downstream_long_funnel.py \
    runtime/v69_downstream_funnel_recovery/RUN_V69_DOWNSTREAM_FUNNEL_RECOVERY.py \
    tests/test_v69_downstream_long_funnel.py

$PYTHON tests/test_v69_downstream_long_funnel.py
$PYTHON scripts/secret_scan.py .
$PYTHON runtime/v69_downstream_funnel_recovery/RUN_V69_DOWNSTREAM_FUNNEL_RECOVERY.py

echo "V69_DOWNSTREAM_FUNNEL_LAUNCHER=PASS"
echo "MT5_CAN_REMAIN_RUNNING=1"
echo "METAEDITOR_REQUIRED=0"
echo "ORDERS_SENT=0"
echo "REAL_MONEY_AUTHORIZED=0"
