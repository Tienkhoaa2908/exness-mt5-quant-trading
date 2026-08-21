#!/usr/bin/env bash
set -Eeuo pipefail

WORK="${WORK:-$HOME/v31_mt5_40usd}"
BRANCH="${BRANCH:-agent/v39-selective-harvest}"
LOG="$HOME/v39_selective_harvest_bootstrap.log"
exec > >(tee -a "$LOG") 2>&1

echo "=== V39 SELECTIVE HARVEST — STAGE A ==="
date
echo "OFFLINE/read-only research. This bootstrap does not launch MT5 and cannot send broker orders."
echo "REAL-MONEY LIVE TRADING remains FORBIDDEN."

[[ -d "$WORK/.git" ]] || { echo "FATAL: repository not found at $WORK" >&2; exit 2; }

git -C "$WORK" fetch origin "$BRANCH"
git -C "$WORK" checkout -f "$BRANCH"
git -C "$WORK" reset --hard "origin/$BRANCH"

echo "HEAD=$(git -C "$WORK" rev-parse HEAD)"
RUNNER="$WORK/runtime/v39_selective_harvest/RUN_V39_SELECTIVE_HARVEST_STAGE_A_GIT_BASH.sh"
[[ -s "$RUNNER" ]] || { echo "FATAL: V39 runner missing: $RUNNER" >&2; exit 3; }

bash -n "$RUNNER"
bash "$RUNNER"
