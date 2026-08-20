#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
REPO_ROOT="$(cd -- "$ROOT/../.." && pwd -P)"
OUT="$ROOT/OUTPUT_V31_1_MT5"
CP="$OUT/checkpoints"
LOG="$OUT/v31_1_mt5_usd40_runner.log"
TERMINAL_EXE="${MT5_TERMINAL_EXE:-/c/Program Files/MetaTrader 5/terminal64.exe}"
METAEDITOR_EXE="${MT5_METAEDITOR_EXE:-/c/Program Files/MetaTrader 5/metaeditor64.exe}"
V30_SHA="4222120de5ded19ab7da172ad4c1e65d2a54b8bac7491fcd7927685b17b09a05"
V31_SHA="45ace4bd7465dbfb8a1b5670b67d372643b1eea057b1d7a44d80b91caf2b7c3e"
REFERENCE_TAPE_SHA="0df85b572f8273f6fef8624bbc12cbded1f77bded046c938eaa9ff5e2e7a3f7f"
STATE_SHA="39df0a74f8536235176362bccffc458e4b623190427536e8462bdae0f6000b76"
STATE_SRC="$ROOT/state_after_chunk2.csv"
SOURCE_BUILDER="$REPO_ROOT/scripts/build_v31_model_gate_source_v2.py"
TAPE_BUILDER="$REPO_ROOT/scripts/build_v31_gate_tape_v2.py"
ANALYZER="$REPO_ROOT/scripts/analyze_v31_1_mt5_usd40.py"

