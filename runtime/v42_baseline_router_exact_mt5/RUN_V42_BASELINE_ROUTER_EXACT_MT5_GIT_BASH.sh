#!/usr/bin/env bash
set -Eeuo pipefail
export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
REPO_ROOT="$(cd -- "$ROOT/../.." && pwd -P)"
OUT="$ROOT/OUTPUT_V42"
CP="$OUT/checkpoints"
LOG="$OUT/v42_baseline_router_runner.log"

TERMINAL_EXE="${MT5_TERMINAL_EXE:-/c/Program Files/MetaTrader 5/terminal64.exe}"
METAEDITOR_EXE="${MT5_METAEDITOR_EXE:-/c/Program Files/MetaTrader 5/metaeditor64.exe}"

V30_SHA="4222120de5ded19ab7da172ad4c1e65d2a54b8bac7491fcd7927685b17b09a05"
V38_ZIP_SHA="224296ae1c02792493c690e3be563dd278b2eab5a13a6cfaefd6e5eae052cf5b"
V34_TAPE_SHA="d70d92d0023c1862af6363d60a7d9e927f928e75ffcf1c0cedcb4f7798128863"
STATE1_SHA="5110519f2fe9722b4c13eb1e5ceec42f00bd04dd3b4f071af28349068b6097b0"
EXPECTED_CONTROL_FINAL=107.432645
EXPECTED_CONTROL_TRADES=563
EXPECTED_BRANCH="agent/v42-baseline-router-exact-mt5"

STATE1="$REPO_ROOT/runtime/v34_parallel_alpha/state_after_chunk1.csv"
F34="$REPO_ROOT/scripts/v34_parallel_alpha_features.py"
S42="$REPO_ROOT/scripts/build_v42_baseline_router_source.py"
A42="$REPO_ROOT/scripts/analyze_v42_baseline_router_mt5.py"
TEST="$REPO_ROOT/tests/test_v42_baseline_router_static.py"
SECRET_SCAN="$REPO_ROOT/scripts/secret_scan.py"
BOOT="$ROOT/BOOTSTRAP_V42_BASELINE_ROUTER_ONE_SHOT_GIT_BASH.sh"
V38_ZIP="$REPO_ROOT/runtime/v38_fast_harvest/OUTPUT_V38/v38_fast_harvest_exact_mt5.zip"

mkdir -p "$OUT" "$CP"
: > "$LOG"
exec > >(tee -a "$LOG") 2>&1

