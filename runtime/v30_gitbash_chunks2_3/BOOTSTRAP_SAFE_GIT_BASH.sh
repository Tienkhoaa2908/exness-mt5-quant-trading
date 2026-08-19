#!/usr/bin/env bash
# Safe interactive bootstrap for V30. Never intentionally exits the parent Git Bash.
set +e

REPO="https://github.com/Tienkhoaa2908/exness-mt5-quant-trading.git"
BRANCH="agent/v30-ml-dl-feature-lake"
WORK="$HOME/v30_mt5_auto"
BOOTLOG="$HOME/v30_bootstrap.log"

{
  echo "=== V30 SAFE GIT BASH BOOTSTRAP ==="
  date
  echo "WORK=$WORK"

  if [[ -d "$WORK/.git" ]]; then
    echo "[1/3] Updating existing repo..."
    git -C "$WORK" fetch origin "$BRANCH"
    rc=$?
    if [[ $rc -ne 0 ]]; then
      echo "ERROR: git fetch failed rc=$rc"
      exit $rc
    fi
    git -C "$WORK" checkout -f "$BRANCH"
    rc=$?
    if [[ $rc -ne 0 ]]; then
      echo "ERROR: git checkout failed rc=$rc"
      exit $rc
    fi
    git -C "$WORK" reset --hard "origin/$BRANCH"
    rc=$?
    if [[ $rc -ne 0 ]]; then
      echo "ERROR: git reset failed rc=$rc"
      exit $rc
    fi
  else
    echo "[1/3] Cloning repo..."
    rm -rf "$WORK"
    git clone --depth 1 --single-branch --branch "$BRANCH" "$REPO" "$WORK"
    rc=$?
    if [[ $rc -ne 0 ]]; then
      echo "ERROR: git clone failed rc=$rc"
      exit $rc
    fi
  fi

  echo "[2/3] Entering runtime folder..."
  cd "$WORK/runtime/v30_gitbash_chunks2_3" || exit 91
  echo "PWD=$(pwd)"
  echo "[3/3] Running V30 chunks 2 + 3..."
  bash ./RUN_V30_CHUNKS_2_3_GIT_BASH.sh
  rc=$?
  echo
  echo "=== RUNNER FINISHED rc=$rc ==="
  exit $rc
} 2>&1 | tee "$BOOTLOG"

RC=${PIPESTATUS[0]}
echo
echo "============================================================"
if [[ $RC -eq 0 ]]; then
  echo "V30 COMPLETED SUCCESSFULLY"
else
  echo "V30 FAILED rc=$RC"
fi
echo "Bootstrap log: $BOOTLOG"
echo "Runner log (if created):"
echo "$WORK/runtime/v30_gitbash_chunks2_3/OUTPUT_GIT_BASH/git_bash_runner.log"
echo "============================================================"
echo
read -r -p "Press ENTER to keep/close this Git Bash window..." _
exit 0
