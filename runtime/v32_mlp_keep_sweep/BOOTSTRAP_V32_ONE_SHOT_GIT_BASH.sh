#!/usr/bin/env bash
# V32 one-shot interactive bootstrap. Does not intentionally close parent Git Bash.
set +e

REPO="https://github.com/Tienkhoaa2908/exness-mt5-quant-trading.git"
BRANCH="agent/v30-ml-dl-feature-lake"
WORK="$HOME/v31_mt5_40usd"
BOOTLOG="$HOME/v32_mlp_keep_sweep_bootstrap.log"

{
  echo "=== V32 DEEPMLP KEEP-RATE EXACT-MT5 SWEEP ==="
  date
  echo "Safety: Strategy Tester research only; REAL-MONEY LIVE TRADING FORBIDDEN."
  echo "Deposit=USD40 continuous; risk ceiling=1.00%/trade."
  echo "Development modes: baseline + DeepMLP keep 50/60/70/80/90%."
  if [[ -d "$WORK/.git" ]]; then
    git -C "$WORK" fetch origin "$BRANCH" || exit $?
    git -C "$WORK" checkout -f "$BRANCH" || exit $?
    git -C "$WORK" reset --hard "origin/$BRANCH" || exit $?
  else
    git clone --depth 1 --single-branch --branch "$BRANCH" "$REPO" "$WORK" || exit $?
  fi
  echo "HEAD=$(git -C "$WORK" rev-parse HEAD)"
  if tasklist.exe //FI "IMAGENAME eq terminal64.exe" 2>/dev/null | tr -d '\r' | grep -qi terminal64.exe; then
    echo "ERROR: MetaTrader 5 is open. Close MT5 completely and rerun this same block."
    exit 70
  fi
  cd "$WORK/runtime/v32_mlp_keep_sweep" || exit 71
  bash ./RUN_V32_DEEP_MLP_KEEP_SWEEP_GIT_BASH.sh
  rc=$?
  echo
  echo "=== V32 RUNNER FINISHED rc=$rc ==="
  exit $rc
} 2>&1 | tee "$BOOTLOG"

RC=${PIPESTATUS[0]}
echo
echo "============================================================"
if [[ $RC -eq 0 ]]; then
  echo "V32 COMPLETED SUCCESSFULLY"
  echo "Upload the ZIP shown after 'UPLOAD THIS ONE ZIP'."
else
  echo "V32 FAILED rc=$RC"
  echo "Do not delete completed checkpoints."
  echo "Bootstrap log: $BOOTLOG"
  echo "Runner log: $WORK/runtime/v32_mlp_keep_sweep/OUTPUT_V32_MT5/v32_mlp_keep_sweep_runner.log"
fi
echo "============================================================"
echo
read -r -p "Press ENTER only after you have read/copied the final status..." _
exit 0
