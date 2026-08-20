#!/usr/bin/env bash
set +e

WORK="${WORK:-$HOME/v31_mt5_40usd}"
BRANCH="${BRANCH:-agent/v30-ml-dl-feature-lake}"
LOG="$HOME/v38_fast_harvest_bootstrap.log"
exec > >(tee -a "$LOG") 2>&1

echo "=== V38 FAST HARVEST LAB — EXACT MT5 ==="
date
echo "Preserves V34 baseline/specialists, V32 keep60 research, and V36 sequence-AI evidence."
echo "Adds exit-only fast-harvest clones + M1/tick telemetry. LIVE orders remain forbidden."

RC=0
if [[ ! -d "$WORK/.git" ]]; then
  echo "FATAL: expected repository at $WORK"
  RC=2
else
  git -C "$WORK" fetch origin "$BRANCH"; RC=$?
  [[ $RC -eq 0 ]] && git -C "$WORK" checkout -f "$BRANCH"; RC=$?
  [[ $RC -eq 0 ]] && git -C "$WORK" reset --hard "origin/$BRANCH"; RC=$?
fi

if [[ $RC -eq 0 ]]; then
  echo "HEAD=$(git -C "$WORK" rev-parse HEAD)"
  RUNNER="$WORK/runtime/v38_fast_harvest/RUN_V38_FAST_HARVEST_EXACT_MT5_GIT_BASH.sh"
  if [[ ! -s "$RUNNER" ]]; then
    echo "FATAL: V38 runner missing: $RUNNER"
    RC=3
  elif ! bash -n "$RUNNER"; then
    echo "FATAL: bash -n failed for V38 runner"
    RC=4
  else
    bash "$RUNNER"
    RC=$?
  fi
fi

echo
echo "=== V38 FINISHED rc=$RC ==="
echo "Bootstrap log: $LOG"
if [[ $RC -ne 0 ]]; then
  echo "If OUTPUT_V38/checkpoints/v38_fast_harvest/MT5_DONE.txt exists, do not rerun tester manually."
  echo "The V38 runner is checkpointed and will recover collection/analysis without duplicating MT5."
fi
read -r -p "Press ENTER after copying the final status... " _
exit $RC
