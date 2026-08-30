#!/usr/bin/env bash
set -Eeuo pipefail

EXPECTED_BRANCH="agent/v61-profit-ratchet-m5-refinement-research"
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
  echo "FATAL: working tree must be clean before V61 fixed research"
  git status --porcelain
  exit 72
fi

if tasklist.exe 2>/dev/null | grep -qi 'terminal64.exe'; then
  echo "FATAL: MetaTrader 5 is open. Close it before V61 Strategy Tester research."
  exit 74
fi
if tasklist.exe 2>/dev/null | grep -qi 'metaeditor64.exe'; then
  echo "FATAL: MetaEditor is open. Close it before V61 Strategy Tester research."
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

PY=""
if command -v py.exe >/dev/null 2>&1; then
  PWIN="$(py.exe -3 -c 'import sys; print(sys.executable)' 2>/dev/null | tr -d '\r' | tail -n 1 || true)"
  if [ -n "$PWIN" ]; then PY="$(win_to_unix "$PWIN")"; fi
fi
if [ -z "$PY" ] && command -v python.exe >/dev/null 2>&1; then
  PY="$(command -v python.exe)"
fi
if [ -z "$PY" ] && command -v python >/dev/null 2>&1; then
  PY="$(command -v python)"
fi

if [ -z "$PY" ] || [ ! -x "$PY" ]; then
  echo "FATAL: no usable Python 3 interpreter found"
  exit 73
fi

"$PY" -c 'import sys; assert sys.version_info >= (3,10)' || {
  echo "FATAL: Python >=3.10 required"
  exit 76
}

echo "============================================================"
echo "V61 FIXED FILE_COMMON ROOT + PROFIT RATCHET + M5 REFINEMENT"
echo 'fixed 0.01 | risk band $0.75-$1.25 | target $3'
echo 'arm at +$2 -> lock +$1 | M5 refinement | OrderCheck'
echo 'canonical evidence root: mt5_quant\v61_profit_ratchet_m5_refinement'
echo "============================================================"
echo "V61_PYTHON=$PY"
"$PY" -c 'import sys; print("V61_PYTHON_VERSION="+sys.version.split()[0])'

"$PY" runtime/v61_profit_ratchet_m5_refinement/RUN_V61_PROFIT_RATCHET_M5_REFINEMENT_FIXED.py
