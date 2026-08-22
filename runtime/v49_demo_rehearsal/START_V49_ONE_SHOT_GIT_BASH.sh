#!/usr/bin/env bash
set -Eeuo pipefail
export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
WORK="${WORK:-$(cd -- "$SCRIPT_DIR/../.." && pwd -P)}"
BRANCH="agent/v49-one-shot-demo-rehearsal"
VENV="$WORK/runtime/v31_mt5_model_gate/OUTPUT_V31_1_MT5/.venv"
PY="$VENV/Scripts/python.exe"
RUNNER="$SCRIPT_DIR/RUN_V49_ONE_SHOT.py"
SUPERVISOR="$SCRIPT_DIR/SUPERVISE_V49_ONE_SHOT.py"
BUILDER="$WORK/scripts/build_v49_one_shot_demo_rehearsal_source.py"
TEST="$WORK/tests/test_v49_one_shot_demo_rehearsal_static.py"

[[ -d "$WORK/.git" ]] || { echo "FATAL: git checkout missing: $WORK" >&2; exit 1; }
[[ "$(git -C "$WORK" branch --show-current)" == "$BRANCH" ]] || { echo "FATAL: checkout $BRANCH first" >&2; exit 1; }
[[ -x "$PY" ]] || { echo "FATAL: expected Python env missing: $PY" >&2; exit 1; }

echo "============================================================"
echo "=== V49 ONE-SHOT EXNESS DEMO PRODUCTION REHEARSAL ==="
echo "============================================================"
echo "WORK=$WORK"
echo "HEAD=$(git -C "$WORK" rev-parse HEAD)"
echo "Frozen alpha: v46_hl10_thr0p05_breadth4"
echo "One integrated campaign: native DEMO entry/exit + reconciliation + notification + final ZIP."
echo "REAL/non-DEMO account is hard-refused by the V49 EA."
echo

echo "=== STATIC / SECRET GATES ==="
bash -n "$0"
"$PY" -m py_compile \
  "$(cygpath -w "$RUNNER")" \
  "$(cygpath -w "$SUPERVISOR")" \
  "$(cygpath -w "$BUILDER")" \
  "$(cygpath -w "$TEST")"
"$PY" "$(cygpath -w "$TEST")"
"$PY" "$(cygpath -w "$WORK/scripts/secret_scan.py")" "$(cygpath -w "$WORK")"

echo
cat <<'EOF'
V49 one-shot transition:
- Keep the Exness account on DEMO.
- If V48 is running and FLAT, the runner closes MT5 gracefully and transitions state automatically.
- If V48 has an OPEN virtual position, it fails closed and leaves V48 running; rerun this same command after V48 returns FLAT.
- Close MetaEditor beforehand if it is open.
- Optional: configure/test MetaQuotes push notifications in MT5 beforehand if phone alerts are wanted.
EOF

echo
"$PY" "$(cygpath -w "$RUNNER")"

echo
echo "============================================================"
echo "V49 one-shot started. Git Bash may be closed after START PASS."
echo "Keep the PC, Internet and MT5 running."
echo "The detached supervisor will create one final ZIP under:"
echo "  runtime/v49_demo_rehearsal/OUTPUT_V49/"
echo "============================================================"
