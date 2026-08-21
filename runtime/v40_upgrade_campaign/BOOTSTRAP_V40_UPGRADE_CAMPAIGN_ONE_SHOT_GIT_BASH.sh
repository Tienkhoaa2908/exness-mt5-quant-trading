#!/usr/bin/env bash
set -Eeuo pipefail
WORK="${WORK:-$HOME/v31_mt5_40usd}"
BRANCH="${BRANCH:-agent/v40-upgrade-campaign}"
REMOTE="${REMOTE:-origin}"
LOG="$HOME/v40_upgrade_campaign_bootstrap.log"
exec > >(tee -a "$LOG") 2>&1

echo "=== V40 UPGRADE CAMPAIGN — ONE SHOT ==="
date
echo "OFFLINE/read-only Stage A. No MT5 launch, no broker orders, LIVE forbidden."
[[ -d "$WORK/.git" ]] || { echo "FATAL: repository not found at $WORK" >&2; exit 2; }
REMOTE_REF="refs/remotes/$REMOTE/$BRANCH"
git -C "$WORK" fetch --no-tags "$REMOTE" "+refs/heads/$BRANCH:$REMOTE_REF"
git -C "$WORK" show-ref --verify --quiet "$REMOTE_REF" || { echo "FATAL: remote branch missing" >&2; exit 3; }
git -C "$WORK" checkout -B "$BRANCH" "$REMOTE_REF"
git -C "$WORK" reset --hard "$REMOTE_REF"
# Deliberately no git clean: accepted V36/V38 runtime evidence and venvs may be untracked.
echo "HEAD=$(git -C "$WORK" rev-parse HEAD)"
echo "BRANCH=$(git -C "$WORK" branch --show-current)"
RUNNER="$WORK/runtime/v40_upgrade_campaign/RUN_V40_UPGRADE_CAMPAIGN_STAGE_A_GIT_BASH.sh"
[[ -s "$RUNNER" ]] || { echo "FATAL: runner missing: $RUNNER" >&2; exit 4; }
bash -n "$RUNNER"
bash "$RUNNER"
