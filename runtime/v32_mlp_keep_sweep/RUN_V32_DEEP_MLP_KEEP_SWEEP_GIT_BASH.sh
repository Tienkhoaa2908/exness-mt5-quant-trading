#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
REPO_ROOT="$(cd -- "$ROOT/../.." && pwd -P)"
OUT="$ROOT/OUTPUT_V32_MT5"
CP="$OUT/checkpoints"
LOG="$OUT/v32_mlp_keep_sweep_runner.log"
TERMINAL_EXE="${MT5_TERMINAL_EXE:-/c/Program Files/MetaTrader 5/terminal64.exe}"
METAEDITOR_EXE="${MT5_METAEDITOR_EXE:-/c/Program Files/MetaTrader 5/metaeditor64.exe}"
V30_SHA="4222120de5ded19ab7da172ad4c1e65d2a54b8bac7491fcd7927685b17b09a05"
V32_SHA="ff131ff8ce1d5ba7c3be42c8d6acdbb6f64a898d51fe6c64771f29e91ae5543a"
REFERENCE_TAPE_SHA="8b3550dbdf451d558349be46d4a1b9391feba04c29cd21968594473eae716356"
STATE_SHA="39df0a74f8536235176362bccffc458e4b623190427536e8462bdae0f6000b76"
STATE_SRC="$ROOT/state_after_chunk2.csv"
SOURCE_BUILDER="$REPO_ROOT/scripts/build_v32_deep_mlp_keep_source.py"
TAPE_BUILDER="$REPO_ROOT/scripts/build_v32_deep_mlp_keep_tape.py"
ANALYZER="$REPO_ROOT/scripts/analyze_v32_deep_mlp_keep_mt5.py"

