#!/usr/bin/env bash
set -Eeuo pipefail

WORK="${WORK:-$HOME/v31_mt5_40usd}"
BRANCH="${BRANCH:-agent/v39-selective-harvest}"
REMOTE="${REMOTE:-origin}"
LOG="$HOME/v39_selective_harvest_bootstrap.log"
exec > >(tee -a "$LOG") 2>&1

echo "=== V39 SELECTIVE HARVEST — STAGE A ==="
date
echo "OFFLINE/read-only research. This bootstrap does not launch MT5 and cannot send broker orders."
echo "REAL-MONEY LIVE TRADING remains FORBIDDEN."

[[ -d "$WORK/.git" ]] || { echo "FATAL: repository not found at $WORK" >&2; exit 2; }

REMOTE_REF="refs/remotes/$REMOTE/$BRANCH"
LOCAL_REF="refs/heads/$BRANCH"

echo "Fetching canonical branch with explicit refspec..."
git -C "$WORK" fetch --no-tags "$REMOTE" "+refs/heads/$BRANCH:$REMOTE_REF"

git -C "$WORK" show-ref --verify --quiet "$REMOTE_REF" || {
  echo "FATAL: remote branch was not materialized at $REMOTE_REF" >&2
  exit 3
}

# Force the local research branch to the canonical remote branch. Deliberately do
# not use git clean: accepted V36/V38 evidence may be untracked local runtime data.
git -C "$WORK" checkout -B "$BRANCH" "$REMOTE_REF"
git -C "$WORK" reset --hard "$REMOTE_REF"

HEAD="$(git -C "$WORK" rev-parse HEAD)"
echo "HEAD=$HEAD"
echo "BRANCH=$(git -C "$WORK" branch --show-current)"

RUNNER="$WORK/runtime/v39_selective_harvest/RUN_V39_SELECTIVE_HARVEST_STAGE_A_GIT_BASH.sh"
[[ -s "$RUNNER" ]] || { echo "FATAL: V39 runner missing: $RUNNER" >&2; exit 4; }

bash -n "$RUNNER"
bash "$RUNNER"
