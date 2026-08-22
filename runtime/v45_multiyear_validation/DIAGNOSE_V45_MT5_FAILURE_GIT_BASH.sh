#!/usr/bin/env bash
set -Eeuo pipefail
export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
REPO_ROOT="$(cd -- "$ROOT/../.." && pwd -P)"
PY="$REPO_ROOT/runtime/v31_mt5_model_gate/OUTPUT_V31_1_MT5/.venv/Scripts/python.exe"
DIAG="$ROOT/DIAGNOSE_V45_MT5_FAILURE.py"

[[ -x "$PY" ]] || { echo "FATAL: pinned Python missing: $PY" >&2; exit 1; }
[[ -s "$DIAG" ]] || { echo "FATAL: diagnostic script missing: $DIAG" >&2; exit 1; }

printf '%s\n' "=== V45 DIAGNOSTICS ONLY ==="
printf '%s\n' "This command DOES NOT launch MT5, MetaEditor, or Strategy Tester."
printf '%s\n' "It only harvests the logs/history inventory from the failed V45 attempt."

"$PY" -m py_compile "$DIAG"
"$PY" "$DIAG"
