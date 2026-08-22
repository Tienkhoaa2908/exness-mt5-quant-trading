#!/usr/bin/env bash
set -Eeuo pipefail
export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
WORK="${WORK:-$(cd -- "$SCRIPT_DIR/../.." && pwd -P)}"
BRANCH="${BRANCH:-agent/v48-demo-paper-forward}"
RUNNER="$SCRIPT_DIR/RUN_V48_DEMO_PAPER_START_HARDENED_V2.py"
LEGACY_RUNNER="$SCRIPT_DIR/RUN_V48_DEMO_PAPER_START.py"
HARD_V1="$SCRIPT_DIR/RUN_V48_DEMO_PAPER_START_HARDENED.py"
STATUS="$SCRIPT_DIR/STATUS_V48_DEMO_PAPER.py"
TEST="$WORK/tests/test_v48_demo_paper_static.py"
HARD_TEST="$WORK/tests/test_v48_demo_paper_hardened_launcher_static.py"
HARD_V2_TEST="$WORK/tests/test_v48_demo_paper_hardened_v2_static.py"
VENV="$WORK/runtime/v31_mt5_model_gate/OUTPUT_V31_1_MT5/.venv"
PY="$VENV/Scripts/python.exe"

[[ -d "$WORK/.git" ]] || { echo "FATAL: Git checkout missing: $WORK" >&2; exit 1; }
[[ "$(git -C "$WORK" branch --show-current)" == "$BRANCH" ]] || { echo "FATAL: checkout $BRANCH first" >&2; exit 1; }
[[ -x "$PY" ]] || { echo "FATAL: expected Python env missing: $PY" >&2; exit 1; }

echo "=== V48 DEMO-PAPER FORWARD — HARDENED V2 ==="
echo "WORK=$WORK"
echo "BRANCH=$(git -C "$WORK" branch --show-current)"
echo "HEAD=$(git -C "$WORK" rev-parse HEAD)"
echo "Frozen primary: v46_hl10_thr0p05_breadth4"
echo "Real-time DEMO feed + internal virtual USD40 book."
echo "Market may be closed: OnInit/timer/dashboard gates must still pass."
echo "Terminal AutoTrading is requested OFF by startup config and verified inside OnInit."
echo "Failed OnInit debris may only be recovered when REASON_INITFAILED=8 evidence is complete."
echo "Broker orders are absent from source. REAL-MONEY LIVE TRADING remains FORBIDDEN."

echo "=== STATIC GATES ==="
bash -n "$0"
"$PY" -m py_compile \
  "$(cygpath -w "$RUNNER")" \
  "$(cygpath -w "$HARD_V1")" \
  "$(cygpath -w "$LEGACY_RUNNER")" \
  "$(cygpath -w "$STATUS")" \
  "$(cygpath -w "$TEST")" \
  "$(cygpath -w "$HARD_TEST")" \
  "$(cygpath -w "$HARD_V2_TEST")"
"$PY" "$(cygpath -w "$TEST")"
"$PY" "$(cygpath -w "$HARD_TEST")"
"$PY" "$(cygpath -w "$HARD_V2_TEST")"

echo "=== START PAPER OBSERVER — HARDENED V2 ==="
"$PY" "$(cygpath -w "$RUNNER")"

echo
echo "V48 paper observer started and passed terminal-permission + market-close-safe timer gates."
echo "Keep MT5 open on the DEMO account. Do not enable Algo Trading."
echo "Check status any time with:"
echo "  bash runtime/v48_demo_paper/STATUS_V48_DEMO_PAPER_GIT_BASH.sh"
