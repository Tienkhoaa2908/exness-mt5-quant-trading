#!/usr/bin/env bash
set -Eeuo pipefail

# V31 AI Router MT5 gate. Strategy Tester / virtual books only.
# REAL-MONEY LIVE TRADING IS FORBIDDEN.
# One run: 2025-08-01 -> 2026-08-01, generated Every-tick model.

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
REPO_ROOT="$(cd -- "$ROOT/../.." && pwd -P)"
OUT="$ROOT/OUTPUT_V31_MT5"
CHECKPOINT="$OUT/checkpoint"
LOG="$OUT/v31_git_bash_runner.log"
PKG="$OUT/package"

TERMINAL_EXE="${MT5_TERMINAL_EXE:-/c/Program Files/MetaTrader 5/terminal64.exe}"
METAEDITOR_EXE="${MT5_METAEDITOR_EXE:-/c/Program Files/MetaTrader 5/metaeditor64.exe}"
V30_SOURCE_SHA="4222120de5ded19ab7da172ad4c1e65d2a54b8bac7491fcd7927685b17b09a05"
V31_SOURCE_SHA="cef304997fc342740c15101d64a610d6265a4835a4cb601a741113868a078f0f"
V31_DATA_SHA="44c8edd55fc5a1b18fe5ec5d0a3454d95600f23d8c3f06ae6048e1c4d16211f3"
V31_NN_SHA="6e977ff55b9ae7ddf5ffa8103642fa882a6a47cdc2ef0f9fe6f16582e242c8f3"
V31_SVM_SHA="8b94f800959b32465302a8eb50c58fff82071368cf3310788c4c3fdb9cebf650"
V31_RFF_SHA="36905a57761ec216e2ca92ac87a2a9a23bd241bace4a86a87124ccb6f2ffe710"
STATE_START_SHA="5110519f2fe9722b4c13eb1e5ceec42f00bd04dd3b4f071af28349068b6097b0"

MODEL_DIR="$REPO_ROOT/models/v31_ai_router"
RELEASE_B64="$MODEL_DIR/release/v31_model_release.tar.gz.b64"
RELEASE_ARCHIVE_SHA="fbcf83f04d2e8661bc36ebba2bea66c172cbc4c08d4b13e74df45a8b9174b9e7"
PREP_DIR="$OUT/prepared_mql"
STATE_START="$ROOT/state_start/state_after_2025_07.csv"
TEMPLATE="$ROOT/experiments/template.ini"

