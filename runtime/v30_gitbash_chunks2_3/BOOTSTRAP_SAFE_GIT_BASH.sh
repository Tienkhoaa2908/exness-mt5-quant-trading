#!/usr/bin/env bash
# Safe interactive bootstrap for V30. Never intentionally exits the parent Git Bash.
set +e

REPO="https://github.com/Tienkhoaa2908/exness-mt5-quant-trading.git"
BRANCH="agent/v30-ml-dl-feature-lake"
WORK="$HOME/v30_mt5_auto"
BOOTLOG="$HOME/v30_bootstrap.log"
SOURCE_SHA_EXPECTED="4222120de5ded19ab7da172ad4c1e65d2a54b8bac7491fcd7927685b17b09a05"
TERMINAL_EXE="${MT5_TERMINAL_EXE:-/c/Program Files/MetaTrader 5/terminal64.exe}"

{
  echo "=== V30 SAFE GIT BASH BOOTSTRAP V3 ==="
  date
  echo "WORK=$WORK"

  if [[ -d "$WORK/.git" ]]; then
    echo "[1/4] Updating existing repo..."
    git -C "$WORK" fetch origin "$BRANCH"
    rc=$?
    if [[ $rc -ne 0 ]]; then echo "ERROR: git fetch failed rc=$rc"; exit $rc; fi
    git -C "$WORK" checkout -f "$BRANCH"
    rc=$?
    if [[ $rc -ne 0 ]]; then echo "ERROR: git checkout failed rc=$rc"; exit $rc; fi
    git -C "$WORK" reset --hard "origin/$BRANCH"
    rc=$?
    if [[ $rc -ne 0 ]]; then echo "ERROR: git reset failed rc=$rc"; exit $rc; fi
  else
    echo "[1/4] Cloning repo..."
    rm -rf "$WORK"
    git clone --depth 1 --single-branch --branch "$BRANCH" "$REPO" "$WORK"
    rc=$?
    if [[ $rc -ne 0 ]]; then echo "ERROR: git clone failed rc=$rc"; exit $rc; fi
  fi

  echo "[2/4] Resolving MT5 data folder from the exact V30 source..."
  APPDATA_U="$(cygpath -u "$APPDATA")"
  TERMINAL_ROOT="$APPDATA_U/MetaQuotes/Terminal"
  if [[ ! -d "$TERMINAL_ROOT" ]]; then
    echo "ERROR: MetaQuotes Terminal root missing: $TERMINAL_ROOT"
    exit 81
  fi

  BEST_SOURCE=""
  BEST_MTIME=0
  EXACT_COUNT=0
  for src in "$TERMINAL_ROOT"/*/MQL5/Experts/mt5_quant/MlDlFeatureLakeV1.mq5; do
    [[ -f "$src" ]] || continue
    h="$(sha256sum "$src" | awk '{print $1}')"
    echo "candidate source: $src sha256=$h"
    if [[ "$h" == "$SOURCE_SHA_EXPECTED" ]]; then
      EXACT_COUNT=$((EXACT_COUNT+1))
      mt="$(stat -c %Y "$src" 2>/dev/null || echo 0)"
      if [[ -z "$BEST_SOURCE" || "$mt" -gt "$BEST_MTIME" ]]; then
        BEST_SOURCE="$src"
        BEST_MTIME="$mt"
      fi
    fi
  done

  if [[ -z "$BEST_SOURCE" ]]; then
    echo "ERROR: Could not find the exact V30 source that already produced Chunk 1."
    echo "Expected SHA256=$SOURCE_SHA_EXPECTED"
    echo "No MT5 test was started."
    exit 82
  fi

  DATA_DIR="${BEST_SOURCE%/MQL5/Experts/mt5_quant/MlDlFeatureLakeV1.mq5}"
  echo "Exact V30 source matches=$EXACT_COUNT"
  echo "Selected MT5 data folder: $(cygpath -w "$DATA_DIR")"

  # The legacy runner maps installation -> data folder using origin/origin.txt.
  # Some MT5 installations store origin.txt as UTF-16/BOM, which caused matches=0.
  # Create a temporary plain-text 'origin' shim only for the exact source-matched
  # data folder, invoke the runner, then restore/remove it immediately afterwards.
  INSTALL_WIN="$(cygpath -w "$(dirname "$TERMINAL_EXE")")"
  ORIGIN_SHIM="$DATA_DIR/origin"
  ORIGIN_BACKUP="$WORK/runtime/v30_gitbash_chunks2_3/OUTPUT_GIT_BASH/.origin_backup_before_v30"
  ORIGIN_EXISTED=0
  mkdir -p "$(dirname "$ORIGIN_BACKUP")"
  if [[ -f "$ORIGIN_SHIM" ]]; then
    cp -f "$ORIGIN_SHIM" "$ORIGIN_BACKUP"
    ORIGIN_EXISTED=1
  else
    rm -f "$ORIGIN_BACKUP"
  fi
  printf '%s' "$INSTALL_WIN" > "$ORIGIN_SHIM"
  echo "Temporary origin shim installed for runner resolution."

  echo "[3/4] Entering runtime folder..."
  cd "$WORK/runtime/v30_gitbash_chunks2_3" || {
    if [[ $ORIGIN_EXISTED -eq 1 ]]; then cp -f "$ORIGIN_BACKUP" "$ORIGIN_SHIM"; else rm -f "$ORIGIN_SHIM"; fi
    exit 91
  }
  echo "PWD=$(pwd)"

  # Git Bash/MSYS rewrites arguments that begin with '/'. MetaEditor and MT5
  # intentionally use Windows CLI switches such as /compile:, /log and /config:.
  # Disable MSYS argument/path conversion for all native Windows child processes
  # launched by the runner. Without this, MetaEditor can silently receive a
  # mangled /compile argument and produce neither EX5 nor the documented .log.
  export MSYS_NO_PATHCONV=1
  export MSYS2_ARG_CONV_EXCL='*'
  echo "MSYS argument conversion disabled for MetaEditor/MT5 CLI switches."

  echo "[4/4] Running V30 chunks 2 + 3..."
  bash ./RUN_V30_CHUNKS_2_3_GIT_BASH.sh
  rc=$?

  if [[ $ORIGIN_EXISTED -eq 1 ]]; then
    cp -f "$ORIGIN_BACKUP" "$ORIGIN_SHIM"
    rm -f "$ORIGIN_BACKUP"
  else
    rm -f "$ORIGIN_SHIM"
  fi
  echo "Temporary origin shim cleaned up."

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
read -r -p "Press ENTER only after you have read/copied the final status..." _
exit 0