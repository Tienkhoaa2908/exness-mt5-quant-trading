#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

PY="runtime/v31_mt5_model_gate/OUTPUT_V31_1_MT5/.venv/Scripts/python.exe"
if [[ ! -x "$PY" ]]; then PY="python"; fi

echo "============================================================"
echo "=== V53 TREND+BOS SHORT BROKER-DEMO CONFIRMATION ==="
echo "============================================================"
echo "Selected candidate: v52_b4_or_b3_trend_bos"
echo "Natural strategy intent only; no execution-probe trades."
echo "Target: >=2 market days and >=1 broker-confirmed natural round trip."
echo "DEMO account only; non-DEMO is fail-closed."
echo

"$PY" runtime/v53_trend_bos_demo/RUN_V53_TREND_BOS_DEMO.py

echo
echo "============================================================"
echo "V53 START COMPLETE"
echo "Do not run START again. Keep MT5, PC and Internet running."
echo "Supervisor will package one ZIP after FINAL."
echo "============================================================"
