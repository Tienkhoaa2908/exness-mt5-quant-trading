#!/usr/bin/env bash
set -Eeuo pipefail

EXPECTED_BRANCH="agent/v58-fixed001-pullback-trend-cost-research"
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
  echo "FATAL: working tree must be clean before V58 replay"
  git status --porcelain
  exit 72
fi
if tasklist.exe 2>/dev/null | grep -qi 'terminal64.exe'; then
  echo "FATAL: MetaTrader 5 is open. Close it before V58 Strategy Tester replay."
  exit 74
fi
if tasklist.exe 2>/dev/null | grep -qi 'metaeditor64.exe'; then
  echo "FATAL: MetaEditor is open. Close it before V58 Strategy Tester replay."
  exit 75
fi

win_to_unix() {
  local p="$1"
  if command -v cygpath >/dev/null 2>&1; then
    cygpath -u "$p" 2>/dev/null || printf '%s\n' "$p"
  else
    printf '%s\n' "$p"
  fi
}
python_ok() {
  local p="$1"
  [ -x "$p" ] || return 1
  "$p" -c 'import sys; assert sys.version_info >= (3,10); import pandas; print(sys.executable)' >/dev/null 2>&1
}

BASE_PY=""
if command -v py.exe >/dev/null 2>&1; then
  BASE_WIN="$(py.exe -3 -c 'import sys; print(sys.executable)' 2>/dev/null | tr -d '\r' | tail -n 1 || true)"
  if [ -n "$BASE_WIN" ]; then BASE_PY="$(win_to_unix "$BASE_WIN")"; fi
fi
if [ -z "$BASE_PY" ] && command -v python.exe >/dev/null 2>&1; then BASE_PY="$(command -v python.exe)"; fi
if [ -z "$BASE_PY" ] && command -v python >/dev/null 2>&1; then BASE_PY="$(command -v python)"; fi
if [ -z "$BASE_PY" ] || [ ! -x "$BASE_PY" ]; then
  echo "FATAL: no usable Python 3 interpreter found"
  exit 73
fi

LOCAL_APP_WIN="${LOCALAPPDATA:-${USERPROFILE:-}/AppData/Local}"
LOCAL_APP_UNIX="$(win_to_unix "$LOCAL_APP_WIN")"
V58_ENV="$LOCAL_APP_UNIX/mt5_quant/v58_python/.venv"
V58_PY="$V58_ENV/Scripts/python.exe"
PY=""
if python_ok "$V58_PY"; then
  PY="$V58_PY"
elif python_ok "$BASE_PY"; then
  PY="$BASE_PY"
else
  echo "V58_PYTHON_BOOTSTRAP=START"
  echo "BASE_PYTHON=$BASE_PY"
  echo "V58_ENV=$V58_ENV"
  mkdir -p "$(dirname "$V58_ENV")"
  rm -rf "$V58_ENV"
  "$BASE_PY" -m venv "$V58_ENV" || { echo "FATAL: failed to create V58 Python environment"; exit 76; }
  "$V58_PY" -m pip install --disable-pip-version-check --no-input "pandas<3" || {
    echo "FATAL: failed to install pandas<3 into V58 environment"; exit 77;
  }
  python_ok "$V58_PY" || { echo "FATAL: bootstrapped V58 Python failed validation"; exit 78; }
  PY="$V58_PY"
  echo "V58_PYTHON_BOOTSTRAP=PASS"
fi

echo "============================================================"
echo "V58 FIXED 0.01 PULLBACK + FAST TREND + COST-AWARE SPREAD"
echo "XAUUSDm M15 | 2026-08-24 -> 2026-08-29"
echo "tester-only | one real-tick pass | fixed lot 0.01"
echo "============================================================"
echo "V58_PYTHON=$PY"
"$PY" -c 'import sys,pandas; print("V58_PYTHON_VERSION="+sys.version.split()[0]); print("V58_PANDAS_VERSION="+pandas.__version__)'

"$PY" runtime/v58_fixed001_pullback_trend_cost/RUN_V58_FIXED001_PULLBACK_TREND_COST.py
