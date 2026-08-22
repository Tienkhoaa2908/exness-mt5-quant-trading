#!/usr/bin/env bash
set -Eeuo pipefail
export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
WORK="$(cd -- "$SCRIPT_DIR/../.." && pwd -P)"
PY="$WORK/runtime/v31_mt5_model_gate/OUTPUT_V31_1_MT5/.venv/Scripts/python.exe"
[[ -x "$PY" ]] || { echo "FATAL: Python env missing: $PY" >&2; exit 1; }
"$PY" "$(cygpath -w "$SCRIPT_DIR/STATUS_V48_DEMO_PAPER.py")"
