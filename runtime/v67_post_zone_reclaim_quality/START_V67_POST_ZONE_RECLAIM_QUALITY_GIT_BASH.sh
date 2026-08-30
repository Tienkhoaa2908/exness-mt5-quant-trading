#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

BRANCH="agent/v67-post-zone-reclaim-quality-research"
RUNNER="runtime/v67_post_zone_reclaim_quality/RUN_V67_POST_ZONE_RECLAIM_QUALITY.py"
STATIC="tests/test_v67_post_zone_reclaim_quality_static.py"

printf '%s\n' '============================================================'
printf '%s\n' 'V67 POST-ZONE RECLAIM QUALITY RESEARCH'
printf '%s\n' 'fixed 0.01 | no first-touch order | deeper penetration + closed-M1 reclaim'
printf '%s\n' 'planned risk $0.85-$1.10 | TP $3.50 | risk/spread >= 4'
printf '%s\n' 'same frozen 12 Model=4 passes; stability over fixed weekly quotas'
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
  printf '%s\n' 'FATAL: MT5 is open; close it before V67'
  exit 103
fi
if tasklist.exe 2>/dev/null | grep -qi 'metaeditor64.exe'; then
  printf '%s\n' 'FATAL: MetaEditor is open; close it before V67'
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

printf 'V67_PYTHON=%s\n' "$PY"
"$PY" --version
"$PY" -m py_compile \
  scripts/build_v67_post_zone_reclaim_quality_source.py \
  scripts/analyze_v67_post_zone_reclaim_quality.py \
  "$STATIC" \
  "$RUNNER"
"$PY" "$STATIC"
"$PY" scripts/secret_scan.py "$ROOT"
printf '%s\n' 'V67_PRE_RUNTIME_STATIC=PASS'

exec "$PY" "$RUNNER"
