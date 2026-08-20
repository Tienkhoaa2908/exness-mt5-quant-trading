#!/usr/bin/env bash
set +e
WORK="${WORK:-$HOME/v31_mt5_40usd}"
BRANCH="${BRANCH:-agent/v30-ml-dl-feature-lake}"
LOG="$HOME/v34_v35_bootstrap.log"
exec > >(tee -a "$LOG") 2>&1
echo "=== V34/V35 PARALLEL ALPHA + AI META-ROUTER ==="
date
RC=0
if [[ ! -d "$WORK/.git" ]]; then echo "FATAL: expected existing repo at $WORK"; RC=2
else
 git -C "$WORK" fetch origin "$BRANCH"; RC=$?
 [[ $RC -eq 0 ]] && git -C "$WORK" checkout -f "$BRANCH"; RC=$?
 [[ $RC -eq 0 ]] && git -C "$WORK" reset --hard "origin/$BRANCH"; RC=$?
fi
if [[ $RC -eq 0 ]]; then
 echo "HEAD=$(git -C "$WORK" rev-parse HEAD)"
 RUNNER="$WORK/runtime/v34_parallel_alpha/RUN_V34_V35_PARALLEL_ALPHA_GIT_BASH.sh"
 if [[ -s "$RUNNER" ]]; then bash "$RUNNER"; RC=$?; else echo "FATAL: runner missing $RUNNER"; RC=3; fi
fi
echo
echo "=== V34/V35 FINISHED rc=$RC ==="
echo "Bootstrap log: $LOG"
echo "Runner log: $WORK/runtime/v34_parallel_alpha/OUTPUT_V34_V35/v34_v35_runner.log"
if [[ $RC -ne 0 ]]; then echo "Do not blindly rerun if MT5_DONE.txt exists; the runner will collect-only on retry."; fi
read -r -p "Press ENTER after copying the final status... " _
exit $RC
