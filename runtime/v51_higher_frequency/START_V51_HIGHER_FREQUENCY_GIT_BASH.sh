#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

PY="runtime/v31_mt5_model_gate/OUTPUT_V31_1_MT5/.venv/Scripts/python.exe"
if [[ ! -x "$PY" ]]; then PY="python"; fi

echo "============================================================"
echo "=== V51 HIGHER-FREQUENCY ONE-SHOT TOURNAMENT ==="
echo "============================================================"
echo "Baseline: frozen v46_hl10_thr0p05_breadth4"
echo "Challengers: breadth4 OR quality-filtered breadth3"
echo "One exact historical MT5 run; one final ZIP."
echo "Close MetaEditor and MT5 before the tester run."
echo

"$PY" runtime/v51_higher_frequency/RUN_V51_HIGHER_FREQUENCY_ONE_SHOT.py

echo
echo "============================================================"
echo "V51 ONE-SHOT COMPLETE"
echo "Upload only: runtime/v51_higher_frequency/OUTPUT_V51/v51_higher_frequency_tournament.zip"
echo "============================================================"
