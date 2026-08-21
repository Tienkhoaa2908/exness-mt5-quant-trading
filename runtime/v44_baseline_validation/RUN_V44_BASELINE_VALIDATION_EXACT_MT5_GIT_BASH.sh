#!/usr/bin/env bash
set -Eeuo pipefail
export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
REPO_ROOT="$(cd -- "$ROOT/../.." && pwd -P)"
OUT="$ROOT/OUTPUT_V44"
CP="$OUT/checkpoints"
LOG="$OUT/v44_baseline_validation_runner.log"

TERMINAL_EXE="${MT5_TERMINAL_EXE:-/c/Program Files/MetaTrader 5/terminal64.exe}"
METAEDITOR_EXE="${MT5_METAEDITOR_EXE:-/c/Program Files/MetaTrader 5/metaeditor64.exe}"

EXPECTED_BRANCH="agent/v44-baseline-robustness-validation"
V30_SHA="4222120de5ded19ab7da172ad4c1e65d2a54b8bac7491fcd7927685b17b09a05"
V38_ZIP_SHA="224296ae1c02792493c690e3be563dd278b2eab5a13a6cfaefd6e5eae052cf5b"
V38_PARENT_SOURCE_SHA="4491d9d15233511d70735a5d8042eaaad1699df38fe2644d6419b08c7407ac12"
V44_SOURCE_SHA="cfde6716916cd6adcf89cec2c7c2795ff762ea845795a9108e0247ee84e311d3"
V34_TAPE_SHA="d70d92d0023c1862af6363d60a7d9e927f928e75ffcf1c0cedcb4f7798128863"
STATE1_SHA="5110519f2fe9722b4c13eb1e5ceec42f00bd04dd3b4f071af28349068b6097b0"

STATE1="$REPO_ROOT/runtime/v34_parallel_alpha/state_after_chunk1.csv"
F34="$REPO_ROOT/scripts/v34_parallel_alpha_features.py"
S44="$REPO_ROOT/scripts/build_v44_baseline_validation_source.py"
A44="$REPO_ROOT/scripts/analyze_v44_baseline_validation.py"
TEST="$REPO_ROOT/tests/test_v44_baseline_validation_static.py"
SECRET_SCAN="$REPO_ROOT/scripts/secret_scan.py"
PACKAGER="$REPO_ROOT/scripts/package_research_bundle_portable.py"
BOOT="$ROOT/BOOTSTRAP_V44_BASELINE_VALIDATION_ONE_SHOT_GIT_BASH.sh"
PACKAGE_ONLY="$ROOT/PACKAGE_V44_EXISTING_OUTPUT_GIT_BASH.sh"
V38_ZIP="$REPO_ROOT/runtime/v38_fast_harvest/OUTPUT_V38/v38_fast_harvest_exact_mt5.zip"

WINDOWS=(
"y01_2025_08_2026_08|annual|2025.08.01|2026.08.01|12"
"h01_2025_08_2026_02|halfyear|2025.08.01|2026.02.01|6"
"h02_2026_02_2026_08|halfyear|2026.02.01|2026.08.01|6"
"q01_2025_08_11|quarter|2025.08.01|2025.11.01|3"
"q02_2025_11_2026_02|quarter|2025.11.01|2026.02.01|3"
"q03_2026_02_05|quarter|2026.02.01|2026.05.01|3"
"q04_2026_05_08|quarter|2026.05.01|2026.08.01|3"
"m01_2025_08|month|2025.08.01|2025.09.01|1"
"m02_2025_09|month|2025.09.01|2025.10.01|1"
"m03_2025_10|month|2025.10.01|2025.11.01|1"
"m04_2025_11|month|2025.11.01|2025.12.01|1"
"m05_2025_12|month|2025.12.01|2026.01.01|1"
"m06_2026_01|month|2026.01.01|2026.02.01|1"
"m07_2026_02|month|2026.02.01|2026.03.01|1"
"m08_2026_03|month|2026.03.01|2026.04.01|1"
"m09_2026_04|month|2026.04.01|2026.05.01|1"
"m10_2026_05|month|2026.05.01|2026.06.01|1"
"m11_2026_06|month|2026.06.01|2026.07.01|1"
"m12_2026_07|month|2026.07.01|2026.08.01|1"
)

