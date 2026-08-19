#!/usr/bin/env bash
set -Eeuo pipefail

# V30 Git Bash runner: Windows orchestration only.
# Tester-only research. REAL-MONEY LIVE TRADING IS FORBIDDEN.
# Purpose: compile the already-accepted V30 EA, run only chunk 2 + chunk 3,
# collect EA output files + state snapshots, and create one upload ZIP.

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
OUT="$ROOT/OUTPUT_GIT_BASH"
CHECKPOINT="$OUT/checkpoints"
LOG="$OUT/git_bash_runner.log"
SOURCE_SHA_EXPECTED="4222120de5ded19ab7da172ad4c1e65d2a54b8bac7491fcd7927685b17b09a05"
TEMPLATE="$ROOT/experiments/ml_dl_feature_lake_v1/template.ini"
BUNDLED_STATE="$ROOT/state_chunk1/v30_ml_dl_feature_lake_state.csv"

TERMINAL_EXE="${MT5_TERMINAL_EXE:-/c/Program Files/MetaTrader 5/terminal64.exe}"
METAEDITOR_EXE="${MT5_METAEDITOR_EXE:-/c/Program Files/MetaTrader 5/metaeditor64.exe}"

mkdir -p "$OUT" "$CHECKPOINT"
exec > >(tee -a "$LOG") 2>&1

