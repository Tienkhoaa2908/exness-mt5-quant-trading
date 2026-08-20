#!/usr/bin/env bash
set +e
REPO="https://github.com/Tienkhoaa2908/exness-mt5-quant-trading.git"
BRANCH="agent/v30-ml-dl-feature-lake"
WORK="$HOME/v31_mt5_40usd"
BOOTLOG="$HOME/v33_multitask_bootstrap.log"
{
  echo "=== V33 MULTITASK NEURAL DIAGNOSTIC ==="
  date
  echo "READ-ONLY: no MT5 launch, no adaptive-state write, no broker orders."
  if [[ -d "$WORK/.git" ]]; then
    git -C "$WORK" fetch origin "$BRANCH" || exit $?
    git -C "$WORK" checkout -f "$BRANCH" || exit $?
    git -C "$WORK" reset --hard "origin/$BRANCH" || exit $?
  else
    git clone --depth 1 --single-branch --branch "$BRANCH" "$REPO" "$WORK" || exit $?
  fi
  echo "HEAD=$(git -C "$WORK" rev-parse HEAD)"
  RUNNER="$WORK/runtime/v33_neural_policy/RUN_V33_MULTITASK_DIAGNOSTIC_GIT_BASH.sh"
  [[ -s "$RUNNER" ]] || { echo "ERROR: runner missing: $RUNNER"; exit 71; }
  bash "$RUNNER"
  rc=$?
  echo "=== V33 DIAGNOSTIC FINISHED rc=$rc ==="
  exit $rc
} 2>&1 | tee "$BOOTLOG"
RC=${PIPESTATUS[0]}
echo
echo "============================================================"
if [[ $RC -eq 0 ]]; then
  echo "V33 DIAGNOSTIC COMPLETED"
  echo "Upload the ZIP printed above."
else
  echo "V33 DIAGNOSTIC FAILED rc=$RC"
  echo "Send log: $BOOTLOG"
fi
echo "============================================================"
read -r -p "Press ENTER after reading/copying the final status..." _
exit 0
