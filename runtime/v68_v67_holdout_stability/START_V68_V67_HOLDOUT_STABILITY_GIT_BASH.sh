#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

BRANCH="agent/v68-v67-holdout-stability-research"
RUNNER="runtime/v68_v67_holdout_stability/RUN_V68_V67_HOLDOUT_STABILITY.py"
STATIC="tests/test_v68_v67_holdout_stability_static.py"

printf '%s\n' '============================================================'
printf '%s\n' 'V68 V67 HOLDOUT STABILITY RESEARCH'
printf '%s\n' 'V67 decision logic unchanged | Sep 2025-May 2026 holdout'
printf '%s\n' '18 Model=4 passes | LONG/SHORT independent'
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
  printf '%s\n' 'FATAL: MT5 is open; close it before V68'
  exit 103
fi
if tasklist.exe 2>/dev/null | grep -qi 'metaeditor64.exe'; then
  printf '%s\n' 'FATAL: MetaEditor is open; close it before V68'
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

printf 'V68_PYTHON=%s\n' "$PY"
"$PY" --version
"$PY" -m py_compile \
  scripts/build_v68_v67_holdout_stability_source.py \
  scripts/analyze_v68_v67_holdout_stability.py \
  "$STATIC" \
  "$RUNNER"
"$PY" "$STATIC"
"$PY" scripts/secret_scan.py "$ROOT"
printf '%s\n' 'V68_PRE_RUNTIME_STATIC=PASS'

exec "$PY" "$RUNNER"
