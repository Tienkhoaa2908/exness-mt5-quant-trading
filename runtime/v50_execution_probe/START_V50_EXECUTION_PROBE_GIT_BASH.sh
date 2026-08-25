#!/usr/bin/env bash
set -Eeuo pipefail
export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
WORK="${WORK:-$(cd -- "$SCRIPT_DIR/../.." && pwd -P)}"
BRANCH="agent/v50-execution-probe"
PY="$WORK/runtime/v31_mt5_model_gate/OUTPUT_V31_1_MT5/.venv/Scripts/python.exe"
RUNNER="$SCRIPT_DIR/RUN_V50_EXECUTION_PROBE.py"
SUPERVISOR="$SCRIPT_DIR/SUPERVISE_V50_EXECUTION_PROBE.py"
BUILDER="$WORK/scripts/build_v50_execution_probe_source.py"
TEST="$WORK/tests/test_v50_execution_probe_static.py"
[[ -d "$WORK/.git" ]] || { echo "FATAL: git checkout missing" >&2; exit 1; }
[[ "$(git -C "$WORK" branch --show-current)" == "$BRANCH" ]] || { echo "FATAL: checkout $BRANCH first" >&2; exit 1; }
[[ -x "$PY" ]] || { echo "FATAL: Python env missing" >&2; exit 1; }
echo "============================================================"
echo "=== V50 FAST DEMO EXECUTION QUALIFICATION ==="
echo "============================================================"
echo "Frozen breadth4 stays unchanged."
echo "Three min-volume DEMO probes qualify order/open/close/reconciliation/notification independently of alpha frequency."
bash -n "$0"
"$PY" -m py_compile "$(cygpath -w "$RUNNER")" "$(cygpath -w "$SUPERVISOR")" "$(cygpath -w "$BUILDER")" "$(cygpath -w "$TEST")"
"$PY" "$(cygpath -w "$TEST")"
"$PY" "$(cygpath -w "$WORK/scripts/secret_scan.py")" "$(cygpath -w "$WORK")"
echo
"$PY" "$(cygpath -w "$RUNNER")"
echo
echo "V50 started. Keep PC + Internet + MT5 running. One final ZIP will appear under runtime/v50_execution_probe/OUTPUT_V50/."
