#!/usr/bin/env bash
set -Eeuo pipefail

EXPECTED_BRANCH="agent/v57-fixed001-trend-smc-research"
ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || {
  echo "FATAL: not inside git repository"
  exit 70
}
cd "$ROOT"

BRANCH="$(git branch --show-current)"
if [ "$BRANCH" != "$EXPECTED_BRANCH" ]; then
  echo "FATAL: wrong branch expected=$EXPECTED_BRANCH actual=$BRANCH"
  exit 71
fi

if [ -n "$(git status --porcelain)" ]; then
  echo "FATAL: working tree must be clean before V57 replay"
  git status --porcelain
  exit 72
fi

PY="$ROOT/runtime/v31_mt5_model_gate/OUTPUT_V31_1_MT5/.venv/Scripts/python.exe"
if [ ! -x "$PY" ]; then
  echo "FATAL: project Python missing: $PY"
  exit 73
fi

if tasklist.exe 2>/dev/null | grep -qi 'terminal64.exe'; then
  echo "FATAL: MetaTrader 5 is open. Close it before V57 Strategy Tester replay."
  exit 74
fi
if tasklist.exe 2>/dev/null | grep -qi 'metaeditor64.exe'; then
  echo "FATAL: MetaEditor is open. Close it before V57 Strategy Tester replay."
  exit 75
fi

echo "============================================================"
echo "V57 FIXED 0.01 TREND + SMC WEEKLY REAL-TICK REPLAY"
echo "XAUUSDm M15 | 2026-08-24 -> 2026-08-29"
echo "tester-only | one real-tick pass | fixed lot 0.01"
echo "============================================================"

"$PY" runtime/v57_fixed001_trend_smc/RUN_V57_FIXED001_TREND_SMC.py
