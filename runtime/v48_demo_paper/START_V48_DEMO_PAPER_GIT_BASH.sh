#!/usr/bin/env bash
set -Eeuo pipefail
export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
WORK="${WORK:-$(cd -- "$SCRIPT_DIR/../.." && pwd -P)}"
BRANCH="${BRANCH:-agent/v48-demo-paper-forward}"
RUNNER="$SCRIPT_DIR/RUN_V48_DEMO_PAPER_START.py"
STATUS="$SCRIPT_DIR/STATUS_V48_DEMO_PAPER.py"
TEST="$WORK/tests/test_v48_demo_paper_static.py"
VENV="$WORK/runtime/v31_mt5_model_gate/OUTPUT_V31_1_MT5/.venv"
PY="$VENV/Scripts/python.exe"

[[ -d "$WORK/.git" ]] || { echo "FATAL: Git checkout missing: $WORK" >&2; exit 1; }
[[ "$(git -C "$WORK" branch --show-current)" == "$BRANCH" ]] || { echo "FATAL: checkout $BRANCH first" >&2; exit 1; }
[[ -x "$PY" ]] || { echo "FATAL: expected Python env missing: $PY" >&2; exit 1; }

echo "=== V48 DEMO-PAPER FORWARD ==="
echo "WORK=$WORK"
echo "BRANCH=$(git -C "$WORK" branch --show-current)"
echo "HEAD=$(git -C "$WORK" rev-parse HEAD)"
echo "Frozen primary: v46_hl10_thr0p05_breadth4"
echo "Real-time DEMO feed + internal virtual USD40 book."
echo "AutoTrading must remain OFF. Broker orders are absent from source."
echo "REAL-MONEY LIVE TRADING remains FORBIDDEN."

echo "=== STATIC GATES ==="
bash -n "$0"
"$PY" -m py_compile "$(cygpath -w "$RUNNER")" "$(cygpath -w "$STATUS")" "$(cygpath -w "$TEST")"
"$PY" "$(cygpath -w "$TEST")"

echo "=== START PAPER OBSERVER ==="
"$PY" "$(cygpath -w "$RUNNER")"

echo
echo "V48 paper observer started. Keep MT5 open on the DEMO account and keep AutoTrading OFF."
echo "Check status any time with:"
echo "  bash runtime/v48_demo_paper/STATUS_V48_DEMO_PAPER_GIT_BASH.sh"