say(){ printf '\n[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"; }
die(){ printf '\nFATAL: %s\n' "$*" >&2; exit 1; }
need(){ command -v "$1" >/dev/null 2>&1 || die "Missing command in Git Bash: $1"; }

trap 'rc=$?; printf "\nFAILED rc=%s line=%s command=%s\n" "$rc" "${BASH_LINENO[0]:-?}" "${BASH_COMMAND:-?}" >&2; exit "$rc"' ERR

need cygpath
need iconv
need awk
need sed
need grep
need sha256sum
need tasklist.exe

[[ -f "$TERMINAL_EXE" ]] || die "MT5 terminal not found: $TERMINAL_EXE"
[[ -f "$METAEDITOR_EXE" ]] || die "MetaEditor not found: $METAEDITOR_EXE"
[[ -f "$TEMPLATE" ]] || die "template.ini missing: $TEMPLATE"
[[ -f "$BUNDLED_STATE" ]] || die "verified chunk1 state missing: $BUNDLED_STATE"
[[ "$(awk -F, 'NR>1 {s+=$2} END {print s+0}' "$BUNDLED_STATE")" == "647" ]] || die "Bundled chunk1 state obs total mismatch"

# Refuse to launch a second terminal instance. Close MT5 first.
if tasklist.exe //FI "IMAGENAME eq terminal64.exe" 2>/dev/null | tr -d '\r' | grep -qi 'terminal64.exe'; then
  die "MT5 is currently open. Close MetaTrader 5 completely, then rerun this Bash script."
fi

APPDATA_U="$(cygpath -u "$APPDATA")"
TERMINAL_ROOT="$APPDATA_U/MetaQuotes/Terminal"
COMMON_FILES="$TERMINAL_ROOT/Common/Files"
LATEST="$COMMON_FILES/mt5_quant/ML_DL_FEATURE_LAKE_LATEST.txt"
STATE_DIR="$COMMON_FILES/mt5_quant/inputs"
STATE="$STATE_DIR/v30_ml_dl_feature_lake_state.csv"

[[ -d "$TERMINAL_ROOT" ]] || die "MetaQuotes Terminal data root missing: $TERMINAL_ROOT"
mkdir -p "$STATE_DIR"

normalize_win_path(){
  printf '%s' "$1" | tr '\\\\' '/' | sed -E 's:/+$::' | tr '[:upper:]' '[:lower:]'
}

INSTALL_WIN="$(cygpath -w "$(dirname "$TERMINAL_EXE")")"
INSTALL_NORM="$(normalize_win_path "$INSTALL_WIN")"
TERMINAL_DATA=""
MATCHES=0

for d in "$TERMINAL_ROOT"/*; do
  [[ -d "$d" ]] || continue
  [[ "$(basename "$d")" == "Common" ]] && continue
  for origin in "$d/origin" "$d/origin.txt"; do
    [[ -f "$origin" ]] || continue
    value="$(tr -d '\000\r\n' < "$origin")"
    [[ -n "$value" ]] || continue
    if [[ "$(normalize_win_path "$value")" == "$INSTALL_NORM" ]]; then
      TERMINAL_DATA="$d"
      MATCHES=$((MATCHES+1))
      break
    fi
  done
done

[[ "$MATCHES" -eq 1 ]] || die "Could not resolve exactly one MT5 data folder for $INSTALL_WIN; matches=$MATCHES"
say "MT5 data folder: $(cygpath -w "$TERMINAL_DATA")"

# Reuse the exact V30 source that already compiled 0/0 and produced Chunk 1.
SOURCE="$TERMINAL_DATA/MQL5/Experts/mt5_quant/MlDlFeatureLakeV1.mq5"
[[ -f "$SOURCE" ]] || die "Existing V30 EA source not found: $SOURCE. Do not download anything; send this error back."
SOURCE_SHA_ACTUAL="$(sha256sum "$SOURCE" | awk '{print $1}')"
[[ "$SOURCE_SHA_ACTUAL" == "$SOURCE_SHA_EXPECTED" ]] || die "Existing V30 EA source SHA mismatch. expected=$SOURCE_SHA_EXPECTED actual=$SOURCE_SHA_ACTUAL"
# Minimal fail-closed source checks. Do not perform research-data validation here.
grep -Eq '#define[[:space:]]+MT5Q_RELEASE_ID[[:space:]]+"v30_ml_dl_feature_lake_v1"' "$SOURCE" || die "EA release marker mismatch"
! grep -Eq '\.minute\b' "$SOURCE" || die "Stale MqlDateTime.minute source blocked"
grep -Eq 'InpWriteBarFeatures[[:space:]]*=[[:space:]]*true' "$SOURCE" || die "InpWriteBarFeatures must default true"
grep -Fq 'mt5_quant\\inputs\\v30_ml_dl_feature_lake_state.csv' "$SOURCE" || die "Expected adaptive-state path missing from EA"
for forbidden in 'OrderSend(' 'OrderSendAsync(' 'CTrade' 'trade.Buy(' 'trade.Sell(' 'PositionOpen('; do
  if grep -Fq "$forbidden" "$SOURCE"; then die "Forbidden native-order token in source: $forbidden"; fi
done

EXPERT_DIR="$TERMINAL_DATA/MQL5/Experts/mt5_quant"
DST_SOURCE="$EXPERT_DIR/MlDlFeatureLakeV1.mq5"
DST_EX5="$EXPERT_DIR/MlDlFeatureLakeV1.ex5"
DST_LOG="$EXPERT_DIR/MlDlFeatureLakeV1.log"
mkdir -p "$EXPERT_DIR" "$TERMINAL_DATA/config"
if [[ "$(cygpath -aw "$SOURCE")" != "$(cygpath -aw "$DST_SOURCE")" ]]; then cp -f "$SOURCE" "$DST_SOURCE"; fi
rm -f "$DST_EX5" "$DST_LOG"

say "Compile gate: MlDlFeatureLakeV1.mq5"
DST_SOURCE_WIN="$(cygpath -w "$DST_SOURCE")"
"$METAEDITOR_EXE" "/compile:$DST_SOURCE_WIN" /log || true
[[ -f "$DST_LOG" ]] || die "MetaEditor compile log missing: $DST_LOG"
summary="$(tr -d '\r' < "$DST_LOG" | grep -Eio 'Result:[[:space:]]*[0-9]+[[:space:]]+errors?,[[:space:]]*[0-9]+[[:space:]]+warnings?' | tail -n1 || true)"
if [[ -z "$summary" ]]; then
  summary="$(tr -d '\r' < "$DST_LOG" | grep -Eio '[0-9]+[[:space:]]+errors?,[[:space:]]*[0-9]+[[:space:]]+warnings?' | tail -n1 || true)"
fi
[[ -n "$summary" ]] || { tail -n 50 "$DST_LOG" || true; die "Could not parse MetaEditor compile summary"; }
errors="$(printf '%s' "$summary" | sed -E 's/.*[^0-9]([0-9]+)[[:space:]]+errors?.*/\1/I')"
warnings="$(printf '%s' "$summary" | sed -E 's/.*errors?,[[:space:]]*([0-9]+)[[:space:]]+warnings?.*/\1/I')"
printf '%s\n' "$summary"
[[ "$errors" == "0" && "$warnings" == "0" ]] || { tail -n 50 "$DST_LOG" || true; die "Compile gate failed errors=$errors warnings=$warnings"; }
[[ -f "$DST_EX5" ]] || die "Fresh EX5 not produced: $DST_EX5"
say "Compile PASS: 0 errors / 0 warnings"

STATE_SHA_EXPECTED="$(sha256sum "$BUNDLED_STATE" | awk '{print $1}')"
[[ -n "$STATE_SHA_EXPECTED" ]] || die "Could not hash bundled state"

read_kv(){
  local key="$1" file="$2"
  [[ -f "$file" ]] || return 1
  awk -F= -v k="$key" '$1==k {sub(/^[^=]*=/,""); gsub(/\r/,""); print; exit}' "$file"
}

make_runtime_ini(){
  local tag="$1" from="$2" to="$3"
  local runtime="$TERMINAL_DATA/config/mt5_quant_ml_dl_feature_lake_gitbash_${tag}.ini"
  local tmp="$OUT/.runtime_${tag}.utf8"
  {
    printf '[Common]\r\nKeepPrivate=1\r\nNewsEnable=0\r\n\r\n'
    tr -d '\r' < "$TEMPLATE" | sed "s/__FROM__/$from/g; s/__TO__/$to/g" | awk '{printf "%s\r\n", $0}'
  } > "$tmp"
  printf '\xFF\xFE' > "$runtime"
  iconv -f UTF-8 -t UTF-16LE "$tmp" >> "$runtime"
  rm -f "$tmp"
  printf '%s' "$runtime"
}

collect_latest(){
  local tag="$1" expected_token="$2" dest="$3" state_snapshot="$4"
  [[ -f "$LATEST" ]] || die "EA locator missing after tester: $LATEST"
  local run_id run_folder
  run_id="$(read_kv run_id "$LATEST" || true)"
  run_folder="$(read_kv run_folder "$LATEST" || true)"
  [[ -n "$run_id" && -n "$run_folder" ]] || die "LATEST locator missing run_id/run_folder"
  [[ "$run_id" == *"$expected_token"* ]] || die "LATEST run_id is not the requested chunk. expected token=$expected_token actual=$run_id"
  run_folder="${run_folder//\\//}"
  local run_dir="$COMMON_FILES/$run_folder"
  [[ -d "$run_dir" ]] || die "Run folder from locator does not exist: $run_dir"
  mkdir -p "$dest"
  for f in bar_features.csv monthly_summary.csv trades.csv manifest.txt; do
    [[ -s "$run_dir/$f" ]] || die "Expected EA output missing/empty: $run_dir/$f"
    cp -f "$run_dir/$f" "$dest/$f"
  done
  [[ -s "$STATE" ]] || die "Adaptive state missing after chunk: $STATE"
  cp -f "$STATE" "$state_snapshot"
  cp -f "$LATEST" "$dest/ML_DL_FEATURE_LAKE_LATEST.txt"
  printf 'tag=%s\nrun_id=%s\nsource_run_folder=%s\ncollected_at=%s\n' \
    "$tag" "$run_id" "$run_folder" "$(date -Iseconds)" > "$dest/COLLECTED.txt"
  say "COLLECT PASS $tag run_id=$run_id"
}

run_chunk(){
  local tag="$1" from="$2" to="$3" expected_token="$4" prior_state="$5" state_after="$6"
  local dest="$CHECKPOINT/$tag"
  local done="$dest/DONE.txt"

  # Minimal idempotence: if a complete checkpoint exists, never rerun MT5.
  if [[ -f "$done" && -s "$state_after" ]]; then
    for f in bar_features.csv monthly_summary.csv trades.csv manifest.txt; do
      [[ -s "$dest/$f" ]] || die "Checkpoint marker exists but $f is missing for $tag"
    done
    cp -f "$state_after" "$STATE"
    say "REUSE CHECKPOINT $tag -- MT5 NOT RERUN"
    return 0
  fi

  [[ -s "$prior_state" ]] || die "Prior adaptive state missing: $prior_state"
  cp -f "$prior_state" "$STATE"
  local before=""
  [[ -f "$LATEST" ]] && before="$(read_kv run_id "$LATEST" || true)"
  local runtime runtime_win
  runtime="$(make_runtime_ini "$tag" "$from" "$to")"
  runtime_win="$(cygpath -w "$runtime")"

  say "RUN $tag  from=$from  to=$to"
  say "Launching MT5. Do not interact with terminal while tester runs."
  "$TERMINAL_EXE" "/config:$runtime_win"
  rc=$?
  say "MT5 process returned rc=$rc"

  [[ -f "$LATEST" ]] || die "LATEST locator absent after MT5 run"
  after="$(read_kv run_id "$LATEST" || true)"
  [[ -n "$after" ]] || die "LATEST run_id empty after MT5 run"
  [[ "$after" != "$before" ]] || die "LATEST run_id did not change; tester output was not refreshed"

  rm -rf "$dest"
  mkdir -p "$dest"
  collect_latest "$tag" "$expected_token" "$dest" "$state_after"
  printf 'done=1\ntag=%s\nfrom=%s\nto=%s\nrun_id=%s\n' "$tag" "$from" "$to" "$after" > "$done"
}

# Always anchor the chain to the verified state after chunk 1 unless chunk 2
# already has a local checkpoint. This avoids depending on whatever a failed
# wrapper may have left in Common Files.
STATE0="$CHECKPOINT/state_after_chunk1_verified.csv"
STATE2="$CHECKPOINT/state_after_chunk2.csv"
STATE3="$CHECKPOINT/state_after_chunk3.csv"
if [[ ! -s "$STATE0" ]]; then cp -f "$BUNDLED_STATE" "$STATE0"; fi
[[ "$(sha256sum "$STATE0" | awk '{print $1}')" == "$STATE_SHA_EXPECTED" ]] || die "Chunk1 state checkpoint hash mismatch"

run_chunk "chunk2_2025_08__2026_02" "2025.08.01" "2026.02.01" "__2025-08-01_00-00-00__" "$STATE0" "$STATE2"
run_chunk "chunk3_2026_02__2026_08" "2026.02.01" "2026.08.01" "__2026-02-01_00-00-00__" "$STATE2" "$STATE3"

# Build a user-upload package. No research-data transformation is done here.
PACKAGE_DIR="$OUT/package"
rm -rf "$PACKAGE_DIR"
mkdir -p "$PACKAGE_DIR/chunk2" "$PACKAGE_DIR/chunk3"
cp -f "$CHECKPOINT/chunk2_2025_08__2026_02/"{bar_features.csv,monthly_summary.csv,trades.csv,manifest.txt,ML_DL_FEATURE_LAKE_LATEST.txt,COLLECTED.txt} "$PACKAGE_DIR/chunk2/"
cp -f "$CHECKPOINT/chunk3_2026_02__2026_08/"{bar_features.csv,monthly_summary.csv,trades.csv,manifest.txt,ML_DL_FEATURE_LAKE_LATEST.txt,COLLECTED.txt} "$PACKAGE_DIR/chunk3/"
cp -f "$STATE0" "$PACKAGE_DIR/state_after_chunk1.csv"
cp -f "$STATE2" "$PACKAGE_DIR/state_after_chunk2.csv"
cp -f "$STATE3" "$PACKAGE_DIR/state_after_chunk3.csv"
cp -f "$LOG" "$PACKAGE_DIR/git_bash_runner.log"

STAMP="$(date '+%Y%m%d_%H%M%S')"
ZIP="$OUT/mt5_quant_v30_chunks2_3_GIT_BASH_${STAMP}.zip"
rm -f "$ZIP"

if command -v python >/dev/null 2>&1; then
  ZIP_WIN="$(cygpath -w "$ZIP")"
  PKG_WIN="$(cygpath -w "$PACKAGE_DIR")"
  python - "$PKG_WIN" "$ZIP_WIN" <<'PY'
import os, sys, zipfile
root, out = sys.argv[1], sys.argv[2]
with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    for base, dirs, files in os.walk(root):
        dirs.sort(); files.sort()
        for name in files:
            p=os.path.join(base,name)
            arc=os.path.relpath(p,root).replace('\\','/')
            z.write(p,arc)
PY
elif command -v tar.exe >/dev/null 2>&1; then
  (cd "$PACKAGE_DIR" && tar.exe -a -c -f "$(cygpath -w "$ZIP")" .)
else
  die "Data collection finished, but neither python nor tar.exe exists to create ZIP. Files are safe in $PACKAGE_DIR"
fi

[[ -s "$ZIP" ]] || die "Final ZIP was not created"
ZIP_SHA="$(sha256sum "$ZIP" | awk '{print $1}')"
printf '%s  %s\n' "$ZIP_SHA" "$(basename "$ZIP")" > "$ZIP.sha256.txt"

say "ALL DONE"
printf '\nUPLOAD THIS ONE ZIP:\n%s\nSHA256=%s\n' "$(cygpath -w "$ZIP")" "$ZIP_SHA"
printf '\nDo not run MT5 again. Upload the ZIP above for offline QA + ML/DL training.\n'
