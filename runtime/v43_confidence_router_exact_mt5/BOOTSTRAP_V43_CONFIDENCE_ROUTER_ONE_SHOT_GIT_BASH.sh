#!/usr/bin/env bash
set -Eeuo pipefail
export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8

WORK="${WORK:-$HOME/v31_mt5_40usd}"
BRANCH="${BRANCH:-agent/v43-confidence-aware-router-exact-mt5}"
REMOTE="${REMOTE:-origin}"
REMOTE_REF="refs/remotes/$REMOTE/$BRANCH"
RUNNER="$WORK/runtime/v43_confidence_router_exact_mt5/RUN_V43_CONFIDENCE_ROUTER_EXACT_MT5_GIT_BASH.sh"
PACKAGE_ONLY="$WORK/runtime/v43_confidence_router_exact_mt5/PACKAGE_V43_EXISTING_OUTPUT_GIT_BASH.sh"
BUNDLE="$WORK/runtime/v43_confidence_router_exact_mt5/OUTPUT_V43/bundle"

[[ -d "$WORK/.git" ]] || { echo "FATAL: Git checkout missing: $WORK" >&2; exit 1; }
echo "=== V43 CONFIDENCE-AWARE ROUTER — EXACT MT5 BOOTSTRAP ==="
echo "REAL-MONEY LIVE TRADING remains FORBIDDEN."

git -C "$WORK" fetch --no-tags "$REMOTE" "+refs/heads/$BRANCH:$REMOTE_REF"
git -C "$WORK" show-ref --verify --quiet "$REMOTE_REF" || { echo "FATAL: remote ref missing $REMOTE_REF" >&2; exit 1; }
git -C "$WORK" checkout -B "$BRANCH" "$REMOTE_REF"
git -C "$WORK" reset --hard "$REMOTE_REF"

echo "HEAD=$(git -C "$WORK" rev-parse HEAD)"
echo "BRANCH=$(git -C "$WORK" branch --show-current)"
echo "PYTHONUTF8=$PYTHONUTF8 PYTHONIOENCODING=$PYTHONIOENCODING"

[[ -s "$RUNNER" ]] || { echo "FATAL: direct V43 runner missing: $RUNNER" >&2; exit 1; }
[[ -s "$PACKAGE_ONLY" ]] || { echo "FATAL: package-only V43 recovery missing: $PACKAGE_ONLY" >&2; exit 1; }
bash -n "$RUNNER"
bash -n "$PACKAGE_ONLY"
cd "$WORK"

if bash "$RUNNER"; then
  exit 0
else
  rc=$?
fi

# Critical recovery invariant learned from V42:
# never rerun exact MT5 merely because final packaging failed after evidence exists.
if [[ -s "$BUNDLE/V43_EVIDENCE.txt" \
   && -s "$BUNDLE/v43_confidence_router_analysis.json" \
   && -s "$BUNDLE/monthly_summary.csv" \
   && -s "$BUNDLE/trades.csv" \
   && -s "$BUNDLE/manifest.txt" ]]; then
  echo "V43 runner returned rc=$rc after completed evidence; attempting package-only recovery. MT5 WILL NOT RERUN."
  bash "$PACKAGE_ONLY"
  exit 0
fi

exit "$rc"