mkdir -p "$OUT" "$CP"
exec > >(tee -a "$LOG") 2>&1
say(){ printf '\n[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"; }
die(){ echo "FATAL: $*" >&2; exit 1; }
trap 'rc=$?; echo "FAILED rc=$rc line=${BASH_LINENO[0]:-?} cmd=${BASH_COMMAND:-?}" >&2; exit $rc' ERR
for c in cygpath sha256sum sed grep awk iconv tasklist.exe wc; do command -v "$c" >/dev/null || die "Missing command in Git Bash: $c"; done
[[ -f "$TERMINAL_EXE" ]] || die "terminal64.exe not found: $TERMINAL_EXE"
[[ -f "$METAEDITOR_EXE" ]] || die "metaeditor64.exe not found: $METAEDITOR_EXE"
[[ -s "$STATE_SRC" ]] || die "state_after_chunk2.csv missing"
[[ "$(sha256sum "$STATE_SRC"|awk '{print $1}')" == "$STATE_SHA" ]] || die "state_after_chunk2 hash mismatch"
for f in "$SOURCE_BUILDER" "$TAPE_BUILDER" "$ANALYZER"; do [[ -s "$f" ]] || die "required script missing: $f"; done

if tasklist.exe //FI "IMAGENAME eq terminal64.exe" 2>/dev/null | tr -d '\r' | grep -qi terminal64.exe; then
  die "MetaTrader 5 is open. Close MT5 completely, then rerun this script."
fi

if command -v python >/dev/null 2>&1; then SYS_PY="$(command -v python)"; elif command -v python3 >/dev/null 2>&1; then SYS_PY="$(command -v python3)"; else die "Python 3 is required."; fi
VENV="$OUT/.venv"; VENV_PY="$VENV/Scripts/python.exe"
if [[ ! -x "$VENV_PY" ]]; then say "Create isolated Python environment"; "$SYS_PY" -m venv "$VENV"; fi
[[ -x "$VENV_PY" ]] || die "venv Python missing: $VENV_PY"
if ! "$VENV_PY" - <<'PY' >/dev/null 2>&1
import numpy,pandas,sklearn,catboost
assert numpy.__version__=='2.3.5'
assert pandas.__version__=='2.2.3'
assert sklearn.__version__=='1.8.0'
assert catboost.__version__=='1.2.8'
PY
then
  say "Install pinned model dependencies"
  "$VENV_PY" -m pip install --disable-pip-version-check --upgrade pip
  "$VENV_PY" -m pip install --disable-pip-version-check "numpy==2.3.5" "pandas==2.2.3" "scikit-learn==1.8.0" "catboost==1.2.8"
fi
"$VENV_PY" -m py_compile "$SOURCE_BUILDER" "$TAPE_BUILDER" "$ANALYZER"
say "Python/model environment PASS"

APPDATA_U="$(cygpath -u "$APPDATA")"; TERMINAL_ROOT="$APPDATA_U/MetaQuotes/Terminal"; COMMON="$TERMINAL_ROOT/Common/Files"
STATE_DIR="$COMMON/mt5_quant/inputs"; STATE="$STATE_DIR/v30_ml_dl_feature_lake_state.csv"; TAPE="$STATE_DIR/v31_1_gate_tape.csv"
TAPE_META="$OUT/v31_1_gate_tape.generated.json"; LATEST="$COMMON/mt5_quant/ML_DL_FEATURE_LAKE_LATEST.txt"; mkdir -p "$STATE_DIR"

DATA=""; MATCH=0; V30_SRC=""
for src in "$TERMINAL_ROOT"/*/MQL5/Experts/mt5_quant/MlDlFeatureLakeV1.mq5; do
  [[ -f "$src" ]] || continue
  h="$(sha256sum "$src"|awk '{print $1}')"
  if [[ "$h" == "$V30_SHA" ]]; then DATA="${src%/MQL5/Experts/mt5_quant/MlDlFeatureLakeV1.mq5}"; V30_SRC="$src"; MATCH=$((MATCH+1)); fi
done
[[ "$MATCH" -eq 1 ]] || die "Could not resolve exactly one accepted V30 MT5 data folder; matches=$MATCH"
say "MT5 data folder: $(cygpath -w "$DATA")"
EXPERT_DIR="$DATA/MQL5/Experts/mt5_quant"; mkdir -p "$EXPERT_DIR" "$DATA/config"

for rid in \
 "ml_dl_feature_lake_v1__XAUUSDm__PERIOD_M15__2025-02-01_00-00-00__756375" \
 "ml_dl_feature_lake_v1__XAUUSDm__PERIOD_M15__2025-08-01_00-00-00__22265" \
 "ml_dl_feature_lake_v1__XAUUSDm__PERIOD_M15__2026-02-01_00-00-00__519093"; do
  rd="$COMMON/mt5_quant/runs/$rid"
  [[ -s "$rd/bar_features.csv" && -s "$rd/trades.csv" && -s "$rd/manifest.txt" ]] || die "Accepted V30 run files missing: $rd"
done

export MSYS_NO_PATHCONV=1
export MSYS2_ARG_CONV_EXCL='*'

BASE_SRC="$OUT/V31_1_ModelGateUsd40.base.mq5"
say "Build tester-only V31.1 source from accepted V30 source"
"$VENV_PY" "$SOURCE_BUILDER" --source "$(cygpath -w "$V30_SRC")" --output "$(cygpath -w "$BASE_SRC")"
[[ "$(sha256sum "$BASE_SRC"|awk '{print $1}')" == "$V31_SHA" ]] || die "V31.1 source hash mismatch"
! grep -Eq 'OrderSend\(|OrderSendAsync\(|CTrade|trade\.Buy\(|trade\.Sell\(' "$BASE_SRC" || die "Forbidden native-order token in V31.1 source"
grep -Fq 'MQLInfoInteger(MQL_TESTER)' "$BASE_SRC" || die "Tester-only guard missing"
grep -Fq 'InpV31ContinuousUsd40 = true' "$BASE_SRC" || die "Continuous USD40 gate missing"

say "Train causal CatBoost / ExtraTrees / DeepMLP / LinearSVM and build current-bar score tape"
"$VENV_PY" "$TAPE_BUILDER" --common-files "$(cygpath -w "$COMMON")" --output "$(cygpath -w "$TAPE")" --metadata "$(cygpath -w "$TAPE_META")"
[[ -s "$TAPE" ]] || die "V31.1 gate tape missing"
LINES="$(wc -l < "$TAPE"|tr -d ' ')"; [[ "$LINES" == "23617" ]] || die "Unexpected gate tape line count=$LINES expected=23617"
TAPE_SHA="$(sha256sum "$TAPE"|awk '{print $1}')"
if [[ "$TAPE_SHA" == "$REFERENCE_TAPE_SHA" ]]; then say "Causal gate tape reference PASS sha=$TAPE_SHA"; else say "Generated tape sha=$TAPE_SHA differs from Linux reference=$REFERENCE_TAPE_SHA; pinned protocol/row checks passed and generated hash will be retained as evidence"; fi
FIRST_TAPE="$(sed -n '2p' "$TAPE"|cut -d, -f1|tr -d '\r')"; LAST_TAPE="$(tail -n 1 "$TAPE"|cut -d, -f1|tr -d '\r')"
[[ "$FIRST_TAPE" == "2025.08.01 00:00:00" ]] || die "Gate tape first current bar wrong: $FIRST_TAPE"
[[ "$LAST_TAPE" == 2026.07.* ]] || die "Gate tape last current bar wrong: $LAST_TAPE"

INSTALL_WIN="$(cygpath -w "$(dirname "$TERMINAL_EXE")")"; ORIGIN="$DATA/origin"; ORIGIN_BAK="$OUT/.origin_backup"; HAD_ORIGIN=0
if [[ -f "$ORIGIN" ]]; then cp -f "$ORIGIN" "$ORIGIN_BAK"; HAD_ORIGIN=1; fi
printf '%s' "$INSTALL_WIN" > "$ORIGIN"
cleanup_origin(){ if [[ $HAD_ORIGIN -eq 1 ]]; then cp -f "$ORIGIN_BAK" "$ORIGIN"; else rm -f "$ORIGIN"; fi; rm -f "$ORIGIN_BAK"; }
trap 'cleanup_origin' EXIT

read_kv(){ awk -F= -v k="$1" '$1==k{sub(/^[^=]*=/,"");gsub(/\r/,"");print;exit}' "$2"; }
compile_ea(){
  local src="$1" log="${src%.mq5}.log" ex5="${src%.mq5}.ex5"; rm -f "$log" "$ex5"
  "$METAEDITOR_EXE" "/compile:$(cygpath -w "$src")" /log || true
  [[ -s "$log" ]] || die "MetaEditor log missing for $src"
  local u8="$OUT/.compile.txt"; if ! iconv -f UTF-16 -t UTF-8 "$log" > "$u8" 2>/dev/null; then tr -d '\r' < "$log" > "$u8"; fi
  local summary="$(tr -d '\r' < "$u8"|grep -Eio 'Result:[[:space:]]*[0-9]+[[:space:]]+errors?,[[:space:]]*[0-9]+[[:space:]]+warnings?'|tail -1||true)"; echo "$summary"
  [[ "$summary" =~ Result:[[:space:]]*0[[:space:]]+errors?,[[:space:]]*0[[:space:]]+warnings? ]] || die "Compile gate failed: $summary"
  [[ -s "$ex5" ]] || die "EX5 missing after compile"
}
make_ini(){
  local expert="$1" tag="$2" ini="$DATA/config/v31_1_${tag}.ini" tmp="$OUT/.ini_utf8"
  cat > "$tmp" <<EOF
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
Expert=mt5_quant\\${expert}.ex5
Symbol=XAUUSDm
Period=M15
Optimization=0
Model=0
FromDate=2026.02.01
ToDate=2026.08.01
ForwardMode=0
Deposit=40
Currency=USD
Leverage=1:200
ExecutionMode=0
OptimizationCriterion=0
UseCloud=0
Visual=0
ShutdownTerminal=1
EOF
  printf '\xFF\xFE' > "$ini"; iconv -f UTF-8 -t UTF-16LE "$tmp" >> "$ini"; rm -f "$tmp"; printf '%s' "$ini"
}
collect(){
  local tag="$1" dest="$CP/$tag"; [[ -s "$LATEST" ]] || die "LATEST locator missing after $tag"
  local run_id="$(read_kv run_id "$LATEST")" run_folder="$(read_kv run_folder "$LATEST")"; [[ -n "$run_id" && -n "$run_folder" ]] || die "Invalid LATEST after $tag"
  run_folder="${run_folder//\\//}"; local rd="$COMMON/$run_folder"; [[ -d "$rd" ]] || die "Run folder missing: $rd"; mkdir -p "$dest"
  for f in monthly_summary.csv trades.csv manifest.txt; do [[ -s "$rd/$f" ]] || die "$f missing for $tag"; cp -f "$rd/$f" "$dest/$f"; done
  grep -Fq 'continuous_usd40=1' "$dest/manifest.txt" || die "continuous USD40 manifest marker missing for $tag"
  cp -f "$LATEST" "$dest/ML_DL_FEATURE_LAKE_LATEST.txt"
  printf 'tag=%s\nrun_id=%s\nsource_run_folder=%s\ntape_sha=%s\nsource_sha=%s\ndeposit_usd=40\nperiod=2026-02-01_to_2026-08-01\n' "$tag" "$run_id" "$run_folder" "$TAPE_SHA" "$V31_SHA" > "$dest/COLLECTED.txt"
  echo done > "$dest/DONE.txt"; say "COLLECT PASS $tag run_id=$run_id"
}
run_mode(){
  local tag="$1" bit="$2" dest="$CP/$tag"
  if [[ -s "$dest/DONE.txt" && -s "$dest/monthly_summary.csv" && -s "$dest/trades.csv" ]]; then say "REUSE CHECKPOINT $tag -- MT5 NOT RERUN"; return; fi
  cp -f "$STATE_SRC" "$STATE"
  local ea="V31_1_ModelGateUsd40_${tag}" src="$EXPERT_DIR/${ea}.mq5"; cp -f "$BASE_SRC" "$src"
  sed -i "s/input int    InpV31GateBit = -1;/input int    InpV31GateBit = ${bit};/" "$src"
  sed -i "s/input string InpOutputTag = \"v31_1_mt5_model_gate_usd40_continuous_v1\";/input string InpOutputTag = \"v31_1_${tag}\";/" "$src"
  sed -i 's/input bool   InpWriteBarFeatures = true;/input bool   InpWriteBarFeatures = false;/' "$src"
  say "Compile $tag gate_bit=$bit"; compile_ea "$src"
  local before=""; [[ -s "$LATEST" ]] && before="$(read_kv run_id "$LATEST"||true)"; local ini="$(make_ini "$ea" "$tag")"
  say "RUN $tag — MT5 Strategy Tester Deposit=40 USD, continuous book risk=1.00%/trade, 2026-02-01 -> 2026-08-01"
  "$TERMINAL_EXE" "/config:$(cygpath -w "$ini")"; local rc=$?; say "MT5 returned rc=$rc for $tag"; [[ $rc -eq 0 ]] || die "MT5 failed for $tag"
  local after="$(read_kv run_id "$LATEST"||true)"; [[ -n "$after" && "$after" != "$before" ]] || die "LATEST did not refresh for $tag"
  collect "$tag"
}

run_mode baseline -1
run_mode catboost 0
run_mode extratrees 1
run_mode deep_mlp 2
run_mode linear_svm 3
run_mode catboost_and_extratrees 4
run_mode majority_2of4 5

PKG="$OUT/package"; rm -rf "$PKG"; mkdir -p "$PKG"
for tag in baseline catboost extratrees deep_mlp linear_svm catboost_and_extratrees majority_2of4; do cp -R "$CP/$tag" "$PKG/$tag"; done
cp -f "$LOG" "$PKG/"; cp -f "$TAPE_META" "$PKG/v31_1_gate_tape.generated.json"
printf 'reference_tape_sha=%s\ngenerated_tape_sha=%s\nsource_sha=%s\nstate_sha=%s\nperiod=2026-02-01_to_2026-08-01\nmt5_tester_deposit_usd=40\ndecision_book=usd40_r1p0_cent_continuous\nrisk_per_trade=1.00%%\ncapital_carries_month_to_month=1\nmonthly_liquidation=1\n' "$REFERENCE_TAPE_SHA" "$TAPE_SHA" "$V31_SHA" "$STATE_SHA" > "$PKG/V31_1_EVIDENCE.txt"

say "Analyze exact MT5 outputs — no Python PnL reconstruction"
"$VENV_PY" "$ANALYZER" --package-root "$(cygpath -w "$PKG")" --output "$(cygpath -w "$PKG/analysis")"
[[ -s "$PKG/analysis/V31_1_EXACT_MT5_REPORT.txt" ]] || die "Exact MT5 analysis report missing"
cat "$PKG/analysis/V31_1_EXACT_MT5_REPORT.txt"

STAMP="$(date '+%Y%m%d_%H%M%S')"; ZIP="$OUT/v31_1_exact_mt5_usd40_${STAMP}.zip"
"$VENV_PY" - "$PKG" "$ZIP" <<'PYZIP'
import os,sys,zipfile
root,out=sys.argv[1:]
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for base,dirs,files in os.walk(root):
        dirs.sort(); files.sort()
        for f in files:
            p=os.path.join(base,f); z.write(p,os.path.relpath(p,root).replace('\\','/'))
PYZIP
[[ -s "$ZIP" ]] || die "Final ZIP missing"; SHA="$(sha256sum "$ZIP"|awk '{print $1}')"
say "ALL DONE"
printf '\nUPLOAD THIS ONE ZIP:\n%s\nSHA256=%s\n' "$(cygpath -w "$ZIP")" "$SHA"
printf '\nPrimary decision table is package/analysis/V31_1_EXACT_MT5_REPORT.txt. PnL/return/DD/trades are from MT5 Strategy Tester outputs.\n'
