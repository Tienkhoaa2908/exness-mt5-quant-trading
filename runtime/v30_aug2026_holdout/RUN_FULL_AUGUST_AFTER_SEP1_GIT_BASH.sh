#!/usr/bin/env bash
set -Eeuo pipefail

# Full August-2026 fresh-holdout acquisition for V30.
# TESTER ONLY. REAL-MONEY LIVE TRADING IS FORBIDDEN.
# Refuses to run before 2026-09-02 local date so a complete August month is available.

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
REPO_ROOT="$(cd "$ROOT/../.." && pwd -P)"
OUT="$ROOT/OUTPUT_AUG2026_HOLDOUT"
LOG="$OUT/runner.log"
CHECKPOINT="$OUT/checkpoint"
SOURCE_SHA_EXPECTED="4222120de5ded19ab7da172ad4c1e65d2a54b8bac7491fcd7927685b17b09a05"
STATE_SRC="$REPO_ROOT/experiments/v30_aug2026_holdout/state_after_2026_07.csv"
STATE_SHA_EXPECTED="63e3e8e652fab73a1e2f9494117b3e4afe199100d504f9db6077c24e610e0c47"
TERMINAL_EXE="${MT5_TERMINAL_EXE:-/c/Program Files/MetaTrader 5/terminal64.exe}"
METAEDITOR_EXE="${MT5_METAEDITOR_EXE:-/c/Program Files/MetaTrader 5/metaeditor64.exe}"
FROM_DATE="2026.08.01"
TO_DATE="2026.09.01"
EXPECTED_TOKEN="__2026-08-01_00-00-00__"
NOT_BEFORE="20260902"

