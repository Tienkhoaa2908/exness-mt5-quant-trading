#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

BRANCH="agent/v66-post-bos-cash-zone-research"
RUNNER="runtime/v66_post_bos_cash_zone/RUN_V66_POST_BOS_CASH_ZONE.py"
STATIC="tests/test_v66_post_bos_cash_zone_static.py"

printf '%s\n' '============================================================'
printf '%s\n' 'V66 POST-BOS CASH-ZONE RESEARCH'
printf '%s\n' 'fixed 0.01 | fixed M1 micro stop | tick retracement entry'
printf '%s\n' 'planned risk $0.85-$1.25 | TP $3.50 | risk/spread >= 4'
printf '%s\n' 'same V65 4 benchmark + 4 bearish windows | 12 Model=4 passes'
printf '%s\n' '============================================================'

CURRENT="$(git branch --show-current)"
HEAD="$(git rev-parse HEAD)"
printf 'BRANCH=%s\n' "$CURRENT"
printf 'HEAD=%s\n' "$HEAD"

if [[ "$CURRENT" != "$BRANCH" ]]; then
  printf 'FATAL: wrong branch expected=%s actual=%s\n' "$BRANCH" "$CURRENT"
  exit 101
fi
if [[ -n "$(git status --porcelain)" ]]; then
  printf '%s\n' 'FATAL: working tree must be clean'
  git status --porcelain
  exit 102
fi
if tasklist.exe 2>/dev/null | grep -qi 'terminal64.exe'; then
  printf '%s\n' 'FATAL: MT5 is open; close it before V66'
  exit 103
fi
if tasklist.exe 2>/dev/null | grep -qi 'metaeditor64.exe'; then
  printf '%s\n' 'FATAL: MetaEditor is open; close it before V66'
  exit 104
fi

PY=""
if command -v py.exe >/dev/null 2>&1; then
  PWIN="$(py.exe -3 -c 'import sys; print(sys.executable)' 2>/dev/null | tr -d '\r' | tail -n 1 || true)"
  if [[ -n "$PWIN" ]] && command -v cygpath >/dev/null 2>&1; then
    PY="$(cygpath -u "$PWIN" 2>/dev/null || true)"
  fi
fi
if [[ -z "$PY" ]] && command -v python.exe >/dev/null 2>&1; then PY="$(command -v python.exe)"; fi
if [[ -z "$PY" ]] && command -v python >/dev/null 2>&1; then PY="$(command -v python)"; fi
if [[ -z "$PY" ]]; then
  printf '%s\n' 'FATAL: Python not found'
  exit 105
fi

printf 'V66_PYTHON=%s\n' "$PY"
"$PY" --version
"$PY" -m py_compile \
  scripts/build_v66_post_bos_cash_zone_source.py \
  scripts/analyze_v66_post_bos_cash_zone.py \
  "$STATIC" \
  "$RUNNER"
"$PY" "$STATIC"
"$PY" scripts/secret_scan.py "$ROOT"
printf '%s\n' 'V66_PRE_RUNTIME_STATIC=PASS'

exec "$PY" "$RUNNER"