mkdir -p "$OUT" "$CP"
exec > >(tee -a "$LOG") 2>&1
say(){ printf '\n[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"; }
die(){ echo "FATAL: $*" >&2; exit 1; }
trap 'rc=$?; echo "FAILED rc=$rc line=${BASH_LINENO[0]:-?} cmd=${BASH_COMMAND:-?}" >&2; exit $rc' ERR
for c in cygpath sha256sum sed grep awk iconv tasklist.exe wc; do command -v "$c" >/dev/null || die "Missing Git Bash command: $c"; done
[[ -f "$TERMINAL_EXE" ]] || die "terminal64.exe not found: $TERMINAL_EXE"
[[ -f "$METAEDITOR_EXE" ]] || die "metaeditor64.exe not found: $METAEDITOR_EXE"
[[ -s "$STATE_SRC" ]] || die "state_after_chunk2.csv missing"
[[ "$(sha256sum "$STATE_SRC"|awk '{print $1}')" == "$STATE_SHA" ]] || die "state_after_chunk2 hash mismatch"
for f in "$SOURCE_BUILDER" "$TAPE_BUILDER" "$ANALYZER"; do [[ -s "$f" ]] || die "required script missing: $f"; done

if tasklist.exe //FI "IMAGENAME eq terminal64.exe" 2>/dev/null | tr -d '\r' | grep -qi terminal64.exe; then die "MetaTrader 5 is open. Close MT5 completely and rerun."; fi

V31_PY="$REPO_ROOT/runtime/v31_mt5_model_gate/OUTPUT_V31_1_MT5/.venv/Scripts/python.exe"
VENV="$OUT/.venv"; VENV_PY="$VENV/Scripts/python.exe"; PY=""
if [[ -x "$V31_PY" ]] && "$V31_PY" - <<'PYCHK' >/dev/null 2>&1
import numpy,pandas,sklearn
assert numpy.__version__=='2.3.5'
assert pandas.__version__=='2.2.3'
assert sklearn.__version__=='1.8.0'
PYCHK
then
  PY="$V31_PY"; say "Reuse pinned V31.1 Python environment"
else
  if command -v python >/dev/null 2>&1; then SYS_PY="$(command -v python)"; elif command -v python3 >/dev/null 2>&1; then SYS_PY="$(command -v python3)"; else die "Python 3 required"; fi
  if [[ ! -x "$VENV_PY" ]]; then "$SYS_PY" -m venv "$VENV"; fi
  if ! "$VENV_PY" - <<'PYCHK' >/dev/null 2>&1
import numpy,pandas,sklearn
assert numpy.__version__=='2.3.5'
assert pandas.__version__=='2.2.3'
assert sklearn.__version__=='1.8.0'
PYCHK
  then
    say "Install pinned V32 dependencies"
    "$VENV_PY" -m pip install --disable-pip-version-check --upgrade pip
    "$VENV_PY" -m pip install --disable-pip-version-check "numpy==2.3.5" "pandas==2.2.3" "scikit-learn==1.8.0"
  fi
  PY="$VENV_PY"
fi
"$PY" -m py_compile "$SOURCE_BUILDER" "$TAPE_BUILDER" "$ANALYZER"
say "Python environment PASS"

APPDATA_U="$(cygpath -u "$APPDATA")"; TERMINAL_ROOT="$APPDATA_U/MetaQuotes/Terminal"; COMMON="$TERMINAL_ROOT/Common/Files"
STATE_DIR="$COMMON/mt5_quant/inputs"; STATE="$STATE_DIR/v30_ml_dl_feature_lake_state.csv"; TAPE="$STATE_DIR/v32_mlp_keep_tape.csv"
TAPE_META="$OUT/v32_mlp_keep_tape.generated.json"; LATEST="$COMMON/mt5_quant/ML_DL_FEATURE_LAKE_LATEST.txt"; mkdir -p "$STATE_DIR"

DATA=""; V30_SRC=""; MATCH=0
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

BASE_SRC="$OUT/V32DeepMlpKeepSweep.base.mq5"
say "Build tester-only V32 source from accepted V30 source"
"$PY" "$SOURCE_BUILDER" --source "$(cygpath -w "$V30_SRC")" --output "$(cygpath -w "$BASE_SRC")"
[[ "$(sha256sum "$BASE_SRC"|awk '{print $1}')" == "$V32_SHA" ]] || die "V32 source hash mismatch"
! grep -Eq 'OrderSend\(|OrderSendAsync\(|CTrade|trade\.Buy\(|trade\.Sell\(' "$BASE_SRC" || die "Forbidden native-order token in V32 source"
grep -Fq 'MQLInfoInteger(MQL_TESTER)' "$BASE_SRC" || die "Tester-only guard missing"

if [[ -s "$TAPE" && -s "$TAPE_META" && "$(wc -l < "$TAPE"|tr -d ' ')" == "23617" && "$(sha256sum "$TAPE"|awk '{print $1}')" == "$REFERENCE_TAPE_SHA" ]]; then
  TAPE_SHA="$REFERENCE_TAPE_SHA"; say "REUSE verified V32 DeepMLP keep-rate tape sha=$TAPE_SHA"
else
  say "Train causal DeepMLP and build nested keep-rate tape 50/60/70/80/90%"
  "$PY" "$TAPE_BUILDER" --common-files "$(cygpath -w "$COMMON")" --output "$(cygpath -w "$TAPE")" --metadata "$(cygpath -w "$TAPE_META")"
  [[ -s "$TAPE" ]] || die "V32 tape missing"
  LINES="$(wc -l < "$TAPE"|tr -d ' ')"; [[ "$LINES" == "23617" ]] || die "Unexpected tape lines=$LINES"
  TAPE_SHA="$(sha256sum "$TAPE"|awk '{print $1}')"; [[ "$TAPE_SHA" == "$REFERENCE_TAPE_SHA" ]] || die "V32 tape hash mismatch expected=$REFERENCE_TAPE_SHA actual=$TAPE_SHA"
fi
FIRST_TAPE="$(sed -n '2p' "$TAPE"|cut -d, -f1|tr -d '\r')"; LAST_TAPE="$(tail -n 1 "$TAPE"|cut -d, -f1|tr -d '\r')"
[[ "$FIRST_TAPE" == "2025.08.01 00:00:00" ]] || die "V32 tape first bar wrong: $FIRST_TAPE"
[[ "$LAST_TAPE" == 2026.07.* ]] || die "V32 tape last bar wrong: $LAST_TAPE"

INSTALL_WIN="$(cygpath -w "$(dirname "$TERMINAL_EXE")")"; ORIGIN="$DATA/origin"; ORIGIN_BAK="$OUT/.origin_backup"; HAD_ORIGIN=0
if [[ -f "$ORIGIN" ]]; then cp -f "$ORIGIN" "$ORIGIN_BAK"; HAD_ORIGIN=1; fi
printf '%s' "$INSTALL_WIN" > "$ORIGIN"
cleanup_origin(){ if [[ "$HAD_ORIGIN" -eq 1 ]]; then cp -f "$ORIGIN_BAK" "$ORIGIN"; else rm -f "$ORIGIN"; fi; rm -f "$ORIGIN_BAK"; }
trap 'cleanup_origin' EXIT

read_kv(){ awk -F= -v k="$1" '$1==k{sub(/^[^=]*=/,"");gsub(/\r/,"");print;exit}' "$2"; }
compile_ea(){
  local src="$1"; local log="${src%.mq5}.log"; local ex5="${src%.mq5}.ex5"; rm -f "$log" "$ex5"
  MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' "$METAEDITOR_EXE" "/compile:$(cygpath -w "$src")" /log || true
  [[ -s "$log" ]] || die "MetaEditor log missing for $src"
  local u8="$OUT/.compile.txt"; if ! iconv -f UTF-16 -t UTF-8 "$log" > "$u8" 2>/dev/null; then tr -d '\r' < "$log" > "$u8"; fi
  local summary; summary="$(tr -d '\r' < "$u8"|grep -Eio 'Result:[[:space:]]*[0-9]+[[:space:]]+errors?,[[:space:]]*[0-9]+[[:space:]]+warnings?'|tail -1||true)"; echo "$summary"
  [[ "$summary" =~ Result:[[:space:]]*0[[:space:]]+errors?,[[:space:]]*0[[:space:]]+warnings? ]] || die "Compile gate failed: $summary"
  [[ -s "$ex5" ]] || die "EX5 missing after compile"
}
make_ini(){
  local expert="$1"; local tag="$2"; local ini="$DATA/config/v32_${tag}.ini"; local tmp="$OUT/.ini_utf8"
  cat > "$tmp" <<EOF_INI
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
EOF_INI
  printf '\xFF\xFE' > "$ini"; iconv -f UTF-8 -t UTF-16LE "$tmp" >> "$ini"; rm -f "$tmp"; printf '%s' "$ini"
}
collect(){
  local tag="$1"; local dest="$CP/$tag"; [[ -s "$LATEST" ]] || die "LATEST locator missing after $tag"
  local run_id; local run_folder; run_id="$(read_kv run_id "$LATEST")"; run_folder="$(read_kv run_folder "$LATEST")"
  [[ -n "$run_id" && -n "$run_folder" ]] || die "Invalid LATEST after $tag"; run_folder="${run_folder//\\//}"; local rd="$COMMON/$run_folder"
  [[ -d "$rd" ]] || die "Run folder missing: $rd"; mkdir -p "$dest"
  for f in monthly_summary.csv trades.csv manifest.txt; do [[ -s "$rd/$f" ]] || die "$f missing for $tag"; cp -f "$rd/$f" "$dest/$f"; done
  grep -Fq 'v32_deep_mlp_keep_sweep=1' "$dest/manifest.txt" || die "V32 manifest marker missing for $tag"
  grep -Fq 'continuous_usd40=1' "$dest/manifest.txt" || die "continuous USD40 marker missing for $tag"
  cp -f "$LATEST" "$dest/ML_DL_FEATURE_LAKE_LATEST.txt"
  printf 'tag=%s\nrun_id=%s\nsource_run_folder=%s\ntape_sha=%s\nsource_sha=%s\ndeposit_usd=40\nperiod=2026-02-01_to_2026-08-01\n' "$tag" "$run_id" "$run_folder" "$TAPE_SHA" "$V32_SHA" > "$dest/COLLECTED.txt"
  echo done > "$dest/DONE.txt"; say "COLLECT PASS $tag run_id=$run_id"
}
run_mode(){
  local tag="$1"; local bit="$2"; local dest="$CP/$tag"
  if [[ -s "$dest/DONE.txt" && -s "$dest/monthly_summary.csv" && -s "$dest/trades.csv" ]]; then say "REUSE CHECKPOINT $tag -- MT5 NOT RERUN"; return; fi
  cp -f "$STATE_SRC" "$STATE"
  local ea="V32DeepMlpKeep_${tag}"; local src="$EXPERT_DIR/${ea}.mq5"; cp -f "$BASE_SRC" "$src"
  sed -i "s/input int    InpV32GateBit = -1;/input int    InpV32GateBit = ${bit};/" "$src"
  sed -i "s/input string InpOutputTag = \"v32_deep_mlp_keep_sweep_usd40_continuous_v1\";/input string InpOutputTag = \"v32_${tag}\";/" "$src"
  sed -i 's/input bool   InpWriteBarFeatures = true;/input bool   InpWriteBarFeatures = false;/' "$src"
  say "Compile $tag gate_bit=$bit"; compile_ea "$src"
  local before=""; [[ -s "$LATEST" ]] && before="$(read_kv run_id "$LATEST"||true)"; local ini; ini="$(make_ini "$ea" "$tag")"
  say "RUN $tag — exact MT5 Deposit=40 USD, continuous risk ceiling 1.00%/trade"
  MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' "$TERMINAL_EXE" "/config:$(cygpath -w "$ini")"; local rc=$?; say "MT5 returned rc=$rc for $tag"; [[ "$rc" -eq 0 ]] || die "MT5 failed for $tag"
  local after; after="$(read_kv run_id "$LATEST"||true)"; [[ -n "$after" && "$after" != "$before" ]] || die "LATEST did not refresh for $tag"; collect "$tag"
}

run_mode baseline -1
run_mode mlp_keep50 0
run_mode mlp_keep60 1
run_mode mlp_keep70 2
run_mode mlp_keep80 3
run_mode mlp_keep90 4

PKG="$OUT/package"; rm -rf "$PKG"; mkdir -p "$PKG"
for tag in baseline mlp_keep50 mlp_keep60 mlp_keep70 mlp_keep80 mlp_keep90; do cp -R "$CP/$tag" "$PKG/$tag"; done
cp -f "$LOG" "$PKG/"; cp -f "$TAPE_META" "$PKG/v32_mlp_keep_tape.generated.json"
printf 'reference_tape_sha=%s\ngenerated_tape_sha=%s\nsource_sha=%s\nstate_sha=%s\nperiod=2026-02-01_to_2026-08-01\nmt5_tester_deposit_usd=40\ndecision_book=usd40_r1p0_cent_continuous\nrisk_ceiling_per_trade=1.00%%\ndevelopment_sweep_not_fresh_confirmation=1\n' "$REFERENCE_TAPE_SHA" "$TAPE_SHA" "$V32_SHA" "$STATE_SHA" > "$PKG/V32_EVIDENCE.txt"

say "Analyze exact MT5 V32 outputs"
"$PY" "$ANALYZER" --package-root "$(cygpath -w "$PKG")" --output "$(cygpath -w "$PKG/analysis")"
[[ -s "$PKG/analysis/V32_EXACT_MT5_REPORT.txt" ]] || die "V32 exact report missing"; cat "$PKG/analysis/V32_EXACT_MT5_REPORT.txt"

STAMP="$(date '+%Y%m%d_%H%M%S')"; ZIP="$OUT/v32_deep_mlp_keep_sweep_exact_mt5_usd40_${STAMP}.zip"
"$PY" - "$PKG" "$ZIP" <<'PYZIP'
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
