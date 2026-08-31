#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
WORK="$(cd -- "$SCRIPT_DIR/../.." && pwd -P)"
PREP="$SCRIPT_DIR/PREPARE_V69_FROZEN_FORWARD_DEMO.py"
BRANCH="agent/v69-frozen-forward-demo-validation"
EXPECTED="${V69_FORWARD_EXPECTED_HEAD:-}"
STAMP="$(date +%Y%m%d_%H%M%S)"
LOG_DIR="$SCRIPT_DIR/OUTPUT_FORWARD_PREP"
LOG="$LOG_DIR/V69_FORWARD_PREP_${STAMP}.log"

if [[ -z "$EXPECTED" ]]; then
    printf '%s\n' 'FATAL: V69_FORWARD_EXPECTED_HEAD is required.'
    printf '%s\n' 'Refusing an unpinned forward preparation.'
    exit 100
fi

cd "$WORK"

printf '%s\n' '============================================================'
printf '%s\n' 'V69 FROZEN FORWARD DEMO - PREPARE ONLY'
printf 'BRANCH=%s\n' "$BRANCH"
printf 'EXPECTED_HEAD=%s\n' "$EXPECTED"
printf '%s\n' '============================================================'

ORIGIN="$(git remote get-url origin)"
CURRENT="$(git branch --show-current)"
HEAD="$(git rev-parse HEAD)"

printf 'ORIGIN=%s\n' "$ORIGIN"
printf 'CURRENT_BRANCH=%s\n' "$CURRENT"
printf 'CURRENT_HEAD=%s\n' "$HEAD"

case "$ORIGIN" in
  *Tienkhoaa2908/exness-mt5-quant-trading*) ;;
  *) printf '%s\n' 'FATAL: wrong repository origin'; exit 101 ;;
esac

[[ "$CURRENT" == "$BRANCH" ]] || {
    printf 'FATAL: wrong branch expected=%s actual=%s\n' "$BRANCH" "$CURRENT"
    exit 102
}

[[ "$HEAD" == "$EXPECTED" ]] || {
    printf 'FATAL: wrong HEAD expected=%s actual=%s\n' "$EXPECTED" "$HEAD"
    exit 103
}

if [[ -n "$(git status --porcelain)" ]]; then
    printf '%s\n' 'FATAL: working tree dirty'
    git status --porcelain
    printf '%s\n' 'DO NOT git clean'
    printf '%s\n' 'DO NOT stash pop'
    exit 104
fi

if tasklist.exe 2>/dev/null | grep -qi 'terminal64.exe'; then
    printf '%s\n' 'FATAL: MT5 is open. Close terminal64.exe before preparation.'
    exit 105
fi

if tasklist.exe 2>/dev/null | grep -qi 'metaeditor64.exe'; then
    printf '%s\n' 'FATAL: MetaEditor is open. Close metaeditor64.exe before preparation.'
    exit 106
fi

[[ -s "$PREP" ]] || {
    printf 'FATAL: missing preparation runner: %s\n' "$PREP"
    exit 107
}

PY=()

if command -v py.exe >/dev/null 2>&1 && py.exe -3 -c 'import sys; print(sys.executable)' >/dev/null 2>&1; then
    PY=(py.exe -3)
elif command -v python.exe >/dev/null 2>&1 && python.exe -c 'import sys; print(sys.executable)' >/dev/null 2>&1; then
    PY=(python.exe)
elif command -v python >/dev/null 2>&1 && python -c 'import sys; print(sys.executable)' >/dev/null 2>&1; then
    PY=(python)
else
    printf '%s\n' 'FATAL: no working Python interpreter found.'
    exit 108
fi

printf 'PYTHON_COMMAND='
printf '%q ' "${PY[@]}"
printf '\n'
"${PY[@]}" --version

printf '%s\n' 'PREPARATION CONTRACT:'
printf '%s\n' '  frozen V69 LONG semantics'
printf '%s\n' '  XAUUSDm M15'
printf '%s\n' '  fixed lot 0.01'
printf '%s\n' '  planned risk $0.85-$1.10'
printf '%s\n' '  emergency loss about $1.20 best effort'
printf '%s\n' '  target +$3.50'
printf '%s\n' '  separation >= $1.30'
printf '%s\n' '  confirmation age >= 30 seconds'
printf '%s\n' '  SHORT disabled'
printf '%s\n' '  DEMO account only'
printf '%s\n' '  REAL money authorization = false'
printf '%s\n' '  this step compiles/installs only; it does not start evidence'

mkdir -p "$LOG_DIR"

set +e
(
  set -Eeuo pipefail
  export V69_FORWARD_EXPECTED_HEAD="$EXPECTED"
  "${PY[@]}" "$PREP"
) 2>&1 | tee "$LOG"
RC=${PIPESTATUS[0]}
set -e

printf '%s\n' '============================================================'
printf 'V69_FORWARD_PREP_EXIT_CODE=%s\n' "$RC"
printf 'V69_FORWARD_PREP_LOG=%s\n' "$LOG"
printf '%s\n' '============================================================'

if [[ "$RC" -ne 0 ]]; then
    printf '%s\n' 'V69_FORWARD_PREPARATION=FAILED'
    printf '%s\n' 'DO NOT rerun blindly.'
    printf '%s\n' 'DO NOT git clean.'
    printf '%s\n' 'DO NOT stash pop.'
    exit "$RC"
fi

printf '%s\n' 'V69_FORWARD_PREPARATION=PASS'
printf '%s\n' 'Next: open an Exness DEMO account, XAUUSDm M15, then attach V69FrozenForwardDemoLong.'
printf '%s\n' 'Do not attach this candidate to a REAL account; the EA also refuses non-DEMO accounts.'
exit 0
