#!/usr/bin/env bash
# V31 one-shot interactive bootstrap. Never intentionally closes the parent Git Bash.
set +e

REPO="https://github.com/Tienkhoaa2908/exness-mt5-quant-trading.git"
BRANCH="agent/v30-ml-dl-feature-lake"
WORK="$HOME/v31_mt5_40usd"
BOOTLOG="$HOME/v31_mt5_40usd_bootstrap.log"

{
  echo "=== V31 USD40 EXACT-MT5 MODEL GATE ==="
  date
  echo "Safety: Strategy Tester research only; REAL-MONEY LIVE TRADING FORBIDDEN."
  echo "Decision capital: USD40; research risk ceiling: 1.00%/trade."
  echo "WORK=$WORK"

  if [[ -d "$WORK/.git" ]]; then
    echo "[1/3] Update repository..."
    git -C "$WORK" fetch origin "$BRANCH" || exit $?
    git -C "$WORK" checkout -f "$BRANCH" || exit $?
    git -C "$WORK" reset --hard "origin/$BRANCH" || exit $?
  else
    echo "[1/3] Clone repository..."
    rm -rf "$WORK"
    git clone --depth 1 --single-branch --branch "$BRANCH" "$REPO" "$WORK" || exit $?
  fi

  echo "HEAD=$(git -C "$WORK" rev-parse HEAD)"
  echo "[2/3] Preflight..."
  if tasklist.exe //FI "IMAGENAME eq terminal64.exe" 2>/dev/null | tr -d '\r' | grep -qi terminal64.exe; then
    echo "ERROR: MetaTrader 5 is currently open. Close MT5 completely and rerun this same block."
    exit 70
  fi

  RUNNER="$WORK/runtime/v31_mt5_model_gate/RUN_V31_MT5_MODEL_GATE_GIT_BASH.sh"
  [[ -s "$RUNNER" ]] || { echo "ERROR: runner missing: $RUNNER"; exit 71; }
  echo "[3/3] Run exact MT5 model gate..."
  cd "$WORK/runtime/v31_mt5_model_gate" || exit 72
  bash ./RUN_V31_MT5_MODEL_GATE_GIT_BASH.sh
  rc=$?
  echo
  echo "=== V31 RUNNER FINISHED rc=$rc ==="
  exit $rc
} 2>&1 | tee "$BOOTLOG"

RC=${PIPESTATUS[0]}
echo
echo "============================================================"
if [[ $RC -eq 0 ]]; then
  echo "V31 COMPLETED SUCCESSFULLY"
  echo "Find the line 'UPLOAD THIS ONE ZIP' above and upload that ZIP."
else
  echo "V31 FAILED rc=$RC"
  echo "Do NOT repeatedly restart MT5 if a completed model checkpoint exists."
  echo "Send this log instead:"
  echo "$BOOTLOG"
  echo "Runner log:"
  echo "$WORK/runtime/v31_mt5_model_gate/OUTPUT_V31_MT5/v31_mt5_model_gate_runner.log"
fi
echo "============================================================"
echo
read -r -p "Press ENTER only after you have read/copied the final status..." _
exit 0
