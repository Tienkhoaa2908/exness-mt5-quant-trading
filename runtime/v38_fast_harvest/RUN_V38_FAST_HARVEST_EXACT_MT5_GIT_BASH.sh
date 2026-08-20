#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
REPO_ROOT="$(cd -- "$ROOT/../.." && pwd -P)"
OUT="$ROOT/OUTPUT_V38"
CP="$OUT/checkpoints"
LOG="$OUT/v38_fast_harvest_runner.log"

TERMINAL_EXE="${MT5_TERMINAL_EXE:-/c/Program Files/MetaTrader 5/terminal64.exe}"
METAEDITOR_EXE="${MT5_METAEDITOR_EXE:-/c/Program Files/MetaTrader 5/metaeditor64.exe}"

V30_SHA="4222120de5ded19ab7da172ad4c1e65d2a54b8bac7491fcd7927685b17b09a05"
V34_ACCEPTED_SHA="8bae2c56d43d11809ae96b5ee2f4bfe59007231ed5642bebe73dfbe2db7a7f10"
V34_TAPE_SHA="d70d92d0023c1862af6363d60a7d9e927f928e75ffcf1c0cedcb4f7798128863"
STATE1_SHA="5110519f2fe9722b4c13eb1e5ceec42f00bd04dd3b4f071af28349068b6097b0"

STATE1="$REPO_ROOT/runtime/v34_parallel_alpha/state_after_chunk1.csv"
F34="$REPO_ROOT/scripts/v34_parallel_alpha_features.py"
S34="$REPO_ROOT/scripts/build_v34_parallel_alpha_source.py"
S38="$REPO_ROOT/scripts/build_v38_fast_harvest_source.py"
A38="$REPO_ROOT/scripts/analyze_v38_fast_harvest_mt5.py"

mkdir -p "$OUT" "$CP"
exec > >(tee -a "$LOG") 2>&1

