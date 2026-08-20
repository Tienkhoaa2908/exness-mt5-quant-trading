#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
OUT="$ROOT/OUTPUT_V31_MT5"
CP="$OUT/checkpoints"
LOG="$OUT/v31_mt5_model_gate_runner.log"
TERMINAL_EXE="${MT5_TERMINAL_EXE:-/c/Program Files/MetaTrader 5/terminal64.exe}"
METAEDITOR_EXE="${MT5_METAEDITOR_EXE:-/c/Program Files/MetaTrader 5/metaeditor64.exe}"
V30_SHA="4222120de5ded19ab7da172ad4c1e65d2a54b8bac7491fcd7927685b17b09a05"
V31_SHA="8dccbe939bb93a188675c4c61f2030f335a311113d97c813ec1e021ebcc052eb"
TAPE_SHA="44c11a98b75c7764e7a07eff245e1864d9dc85acc4a116a5cd162acb241539fc"
STATE_SRC="$ROOT/state_after_chunk2.csv"
SOURCE_PART="$ROOT/payload/v31_source.gz.b64.part00"
TAPE_PART_GLOB="$ROOT/payload/v31_tape.gz.b64.part"'??'

mkdir -p "$OUT" "$CP"
exec > >(tee -a "$LOG") 2>&1
say(){ printf '\n[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"; }
die(){ echo "FATAL: $*" >&2; exit 1; }
trap 'rc=$?; echo "FAILED rc=$rc line=${BASH_LINENO[0]:-?} cmd=${BASH_COMMAND:-?}" >&2; exit $rc' ERR
for c in cygpath sha256sum base64 gzip sed grep awk iconv tasklist.exe; do command -v "$c" >/dev/null || die "Missing command: $c"; done
[[ -f "$TERMINAL_EXE" ]] || die "terminal64.exe not found: $TERMINAL_EXE"
[[ -f "$METAEDITOR_EXE" ]] || die "metaeditor64.exe not found: $METAEDITOR_EXE"
[[ -s "$STATE_SRC" ]] || die "state_after_chunk2.csv missing"
[[ -s "$SOURCE_PART" ]] || die "V31 source payload missing"

if tasklist.exe //FI "IMAGENAME eq terminal64.exe" 2>/dev/null | tr -d '\r' | grep -qi terminal64.exe; then
  die "MetaTrader 5 is open. Close MT5 completely, then rerun this script."
fi

APPDATA_U="$(cygpath -u "$APPDATA")"
TERMINAL_ROOT="$APPDATA_U/MetaQuotes/Terminal"
COMMON="$TERMINAL_ROOT/Common/Files"
STATE_DIR="$COMMON/mt5_quant/inputs"
STATE="$STATE_DIR/v30_ml_dl_feature_lake_state.csv"
TAPE="$STATE_DIR/v31_gate_tape.csv"
LATEST="$COMMON/mt5_quant/ML_DL_FEATURE_LAKE_LATEST.txt"
mkdir -p "$STATE_DIR"

DATA=""; MATCH=0
for src in "$TERMINAL_ROOT"/*/MQL5/Experts/mt5_quant/MlDlFeatureLakeV1.mq5; do
  [[ -f "$src" ]] || continue
  h="$(sha256sum "$src" | awk '{print $1}')"
  if [[ "$h" == "$V30_SHA" ]]; then DATA="${src%/MQL5/Experts/mt5_quant/MlDlFeatureLakeV1.mq5}"; MATCH=$((MATCH+1)); fi
done
[[ "$MATCH" -eq 1 ]] || die "Could not resolve exactly one accepted MT5 data folder; matches=$MATCH"
say "MT5 data folder: $(cygpath -w "$DATA")"
EXPERT_DIR="$DATA/MQL5/Experts/mt5_quant"; mkdir -p "$EXPERT_DIR" "$DATA/config"

export MSYS_NO_PATHCONV=1
export MSYS2_ARG_CONV_EXCL='*'

BASE_SRC="$OUT/V31ModelGateLabV1.base.mq5"
base64 -d "$SOURCE_PART" | gzip -d > "$BASE_SRC"
[[ "$(sha256sum "$BASE_SRC" | awk '{print $1}')" == "$V31_SHA" ]] || die "V31 source hash mismatch"
! grep -Eq 'OrderSend\(|OrderSendAsync\(|CTrade|trade\.Buy\(|trade\.Sell\(' "$BASE_SRC" || die "Forbidden native-order token in V31 source"
grep -Fq 'MQLInfoInteger(MQL_TESTER)' "$BASE_SRC" || die "Tester-only guard missing"

cat $TAPE_PART_GLOB | base64 -d | gzip -d > "$TAPE"
[[ "$(sha256sum "$TAPE" | awk '{print $1}')" == "$TAPE_SHA" ]] || die "Gate tape hash mismatch"
say "V31 causal score tape verified"

INSTALL_WIN="$(cygpath -w "$(dirname "$TERMINAL_EXE")")"
ORIGIN="$DATA/origin"; ORIGIN_BAK="$OUT/.origin_backup"; HAD_ORIGIN=0
if [[ -f "$ORIGIN" ]]; then cp -f "$ORIGIN" "$ORIGIN_BAK"; HAD_ORIGIN=1; fi
printf '%s' "$INSTALL_WIN" > "$ORIGIN"
cleanup_origin(){ if [[ $HAD_ORIGIN -eq 1 ]]; then cp -f "$ORIGIN_BAK" "$ORIGIN"; else rm -f "$ORIGIN"; fi; rm -f "$ORIGIN_BAK"; }
trap 'cleanup_origin' EXIT

read_kv(){ awk -F= -v k="$1" '$1==k{sub(/^[^=]*=/,"");gsub(/\r/,"");print;exit}' "$2"; }
compile_ea(){
  local src="$1" log="${src%.mq5}.log" ex5="${src%.mq5}.ex5"
  rm -f "$log" "$ex5"
  "$METAEDITOR_EXE" "/compile:$(cygpath -w "$src")" /log || true
  [[ -s "$log" ]] || die "MetaEditor log missing for $src"
  local u8="$OUT/.compile.txt"
  if ! iconv -f UTF-16 -t UTF-8 "$log" > "$u8" 2>/dev/null; then tr -d '\r' < "$log" > "$u8"; fi
  local summary="$(tr -d '\r' < "$u8" | grep -Eio 'Result:[[:space:]]*[0-9]+[[:space:]]+errors?,[[:space:]]*[0-9]+[[:space:]]+warnings?' | tail -1 || true)"
  echo "$summary"
  [[ "$summary" =~ Result:[[:space:]]*0[[:space:]]+errors?,[[:space:]]*0[[:space:]]+warnings? ]] || die "Compile gate failed: $summary"
  [[ -s "$ex5" ]] || die "EX5 missing after compile"
}

make_ini(){
  local expert="$1" tag="$2" ini="$DATA/config/v31_${tag}.ini"
  local tmp="$OUT/.ini_utf8"
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
  local tag="$1" dest="$CP/$tag"
  [[ -s "$LATEST" ]] || die "LATEST locator missing after $tag"
  local run_id="$(read_kv run_id "$LATEST")" run_folder="$(read_kv run_folder "$LATEST")"
  [[ -n "$run_id" && -n "$run_folder" ]] || die "Invalid LATEST after $tag"
  run_folder="${run_folder//\\//}"; local rd="$COMMON/$run_folder"
  [[ -d "$rd" ]] || die "Run folder missing: $rd"
  mkdir -p "$dest"
  for f in monthly_summary.csv trades.csv manifest.txt; do [[ -s "$rd/$f" ]] || die "$f missing for $tag"; cp -f "$rd/$f" "$dest/$f"; done
  cp -f "$LATEST" "$dest/ML_DL_FEATURE_LAKE_LATEST.txt"
  printf 'tag=%s\nrun_id=%s\nsource_run_folder=%s\n' "$tag" "$run_id" "$run_folder" > "$dest/COLLECTED.txt"
  echo done > "$dest/DONE.txt"
  say "COLLECT PASS $tag run_id=$run_id"
}

run_mode(){
  local tag="$1" bit="$2" dest="$CP/$tag"
  if [[ -s "$dest/DONE.txt" && -s "$dest/monthly_summary.csv" && -s "$dest/trades.csv" ]]; then say "REUSE CHECKPOINT $tag -- MT5 NOT RERUN"; return; fi
  cp -f "$STATE_SRC" "$STATE"
  local ea="V31ModelGateLabV1_${tag}" src="$EXPERT_DIR/${ea}.mq5"
  cp -f "$BASE_SRC" "$src"
  sed -i "s/input int    InpV31GateBit = -1;/input int    InpV31GateBit = ${bit};/" "$src"
  sed -i "s/input string InpOutputTag = \"v31_mt5_model_gate_lab_v1\";/input string InpOutputTag = \"v31_${tag}\";/" "$src"
  sed -i 's/input bool   InpWriteBarFeatures = true;/input bool   InpWriteBarFeatures = false;/' "$src"
  say "Compile $tag gate_bit=$bit"; compile_ea "$src"
  local before=""; [[ -s "$LATEST" ]] && before="$(read_kv run_id "$LATEST" || true)"
  local ini="$(make_ini "$ea" "$tag")"
  say "RUN $tag 2026-02-01 -> 2026-08-01; virtual USD40 r1.0 book is the target metric"
  "$TERMINAL_EXE" "/config:$(cygpath -w "$ini")"
  local rc=$?; say "MT5 returned rc=$rc for $tag"
  [[ $rc -eq 0 ]] || die "MT5 failed for $tag"
  local after="$(read_kv run_id "$LATEST" || true)"; [[ -n "$after" && "$after" != "$before" ]] || die "LATEST did not refresh for $tag"
  collect "$tag"
}

run_mode baseline -1
run_mode catboost 0
run_mode extratrees 1
run_mode mlp_32_16 2
run_mode linear_svm 3

PKG="$OUT/package"; rm -rf "$PKG"; mkdir -p "$PKG"
for tag in baseline catboost extratrees mlp_32_16 linear_svm; do cp -R "$CP/$tag" "$PKG/$tag"; done
cp -f "$LOG" "$PKG/"
cp -f "$ROOT/model_tape_metadata.json" "$PKG/"
STAMP="$(date '+%Y%m%d_%H%M%S')"; ZIP="$OUT/v31_mt5_model_gate_40usd_${STAMP}.zip"
if command -v python >/dev/null 2>&1; then
 python - "$PKG" "$ZIP" <<'PY'
import os,sys,zipfile
root,out=sys.argv[1:]
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for base,dirs,files in os.walk(root):
  dirs.sort(); files.sort()
  for f in files:
   p=os.path.join(base,f); z.write(p,os.path.relpath(p,root).replace('\\','/'))
PY
else
 (cd "$PKG" && tar.exe -a -c -f "$(cygpath -w "$ZIP")" .)
fi
[[ -s "$ZIP" ]] || die "Final ZIP missing"
SHA="$(sha256sum "$ZIP"|awk '{print $1}')"
say "ALL DONE"
printf '\nUPLOAD THIS ONE ZIP:\n%s\nSHA256=%s\n' "$(cygpath -w "$ZIP")" "$SHA"
