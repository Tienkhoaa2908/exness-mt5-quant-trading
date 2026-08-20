#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
REPO_ROOT="$(cd -- "$ROOT/../.." && pwd -P)"
OUT="$ROOT/OUTPUT_V34_V35"
CP="$OUT/checkpoints"
LOG="$OUT/v34_v35_runner.log"
TERMINAL_EXE="${MT5_TERMINAL_EXE:-/c/Program Files/MetaTrader 5/terminal64.exe}"
METAEDITOR_EXE="${MT5_METAEDITOR_EXE:-/c/Program Files/MetaTrader 5/metaeditor64.exe}"
V30_SHA="4222120de5ded19ab7da172ad4c1e65d2a54b8bac7491fcd7927685b17b09a05"
V34_SHA="8d3700911e2fe680a2a4b02994680e812825ab6cf517bf509aaa4ac230526a77"
V35_SHA="663d97b9345341aa98827e5da31ad441792f944d7c597b7a91bd94c6485e6709"
V34_TAPE_SHA="d70d92d0023c1862af6363d60a7d9e927f928e75ffcf1c0cedcb4f7798128863"
STATE1_SHA="5110519f2fe9722b4c13eb1e5ceec42f00bd04dd3b4f071af28349068b6097b0"
STATE2_SHA="39df0a74f8536235176362bccffc458e4b623190427536e8462bdae0f6000b76"
STATE1="$ROOT/state_after_chunk1.csv"; STATE2="$ROOT/state_after_chunk2.csv"
F34="$REPO_ROOT/scripts/v34_parallel_alpha_features.py"
S34="$REPO_ROOT/scripts/build_v34_parallel_alpha_source.py"
A34="$REPO_ROOT/scripts/analyze_v34_parallel_alpha_mt5.py"
T35="$REPO_ROOT/scripts/v35_train_specialist_router.py"
S35="$REPO_ROOT/scripts/build_v35_meta_router_source.py"
A35="$REPO_ROOT/scripts/analyze_v35_meta_router_mt5.py"
mkdir -p "$OUT" "$CP"
exec > >(tee -a "$LOG") 2>&1
say(){ printf '\n[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"; }
die(){ echo "FATAL: $*" >&2; exit 1; }
trap 'rc=$?; echo "FAILED rc=$rc line=${BASH_LINENO[0]:-?} cmd=${BASH_COMMAND:-?}" >&2; exit $rc' ERR
for c in cygpath sha256sum sed grep awk iconv tasklist.exe wc; do command -v "$c" >/dev/null || die "Missing Git Bash command: $c"; done
[[ -f "$TERMINAL_EXE" && -f "$METAEDITOR_EXE" ]] || die "MT5/MetaEditor executable missing"
for f in "$F34" "$S34" "$A34" "$T35" "$S35" "$A35" "$STATE1" "$STATE2"; do [[ -s "$f" ]] || die "required file missing: $f"; done
[[ "$(sha256sum "$STATE1"|awk '{print $1}')" == "$STATE1_SHA" ]] || die "state1 hash mismatch"
[[ "$(sha256sum "$STATE2"|awk '{print $1}')" == "$STATE2_SHA" ]] || die "state2 hash mismatch"
if tasklist.exe //FI "IMAGENAME eq terminal64.exe" 2>/dev/null | tr -d '\r' | grep -qi terminal64.exe; then die "MetaTrader 5 is open. Close MT5 completely and rerun."; fi

V31_PY="$REPO_ROOT/runtime/v31_mt5_model_gate/OUTPUT_V31_1_MT5/.venv/Scripts/python.exe"
VENV="$OUT/.venv"; VENV_PY="$VENV/Scripts/python.exe"; PY=""
if [[ -x "$V31_PY" ]] && "$V31_PY" - <<'PYCHK' >/dev/null 2>&1
import numpy,pandas,sklearn
assert numpy.__version__=='2.3.5'; assert pandas.__version__=='2.2.3'; assert sklearn.__version__=='1.8.0'
PYCHK
then PY="$V31_PY"; say "Reuse pinned V31/V32 Python environment"
else
  if command -v python >/dev/null 2>&1; then SYS_PY="$(command -v python)"; elif command -v python3 >/dev/null 2>&1; then SYS_PY="$(command -v python3)"; else die "Python 3 required"; fi
  [[ -x "$VENV_PY" ]] || "$SYS_PY" -m venv "$VENV"
  if ! "$VENV_PY" - <<'PYCHK' >/dev/null 2>&1
import numpy,pandas,sklearn
assert numpy.__version__=='2.3.5'; assert pandas.__version__=='2.2.3'; assert sklearn.__version__=='1.8.0'
PYCHK
  then "$VENV_PY" -m pip install --disable-pip-version-check --upgrade pip; "$VENV_PY" -m pip install --disable-pip-version-check "numpy==2.3.5" "pandas==2.2.3" "scikit-learn==1.8.0"; fi
  PY="$VENV_PY"
fi
"$PY" -m py_compile "$F34" "$S34" "$A34" "$T35" "$S35" "$A35"
say "Python environment PASS"

APPDATA_U="$(cygpath -u "$APPDATA")"; TERM_ROOT="$APPDATA_U/MetaQuotes/Terminal"; COMMON="$TERM_ROOT/Common/Files"; INPUTS="$COMMON/mt5_quant/inputs"; mkdir -p "$INPUTS"
LATEST="$COMMON/mt5_quant/ML_DL_FEATURE_LAKE_LATEST.txt"
DATA=""; V30_SRC=""; MATCH=0
for src in "$TERM_ROOT"/*/MQL5/Experts/mt5_quant/MlDlFeatureLakeV1.mq5; do [[ -f "$src" ]] || continue; h="$(sha256sum "$src"|awk '{print $1}')"; if [[ "$h" == "$V30_SHA" ]]; then DATA="${src%/MQL5/Experts/mt5_quant/MlDlFeatureLakeV1.mq5}"; V30_SRC="$src"; MATCH=$((MATCH+1)); fi; done
[[ "$MATCH" -eq 1 ]] || die "Could not resolve exactly one accepted V30 source; matches=$MATCH"
EXPERT_DIR="$DATA/MQL5/Experts/mt5_quant"; mkdir -p "$EXPERT_DIR" "$DATA/config"
say "MT5 data folder: $(cygpath -w "$DATA")"

for rid in \
 "ml_dl_feature_lake_v1__XAUUSDm__PERIOD_M15__2025-02-01_00-00-00__756375" \
 "ml_dl_feature_lake_v1__XAUUSDm__PERIOD_M15__2025-08-01_00-00-00__22265" \
 "ml_dl_feature_lake_v1__XAUUSDm__PERIOD_M15__2026-02-01_00-00-00__519093"; do
  rd="$COMMON/mt5_quant/runs/$rid"; [[ -s "$rd/bar_features.csv" && -s "$rd/trades.csv" && -s "$rd/manifest.txt" ]] || die "Accepted V30 run missing: $rd"
done

TAPE34="$INPUTS/v34_parallel_alpha_tape.csv"; META34="$OUT/v34_parallel_alpha_tape.json"
if [[ -s "$TAPE34" && "$(sha256sum "$TAPE34"|awk '{print $1}')" == "$V34_TAPE_SHA" ]]; then say "REUSE verified V34 causal alpha tape"
else say "Build V34 causal SMC/PA/Wyckoff/microstructure specialist tape"; "$PY" "$F34" --common-files "$(cygpath -w "$COMMON")" --output "$(cygpath -w "$TAPE34")" --metadata "$(cygpath -w "$META34")"; fi
[[ "$(sha256sum "$TAPE34"|awk '{print $1}')" == "$V34_TAPE_SHA" ]] || die "V34 tape hash mismatch"
[[ "$(wc -l < "$TAPE34"|tr -d ' ')" == "23618" ]] || die "V34 tape row count mismatch"

BASE34="$OUT/V34ParallelAlphaLab.base.mq5"; "$PY" "$S34" --source "$(cygpath -w "$V30_SRC")" --output "$(cygpath -w "$BASE34")"
[[ "$(sha256sum "$BASE34"|awk '{print $1}')" == "$V34_SHA" ]] || die "V34 source hash mismatch"
! grep -Eq 'OrderSend\(|OrderSendAsync\(|\bCTrade\b|trade\.Buy\(|trade\.Sell\(' "$BASE34" || die "forbidden order token in V34"

decode_compile(){ local log="$1" out="$2"; if ! iconv -f UTF-16 -t UTF-8 "$log" > "$out" 2>/dev/null; then tr -d '\r' < "$log" > "$out"; fi; }
compile_ea(){ local src="$1"; local log="${src%.mq5}.log"; local ex5="${src%.mq5}.ex5"; rm -f "$log" "$ex5"; MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' "$METAEDITOR_EXE" "/compile:$(cygpath -w "$src")" /log || true; [[ -s "$log" ]] || die "compile log missing $src"; local u8="$OUT/.compile.txt"; decode_compile "$log" "$u8"; local sum; sum="$(tr -d '\r' < "$u8"|grep -Eio 'Result:[[:space:]]*[0-9]+[[:space:]]+errors?,[[:space:]]*[0-9]+[[:space:]]+warnings?'|tail -1||true)"; echo "$sum"; [[ "$sum" =~ Result:[[:space:]]*0[[:space:]]+errors?,[[:space:]]*0[[:space:]]+warnings? ]] || die "compile failed: $sum"; [[ -s "$ex5" ]] || die "EX5 missing"; }
read_kv(){ awk -F= -v k="$1" '$1==k{sub(/^[^=]*=/,"");gsub(/\r/,"");print;exit}' "$2"; }
make_ini(){ local expert="$1" from="$2" to="$3" tag="$4"; local ini="$DATA/config/${tag}.ini" tmp="$OUT/.ini"; cat > "$tmp" <<EOF
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
 printf '\xFF\xFE' > "$ini"; iconv -f UTF-8 -t UTF-16LE "$tmp" >> "$ini"; rm -f "$tmp"; printf '%s' "$ini"; }
collect_run(){ local tag="$1" dest="$2" marker="$3"; [[ -s "$LATEST" ]] || die "LATEST missing after $tag"; local rid folder; rid="$(read_kv run_id "$LATEST")"; folder="$(read_kv run_folder "$LATEST")"; [[ -n "$rid" && -n "$folder" ]] || die "invalid LATEST"; folder="${folder//\\//}"; local rd="$COMMON/$folder"; [[ -d "$rd" ]] || die "run folder missing $rd"; mkdir -p "$dest"; for f in monthly_summary.csv trades.csv manifest.txt; do [[ -s "$rd/$f" ]] || die "$f missing for $tag"; cp -f "$rd/$f" "$dest/$f"; done; [[ -s "$rd/intra_trade_m15.csv" ]] && cp -f "$rd/intra_trade_m15.csv" "$dest/intra_trade_m15.csv" || true; grep -Fq "$marker" "$dest/manifest.txt" || die "manifest marker missing $marker"; cp -f "$LATEST" "$dest/LATEST.txt"; printf '%s' "$rd" > "$dest/SOURCE_RUN_FOLDER.txt"; echo done > "$dest/DONE.txt"; say "COLLECT PASS $tag run_id=$rid"; }
run_mt5_checkpoint(){ local tag="$1" expert="$2" from="$3" to="$4" state="$5" marker="$6" dest="$CP/$tag"; if [[ -s "$dest/DONE.txt" ]]; then say "REUSE CHECKPOINT $tag — MT5 NOT RERUN"; return; fi; if [[ -s "$dest/MT5_DONE.txt" ]]; then say "RECOVER collection-only $tag — MT5 NOT RERUN"; collect_run "$tag" "$dest" "$marker"; return; fi; cp -f "$state" "$INPUTS/v30_ml_dl_feature_lake_state.csv"; local before=""; [[ -s "$LATEST" ]] && before="$(read_kv run_id "$LATEST"||true)"; local ini; ini="$(make_ini "$expert" "$from" "$to" "$tag")"; say "RUN $tag — exact MT5 Deposit=40"; MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' "$TERMINAL_EXE" "/config:$(cygpath -w "$ini")"; local rc=$?; [[ "$rc" -eq 0 ]] || die "MT5 failed rc=$rc"; local after; after="$(read_kv run_id "$LATEST"||true)"; [[ -n "$after" && "$after" != "$before" ]] || die "LATEST did not refresh after $tag"; mkdir -p "$dest"; echo "$after" > "$dest/MT5_DONE.txt"; collect_run "$tag" "$dest" "$marker"; }

EA34="$EXPERT_DIR/V34ParallelAlphaLab.mq5"; cp -f "$BASE34" "$EA34"; say "Compile V34 Parallel Alpha Lab"; compile_ea "$EA34"
run_mt5_checkpoint "v34_parallel_alpha" "V34ParallelAlphaLab" "2025.08.01" "2026.08.01" "$STATE1" "v34_parallel_alpha_lab=1"
"$PY" "$A34" --run-folder "$(cygpath -w "$CP/v34_parallel_alpha")" --output "$(cygpath -w "$OUT/v34_analysis.json")"

V34_COMMON_RUN="$(cat "$CP/v34_parallel_alpha/SOURCE_RUN_FOLDER.txt")"
TAPE35="$INPUTS/v35_specialist_router_tape.csv"; META35="$OUT/v35_router_metadata.json"
say "Train walk-forward AI specialist meta-router from V34 exact outcomes"
"$PY" "$T35" --common-files "$(cygpath -w "$COMMON")" --v34-run-folder "$(cygpath -w "$V34_COMMON_RUN")" --alpha-tape "$(cygpath -w "$TAPE34")" --output "$(cygpath -w "$TAPE35")" --metadata "$(cygpath -w "$META35")"
[[ -s "$TAPE35" && -s "$META35" ]] || die "V35 router tape missing"
BASE35="$OUT/V35AiSpecialistMetaRouter.base.mq5"; "$PY" "$S35" --source "$(cygpath -w "$BASE34")" --output "$(cygpath -w "$BASE35")"; [[ "$(sha256sum "$BASE35"|awk '{print $1}')" == "$V35_SHA" ]] || die "V35 source hash mismatch"
EA35="$EXPERT_DIR/V35AiSpecialistMetaRouter.mq5"; cp -f "$BASE35" "$EA35"; say "Compile V35 AI Specialist Meta Router"; compile_ea "$EA35"
run_mt5_checkpoint "v35_ai_meta_router" "V35AiSpecialistMetaRouter" "2026.02.01" "2026.08.01" "$STATE2" "v35_ai_all_expert_meta_router=1"
"$PY" "$A35" --run-folder "$(cygpath -w "$CP/v35_ai_meta_router")" --output "$(cygpath -w "$OUT/v35_analysis.json")"

ZIP="$OUT/v34_v35_parallel_alpha_exact_mt5.zip"
"$PY" - "$OUT" "$ZIP" <<'PYZIP'
import os,sys,zipfile
root,out=sys.argv[1],sys.argv[2]
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for dp,_,fs in os.walk(root):
  for f in fs:
   p=os.path.join(dp,f)
   if os.path.abspath(p)==os.path.abspath(out) or '/.venv/' in p.replace('\\','/'): continue
   z.write(p,os.path.relpath(p,root))
PYZIP
SHA="$(sha256sum "$ZIP"|awk '{print $1}')"
say "ALL DONE"
printf '\nUPLOAD THIS ONE ZIP:\n%s\nSHA256=%s\n' "$(cygpath -w "$ZIP")" "$SHA"