mkdir -p "$OUT" "$CHECKPOINT"
exec > >(tee -a "$LOG") 2>&1
say(){ printf '\n[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"; }
die(){ printf '\nFATAL: %s\n' "$*" >&2; exit 1; }
need(){ command -v "$1" >/dev/null 2>&1 || die "Missing command in Git Bash: $1"; }
trap 'rc=$?; printf "\nFAILED rc=%s line=%s command=%s\n" "$rc" "${BASH_LINENO[0]:-?}" "${BASH_COMMAND:-?}" >&2' ERR

need cygpath; need iconv; need awk; need sed; need grep; need sha256sum; need tasklist.exe; need tar.exe; need base64; need gzip
[[ -f "$TERMINAL_EXE" ]] || die "MT5 terminal not found: $TERMINAL_EXE"
[[ -f "$METAEDITOR_EXE" ]] || die "MetaEditor not found: $METAEDITOR_EXE"
[[ -f "$TEMPLATE" ]] || die "runtime template missing"
[[ -f "$STATE_START" ]] || die "July-2025 adaptive state checkpoint missing"
[[ "$(sha256sum "$STATE_START" | awk '{print $1}')" == "$STATE_START_SHA" ]] || die "start-state SHA mismatch"
[[ -s "$RELEASE_B64" ]] || die "V31 packed model release missing: $RELEASE_B64"
rm -rf "$PREP_DIR"; mkdir -p "$PREP_DIR"
RELEASE_TGZ="$OUT/v31_model_release.tar.gz"
base64 -d "$RELEASE_B64" > "$RELEASE_TGZ" || die "Could not decode V31 model release"
[[ "$(sha256sum "$RELEASE_TGZ" | awk '{print $1}')" == "$RELEASE_ARCHIVE_SHA" ]] || die "V31 release archive SHA mismatch"
tar -xzf "$RELEASE_TGZ" -C "$PREP_DIR" || die "Could not extract V31 model release"
for f in V31AiRouterLabV1.mq5 V31AiModelData.mqh V31AiNnWeights.mqh V31AiSvmWeights.mqh V31AiRffWeights.mqh; do [[ -s "$PREP_DIR/$f" ]] || die "Extracted V31 file missing: $f"; done
[[ "$(sha256sum "$PREP_DIR/V31AiRouterLabV1.mq5" | awk '{print $1}')" == "$V31_SOURCE_SHA" ]] || die "V31 source SHA mismatch"
[[ "$(sha256sum "$PREP_DIR/V31AiModelData.mqh" | awk '{print $1}')" == "$V31_DATA_SHA" ]] || die "V31 model-data SHA mismatch"
[[ "$(sha256sum "$PREP_DIR/V31AiNnWeights.mqh" | awk '{print $1}')" == "$V31_NN_SHA" ]] || die "V31 NN-weight SHA mismatch after reconstruction"
[[ "$(sha256sum "$PREP_DIR/V31AiSvmWeights.mqh" | awk '{print $1}')" == "$V31_SVM_SHA" ]] || die "V31 SVM-weight SHA mismatch"
[[ "$(sha256sum "$PREP_DIR/V31AiRffWeights.mqh" | awk '{print $1}')" == "$V31_RFF_SHA" ]] || die "V31 RFF-weight SHA mismatch after reconstruction"
SRC_DIR="$PREP_DIR"

# Fail closed if MT5 is already open. Avoid two terminals sharing tester/common files.
if tasklist.exe //FI "IMAGENAME eq terminal64.exe" 2>/dev/null | tr -d '\r' | grep -qi 'terminal64.exe'; then
  die "MT5 is open. Close MetaTrader 5 completely, then run this script again."
fi

APPDATA_U="$(cygpath -u "$APPDATA")"
TERMINAL_ROOT="$APPDATA_U/MetaQuotes/Terminal"
COMMON_FILES="$TERMINAL_ROOT/Common/Files"
STATE_DIR="$COMMON_FILES/mt5_quant/inputs"
STATE="$STATE_DIR/v30_ml_dl_feature_lake_state.csv"
LATEST="$COMMON_FILES/mt5_quant/V31_AI_ROUTER_LATEST.txt"
[[ -d "$TERMINAL_ROOT" ]] || die "MetaQuotes Terminal root missing: $TERMINAL_ROOT"
mkdir -p "$STATE_DIR"

# Resolve the same MT5 data folder that contains the accepted V30 source.
TERMINAL_DATA=""; MATCHES=0
for src in "$TERMINAL_ROOT"/*/MQL5/Experts/mt5_quant/MlDlFeatureLakeV1.mq5; do
  [[ -f "$src" ]] || continue
  h="$(sha256sum "$src" | awk '{print $1}')"
  if [[ "$h" == "$V30_SOURCE_SHA" ]]; then
    TERMINAL_DATA="${src%/MQL5/Experts/mt5_quant/MlDlFeatureLakeV1.mq5}"
    MATCHES=$((MATCHES+1))
  fi
done
[[ "$MATCHES" -eq 1 ]] || die "Could not resolve exactly one accepted MT5 data folder; matches=$MATCHES"
say "MT5 data folder: $(cygpath -w "$TERMINAL_DATA")"

EXPERT_DIR="$TERMINAL_DATA/MQL5/Experts/mt5_quant"
mkdir -p "$EXPERT_DIR" "$TERMINAL_DATA/config"
for f in V31AiRouterLabV1.mq5 V31AiModelData.mqh V31AiNnWeights.mqh V31AiSvmWeights.mqh V31AiRffWeights.mqh; do
  cp -f "$SRC_DIR/$f" "$EXPERT_DIR/$f"
done

# Native Windows programs use /compile and /config switches; block MSYS rewriting.
export MSYS_NO_PATHCONV=1
export MSYS2_ARG_CONV_EXCL='*'

DST_SOURCE="$EXPERT_DIR/V31AiRouterLabV1.mq5"
DST_EX5="$EXPERT_DIR/V31AiRouterLabV1.ex5"
DST_LOG="$EXPERT_DIR/V31AiRouterLabV1.log"
rm -f "$DST_EX5" "$DST_LOG"
say "Compile gate: V31AiRouterLabV1.mq5"
"$METAEDITOR_EXE" "/compile:$(cygpath -w "$DST_SOURCE")" /log || true
[[ -s "$DST_LOG" ]] || die "MetaEditor compile log missing"
COMPILE_UTF8="$OUT/metaeditor_compile_utf8.txt"
if iconv -f UTF-16 -t UTF-8 "$DST_LOG" > "$COMPILE_UTF8" 2>/dev/null; then :; else tr -d '\r' < "$DST_LOG" > "$COMPILE_UTF8"; fi
tr -d '\r' < "$COMPILE_UTF8" > "$COMPILE_UTF8.tmp"; mv -f "$COMPILE_UTF8.tmp" "$COMPILE_UTF8"
summary="$(grep -Eio 'Result:[[:space:]]*[0-9]+[[:space:]]+errors?,[[:space:]]*[0-9]+[[:space:]]+warnings?' "$COMPILE_UTF8" | tail -n1 || true)"
[[ -n "$summary" ]] || { tail -n 80 "$COMPILE_UTF8" || true; die "Could not parse compile result"; }
printf '%s\n' "$summary"
errors="$(printf '%s' "$summary" | grep -Eo '[0-9]+[[:space:]]+errors?' | grep -Eo '[0-9]+' | tail -n1)"
warnings="$(printf '%s' "$summary" | grep -Eo '[0-9]+[[:space:]]+warnings?' | grep -Eo '[0-9]+' | tail -n1)"
[[ "$errors" == 0 && "$warnings" == 0 ]] || die "Compile gate failed errors=$errors warnings=$warnings"
[[ -s "$DST_EX5" ]] || die "Fresh V31 EX5 not produced"
say "Compile PASS: 0 errors / 0 warnings"

read_kv(){ local key="$1" file="$2"; awk -F= -v k="$key" '$1==k {sub(/^[^=]*=/,""); gsub(/\r/,""); print; exit}' "$file"; }

DONE="$CHECKPOINT/DONE.txt"
if [[ -f "$DONE" && -s "$CHECKPOINT/monthly_summary.csv" && -s "$CHECKPOINT/trades.csv" && -s "$CHECKPOINT/manifest.txt" && -s "$CHECKPOINT/state_after_v31.csv" ]]; then
  say "REUSE COMPLETE V31 CHECKPOINT -- MT5 NOT RERUN"
else
  # Preserve the user's current Common-Files state and restore it after the historical gate.
  BACKUP="$OUT/state_before_v31_user_environment.csv"
  HAD_STATE=0
  if [[ -s "$STATE" ]]; then cp -f "$STATE" "$BACKUP"; HAD_STATE=1; else rm -f "$BACKUP"; fi
  restore_state(){
    if [[ "$HAD_STATE" -eq 1 && -s "$BACKUP" ]]; then cp -f "$BACKUP" "$STATE"; else rm -f "$STATE"; fi
  }
  trap restore_state EXIT
  cp -f "$STATE_START" "$STATE"
  [[ "$(sha256sum "$STATE" | awk '{print $1}')" == "$STATE_START_SHA" ]] || die "Common-Files start state copy failed"

  before=""; [[ -f "$LATEST" ]] && before="$(read_kv run_id "$LATEST" || true)"
  RUNTIME_UTF8="$OUT/v31_runtime_utf8.ini"
  RUNTIME="$TERMINAL_DATA/config/mt5_quant_v31_ai_router_holdout.ini"
  cp -f "$TEMPLATE" "$RUNTIME_UTF8"
  printf '\xFF\xFE' > "$RUNTIME"
  iconv -f UTF-8 -t UTF-16LE "$RUNTIME_UTF8" >> "$RUNTIME"

  say "RUN V31 historical MT5 implementation gate: 2025-08-01 -> 2026-08-01"
  say "Model=Every tick (generated tester ticks); this is NOT claimed as real-tick history."
  "$TERMINAL_EXE" "/config:$(cygpath -w "$RUNTIME")"
  rc=$?
  say "MT5 returned rc=$rc"
  [[ "$rc" -eq 0 ]] || die "MT5 process failed rc=$rc"
  [[ -s "$LATEST" ]] || die "V31 locator missing after MT5"
  after="$(read_kv run_id "$LATEST" || true)"
  [[ -n "$after" && "$after" != "$before" ]] || die "V31 run_id did not refresh"
  [[ "$after" == *"__2025-08-01_00-00-00__"* ]] || die "Unexpected V31 run interval: $after"
  run_folder="$(read_kv run_folder "$LATEST")"; run_folder="${run_folder//\\//}"
  RUN_DIR="$COMMON_FILES/$run_folder"
  [[ -d "$RUN_DIR" ]] || die "V31 run folder missing: $RUN_DIR"

  rm -rf "$CHECKPOINT"; mkdir -p "$CHECKPOINT"
  for f in bar_features.csv monthly_summary.csv trades.csv manifest.txt; do
    [[ -s "$RUN_DIR/$f" ]] || die "V31 output missing/empty: $f"
    cp -f "$RUN_DIR/$f" "$CHECKPOINT/$f"
  done
  cp -f "$LATEST" "$CHECKPOINT/V31_AI_ROUTER_LATEST.txt"
  [[ -s "$STATE" ]] || die "V31 final adaptive state missing"
  cp -f "$STATE" "$CHECKPOINT/state_after_v31.csv"
  cp -f "$STATE_START" "$CHECKPOINT/state_start_2025_07.csv"
  cp -f "$COMPILE_UTF8" "$CHECKPOINT/metaeditor_compile_utf8.txt"

  grep -q '^format=mt5_quant_v31_ai_router_lab_v1' "$CHECKPOINT/manifest.txt" || die "manifest format mismatch"
  grep -q '^candidate_count=15' "$CHECKPOINT/manifest.txt" || die "manifest candidate_count mismatch"
  grep -q '^base_candidate_count=12' "$CHECKPOINT/manifest.txt" || die "manifest base count mismatch"
  grep -q '^native_broker_orders=0' "$CHECKPOINT/manifest.txt" || die "native-order safety marker missing"
  grep -q '^external_broker_orders=0' "$CHECKPOINT/manifest.txt" || die "external-order safety marker missing"
  grep -q '^ai_models=distilled_relu_nn,linear_svr,rff_rbf_kernel_ridge' "$CHECKPOINT/manifest.txt" || die "AI model manifest mismatch"
  rows=$(( $(wc -l < "$CHECKPOINT/monthly_summary.csv") - 1 ))
  [[ "$rows" -eq 720 ]] || die "monthly summary row count mismatch: expected 720, got $rows"
  months="$(awk -F, 'NR>1{gsub(/\r/,"",$1); print $1}' "$CHECKPOINT/monthly_summary.csv" | sort -u | wc -l | tr -d ' ')"
  [[ "$months" -eq 12 ]] || die "expected 12 monthly summary months, got $months"
  printf 'done=1\nrun_id=%s\nsummary_rows=%s\nmonths=%s\n' "$after" "$rows" "$months" > "$DONE"
  restore_state
  trap - EXIT
  say "COLLECT PASS: 12 months x 15 candidates x 4 books"
fi

# Quick fixed-$40 metrics. Formal analysis is performed after ZIP upload.
METRICS="$CHECKPOINT/V31_QUICK_METRICS.txt"
awk -F, '
BEGIN{OFS="\t"}
NR==1{next}
$5=="usd40_r1p0_cent" && ($2 ~ /^ai_/ || $2=="adaptive_ewma_hl8_thr0") {
  c=$2; n[c]++; ret[c]+=$28; tr[c]+=$21; vr[c]+=$32; mr[c]+=$33;
  if($28>0) pos[c]++; if($28>=15) hit[c]++;
  if(!(c in worst) || $28<worst[c]) worst[c]=$28;
  if(!(c in maxdd) || $29>maxdd[c]) maxdd[c]=$29;
}
END{
 print "candidate","months","avg_return_pct","positive_months","months_ge_15pct","worst_month_pct","max_monthly_mtm_dd_pct","trades","volume_reject","margin_reject";
 for(c in n) printf "%s\t%d\t%.4f\t%d\t%d\t%.4f\t%.4f\t%d\t%d\t%d\n",c,n[c],ret[c]/n[c],pos[c]+0,hit[c]+0,worst[c],maxdd[c],tr[c],vr[c],mr[c];
}' "$CHECKPOINT/monthly_summary.csv" > "$METRICS"
cat "$METRICS"

rm -rf "$PKG"; mkdir -p "$PKG"
cp -f "$CHECKPOINT/"{bar_features.csv,monthly_summary.csv,trades.csv,manifest.txt,V31_AI_ROUTER_LATEST.txt,state_start_2025_07.csv,state_after_v31.csv,metaeditor_compile_utf8.txt,V31_QUICK_METRICS.txt,DONE.txt} "$PKG/"
cp -f "$LOG" "$PKG/v31_git_bash_runner.log"
for f in V31AiRouterLabV1.mq5 V31AiModelData.mqh V31AiNnWeights.mqh V31AiSvmWeights.mqh V31AiRffWeights.mqh; do cp -f "$SRC_DIR/$f" "$PKG/$f"; done
STAMP="$(date '+%Y%m%d_%H%M%S')"
ZIP="$OUT/mt5_quant_v31_ai_router_MT5_${STAMP}.zip"
rm -f "$ZIP"
(cd "$PKG" && tar.exe -a -c -f "$(cygpath -w "$ZIP")" .)
[[ -s "$ZIP" ]] || die "Final ZIP not created"
ZIP_SHA="$(sha256sum "$ZIP" | awk '{print $1}')"
printf '%s  %s\n' "$ZIP_SHA" "$(basename "$ZIP")" > "$ZIP.sha256.txt"
say "ALL DONE"
printf '\nUPLOAD THIS ONE ZIP:\n%s\nSHA256=%s\n' "$(cygpath -w "$ZIP")" "$ZIP_SHA"
printf '\nDo not rerun MT5. Upload the ZIP for formal $40 / 15%%-per-month evaluation.\n'
