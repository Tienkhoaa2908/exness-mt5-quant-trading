#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

BRANCH="agent/v64-microstructure-trigger-shadow-research"
RUNNER="runtime/v64_microstructure_trigger_shadow/RUN_V64_MICROSTRUCTURE_TRIGGER_SHADOW_FIXED.py"
ORIGINAL_RUNNER="runtime/v64_microstructure_trigger_shadow/RUN_V64_MICROSTRUCTURE_TRIGGER_SHADOW.py"
STATIC="tests/test_v64_microstructure_trigger_shadow_static.py"
LOCATOR_TEST="tests/test_v64_mt5_locator_compat_static.py"

printf '%s\n' '============================================================'
printf '%s\n' 'V64 MICROSTRUCTURE TRIGGER + NOISE SHADOW RESEARCH'
printf '%s\n' 'fixed 0.01 | planned risk $0.85-$1.20 | TP $3.50'
printf '%s\n' 'risk/spread >= 4 | sweep/reclaim/BOS | two archetypes'
printf '%s\n' '8 benchmark + 4 bearish SHORT Model=4 passes'
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
  printf '%s\n' 'FATAL: MT5 is open; close it before V64'
  exit 103
fi
if tasklist.exe 2>/dev/null | grep -qi 'metaeditor64.exe'; then
  printf '%s\n' 'FATAL: MetaEditor is open; close it before V64'
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

printf 'V64_PYTHON=%s\n' "$PY"
"$PY" --version

"$PY" -m py_compile \
  scripts/build_v64_microstructure_trigger_shadow_source.py \
  scripts/build_v64_microstructure_trigger_shadow_source_fixed.py \
  scripts/build_v64_microstructure_trigger_shadow_screen_source.py \
  scripts/analyze_v64_microstructure_trigger_shadow.py \
  "$STATIC" \
  "$LOCATOR_TEST" \
  "$ORIGINAL_RUNNER" \
  "$RUNNER"

"$PY" "$STATIC"
"$PY" -m pytest -q "$LOCATOR_TEST"
"$PY" scripts/secret_scan.py "$ROOT"
printf '%s\n' 'V64_PRE_RUNTIME_STATIC=PASS'

exec "$PY" "$RUNNER"
