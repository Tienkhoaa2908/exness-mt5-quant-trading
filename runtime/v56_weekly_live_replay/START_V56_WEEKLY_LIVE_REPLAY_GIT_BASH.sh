#!/usr/bin/env bash
set -Eeuo pipefail

cd "$(git rev-parse --show-toplevel)"
EXPECTED_BRANCH="agent/v54-production-readiness-hardening"
BRANCH="$(git branch --show-current)"

if [[ "$BRANCH" != "$EXPECTED_BRANCH" ]]; then
  echo "FATAL: expected branch=$EXPECTED_BRANCH actual=$BRANCH" >&2
  exit 20
fi

if tasklist.exe 2>/dev/null | grep -qi "terminal64.exe"; then
  echo "FATAL: MetaTrader 5 is open. Close it before V56 weekly Strategy Tester replay." >&2
  exit 21
fi

if tasklist.exe 2>/dev/null | grep -qi "metaeditor64.exe"; then
  echo "FATAL: MetaEditor is open. Close it before V56 weekly Strategy Tester replay." >&2
  exit 22
fi

python runtime/v56_weekly_live_replay/RUN_V56_WEEKLY_LIVE_REPLAY.py
