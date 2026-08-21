#!/usr/bin/env bash
set -Eeuo pipefail
WORK="${WORK:-$HOME/v31_mt5_40usd}"; BRANCH="${BRANCH:-agent/v41-baseline-stack-action-value}"; REMOTE="${REMOTE:-origin}"
REMOTE_REF="refs/remotes/$REMOTE/$BRANCH"; LOCAL_REF="refs/heads/$BRANCH"
echo "=== V41 BASELINE STACK + ACTION VALUE ==="
echo "OFFLINE/read-only research. REAL-MONEY LIVE TRADING remains FORBIDDEN."
[[ -d "$WORK/.git" ]] || { echo "FATAL: Git repo not found: $WORK" >&2; exit 1; }
git -C "$WORK" fetch --no-tags "$REMOTE" "+refs/heads/$BRANCH:$REMOTE_REF"
git -C "$WORK" show-ref --verify --quiet "$REMOTE_REF" || { echo "FATAL: remote branch missing" >&2; exit 1; }
git -C "$WORK" checkout -B "$BRANCH" "$REMOTE_REF"
git -C "$WORK" reset --hard "$REMOTE_REF"
# no git clean: accepted V36/V38 runtime evidence and .venv may be untracked and must be preserved.
echo "HEAD=$(git -C "$WORK" rev-parse HEAD)"; echo "BRANCH=$(git -C "$WORK" branch --show-current)"
bash "$WORK/runtime/v41_baseline_stack/RUN_V41_BASELINE_STACK_STAGE_A_GIT_BASH.sh"