say(){ printf '\n[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"; }
die(){ echo "FATAL: $*" >&2; exit 1; }
trap 'rc=$?; echo "FAILED rc=$rc line=${BASH_LINENO[0]:-?} cmd=${BASH_COMMAND:-?}" >&2; exit $rc' ERR

for c in cygpath sha256sum grep awk iconv tasklist.exe wc tr; do
  command -v "$c" >/dev/null || die "Missing Git Bash command: $c"
done
[[ -f "$TERMINAL_EXE" && -f "$METAEDITOR_EXE" ]] || die "MT5/MetaEditor executable missing"
for f in "$STATE1" "$F34" "$S34" "$S38" "$A38"; do [[ -s "$f" ]] || die "required file missing: $f"; done
[[ "$(sha256sum "$STATE1"|awk '{print $1}')" == "$STATE1_SHA" ]] || die "state1 hash mismatch"

if tasklist.exe //FI "IMAGENAME eq terminal64.exe" 2>/dev/null | tr -d '\r' | grep -qi terminal64.exe; then
  die "MetaTrader 5 is open. Close MT5 completely and rerun."
fi

V31_PY="$REPO_ROOT/runtime/v31_mt5_model_gate/OUTPUT_V31_1_MT5/.venv/Scripts/python.exe"
[[ -x "$V31_PY" ]] || die "Pinned V31/V32 Python environment missing: $V31_PY"
PY="$V31_PY"
"$PY" - <<'PYCHK'
import numpy,pandas,sklearn
assert numpy.__version__=='2.3.5'
assert pandas.__version__=='2.2.3'
assert sklearn.__version__=='1.8.0'
PYCHK
"$PY" -m py_compile "$F34" "$S34" "$S38" "$A38"
"$PY" -m pytest -q "$REPO_ROOT/tests/test_v38_fast_harvest_static.py"
say "Python/static tests PASS"

APPDATA_U="$(cygpath -u "$APPDATA")"
TERM_ROOT="$APPDATA_U/MetaQuotes/Terminal"
COMMON="$TERM_ROOT/Common/Files"
INPUTS="$COMMON/mt5_quant/inputs"
mkdir -p "$INPUTS"
LATEST="$COMMON/mt5_quant/ML_DL_FEATURE_LAKE_LATEST.txt"

DATA=""
V30_SRC=""
MATCH=0
for src in "$TERM_ROOT"/*/MQL5/Experts/mt5_quant/MlDlFeatureLakeV1.mq5; do
  [[ -f "$src" ]] || continue
  h="$(sha256sum "$src"|awk '{print $1}')"
  if [[ "$h" == "$V30_SHA" ]]; then
    DATA="${src%/MQL5/Experts/mt5_quant/MlDlFeatureLakeV1.mq5}"
    V30_SRC="$src"
    MATCH=$((MATCH+1))
  fi
done
[[ "$MATCH" -eq 1 ]] || die "Could not resolve exactly one accepted V30 source; matches=$MATCH"

EXPERT_DIR="$DATA/MQL5/Experts/mt5_quant"
mkdir -p "$EXPERT_DIR" "$DATA/config"
say "MT5 data folder: $(cygpath -w "$DATA")"

for rid in \
 "ml_dl_feature_lake_v1__XAUUSDm__PERIOD_M15__2025-02-01_00-00-00__756375" \
 "ml_dl_feature_lake_v1__XAUUSDm__PERIOD_M15__2025-08-01_00-00-00__22265" \
 "ml_dl_feature_lake_v1__XAUUSDm__PERIOD_M15__2026-02-01_00-00-00__519093"; do
  rd="$COMMON/mt5_quant/runs/$rid"
  [[ -s "$rd/bar_features.csv" && -s "$rd/trades.csv" && -s "$rd/manifest.txt" ]] || die "Accepted V30 run missing: $rd"
done

TAPE34="$INPUTS/v34_parallel_alpha_tape.csv"
META34="$OUT/v34_parallel_alpha_tape.json"
if [[ -s "$TAPE34" && "$(sha256sum "$TAPE34"|awk '{print $1}')" == "$V34_TAPE_SHA" ]]; then
  say "REUSE verified V34 causal specialist tape"
else
  say "Build V34 causal specialist tape"
  "$PY" "$F34" --common-files "$(cygpath -w "$COMMON")" --output "$(cygpath -w "$TAPE34")" --metadata "$(cygpath -w "$META34")"
fi
[[ "$(sha256sum "$TAPE34"|awk '{print $1}')" == "$V34_TAPE_SHA" ]] || die "V34 tape hash mismatch"
[[ "$(wc -l < "$TAPE34"|tr -d ' ')" == "23618" ]] || die "V34 tape row count mismatch"

BASE34A="$OUT/V34ParallelAlphaLab.base.a.mq5"
BASE34B="$OUT/V34ParallelAlphaLab.base.b.mq5"
"$PY" "$S34" --source "$(cygpath -w "$V30_SRC")" --output "$(cygpath -w "$BASE34A")"
"$PY" "$S34" --source "$(cygpath -w "$V30_SRC")" --output "$(cygpath -w "$BASE34B")"
SHA34A="$(sha256sum "$BASE34A"|awk '{print $1}')"
SHA34B="$(sha256sum "$BASE34B"|awk '{print $1}')"
[[ "$SHA34A" == "$SHA34B" ]] || die "V34 deterministic double-build mismatch $SHA34A != $SHA34B"
[[ "$SHA34A" == "$V34_ACCEPTED_SHA" ]] || die "V34 accepted source mismatch expected=$V34_ACCEPTED_SHA actual=$SHA34A"
say "Accepted V34 base reproduced sha=$SHA34A"

BASE38A="$OUT/V38FastHarvestLab.base.a.mq5"
BASE38B="$OUT/V38FastHarvestLab.base.b.mq5"
"$PY" "$S38" --source "$(cygpath -w "$BASE34A")" --output "$(cygpath -w "$BASE38A")"
"$PY" "$S38" --source "$(cygpath -w "$BASE34A")" --output "$(cygpath -w "$BASE38B")"
SHA38A="$(sha256sum "$BASE38A"|awk '{print $1}')"
SHA38B="$(sha256sum "$BASE38B"|awk '{print $1}')"
[[ "$SHA38A" == "$SHA38B" ]] || die "V38 deterministic double-build mismatch $SHA38A != $SHA38B"
say "V38 deterministic source PASS sha=$SHA38A"

"$PY" - "$BASE38A" <<'PYMQLLINT'
from pathlib import Path
import sys,re
p=Path(sys.argv[1])
text=p.read_text(encoding='utf-8-sig')
bad=[]
for ln,line in enumerate(text.splitlines(),1):
    ins=False
    for i,ch in enumerate(line):
        if ch!='"':
            continue
        bs=0;j=i-1
        while j>=0 and line[j]=='\\':
            bs+=1;j-=1
        if bs%2==0:
            ins=not ins
    if ins:
        bad.append(f'line {ln}: unterminated MQL string literal')
if re.search(r'OrderSend\(|OrderSendAsync\(|\bCTrade\b|trade\.Buy\(|trade\.Sell\(',text):
    bad.append('forbidden native order token')
required=[
    'MQLInfoInteger(MQL_TESTER)',
    '#define CANDIDATE_COUNT 23',
    'v38_adaptive_fast_tp0p50',
    'v38_adaptive_fast_tp0p75',
    'v38_adaptive_fast_tp1p00',
    'v38_adaptive_fast_gb0p25_after0p75',
    'v38_adaptive_velocity_decay_after0p50',
    'v38_adaptive_timebox30m',
    'V38FastExitTriggered',
    'intra_trade_m1_fast.csv',
]
for token in required:
    if token not in text:
        bad.append('missing token '+token)
if bad:
    print('GENERATED V38 MQL LINT FAILED')
    print('\n'.join(bad[:50]))
    raise SystemExit(78)
print('Generated V38 MQL lint PASS:',p)
PYMQLLINT

decode_compile(){
  local log="$1"
  local out="$2"
  if ! iconv -f UTF-16 -t UTF-8 "$log" > "$out" 2>/dev/null; then
    tr -d '\r' < "$log" > "$out"
  fi
}

compile_ea(){
  local src="$1"
  local log="${src%.mq5}.log"
  local ex5="${src%.mq5}.ex5"
  rm -f "$log" "$ex5"
  MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' "$METAEDITOR_EXE" "/compile:$(cygpath -w "$src")" /log || true
  [[ -s "$log" ]] || die "compile log missing $src"
  local u8="$OUT/.compile_v38.txt"
  decode_compile "$log" "$u8"
  local sum
  sum="$(tr -d '\r' < "$u8"|grep -Eio 'Result:[[:space:]]*[0-9]+[[:space:]]+errors?,[[:space:]]*[0-9]+[[:space:]]+warnings?'|tail -1||true)"
  if [[ ! "$sum" =~ Result:[[:space:]]*0[[:space:]]+errors?,[[:space:]]*0[[:space:]]+warnings? ]]; then
    cat "$u8"
    die "compile failed: $sum"
  fi
  echo "$sum"
  [[ -s "$ex5" ]] || die "EX5 missing"
  cp -f "$u8" "$OUT/V38FastHarvestLab.compile.txt"
}

read_kv(){
  local key="$1"
  local file="$2"
  awk -F= -v k="$key" '$1==k{sub(/^[^=]*=/,"");gsub(/\r/,"");print;exit}' "$file"
}

make_ini(){
  local expert="$1"
  local from="$2"
  local to="$3"
  local tag="$4"
  local ini="$DATA/config/${tag}.ini"
  local tmp="$OUT/.${tag}.ini"
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
FromDate=${from}
ToDate=${to}
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
  printf '\xFF\xFE' > "$ini"
  iconv -f UTF-8 -t UTF-16LE "$tmp" >> "$ini"
  rm -f "$tmp"
  printf '%s' "$ini"
}

collect_run(){
  local tag="$1"
  local dest="$2"
  local marker="$3"
  [[ -s "$dest/SOURCE_RUN_FOLDER.txt" ]] || die "SOURCE_RUN_FOLDER missing for $tag"
  local rd
  rd="$(cat "$dest/SOURCE_RUN_FOLDER.txt")"
  [[ -d "$rd" ]] || die "run folder missing $rd"
  mkdir -p "$dest"
  for f in monthly_summary.csv trades.csv manifest.txt; do
    [[ -s "$rd/$f" ]] || die "$f missing for $tag"
    cp -f "$rd/$f" "$dest/$f"
  done
  [[ -s "$rd/intra_trade_m15.csv" ]] && cp -f "$rd/intra_trade_m15.csv" "$dest/intra_trade_m15.csv" || true
  [[ -s "$rd/intra_trade_m1_fast.csv" ]] || die "V38 M1 fast telemetry missing"
  cp -f "$rd/intra_trade_m1_fast.csv" "$dest/intra_trade_m1_fast.csv"
  grep -Fq "$marker" "$dest/manifest.txt" || die "manifest marker missing $marker"
  echo done > "$dest/DONE.txt"
  say "COLLECT PASS $tag"
}

run_mt5_checkpoint(){
  local tag="$1"
  local expert="$2"
  local from="$3"
  local to="$4"
  local state="$5"
  local marker="$6"
  local dest="$CP/$tag"
  mkdir -p "$dest"

  if [[ -s "$dest/DONE.txt" ]]; then
    say "REUSE CHECKPOINT $tag — MT5 NOT RERUN"
    return
  fi
  if [[ -s "$dest/MT5_DONE.txt" ]]; then
    say "RECOVER collection-only $tag — MT5 NOT RERUN"
    collect_run "$tag" "$dest" "$marker"
    return
  fi

  local state_target="$INPUTS/v30_ml_dl_feature_lake_state.csv"
  local backup="$OUT/state_before_v38.csv"
  local had_state=0
  if [[ -s "$state_target" ]]; then
    cp -f "$state_target" "$backup"
    had_state=1
  fi
  cp -f "$state" "$state_target"

  local before=""
  [[ -s "$LATEST" ]] && before="$(read_kv run_id "$LATEST"||true)"
  local ini
  ini="$(make_ini "$expert" "$from" "$to" "$tag")"

  say "RUN $tag — exact MT5 Deposit=40, tester-only, aggregate research risk unchanged"
  set +e
  MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' "$TERMINAL_EXE" "/config:$(cygpath -w "$ini")"
  local rc=$?
  set -e

  if [[ -s "$state_target" ]]; then cp -f "$state_target" "$OUT/state_after_v38.csv"; fi
  if [[ "$had_state" -eq 1 ]]; then cp -f "$backup" "$state_target"; else rm -f "$state_target"; fi

  [[ "$rc" -eq 0 ]] || die "MT5 failed rc=$rc"
  [[ -s "$LATEST" ]] || die "LATEST missing after $tag"
  local after folder
  after="$(read_kv run_id "$LATEST"||true)"
  folder="$(read_kv run_folder "$LATEST"||true)"
  [[ -n "$after" && "$after" != "$before" ]] || die "LATEST did not refresh after $tag"
  [[ -n "$folder" ]] || die "run_folder missing from LATEST"
  folder="${folder//\\//}"
  local rd="$COMMON/$folder"
  [[ -d "$rd" ]] || die "new run folder missing $rd"
  printf '%s' "$rd" > "$dest/SOURCE_RUN_FOLDER.txt"
  printf '%s' "$after" > "$dest/MT5_DONE.txt"
  cp -f "$LATEST" "$dest/LATEST.txt"
  collect_run "$tag" "$dest" "$marker"
}

EA38="$EXPERT_DIR/V38FastHarvestLab.mq5"
cp -f "$BASE38A" "$EA38"
say "Compile V38 Fast Harvest Lab"
compile_ea "$EA38"

run_mt5_checkpoint "v38_fast_harvest" "V38FastHarvestLab" "2025.08.01" "2026.08.01" "$STATE1" "v38_fast_harvest_lab=1"

ANJSON="$OUT/v38_fast_harvest_analysis.json"
ANCSV="$OUT/v38_fast_harvest_comparison.csv"
"$PY" "$A38" --run-folder "$(cygpath -w "$CP/v38_fast_harvest")" --output "$(cygpath -w "$ANJSON")" --csv "$(cygpath -w "$ANCSV")"

EVID="$OUT/V38_EVIDENCE.txt"
{
  echo "schema=v38_fast_harvest_evidence_v1"
  echo "head=$(git -C "$REPO_ROOT" rev-parse HEAD)"
  echo "v30_sha=$V30_SHA"
  echo "v34_accepted_sha=$SHA34A"
  echo "v38_source_sha=$SHA38A"
  echo "v34_tape_sha=$V34_TAPE_SHA"
  echo "state1_sha=$STATE1_SHA"
  echo "period=2025-08-01_to_2026-08-01"
  echo "symbol=XAUUSDm"
  echo "period_tf=M15"
  echo "tester_model=0"
  echo "deposit=40"
  echo "leverage=1:200"
  echo "tester_only=1"
  echo "native_broker_orders=0"
  echo "external_broker_orders=0"
  echo "risk_ceiling_per_trade=1.00%"
  echo "control=adaptive_ewma_hl8_thr0"
  echo "fast_arms=tp0p50,tp0p75,tp1p00,giveback0p25_after0p75,velocity_decay_after0p50,timebox30m"
  echo "m1_telemetry=1"
} > "$EVID"

ZIP="$OUT/v38_fast_harvest_exact_mt5.zip"
"$PY" - "$OUT" "$ZIP" <<'PYZIP'
import os,sys,zipfile
root,out=sys.argv[1],sys.argv[2]
include=[
    'V38_EVIDENCE.txt',
    'v38_fast_harvest_runner.log',
    'V38FastHarvestLab.compile.txt',
    'V38FastHarvestLab.base.a.mq5',
    'v38_fast_harvest_analysis.json',
    'v38_fast_harvest_comparison.csv',
    'state_after_v38.csv',
]
cp=os.path.join(root,'checkpoints','v38_fast_harvest')
for name in ['DONE.txt','MT5_DONE.txt','LATEST.txt','SOURCE_RUN_FOLDER.txt','manifest.txt','monthly_summary.csv','trades.csv','intra_trade_m15.csv','intra_trade_m1_fast.csv']:
    p=os.path.join(cp,name)
    if os.path.isfile(p):
        include.append(os.path.relpath(p,root))
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for rel in include:
        p=os.path.join(root,rel)
        if os.path.isfile(p):
            z.write(p,rel)
PYZIP

ZIP_SHA="$(sha256sum "$ZIP"|awk '{print $1}')"
say "ALL DONE"
echo "UPLOAD THIS ONE ZIP:"
cygpath -w "$ZIP"
echo "SHA256=$ZIP_SHA"
