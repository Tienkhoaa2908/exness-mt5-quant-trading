#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"
EXPECTED_BRANCH="agent/v54-production-readiness-hardening"
BRANCH="$(git branch --show-current)"

if [[ "$BRANCH" != "$EXPECTED_BRANCH" ]]; then
  echo "FATAL: expected branch=$EXPECTED_BRANCH actual=$BRANCH" >&2
  exit 20
fi

python runtime/v55_account_agnostic/RUN_V55_WINDOWS_GATE.py "$@"
