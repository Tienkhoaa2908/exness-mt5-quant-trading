#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"
BRANCH="agent/v54-production-readiness-hardening"

git fetch --no-tags origin "+refs/heads/$BRANCH:refs/remotes/origin/$BRANCH"
git checkout -B "$BRANCH" "refs/remotes/origin/$BRANCH"
git reset --hard "refs/remotes/origin/$BRANCH"

test -z "$(git status --porcelain)" || {
  echo "FATAL: working tree is not clean" >&2
  exit 1
}

python runtime/v54_production_readiness/RUN_V54_PRODUCTION_READINESS.py
