#!/usr/bin/env bash
# V31.1 one-shot interactive bootstrap. Never intentionally closes the parent Git Bash.
set +e

REPO="https://github.com/Tienkhoaa2908/exness-mt5-quant-trading.git"
BRANCH="agent/v30-ml-dl-feature-lake"
WORK="$HOME/v31_mt5_40usd"
BOOTLOG="$HOME/v31_mt5_40usd_bootstrap.log"

{
  echo "=== V31.1 CONTINUOUS USD40 EXACT-MT5 MODEL GATE ==="
  date
  echo "Safety: Strategy Tester research only; REAL-MONEY LIVE TRADING FORBIDDEN."
  echo "Tester Deposit=USD40; continuous target book risk=1.00%/trade."
  echo "Models: baseline, CatBoost, ExtraTrees, DeepMLP 64-32-16, LinearSVM, CB+ET, majority."
  echo "WORK=$WORK"

  if [[ -d "$WORK/.git" ]]; then
    echo "[1/4] Update repository..."
    git -C "$WORK" fetch origin "$BRANCH" || exit $?
    git -C "$WORK" checkout -f "$BRANCH" || exit $?
    git -C "$WORK" reset --hard "origin/$BRANCH" || exit $?
  else
    echo "[1/4] Clone repository..."
    rm -rf "$WORK"
    git clone --depth 1 --single-branch --branch "$BRANCH" "$REPO" "$WORK" || exit $?
  fi

  echo "HEAD=$(git -C "$WORK" rev-parse HEAD)"
  echo "[2/4] Preflight..."
  if tasklist.exe //FI "IMAGENAME eq terminal64.exe" 2>/dev/null | tr -d '\r' | grep -qi terminal64.exe; then
    echo "ERROR: MetaTrader 5 is currently open. Close MT5 completely and rerun this same block."
    exit 70
  fi

  RUNNER="$WORK/runtime/v31_mt5_model_gate/RUN_V31_1_EXACT_MT5_USD40_GIT_BASH.sh"
  PATCHER="$WORK/scripts/patch_v31_1_runner_locals.py"
  [[ -s "$RUNNER" ]] || { echo "ERROR: V31.1 runner missing: $RUNNER"; exit 71; }
  [[ -s "$PATCHER" ]] || { echo "ERROR: V31.1 runner patcher missing: $PATCHER"; exit 73; }

  echo "[3/4] Apply deterministic Bash local-declaration hardening..."
  if command -v python >/dev/null 2>&1; then PY_BOOT="$(command -v python)"; elif command -v python3 >/dev/null 2>&1; then PY_BOOT="$(command -v python3)"; else echo "ERROR: Python 3 not found for bootstrap patch"; exit 74; fi
  "$PY_BOOT" "$PATCHER" "$RUNNER" || exit $?
  bash -n "$RUNNER" || { echo "ERROR: patched runner failed bash -n"; exit 75; }

  echo "[4/4] Run exact MT5 model tournament..."
  cd "$WORK/runtime/v31_mt5_model_gate" || exit 72
  bash ./RUN_V31_1_EXACT_MT5_USD40_GIT_BASH.sh
  rc=$?
  echo
  echo "=== V31.1 RUNNER FINISHED rc=$rc ==="
  exit $rc
} 2>&1 | tee "$BOOTLOG"

RC=${PIPESTATUS[0]}
echo
echo "============================================================"
if [[ $RC -eq 0 ]]; then
  echo "V31.1 COMPLETED SUCCESSFULLY"
  echo "The exact MT5 comparison is printed above."
  echo "Find 'UPLOAD THIS ONE ZIP' and upload that ZIP."
else
  echo "V31.1 FAILED rc=$RC"
  echo "Do NOT repeatedly rerun completed model checkpoints."
  echo "Send this log: $BOOTLOG"
  echo "Runner log:"
  echo "$WORK/runtime/v31_mt5_model_gate/OUTPUT_V31_1_MT5/v31_1_mt5_usd40_runner.log"
fi
echo "============================================================"
echo
read -r -p "Press ENTER only after you have read/copied the final status..." _
exit 0
