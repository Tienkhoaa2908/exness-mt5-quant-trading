#!/usr/bin/env bash
set -Eeuo pipefail
export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8

WORK="${WORK:-$HOME/v31_mt5_40usd}"
BRANCH="${BRANCH:-agent/v42-baseline-router-exact-mt5}"
REMOTE="${REMOTE:-origin}"
REMOTE_REF="refs/remotes/$REMOTE/$BRANCH"
RUNNER="$WORK/runtime/v42_baseline_router_exact_mt5/RUN_V42_BASELINE_ROUTER_EXACT_MT5_GIT_BASH.sh"
PACKAGE_ONLY="$WORK/runtime/v42_baseline_router_exact_mt5/PACKAGE_V42_EXISTING_OUTPUT_GIT_BASH.sh"
BUNDLE="$WORK/runtime/v42_baseline_router_exact_mt5/OUTPUT_V42/bundle"

[[ -d "$WORK/.git" ]] || { echo "FATAL: Git checkout missing: $WORK" >&2; exit 1; }
echo "=== V42 BASELINE ROUTER — EXACT MT5 BOOTSTRAP ==="
echo "REAL-MONEY LIVE TRADING remains FORBIDDEN."

git -C "$WORK" fetch --no-tags "$REMOTE" "+refs/heads/$BRANCH:$REMOTE_REF"
git -C "$WORK" show-ref --verify --quiet "$REMOTE_REF" || { echo "FATAL: remote ref missing $REMOTE_REF" >&2; exit 1; }
git -C "$WORK" checkout -B "$BRANCH" "$REMOTE_REF"
git -C "$WORK" reset --hard "$REMOTE_REF"

echo "HEAD=$(git -C "$WORK" rev-parse HEAD)"
echo "BRANCH=$(git -C "$WORK" branch --show-current)"
echo "PYTHONUTF8=$PYTHONUTF8 PYTHONIOENCODING=$PYTHONIOENCODING"

[[ -s "$RUNNER" ]] || { echo "FATAL: direct V42 runner missing: $RUNNER" >&2; exit 1; }
[[ -s "$PACKAGE_ONLY" ]] || { echo "FATAL: package-only V42 recovery missing: $PACKAGE_ONLY" >&2; exit 1; }
bash -n "$RUNNER"
bash -n "$PACKAGE_ONLY"
cd "$WORK"

if bash "$RUNNER"; then
  exit 0
else
  rc=$?
fi

# Do not mask research/runtime failures. Only recover when the exact MT5 run and
# analyzer already completed and the remaining failure is final packaging.
if [[ -s "$BUNDLE/V42_EVIDENCE.txt" \
   && -s "$BUNDLE/v42_baseline_router_analysis.json" \
   && -s "$BUNDLE/monthly_summary.csv" \
   && -s "$BUNDLE/trades.csv" \
   && -s "$BUNDLE/manifest.txt" ]]; then
  echo "V42 runner returned rc=$rc after completed evidence; attempting package-only recovery."
  bash "$PACKAGE_ONLY"
  exit 0
fi

exit "$rc"