mkdir -p "$OUT" "$CHECKPOINT"
exec > >(tee -a "$LOG") 2>&1
say(){ printf '\n[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"; }
die(){ printf '\nFATAL: %s\n' "$*" >&2; exit 1; }
need(){ command -v "$1" >/dev/null 2>&1 || die "Missing Git Bash command: $1"; }
trap 'rc=$?; printf "\nFAILED rc=%s line=%s command=%s\n" "$rc" "${BASH_LINENO[0]:-?}" "${BASH_COMMAND:-?}" >&2; exit "$rc"' ERR

for cmd in cygpath iconv awk sed grep sha256sum tasklist.exe stat; do need "$cmd"; done
[[ "$(date '+%Y%m%d')" -ge "$NOT_BEFORE" ]] || die "Fresh August holdout is frozen. Do not run before 2026-09-02 local date."
[[ -f "$TERMINAL_EXE" ]] || die "MT5 terminal not found: $TERMINAL_EXE"
[[ -f "$METAEDITOR_EXE" ]] || die "MetaEditor not found: $METAEDITOR_EXE"
[[ -s "$STATE_SRC" ]] || die "Frozen July state missing: $STATE_SRC"
[[ "$(sha256sum "$STATE_SRC" | awk '{print $1}')" == "$STATE_SHA_EXPECTED" ]] || die "Frozen July state SHA mismatch"

# Git Bash/MSYS otherwise rewrites native Windows /compile and /config switches.
export MSYS_NO_PATHCONV=1
export MSYS2_ARG_CONV_EXCL='*'

if tasklist.exe //FI "IMAGENAME eq terminal64.exe" 2>/dev/null | tr -d '\r' | grep -qi 'terminal64.exe'; then
  die "MT5 is open. Close MetaTrader 5 completely before the holdout acquisition."
fi

APPDATA_U="$(cygpath -u "$APPDATA")"
TERMINAL_ROOT="$APPDATA_U/MetaQuotes/Terminal"
COMMON_FILES="$TERMINAL_ROOT/Common/Files"
LATEST="$COMMON_FILES/mt5_quant/ML_DL_FEATURE_LAKE_LATEST.txt"
STATE_DIR="$COMMON_FILES/mt5_quant/inputs"
STATE="$STATE_DIR/v30_ml_dl_feature_lake_state.csv"
mkdir -p "$STATE_DIR"

# Resolve the exact accepted V30 data folder by source SHA, not origin.txt format.
DATA_DIR=""; SOURCE=""; MATCHES=0; BEST_MTIME=0
for src in "$TERMINAL_ROOT"/*/MQL5/Experts/mt5_quant/MlDlFeatureLakeV1.mq5; do
  [[ -f "$src" ]] || continue
  h="$(sha256sum "$src" | awk '{print $1}')"
  if [[ "$h" == "$SOURCE_SHA_EXPECTED" ]]; then
    MATCHES=$((MATCHES+1)); mt="$(stat -c %Y "$src" 2>/dev/null || echo 0)"
    if [[ -z "$SOURCE" || "$mt" -gt "$BEST_MTIME" ]]; then SOURCE="$src"; BEST_MTIME="$mt"; fi
  fi
done
[[ -n "$SOURCE" ]] || die "Exact accepted V30 source not found under MT5 data folders"
DATA_DIR="${SOURCE%/MQL5/Experts/mt5_quant/MlDlFeatureLakeV1.mq5}"
say "Accepted V30 source matches=$MATCHES"
say "Selected MT5 data folder: $(cygpath -w "$DATA_DIR")"

grep -Eq '#define[[:space:]]+MT5Q_RELEASE_ID[[:space:]]+"v30_ml_dl_feature_lake_v1"' "$SOURCE" || die "EA release marker mismatch"
! grep -Eq '\.minute\b' "$SOURCE" || die "Stale MqlDateTime.minute source blocked"
grep -Eq 'InpWriteBarFeatures[[:space:]]*=[[:space:]]*true' "$SOURCE" || die "InpWriteBarFeatures default is not true"
for forbidden in 'OrderSend(' 'OrderSendAsync(' 'CTrade' 'trade.Buy(' 'trade.Sell(' 'PositionOpen('; do
  if grep -Fq "$forbidden" "$SOURCE"; then die "Forbidden native-order token: $forbidden"; fi
done

EXPERT_DIR="$DATA_DIR/MQL5/Experts/mt5_quant"
EX5="$EXPERT_DIR/MlDlFeatureLakeV1.ex5"
COMPILE_LOG="$EXPERT_DIR/MlDlFeatureLakeV1.log"
rm -f "$EX5" "$COMPILE_LOG"
say "Compile gate"
SOURCE_WIN="$(cygpath -w "$SOURCE")"
"$METAEDITOR_EXE" "/compile:$SOURCE_WIN" /log || true
[[ -f "$COMPILE_LOG" ]] || die "MetaEditor compile log missing"
NORMALIZED_LOG="$OUT/metaeditor_compile_utf8.log"
if iconv -f UTF-16 -t UTF-8 "$COMPILE_LOG" > "$NORMALIZED_LOG" 2>/dev/null; then :; else tr -d '\r' < "$COMPILE_LOG" > "$NORMALIZED_LOG"; fi
tr -d '\r' < "$NORMALIZED_LOG" > "$NORMALIZED_LOG.tmp" && mv -f "$NORMALIZED_LOG.tmp" "$NORMALIZED_LOG"
summary="$(grep -Eio 'Result:[[:space:]]*[0-9]+[[:space:]]+errors?,[[:space:]]*[0-9]+[[:space:]]+warnings?' "$NORMALIZED_LOG" | tail -n1 || true)"
[[ -n "$summary" ]] || die "Could not parse MetaEditor compile result"
printf '%s\n' "$summary"
[[ "$summary" =~ Result:[[:space:]]*0[[:space:]]+errors?,[[:space:]]*0[[:space:]]+warnings? ]] || die "Compile gate is not 0 errors / 0 warnings"
[[ -s "$EX5" ]] || die "Fresh EX5 not produced"

read_kv(){ local key="$1" file="$2"; [[ -f "$file" ]] || return 1; awk -F= -v k="$key" '$1==k {sub(/^[^=]*=/,""); gsub(/\r/,""); print; exit}' "$file"; }

# If a previous invocation already completed MT5 but died during collection, recover without rerunning tester.
LAUNCH_DONE="$CHECKPOINT/MT5_LAUNCH_COMPLETED.txt"
DONE="$CHECKPOINT/DONE.txt"
if [[ -f "$DONE" ]]; then
  say "Holdout checkpoint already complete; MT5 WILL NOT RERUN"
else
  if [[ ! -f "$LAUNCH_DONE" ]]; then
    if [[ -f "$STATE" ]]; then cp -f "$STATE" "$OUT/state_before_holdout_backup.csv"; fi
    cp -f "$STATE_SRC" "$STATE"
    [[ "$(sha256sum "$STATE" | awk '{print $1}')" == "$STATE_SHA_EXPECTED" ]] || die "Common Files state reset failed"

    CONFIG="$DATA_DIR/config/mt5_quant_v30_aug2026_fresh_holdout.ini"
    TMP="$OUT/holdout_config_utf8.ini"
    cat > "$TMP" <<EOF
[Common]
KeepPrivate=1
NewsEnable=0

[Experts]
AllowLiveTrading=0
AllowDllImport=0
Enabled=1
Account=0
Profile=0

[Tester]
Expert=mt5_quant\\MlDlFeatureLakeV1.ex5
Symbol=XAUUSDm
Period=M15
Optimization=0
Model=0
FromDate=$FROM_DATE
ToDate=$TO_DATE
ForwardMode=0
Deposit=10000
Currency=USD
Leverage=1:200
ExecutionMode=0
OptimizationCriterion=0
UseCloud=0
Visual=0
ShutdownTerminal=1
EOF
    printf '\xFF\xFE' > "$CONFIG"
    iconv -f UTF-8 -t UTF-16LE "$TMP" >> "$CONFIG"
    BEFORE=""; [[ -f "$LATEST" ]] && BEFORE="$(read_kv run_id "$LATEST" || true)"
    say "RUN FRESH HOLDOUT from=$FROM_DATE to=$TO_DATE"
    CONFIG_WIN="$(cygpath -w "$CONFIG")"
    "$TERMINAL_EXE" "/config:$CONFIG_WIN"
    RC=$?
    say "MT5 returned rc=$RC"
    printf 'mt5_returned=1\nrc=%s\ncompleted_at=%s\nbefore_run_id=%s\n' "$RC" "$(date -Iseconds)" "$BEFORE" > "$LAUNCH_DONE"
  else
    say "MT5 launch-complete marker exists; attempting collection only, MT5 WILL NOT RERUN"
  fi

  [[ -f "$LATEST" ]] || die "LATEST locator missing after holdout"
  RUN_ID="$(read_kv run_id "$LATEST" || true)"; RUN_FOLDER="$(read_kv run_folder "$LATEST" || true)"
  [[ "$RUN_ID" == *"$EXPECTED_TOKEN"* ]] || die "LATEST is not August holdout: $RUN_ID"
  RUN_FOLDER="${RUN_FOLDER//\\//}"
  RUN_DIR="$COMMON_FILES/$RUN_FOLDER"
  [[ -d "$RUN_DIR" ]] || die "Holdout run folder missing: $RUN_DIR"
  for f in bar_features.csv monthly_summary.csv trades.csv manifest.txt; do [[ -s "$RUN_DIR/$f" ]] || die "Missing holdout output: $f"; done
  [[ -s "$STATE" ]] || die "State after holdout missing"

  rm -rf "$CHECKPOINT/data"; mkdir -p "$CHECKPOINT/data"
  for f in bar_features.csv monthly_summary.csv trades.csv manifest.txt; do cp -f "$RUN_DIR/$f" "$CHECKPOINT/data/$f"; done
  cp -f "$LATEST" "$CHECKPOINT/data/ML_DL_FEATURE_LAKE_LATEST.txt"
  cp -f "$STATE" "$CHECKPOINT/data/state_after_august.csv"
  cp -f "$STATE_SRC" "$CHECKPOINT/data/state_before_august.csv"
  cp -f "$REPO_ROOT/experiments/v30_aug2026_holdout/frozen_gate.json" "$CHECKPOINT/data/frozen_gate.json"
  printf 'done=1\nrun_id=%s\nrun_folder=%s\ncollected_at=%s\n' "$RUN_ID" "$RUN_FOLDER" "$(date -Iseconds)" > "$DONE"
fi

PACKAGE="$OUT/package"; rm -rf "$PACKAGE"; mkdir -p "$PACKAGE"; cp -f "$CHECKPOINT/data/"* "$PACKAGE/"; cp -f "$LOG" "$PACKAGE/runner.log"
STAMP="$(date '+%Y%m%d_%H%M%S')"; ZIP="$OUT/mt5_quant_v30_aug2026_FRESH_HOLDOUT_${STAMP}.zip"; rm -f "$ZIP"
if command -v python >/dev/null 2>&1; then
  python - "$(cygpath -w "$PACKAGE")" "$(cygpath -w "$ZIP")" <<'PY'
import os,sys,zipfile
root,out=sys.argv[1],sys.argv[2]
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for base,dirs,files in os.walk(root):
        dirs.sort();files.sort()
        for name in files:
            p=os.path.join(base,name);z.write(p,os.path.relpath(p,root).replace('\\','/'))
PY
else
  (cd "$PACKAGE" && tar.exe -a -c -f "$(cygpath -w "$ZIP")" .)
fi
[[ -s "$ZIP" ]] || die "Final holdout ZIP missing"
SHA="$(sha256sum "$ZIP" | awk '{print $1}')"
say "ALL DONE — FRESH AUGUST HOLDOUT ACQUIRED"
printf '\nUPLOAD THIS ONE ZIP:\n%s\nSHA256=%s\n' "$(cygpath -w "$ZIP")" "$SHA"
printf '\nDo not rerun or retune August before offline evaluation.\n'
