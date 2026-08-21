#!/usr/bin/env bash
set -Eeuo pipefail
export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8

WORK="${WORK:-$HOME/v31_mt5_40usd}"
BRANCH="${BRANCH:-agent/v42-baseline-router-exact-mt5}"
REMOTE="${REMOTE:-origin}"
REMOTE_REF="refs/remotes/$REMOTE/$BRANCH"
RUNNER="$WORK/runtime/v42_baseline_router_exact_mt5/RUN_V42_BASELINE_ROUTER_EXACT_MT5_GIT_BASH.sh"

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
bash -n "$RUNNER"
cd "$WORK"
bash "$RUNNER"