mkdir -p "$OUT" "$CP"
: > "$LOG"
exec > >(tee -a "$LOG") 2>&1

say(){ printf '\n[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"; }
die(){ echo "FATAL: $*" >&2; exit 1; }
trap 'rc=$?; echo "FAILED rc=$rc line=${BASH_LINENO[0]:-?} cmd=${BASH_COMMAND:-?}" >&2; exit $rc' ERR

say "V44 BASELINE ROBUSTNESS / DEPLOYMENT-READINESS — EXACT MT5"
echo "Strategy Tester only. REAL-MONEY LIVE TRADING remains FORBIDDEN."
echo "This campaign does not retune the three frozen routers on the 19 validation windows."
echo "A PASS can authorize PAPER/DEMO research only; LIVE_AUTHORIZED=0."

for c in cygpath sha256sum grep awk iconv tasklist.exe wc tr git sleep ls find; do
  command -v "$c" >/dev/null || die "Missing Git Bash command: $c"
done
[[ -f "$TERMINAL_EXE" && -f "$METAEDITOR_EXE" ]] || die "MT5/MetaEditor executable missing"
for f in "$STATE1" "$F34" "$S44" "$A44" "$TEST" "$SECRET_SCAN" "$PACKAGER" "$BOOT" "$PACKAGE_ONLY" "$V38_ZIP"; do
  [[ -s "$f" ]] || die "required file missing: $f"
done
[[ "$(sha256sum "$STATE1" | awk '{print $1}')" == "$STATE1_SHA" ]] || die "state1 hash mismatch"
[[ "$(sha256sum "$V38_ZIP" | awk '{print $1}')" == "$V38_ZIP_SHA" ]] || die "accepted V38 ZIP hash mismatch"

HEAD="$(git -C "$REPO_ROOT" rev-parse HEAD)"
BRANCH="$(git -C "$REPO_ROOT" branch --show-current)"
echo "HEAD=$HEAD"
echo "BRANCH=$BRANCH"
echo "PYTHONUTF8=$PYTHONUTF8 PYTHONIOENCODING=$PYTHONIOENCODING"
[[ "$BRANCH" == "$EXPECTED_BRANCH" ]] || die "wrong branch expected=$EXPECTED_BRANCH actual=$BRANCH"

if tasklist.exe //FI "IMAGENAME eq terminal64.exe" 2>/dev/null | tr -d '\r' | grep -qi terminal64.exe; then
  die "MetaTrader 5 is open. Close MT5 completely and rerun."
fi

V31_PY="$REPO_ROOT/runtime/v31_mt5_model_gate/OUTPUT_V31_1_MT5/.venv/Scripts/python.exe"
[[ -x "$V31_PY" ]] || die "Pinned V31/V32 Python environment missing: $V31_PY"
PY="$V31_PY"

"$PY" - <<'PYCHK'
import sys,numpy,pandas,sklearn
assert sys.version_info >= (3,10)
assert numpy.__version__=='2.3.5'
assert pandas.__version__=='2.2.3'
assert sklearn.__version__=='1.8.0'
print('Python',sys.version.split()[0])
print('numpy',numpy.__version__,'pandas',pandas.__version__,'sklearn',sklearn.__version__)
PYCHK

say "Static/packaging/recovery gates before MetaEditor or MT5"
"$PY" -m py_compile "$F34" "$S44" "$A44" "$TEST" "$SECRET_SCAN" "$PACKAGER"
if "$PY" - <<'PYCHECK' >/dev/null 2>&1
import pytest
PYCHECK
then
  "$PY" -m pytest -q "$TEST" "$REPO_ROOT/tests/test_package_research_bundle_portable.py"
else
  echo "pytest unavailable: running dependency-free V44 gate"
  "$PY" "$TEST"
  "$PY" "$REPO_ROOT/tests/test_package_research_bundle_portable.py"
fi
"$PY" "$SECRET_SCAN" "$REPO_ROOT"
bash -n "$0"
bash -n "$BOOT"
bash -n "$PACKAGE_ONLY"

APPDATA_U="$(cygpath -u "$APPDATA")"
TERM_ROOT="$APPDATA_U/MetaQuotes/Terminal"
COMMON="$TERM_ROOT/Common/Files"
INPUTS="$COMMON/mt5_quant/inputs"
LATEST="$COMMON/mt5_quant/ML_DL_FEATURE_LAKE_LATEST.txt"
mkdir -p "$INPUTS"

DATA=""
MATCH=0
for src in "$TERM_ROOT"/*/MQL5/Experts/mt5_quant/MlDlFeatureLakeV1.mq5; do
  [[ -f "$src" ]] || continue
  if [[ "$(sha256sum "$src" | awk '{print $1}')" == "$V30_SHA" ]]; then
    DATA="${src%/MQL5/Experts/mt5_quant/MlDlFeatureLakeV1.mq5}"
    MATCH=$((MATCH+1))
  fi
done
[[ "$MATCH" -eq 1 ]] || die "Could not resolve exactly one accepted MT5 data folder; matches=$MATCH"
EXPERT_DIR="$DATA/MQL5/Experts/mt5_quant"
mkdir -p "$EXPERT_DIR" "$DATA/config"
say "MT5 data folder: $(cygpath -w "$DATA")"

TAPE34="$INPUTS/v34_parallel_alpha_tape.csv"
if [[ -s "$TAPE34" && "$(sha256sum "$TAPE34" | awk '{print $1}')" == "$V34_TAPE_SHA" ]]; then
  say "REUSE verified V34 causal specialist tape"
else
  say "Build V34 causal specialist tape"
  "$PY" "$F34" --common-files "$(cygpath -w "$COMMON")" --output "$(cygpath -w "$TAPE34")" --metadata "$(cygpath -w "$OUT/v34_parallel_alpha_tape.json")"
fi
[[ "$(sha256sum "$TAPE34" | awk '{print $1}')" == "$V34_TAPE_SHA" ]] || die "V34 tape hash mismatch"
[[ "$(wc -l < "$TAPE34" | tr -d ' ')" == "23618" ]] || die "V34 tape row count mismatch"

PARENT38="$OUT/V38FastHarvestLab.accepted_parent.mq5"
"$PY" - "$V38_ZIP" "$PARENT38" "$V38_PARENT_SOURCE_SHA" <<'PYV38'
from pathlib import Path
import hashlib,sys,zipfile
zp=Path(sys.argv[1]); out=Path(sys.argv[2]); expected=sys.argv[3]
with zipfile.ZipFile(zp) as z:
    bad=z.testzip()
    if bad is not None: raise RuntimeError(f'accepted V38 ZIP CRC failure: {bad}')
    hits=[n for n in z.namelist() if Path(n).name=='V38FastHarvestLab.base.a.mq5']
    if len(hits)!=1: raise RuntimeError(f'expected one V38 parent source, found={hits}')
    data=z.read(hits[0])
actual=hashlib.sha256(data).hexdigest()
if actual!=expected: raise RuntimeError(f'V38 parent source SHA mismatch expected={expected} actual={actual}')
text=data.decode('utf-8-sig')
for token in ['#define MT5Q_RELEASE_ID "v38_fast_harvest_lab_v1"','#define CANDIDATE_COUNT 23','adaptive_ewma_hl8_thr0','adaptive_ewma_hl8_thr0p05','adaptive_ewma_hl10_thr0p05','MQLInfoInteger(MQL_TESTER)']:
    if token not in text: raise RuntimeError('accepted V38 parent token missing: '+token)
out.write_bytes(data)
print('Accepted V38 immutable parent PASS sha256='+actual)
PYV38

say "Deterministic source reconstruction: accepted V38 -> V44 telemetry-only validation source"
BASE44A="$OUT/V44BaselineValidationLab.base.a.mq5"
BASE44B="$OUT/V44BaselineValidationLab.base.b.mq5"
"$PY" "$S44" --source "$(cygpath -w "$PARENT38")" --output "$(cygpath -w "$BASE44A")"
"$PY" "$S44" --source "$(cygpath -w "$PARENT38")" --output "$(cygpath -w "$BASE44B")"
SHA44A="$(sha256sum "$BASE44A" | awk '{print $1}')"
SHA44B="$(sha256sum "$BASE44B" | awk '{print $1}')"
[[ "$SHA44A" == "$SHA44B" ]] || die "V44 deterministic double-build mismatch"
[[ "$SHA44A" == "$V44_SOURCE_SHA" ]] || die "V44 frozen source hash mismatch expected=$V44_SOURCE_SHA actual=$SHA44A"
echo "V44_SOURCE_SHA=$SHA44A"

"$PY" - "$BASE44A" <<'PYMQL'
from pathlib import Path
import sys
text=Path(sys.argv[1]).read_text(encoding='utf-8-sig')
for bad in ('OrderSend(','OrderSendAsync(','CTrade','trade.Buy(','trade.Sell('):
    if bad in text: raise RuntimeError('forbidden native order token: '+bad)
for tok in ('MQLInfoInteger(MQL_TESTER)','#define CANDIDATE_COUNT 23','v44_baseline_validation=1','v44_strategy_logic_changed=0','v44_risk_changed=0','v44_live_authorized=0','adaptive_ewma_hl8_thr0','adaptive_ewma_hl8_thr0p05','adaptive_ewma_hl10_thr0p05'):
    if tok not in text: raise RuntimeError('V44 MQL token missing: '+tok)
print('Generated V44 MQL lint PASS')
PYMQL

decode_compile(){
  local log="$1" out="$2"
  if ! iconv -f UTF-16 -t UTF-8 "$log" > "$out" 2>/dev/null; then
    tr -d '\r' < "$log" > "$out"
  fi
}
compile_summary(){
  local log="$1" u8="$2"
  decode_compile "$log" "$u8"
  tr -d '\r' < "$u8" | grep -Eio 'Result:[[:space:]]*[0-9]+[[:space:]]+errors?,[[:space:]]*[0-9]+[[:space:]]+warnings?' | tail -1 || true
}
compile_checkpoint_valid(){
  local src="$1" expected_sha="$2"
  local log="${src%.mq5}.log" ex5="${src%.mq5}.ex5" marker="${src%.mq5}.compile_source_sha256"
  local u8="$OUT/.compile_v44_reuse.txt" sum=""
  [[ -s "$src" && -s "$log" && -s "$ex5" ]] || return 1
  [[ "$(sha256sum "$src" | awk '{print $1}')" == "$expected_sha" ]] || return 1
  sum="$(compile_summary "$log" "$u8")"
  [[ "$sum" =~ Result:[[:space:]]*0[[:space:]]+errors?,[[:space:]]*0[[:space:]]+warnings? ]] || return 1
  if [[ -s "$marker" ]]; then
    [[ "$(tr -d '\r\n' < "$marker")" == "$expected_sha" ]] || return 1
  else
    "$PY" - "$src" "$log" "$ex5" <<'PYMTIME' || return 1
from pathlib import Path
import sys
src,log,ex5=map(Path,sys.argv[1:])
s=src.stat().st_mtime_ns
if log.stat().st_mtime_ns < s or ex5.stat().st_mtime_ns < s: raise SystemExit(1)
PYMTIME
  fi
  printf '%s\n' "$expected_sha" > "$marker"
  cp -f "$u8" "$OUT/V44BaselineValidationLab.compile.txt"
  echo "REUSE COMPILE CHECKPOINT source_sha=$expected_sha summary=$sum"
  return 0
}
compile_ea(){
  local src="$1" expected_sha="$2"
  local log="${src%.mq5}.log" ex5="${src%.mq5}.ex5" marker="${src%.mq5}.compile_source_sha256"
  local src_w include_w rc i u8 sum ready
  if compile_checkpoint_valid "$src" "$expected_sha"; then return 0; fi
  rm -f "$log" "$ex5" "$marker"
  if tasklist.exe //FI "IMAGENAME eq metaeditor64.exe" 2>/dev/null | tr -d '\r' | grep -qi metaeditor64.exe; then
    die "MetaEditor is open. Close MetaEditor and rerun."
  fi
  src_w="$(cygpath -w "$src")"; include_w="$(cygpath -w "$DATA/MQL5")"
  echo "METAEDITOR_COMPILE_SOURCE=$src_w"
  if MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' "$METAEDITOR_EXE" "/compile:$src_w" "/include:$include_w" /log; then rc=0; else rc=$?; fi
  echo "METAEDITOR_LAUNCH_RC=$rc"
  u8="$OUT/.compile_v44.txt"; ready=0; sum=""
  for ((i=0;i<1200;i++)); do
    if [[ -s "$log" ]]; then
      sum="$(compile_summary "$log" "$u8")"
      if [[ -n "$sum" ]]; then
        if [[ ! "$sum" =~ Result:[[:space:]]*0[[:space:]]+errors?,[[:space:]]*0[[:space:]]+warnings? ]]; then
          cat "$u8"; die "compile failed launcher_rc=$rc summary=$sum"
        fi
        if [[ -s "$ex5" ]]; then ready=1; break; fi
      fi
    fi
    sleep 0.25
  done
  [[ "$ready" -eq 1 ]] || { [[ -s "$u8" ]] && cat "$u8" || true; ls -la "$(dirname "$src")" | tail -60 || true; die "MetaEditor compile artifact postcondition failed rc=$rc"; }
  [[ "$(sha256sum "$src" | awk '{print $1}')" == "$expected_sha" ]] || die "compiled source hash changed unexpectedly"
  printf '%s\n' "$expected_sha" > "$marker"
  cp -f "$u8" "$OUT/V44BaselineValidationLab.compile.txt"
  echo "$sum"
}

EA44="$EXPERT_DIR/V44BaselineValidationLab.mq5"
if [[ -s "$EA44" && "$(sha256sum "$EA44" | awk '{print $1}')" == "$V44_SOURCE_SHA" ]]; then
  say "REUSE installed V44 source bytes"
else
  cp -f "$BASE44A" "$EA44"
fi
say "Compile/reuse V44 validation EA"
compile_ea "$EA44" "$V44_SOURCE_SHA"

read_kv(){
  local key="$1" file="$2"
  awk -F= -v k="$key" '$1==k{sub(/^[^=]*=/,"");gsub(/\r/,"");print;exit}' "$file"
}
make_ini(){
  local tag="$1" from="$2" to="$3"
  local ini="$DATA/config/v44_${tag}.ini" tmp="$OUT/.v44_${tag}.ini"
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
Expert=mt5_quant\\V44BaselineValidationLab.ex5
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
EOF_INI
  printf '\xFF\xFE' > "$ini"
  iconv -f UTF-8 -t UTF-16LE "$tmp" >> "$ini"
  rm -f "$tmp"
  printf '%s' "$ini"
}
collect_ready(){
  local rd="$1" i
  for ((i=0;i<1200;i++)); do
    if [[ -s "$rd/monthly_summary.csv" && -s "$rd/trades.csv" && -s "$rd/manifest.txt" ]] \
       && grep -Fq 'v44_baseline_validation=1' "$rd/manifest.txt" \
       && grep -Fq 'v44_strategy_logic_changed=0' "$rd/manifest.txt" \
       && grep -Fq 'v44_risk_changed=0' "$rd/manifest.txt" \
       && grep -Fq 'v44_live_authorized=0' "$rd/manifest.txt" \
       && grep -Fq 'tester_only=1' "$rd/manifest.txt" \
       && grep -Fq 'native_broker_orders=0' "$rd/manifest.txt" \
       && grep -Fq 'external_broker_orders=0' "$rd/manifest.txt"; then
      return 0
    fi
    sleep 0.25
  done
  return 1
}
collect_window(){
  local tag="$1" kind="$2" from="$3" to="$4" months="$5" dest="$CP/$tag"
  [[ -s "$dest/SOURCE_RUN_FOLDER.txt" ]] || die "$tag source run folder pointer missing"
  local rd
  rd="$(cat "$dest/SOURCE_RUN_FOLDER.txt")"
  [[ -d "$rd" ]] || die "$tag source run folder missing: $rd"
  collect_ready "$rd" || { ls -la "$rd" || true; die "$tag run folder never reached complete artifact state"; }
  cp -f "$rd/monthly_summary.csv" "$dest/monthly_summary.csv"
  cp -f "$rd/trades.csv" "$dest/trades.csv"
  cp -f "$rd/manifest.txt" "$dest/manifest.txt"
  printf 'tag=%s\nkind=%s\nfrom=%s\nto=%s\nmonths=%s\nrestart_state_sha=%s\n' "$tag" "$kind" "$from" "$to" "$months" "$STATE1_SHA" > "$dest/WINDOW.txt"
  echo done > "$dest/DONE.txt"
}
run_window(){
  local tag="$1" kind="$2" from="$3" to="$4" months="$5" dest="$CP/$tag"
  mkdir -p "$dest"
  if [[ -s "$dest/DONE.txt" && -s "$dest/monthly_summary.csv" && -s "$dest/trades.csv" && -s "$dest/manifest.txt" ]]; then
    say "REUSE COMPLETE $tag — MT5 NOT RERUN"
    return
  fi
  if [[ -s "$dest/MT5_DONE.txt" && -s "$dest/SOURCE_RUN_FOLDER.txt" ]]; then
    say "RECOVER COLLECTION-ONLY $tag — MT5 NOT RERUN"
    collect_window "$tag" "$kind" "$from" "$to" "$months"
    return
  fi

  local state_target="$INPUTS/v30_ml_dl_feature_lake_state.csv" backup="$OUT/state_before_${tag}.csv" had_state=0
  if [[ -s "$state_target" ]]; then cp -f "$state_target" "$backup"; had_state=1; fi
  cp -f "$STATE1" "$state_target"

  local before="" after="" folder="" ini rc i
  [[ -s "$LATEST" ]] && before="$(read_kv run_id "$LATEST" || true)"
  ini="$(make_ini "$tag" "$from" "$to")"
  say "RUN $tag kind=$kind exact MT5 $from -> $to Deposit=40 Model=0"
  if MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' "$TERMINAL_EXE" "/config:$(cygpath -w "$ini")"; then rc=0; else rc=$?; fi
  echo "MT5_LAUNCH_RC=$rc"

  if [[ "$had_state" -eq 1 ]]; then cp -f "$backup" "$state_target"; else rm -f "$state_target"; fi

  for ((i=0;i<3600;i++)); do
    if [[ -s "$LATEST" ]]; then
      after="$(read_kv run_id "$LATEST" || true)"
      folder="$(read_kv run_folder "$LATEST" || true)"
      [[ -n "$after" && "$after" != "$before" && -n "$folder" ]] && break
    fi
    sleep 0.5
  done
  [[ -n "$after" && "$after" != "$before" && -n "$folder" ]] || die "$tag LATEST did not refresh after MT5 rc=$rc"
  folder="${folder//\\//}"
  local rd="$COMMON/$folder"
  [[ -d "$rd" ]] || die "$tag new run folder missing: $rd"
  printf '%s' "$rd" > "$dest/SOURCE_RUN_FOLDER.txt"
  printf '%s' "$after" > "$dest/MT5_DONE.txt"
  cp -f "$LATEST" "$dest/LATEST.txt"
  collect_window "$tag" "$kind" "$from" "$to" "$months"
}

say "ANNUAL HARD REPRODUCTION GATE FIRST"
IFS='|' read -r tag kind from to months <<< "${WINDOWS[0]}"
run_window "$tag" "$kind" "$from" "$to" "$months"
PREJSON="$OUT/v44_annual_preflight.json"
PRECSV="$OUT/v44_annual_preflight.csv"
"$PY" "$A44" --checkpoint-root "$(cygpath -w "$CP")" --output "$(cygpath -w "$PREJSON")" --csv "$(cygpath -w "$PRECSV")" --verify-annual-only
say "Annual accepted-control reproduction PASS; running remaining 18 restart windows"

for ((wi=1; wi<${#WINDOWS[@]}; wi++)); do
  IFS='|' read -r tag kind from to months <<< "${WINDOWS[$wi]}"
  run_window "$tag" "$kind" "$from" "$to" "$months"
done

ANJSON="$OUT/v44_baseline_validation_analysis.json"
ANCSV="$OUT/v44_window_metrics.csv"
"$PY" "$A44" --checkpoint-root "$(cygpath -w "$CP")" --output "$(cygpath -w "$ANJSON")" --csv "$(cygpath -w "$ANCSV")"

EVID="$OUT/V44_EVIDENCE.txt"
{
  echo "schema=v44_baseline_robustness_validation_exact_mt5_v1"
  echo "head=$HEAD"
  echo "branch=$BRANCH"
  echo "v38_parent_zip_sha=$V38_ZIP_SHA"
  echo "v38_parent_source_sha=$V38_PARENT_SOURCE_SHA"
  echo "v44_source_sha=$V44_SOURCE_SHA"
  echo "v34_tape_sha=$V34_TAPE_SHA"
  echo "state1_sha=$STATE1_SHA"
  echo "window_count=19"
  echo "monthly_windows=12"
  echo "quarter_windows=4"
  echo "halfyear_windows=2"
  echo "annual_windows=1"
  echo "window_state_semantics=accepted_2025_08_state_restart_each_window"
  echo "candidate_focus=adaptive_ewma_hl8_thr0,adaptive_ewma_hl8_thr0p05,adaptive_ewma_hl10_thr0p05"
  echo "strategy_logic_changed=0"
  echo "risk_changed=0"
  echo "risk_ceiling_per_trade=1.00%"
  echo "tester_only=1"
  echo "native_broker_orders=0"
  echo "external_broker_orders=0"
  echo "live_trading=FORBIDDEN"
  echo "live_authorized=0"
  echo "paper_demo_only_if_gate_passes=1"
  echo "same_window_retuning=FORBIDDEN"
} > "$EVID"

BUNDLE="$OUT/bundle"
rm -rf "$BUNDLE"
mkdir -p "$BUNDLE"
for f in "$EVID" "$LOG" "$OUT/V44BaselineValidationLab.compile.txt" "$PARENT38" "$BASE44A" "$ANJSON" "$ANCSV" "$PREJSON" "$PRECSV" "$S44" "$A44" "$TEST" "$0" "$BOOT" "$PACKAGE_ONLY" "$PACKAGER"; do
  [[ -s "$f" ]] && cp -f "$f" "$BUNDLE/$(basename "$f")"
done
for spec in "${WINDOWS[@]}"; do
  IFS='|' read -r tag kind from to months <<< "$spec"
  d="$CP/$tag"
  for f in WINDOW.txt LATEST.txt SOURCE_RUN_FOLDER.txt manifest.txt monthly_summary.csv trades.csv; do
    [[ -s "$d/$f" ]] && cp -f "$d/$f" "$BUNDLE/${tag}__${f}" || true
  done
done

ZIP="$OUT/v44_baseline_robustness_validation.zip"
"$PY" "$PACKAGER" --bundle "$(cygpath -w "$BUNDLE")" --output "$(cygpath -w "$ZIP")"
ZIP_SHA="$(sha256sum "$ZIP" | awk '{print $1}')"

say "V44 BASELINE ROBUSTNESS VALIDATION DONE"
"$PY" - "$ANJSON" <<'PYPRINT'
import json,sys
d=json.load(open(sys.argv[1],encoding='utf-8'))
print("STATUS="+d["status"])
print("DEPLOYMENT_RESEARCH_WINNER="+d["deployment_research_winner"])
print("PAPER_DEMO_READY="+(",".join(d["paper_demo_ready_candidates"]) or "NONE"))
print("LIVE_AUTHORIZED=0")
for s in d["candidates"]:
    a=s["annual"]
    print(f"{s['candidate']}: annual_end=${a['ending_usd']:.6f} geo={a['geo_month_pct']:.4f}% dd={a['max_mtm_dd_pct']:.4f}% PF={a['profit_factor']:.3f} monthly_restart_positive={s['monthly_restart_positive']}/12 quarter_positive={s['quarter_restart_positive']}/4 halfyear_positive={s['halfyear_restart_positive']}/2")
PYPRINT

echo "UPLOAD THIS ONE ZIP:"
cygpath -w "$ZIP"
echo "SHA256=$ZIP_SHA"
