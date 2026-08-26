#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

PY="runtime/v31_mt5_model_gate/OUTPUT_V31_1_MT5/.venv/Scripts/python.exe"
if [[ ! -x "$PY" ]]; then PY="python"; fi

echo "============================================================"
echo "=== V52R REAL-TICK REPRODUCIBILITY ONE-SHOT ==="
echo "============================================================"
echo "Exact V52 source; no alpha retune."
echo "Tester model: Every tick based on real ticks (Model=4)."
echo "Post-run: fail-closed price/R integrity gate before selection."
echo "Close MetaEditor and MT5 before starting."
echo

"$PY" runtime/v52r_real_tick/RUN_V52R_REAL_TICK_ONE_SHOT.py

echo
echo "============================================================"
echo "V52R ONE-SHOT COMPLETE"
echo "Upload only: runtime/v52r_real_tick/OUTPUT_V52R/v52r_real_tick_repro.zip"
echo "============================================================"