say(){ printf '\n[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"; }
die(){ echo "FATAL: $*" >&2; exit 1; }
trap 'rc=$?; echo "FAILED rc=$rc line=${BASH_LINENO[0]:-?} cmd=${BASH_COMMAND:-?}" >&2; exit $rc' ERR

say "V42 BASELINE ROUTER UPGRADE — EXACT MT5"
echo "Strategy Tester only. REAL-MONEY LIVE TRADING remains FORBIDDEN."
echo "This run launches MetaEditor and MT5 Strategy Tester; it cannot authorize live trading."

for c in cygpath sha256sum grep awk iconv tasklist.exe wc tr git sleep ls; do
  command -v "$c" >/dev/null || die "Missing Git Bash command: $c"
done
[[ -f "$TERMINAL_EXE" && -f "$METAEDITOR_EXE" ]] || die "MT5/MetaEditor executable missing"
for f in "$STATE1" "$F34" "$S42" "$A42" "$TEST" "$SECRET_SCAN" "$BOOT"; do
  [[ -s "$f" ]] || die "required file missing: $f"
done
[[ "$(sha256sum "$STATE1" | awk '{print $1}')" == "$STATE1_SHA" ]] || die "state1 hash mismatch"

HEAD="$(git -C "$REPO_ROOT" rev-parse HEAD)"
BRANCH="$(git -C "$REPO_ROOT" branch --show-current)"
echo "HEAD=$HEAD"
echo "BRANCH=$BRANCH"
echo "PYTHONUTF8=$PYTHONUTF8 PYTHONIOENCODING=$PYTHONIOENCODING"
[[ "$BRANCH" == "$EXPECTED_BRANCH" ]] || die "wrong branch: expected=$EXPECTED_BRANCH actual=$BRANCH"

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

say "Compile + V42 static tests + tracked-source secret scan"
"$PY" -m py_compile "$F34" "$S42" "$A42" "$TEST" "$SECRET_SCAN"
if "$PY" - <<'PYCHECK' >/dev/null 2>&1
import pytest
PYCHECK
then
  "$PY" -m pytest -q "$TEST"
else
  echo "pytest unavailable: running dependency-free V42 gate"
  "$PY" "$TEST"
fi
"$PY" "$SECRET_SCAN" "$REPO_ROOT"
bash -n "$0"
bash -n "$BOOT"

APPDATA_U="$(cygpath -u "$APPDATA")"
TERM_ROOT="$APPDATA_U/MetaQuotes/Terminal"
COMMON="$TERM_ROOT/Common/Files"
INPUTS="$COMMON/mt5_quant/inputs"
LATEST="$COMMON/mt5_quant/ML_DL_FEATURE_LAKE_LATEST.txt"
mkdir -p "$INPUTS"

DATA=""
V30_SRC=""
MATCH=0
for src in "$TERM_ROOT"/*/MQL5/Experts/mt5_quant/MlDlFeatureLakeV1.mq5; do
  [[ -f "$src" ]] || continue
  h="$(sha256sum "$src" | awk '{print $1}')"
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
if [[ -s "$TAPE34" && "$(sha256sum "$TAPE34" | awk '{print $1}')" == "$V34_TAPE_SHA" ]]; then
  say "REUSE verified V34 causal specialist tape"
else
  say "Build V34 causal specialist tape"
  "$PY" "$F34" --common-files "$(cygpath -w "$COMMON")" --output "$(cygpath -w "$TAPE34")" --metadata "$(cygpath -w "$META34")"
fi
[[ "$(sha256sum "$TAPE34" | awk '{print $1}')" == "$V34_TAPE_SHA" ]] || die "V34 tape hash mismatch"
[[ "$(wc -l < "$TAPE34" | tr -d ' ')" == "23618" ]] || die "V34 tape row count mismatch"

[[ -s "$V38_ZIP" ]] || die "Accepted V38 ZIP missing: $V38_ZIP"
ACTUAL_V38_ZIP_SHA="$(sha256sum "$V38_ZIP" | awk '{print $1}')"
[[ "$ACTUAL_V38_ZIP_SHA" == "$V38_ZIP_SHA" ]] || die "Accepted V38 ZIP SHA mismatch expected=$V38_ZIP_SHA actual=$ACTUAL_V38_ZIP_SHA"
say "Anchor immutable parent to accepted V38 exact-MT5 ZIP"
BASE38A="$OUT/V38FastHarvestLab.accepted_parent.mq5"
"$PY" - "$V38_ZIP" "$BASE38A" <<'PYV38'
from pathlib import Path
import hashlib,sys,zipfile
zp=Path(sys.argv[1]); out=Path(sys.argv[2])
with zipfile.ZipFile(zp) as z:
    bad=z.testzip()
    if bad is not None:
        raise RuntimeError(f'accepted V38 ZIP CRC failure: {bad}')
    hits=[n for n in z.namelist() if Path(n).name=='V38FastHarvestLab.base.a.mq5']
    if len(hits)!=1:
        raise RuntimeError(f'expected exactly one V38 parent source in accepted ZIP, found={hits}')
    data=z.read(hits[0])
text=data.decode('utf-8-sig')
for token in ['#define MT5Q_RELEASE_ID "v38_fast_harvest_lab_v1"','#define CANDIDATE_COUNT 23','adaptive_ewma_hl8_thr0','MQLInfoInteger(MQL_TESTER)']:
    if token not in text:
        raise RuntimeError('accepted V38 parent token missing: '+token)
out.write_bytes(data)
print('Accepted V38 parent source PASS sha256='+hashlib.sha256(data).hexdigest()+' member='+hits[0])
PYV38
SHA38A="$(sha256sum "$BASE38A" | awk '{print $1}')"

say "Deterministic source reconstruction: accepted V38 -> V42"
BASE42A="$OUT/V42BaselineRouterLab.base.a.mq5"
BASE42B="$OUT/V42BaselineRouterLab.base.b.mq5"
"$PY" "$S42" --source "$(cygpath -w "$BASE38A")" --output "$(cygpath -w "$BASE42A")"
"$PY" "$S42" --source "$(cygpath -w "$BASE38A")" --output "$(cygpath -w "$BASE42B")"
SHA42A="$(sha256sum "$BASE42A" | awk '{print $1}')"
SHA42B="$(sha256sum "$BASE42B" | awk '{print $1}')"
[[ "$SHA42A" == "$SHA42B" ]] || die "V42 deterministic double-build mismatch"
echo "V38_PARENT_ZIP_SHA=$ACTUAL_V38_ZIP_SHA"
echo "V38_PARENT_SOURCE_SHA=$SHA38A"
echo "V42_SHA=$SHA42A"

"$PY" - "$BASE42A" <<'PYMQLLINT'
from pathlib import Path
import re,sys
p=Path(sys.argv[1])
text=p.read_text(encoding='utf-8-sig')
bad=[]
if re.search(r'OrderSend\(|OrderSendAsync\(|\bCTrade\b|trade\.Buy\(|trade\.Sell\(',text):
    bad.append('forbidden native order token')
for token in [
    'MQLInfoInteger(MQL_TESTER)',
    '#define CANDIDATE_COUNT 29',
    'v42_baseline_router_upgrade=1',
    'v42_risk_changed=0',
    'v42_entry_exit_geometry_changed=0',
    'V42DirectionSwitchAllows',
    'v42_hl8_switch15m',
    'v42_hl8_switch30m',
    'v42_hl8_thr0p05_switch15m',
    'v42_hl10_thr0p05_switch15m',
    'v42_hl12_thr0p05_switch15m',
    'v42_cp_fast5_slow20_switch15m',
]:
    if token not in text:
        bad.append('missing token '+token)
if bad:
    print('\n'.join(bad))
    raise SystemExit(78)
print('Generated V42 MQL lint PASS:',p)
PYMQLLINT

decode_compile(){
  local log="$1"
  local out="$2"
  if ! iconv -f UTF-16 -t UTF-8 "$log" > "$out" 2>/dev/null; then
    tr -d '\r' < "$log" > "$out"
  fi
}

compile_summary(){
  local log="$1"
  local u8="$2"
  decode_compile "$log" "$u8"
  tr -d '\r' < "$u8" | grep -Eio 'Result:[[:space:]]*[0-9]+[[:space:]]+errors?,[[:space:]]*[0-9]+[[:space:]]+warnings?' | tail -1 || true
}

compile_checkpoint_valid(){
  local src="$1"
  local expected_sha="$2"
  local log="${src%.mq5}.log"
  local ex5="${src%.mq5}.ex5"
  local marker="${src%.mq5}.compile_source_sha256"
  local u8="$OUT/.compile_v42_reuse_check.txt"
  local sum=""

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
if log.stat().st_mtime_ns < s or ex5.stat().st_mtime_ns < s:
    raise SystemExit(1)
PYMTIME
  fi

  printf '%s\n' "$expected_sha" > "$marker"
  cp -f "$u8" "$OUT/V42BaselineRouterLab.compile.txt"
  echo "REUSE COMPILE CHECKPOINT source_sha=$expected_sha summary=$sum"
  return 0
}

compile_ea(){
  local src="$1"
  local expected_sha="$2"
  local log="${src%.mq5}.log"
  local ex5="${src%.mq5}.ex5"
  local marker="${src%.mq5}.compile_source_sha256"
  local src_w include_w rc i u8 sum ready

  if compile_checkpoint_valid "$src" "$expected_sha"; then
    return 0
  fi

  rm -f "$log" "$ex5" "$marker"
  if tasklist.exe //FI "IMAGENAME eq metaeditor64.exe" 2>/dev/null | tr -d '\r' | grep -qi metaeditor64.exe; then
    die "MetaEditor is already open. Close MetaEditor completely and rerun."
  fi

  src_w="$(cygpath -w "$src")"
  include_w="$(cygpath -w "$DATA/MQL5")"
  echo "METAEDITOR_COMPILE_SOURCE=$src_w"
  echo "METAEDITOR_INCLUDE_ROOT=$include_w"
  if MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' "$METAEDITOR_EXE" "/compile:$src_w" "/include:$include_w" /log; then
    rc=0
  else
    rc=$?
  fi
  echo "METAEDITOR_LAUNCH_RC=$rc"

  u8="$OUT/.compile_v42.txt"
  sum=""
  ready=0
  for ((i=0;i<1200;i++)); do
    if [[ -s "$log" ]]; then
      sum="$(compile_summary "$log" "$u8")"
      if [[ -n "$sum" ]]; then
        if [[ ! "$sum" =~ Result:[[:space:]]*0[[:space:]]+errors?,[[:space:]]*0[[:space:]]+warnings? ]]; then
          cat "$u8"
          die "compile failed: launcher_rc=$rc summary=$sum"
        fi
        if [[ -s "$ex5" ]]; then
          ready=1
          break
        fi
      fi
    fi
    sleep 0.25
  done

  if [[ "$ready" -ne 1 ]]; then
    echo "METAEDITOR_DIAGNOSTIC: compile artifacts did not reach log+Result+EX5 postcondition"
    tasklist.exe //FI "IMAGENAME eq metaeditor64.exe" 2>/dev/null | tr -d '\r' || true
    echo "SOURCE_DIR_LISTING:"
    ls -la "$(dirname "$src")" | tail -60 || true
    if [[ -s "$log" ]]; then
      sum="$(compile_summary "$log" "$u8")"
      cat "$u8" || true
      echo "LAST_COMPILE_SUMMARY=$sum"
    fi
    die "MetaEditor compile postcondition failed: launcher_rc=$rc"
  fi

  [[ "$(sha256sum "$src" | awk '{print $1}')" == "$expected_sha" ]] || die "compiled source hash changed unexpectedly"
  printf '%s\n' "$expected_sha" > "$marker"
  cp -f "$u8" "$OUT/V42BaselineRouterLab.compile.txt"
  echo "$sum"
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

collect_run(){
  local tag="$1"
  local dest="$2"
  local marker="$3"
  [[ -s "$dest/SOURCE_RUN_FOLDER.txt" ]] || die "SOURCE_RUN_FOLDER missing for $tag"
  local rd
  rd="$(cat "$dest/SOURCE_RUN_FOLDER.txt")"
  [[ -d "$rd" ]] || die "run folder missing $rd"
  for f in monthly_summary.csv trades.csv manifest.txt; do
    [[ -s "$rd/$f" ]] || die "$f missing"
    cp -f "$rd/$f" "$dest/$f"
  done
  grep -Fq "$marker" "$dest/manifest.txt" || die "manifest marker missing"
  grep -Fq "tester_only=1" "$dest/manifest.txt" || die "tester marker missing"
  grep -Fq "native_broker_orders=0" "$dest/manifest.txt" || die "native order marker mismatch"
  grep -Fq "external_broker_orders=0" "$dest/manifest.txt" || die "external order marker mismatch"
  echo done > "$dest/DONE.txt"
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
  local backup="$OUT/state_before_v42.csv"
  local had_state=0
  if [[ -s "$state_target" ]]; then
    cp -f "$state_target" "$backup"
    had_state=1
  fi
  cp -f "$state" "$state_target"

  local before=""
  [[ -s "$LATEST" ]] && before="$(read_kv run_id "$LATEST" || true)"
  local ini
  ini="$(make_ini "$expert" "$from" "$to" "$tag")"
  say "RUN v42_baseline_router — exact MT5 Deposit=40, Model=0, tester-only, risk<=1.00%"

  local rc
  if MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' "$TERMINAL_EXE" "/config:$(cygpath -w "$ini")"; then
    rc=0
  else
    rc=$?
  fi
  echo "MT5_LAUNCH_RC=$rc"

  [[ -s "$state_target" ]] && cp -f "$state_target" "$OUT/state_after_v42.csv"
  if [[ "$had_state" -eq 1 ]]; then
    cp -f "$backup" "$state_target"
  else
    rm -f "$state_target"
  fi

  local after="" folder="" i
  for ((i=0;i<240;i++)); do
    if [[ -s "$LATEST" ]]; then
      after="$(read_kv run_id "$LATEST" || true)"
      folder="$(read_kv run_folder "$LATEST" || true)"
      if [[ -n "$after" && "$after" != "$before" && -n "$folder" ]]; then
        break
      fi
    fi
    sleep 0.5
  done
  [[ -n "$after" && "$after" != "$before" && -n "$folder" ]] || die "LATEST did not refresh after MT5; launcher_rc=$rc"

  folder="${folder//\\//}"
  local rd="$COMMON/$folder"
  [[ -d "$rd" ]] || die "new run folder missing $rd"
  printf '%s' "$rd" > "$dest/SOURCE_RUN_FOLDER.txt"
  printf '%s' "$after" > "$dest/MT5_DONE.txt"
  cp -f "$LATEST" "$dest/LATEST.txt"
  collect_run "$tag" "$dest" "$marker"
}

EA42="$EXPERT_DIR/V42BaselineRouterLab.mq5"
if [[ -s "$EA42" && "$(sha256sum "$EA42" | awk '{print $1}')" == "$SHA42A" ]]; then
  say "REUSE installed V42 source bytes sha=$SHA42A"
else
  cp -f "$BASE42A" "$EA42"
fi
say "Compile/reuse V42 Baseline Router Lab with direct MetaEditor artifact gate"
compile_ea "$EA42" "$SHA42A"

run_mt5_checkpoint "v42_baseline_router" "V42BaselineRouterLab" "2025.08.01" "2026.08.01" "$STATE1" "v42_baseline_router_upgrade=1"

ANJSON="$OUT/v42_baseline_router_analysis.json"
ANCSV="$OUT/v42_baseline_router_comparison.csv"
"$PY" "$A42" --run-folder "$(cygpath -w "$CP/v42_baseline_router")" --output "$(cygpath -w "$ANJSON")" --csv "$(cygpath -w "$ANCSV")"

EVID="$OUT/V42_EVIDENCE.txt"
{
  echo "schema=v42_baseline_router_exact_mt5_evidence_v5"
  echo "head=$HEAD"
  echo "branch=$BRANCH"
  echo "runner_architecture=direct_v32_v34_v38_style_with_compile_checkpoint_v1"
  echo "v30_sha=$V30_SHA"
  echo "v38_parent_zip_sha=$ACTUAL_V38_ZIP_SHA"
  echo "v38_parent_source_sha=$SHA38A"
  echo "v42_source_sha=$SHA42A"
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
  echo "live_trading=FORBIDDEN"
  echo "risk_changed=0"
  echo "risk_ceiling_per_trade=1.00%"
  echo "entry_exit_geometry_changed=0"
  echo "control=adaptive_ewma_hl8_thr0"
  echo "expected_control_final=$EXPECTED_CONTROL_FINAL"
  echo "expected_control_trades=$EXPECTED_CONTROL_TRADES"
  echo "target_geo_month=15.00%"
  echo "development_only=1"
  echo "fresh_holdout_required_for_promotion=1"
} > "$EVID"

BUNDLE_DIR="$OUT/bundle"
rm -rf "$BUNDLE_DIR"
mkdir -p "$BUNDLE_DIR"
for f in \
  "$EVID" \
  "$LOG" \
  "$OUT/V42BaselineRouterLab.compile.txt" \
  "$BASE38A" \
  "$BASE42A" \
  "$ANJSON" \
  "$ANCSV" \
  "$S42" \
  "$A42" \
  "$TEST" \
  "$0" \
  "$BOOT"; do
  [[ -s "$f" ]] && cp -f "$f" "$BUNDLE_DIR/$(basename "$f")"
done
for f in DONE.txt MT5_DONE.txt LATEST.txt SOURCE_RUN_FOLDER.txt manifest.txt monthly_summary.csv trades.csv; do
  p="$CP/v42_baseline_router/$f"
  [[ -s "$p" ]] && cp -f "$p" "$BUNDLE_DIR/$f" || true
done

MAN="$BUNDLE_DIR/bundle_manifest_sha256.txt"
(
  cd "$BUNDLE_DIR"
  find . -maxdepth 1 -type f ! -name 'bundle_manifest_sha256.txt' -printf '%f\0' | sort -z | while IFS= read -r -d '' f; do
    sha256sum "$f"
  done
) > "$MAN"

ZIP="$OUT/v42_baseline_router_exact_mt5.zip"
rm -f "$ZIP"
"$PY" - "$BUNDLE_DIR" "$ZIP" <<'PYZIP'
from pathlib import Path
import hashlib,sys,zipfile
r=Path(sys.argv[1]); rows=(r/'bundle_manifest_sha256.txt').read_text(encoding='utf-8').splitlines(); assert rows
for line in rows:
    h,n=line.split('  ',1)
    assert hashlib.sha256((r/n).read_bytes()).hexdigest()==h
out=Path(sys.argv[2])
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in sorted(r.iterdir(),key=lambda x:x.name):
        if p.is_file(): z.write(p,p.name)
with zipfile.ZipFile(out) as z:
    assert z.testzip() is None
print('V42 ZIP/manifest PASS')
PYZIP

ZIP_SHA="$(sha256sum "$ZIP" | awk '{print $1}')"
say "V42 EXACT-MT5 DONE"
"$PY" - "$ANJSON" <<'PYPRINT'
import json,sys
d=json.load(open(sys.argv[1],encoding='utf-8'))
c=d['exact_control']
w=next(x for x in d['v42_challengers'] if x['candidate']==d['development_v42_return_winner'])
print(f"EXACT_CONTROL_END_USD={c['ending_usd']:.6f}")
print(f"EXACT_CONTROL_GEO_MONTH={c['geo_month_pct']:.4f}%")
print(f"EXACT_CONTROL_MAX_DD={c['max_mtm_dd_pct']:.4f}%")
print(f"V42_WINNER={w['candidate']}")
print(f"V42_WINNER_END_USD={w['ending_usd']:.6f}")
print(f"V42_WINNER_GEO_MONTH={w['geo_month_pct']:.4f}%")
print(f"V42_WINNER_MAX_DD={w['max_mtm_dd_pct']:.4f}%")
print('ELIGIBLE_TO_FREEZE='+(','.join(d['eligible_to_freeze_for_fresh_holdout']) or 'NONE'))
print(f"TARGET_GEO_MONTH={d['aspirational_target']['geo_month_pct']:.2f}%")
PYPRINT

echo "UPLOAD THIS ONE ZIP:"
cygpath -w "$ZIP"
echo "SHA256=$ZIP_SHA"
