#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

PY="runtime/v31_mt5_model_gate/OUTPUT_V31_1_MT5/.venv/Scripts/python.exe"
if [[ ! -x "$PY" ]]; then PY="python"; fi

echo "============================================================"
echo "=== V52 SOURCE-AWARE ONE-SHOT TOURNAMENT ==="
echo "============================================================"
echo "Baseline: frozen v46_hl10_thr0p05_breadth4"
echo "Challengers: breadth4 OR source-filtered exactly-3 healthy lane"
echo "Sources: TREND20_H1 / BOS_FVG_H1 / either"
echo "One exact historical MT5 run; one final ZIP."
echo "Close MetaEditor and MT5 before the tester run."
echo

"$PY" runtime/v52_source_aware/RUN_V52_SOURCE_AWARE_ONE_SHOT.py

echo
echo "============================================================"
echo "V52 ONE-SHOT COMPLETE"
echo "Upload only: runtime/v52_source_aware/OUTPUT_V52/v52_source_aware_tournament.zip"
echo "============================================================"
