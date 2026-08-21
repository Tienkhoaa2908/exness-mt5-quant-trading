#!/usr/bin/env bash
set -Eeuo pipefail
export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
REPO_ROOT="$(cd -- "$ROOT/../.." && pwd -P)"
OUT="$ROOT/OUTPUT_V42"
CP="$OUT/checkpoints"
LOG="$OUT/v42_resume_runner.log"

TERMINAL_EXE="${MT5_TERMINAL_EXE:-/c/Program Files/MetaTrader 5/terminal64.exe}"
V30_SHA="4222120de5ded19ab7da172ad4c1e65d2a54b8bac7491fcd7927685b17b09a05"
V38_ZIP_SHA="224296ae1c02792493c690e3be563dd278b2eab5a13a6cfaefd6e5eae052cf5b"
V42_SOURCE_SHA="142bb4fdb066de712395f32942e8ff24cbc3af0a4c9d82c88f96317d8acc248e"
V34_TAPE_SHA="d70d92d0023c1862af6363d60a7d9e927f928e75ffcf1c0cedcb4f7798128863"
STATE1_SHA="5110519f2fe9722b4c13eb1e5ceec42f00bd04dd3b4f071af28349068b6097b0"
EXPECTED_BRANCH="agent/v42-baseline-router-exact-mt5"
EXPECTED_CONTROL_FINAL=107.432645
EXPECTED_CONTROL_TRADES=563

STATE1="$REPO_ROOT/runtime/v34_parallel_alpha/state_after_chunk1.csv"
A42="$REPO_ROOT/scripts/analyze_v42_baseline_router_mt5.py"
SECRET_SCAN="$REPO_ROOT/scripts/secret_scan.py"
V38_ZIP="$REPO_ROOT/runtime/v38_fast_harvest/OUTPUT_V38/v38_fast_harvest_exact_mt5.zip"
DIRECT_RUNNER="$ROOT/RUN_V42_BASELINE_ROUTER_EXACT_MT5_GIT_BASH.sh"
BOOT="$ROOT/BOOTSTRAP_V42_BASELINE_ROUTER_ONE_SHOT_GIT_BASH.sh"

mkdir -p "$OUT" "$CP"
: > "$LOG"
exec > >(tee -a "$LOG") 2>&1
say(){ printf '\n[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"; }
die(){ echo "FATAL: $*" >&2; exit 1; }
trap 'rc=$?; echo "FAILED rc=$rc line=${BASH_LINENO[0]:-?} cmd=${BASH_COMMAND:-?}" >&2; exit $rc' ERR

say "V42 RESUME FROM VERIFIED COMPILED EA"
echo "Strategy Tester only. REAL-MONEY LIVE TRADING remains FORBIDDEN."
echo "This recovery path does NOT launch MetaEditor and does NOT rebuild V42 source."

for c in cygpath sha256sum grep awk iconv tasklist.exe tr git sleep ls; do
  command -v "$c" >/dev/null || die "Missing Git Bash command: $c"
done
[[ -f "$TERMINAL_EXE" ]] || die "MT5 executable missing"
for f in "$STATE1" "$A42" "$SECRET_SCAN" "$V38_ZIP" "$DIRECT_RUNNER" "$BOOT"; do
  [[ -s "$f" ]] || die "required recovery file missing: $f"
done

HEAD="$(git -C "$REPO_ROOT" rev-parse HEAD)"
BRANCH="$(git -C "$REPO_ROOT" branch --show-current)"
echo "HEAD=$HEAD"
echo "BRANCH=$BRANCH"
[[ "$BRANCH" == "$EXPECTED_BRANCH" ]] || die "wrong branch: expected=$EXPECTED_BRANCH actual=$BRANCH"
[[ "$(sha256sum "$STATE1" | awk '{print $1}')" == "$STATE1_SHA" ]] || die "state1 hash mismatch"
[[ "$(sha256sum "$V38_ZIP" | awk '{print $1}')" == "$V38_ZIP_SHA" ]] || die "accepted V38 ZIP SHA mismatch"

if tasklist.exe //FI "IMAGENAME eq terminal64.exe" 2>/dev/null | tr -d '\r' | grep -qi terminal64.exe; then
  die "MetaTrader 5 is open. Close MT5 completely and rerun resume."
fi

V31_PY="$REPO_ROOT/runtime/v31_mt5_model_gate/OUTPUT_V31_1_MT5/.venv/Scripts/python.exe"
[[ -x "$V31_PY" ]] || die "Pinned V31/V32 Python environment missing: $V31_PY"
PY="$V31_PY"
"$PY" -m py_compile "$A42" "$SECRET_SCAN"
bash -n "$0"
"$PY" "$SECRET_SCAN" "$REPO_ROOT"

APPDATA_U="$(cygpath -u "$APPDATA")"
TERM_ROOT="$APPDATA_U/MetaQuotes/Terminal"
COMMON="$TERM_ROOT/Common/Files"
INPUTS="$COMMON/mt5_quant/inputs"
LATEST="$COMMON/mt5_quant/ML_DL_FEATURE_LAKE_LATEST.txt"
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
mkdir -p "$DATA/config" "$INPUTS"
say "MT5 data folder: $(cygpath -w "$DATA")"

EA42="$EXPERT_DIR/V42BaselineRouterLab.mq5"
LOG42="$EXPERT_DIR/V42BaselineRouterLab.log"
EX542="$EXPERT_DIR/V42BaselineRouterLab.ex5"
[[ -s "$EA42" && -s "$LOG42" && -s "$EX542" ]] || die "compiled V42 mq5/log/ex5 recovery artifacts are incomplete"
ACTUAL_V42_SHA="$(sha256sum "$EA42" | awk '{print $1}')"
[[ "$ACTUAL_V42_SHA" == "$V42_SOURCE_SHA" ]] || die "installed V42 source SHA mismatch expected=$V42_SOURCE_SHA actual=$ACTUAL_V42_SHA"

COMPILE_U8="$OUT/V42BaselineRouterLab.compile.txt"
if ! iconv -f UTF-16 -t UTF-8 "$LOG42" > "$COMPILE_U8" 2>/dev/null; then
  tr -d '\r' < "$LOG42" > "$COMPILE_U8"
fi
COMPILE_SUMMARY="$(tr -d '\r' < "$COMPILE_U8" | grep -Eio 'Result:[[:space:]]*[0-9]+[[:space:]]+errors?,[[:space:]]*[0-9]+[[:space:]]+warnings?' | tail -1 || true)"
[[ "$COMPILE_SUMMARY" =~ Result:[[:space:]]*0[[:space:]]+errors?,[[:space:]]*0[[:space:]]+warnings? ]] || { cat "$COMPILE_U8"; die "existing V42 compile is not 0 errors / 0 warnings: $COMPILE_SUMMARY"; }

"$PY" - "$EA42" "$LOG42" "$EX542" <<'PYMTIME'
from pathlib import Path
import sys
src,log,ex5=map(Path,sys.argv[1:])
s=src.stat().st_mtime_ns
if log.stat().st_mtime_ns < s or ex5.stat().st_mtime_ns < s:
    raise SystemExit('compiled log/ex5 are older than the installed V42 source')
PYMTIME

echo "REUSE VERIFIED COMPILED V42 EA source_sha=$V42_SOURCE_SHA summary=$COMPILE_SUMMARY"

TAPE34="$INPUTS/v34_parallel_alpha_tape.csv"
[[ -s "$TAPE34" ]] || die "V34 causal specialist tape missing"
[[ "$(sha256sum "$TAPE34" | awk '{print $1}')" == "$V34_TAPE_SHA" ]] || die "V34 tape hash mismatch"

PARENT38="$OUT/V38FastHarvestLab.accepted_parent.mq5"
"$PY" - "$V38_ZIP" "$PARENT38" <<'PYV38'
from pathlib import Path
import hashlib,sys,zipfile
zp=Path(sys.argv[1]); out=Path(sys.argv[2])
with zipfile.ZipFile(zp) as z:
    bad=z.testzip()
    if bad is not None: raise RuntimeError(f'accepted V38 ZIP CRC failure: {bad}')
    hits=[n for n in z.namelist() if Path(n).name=='V38FastHarvestLab.base.a.mq5']
    if len(hits)!=1: raise RuntimeError(f'expected one accepted V38 parent source, found={hits}')
    data=z.read(hits[0])
out.write_bytes(data)
print('Accepted V38 ZIP/parent PASS parent_sha='+hashlib.sha256(data).hexdigest())
PYV38
PARENT38_SHA="$(sha256sum "$PARENT38" | awk '{print $1}')"

read_kv(){
  local key="$1" file="$2"
  awk -F= -v k="$key" '$1==k{sub(/^[^=]*=/,"");gsub(/\r/,"");print;exit}' "$file"
}

make_ini(){
  local ini="$DATA/config/v42_baseline_router_resume.ini"
  local tmp="$OUT/.v42_resume.ini"
  cat > "$tmp" <<'EOF_INI'
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
Expert=mt5_quant\V42BaselineRouterLab.ex5
Symbol=XAUUSDm
Period=M15
Optimization=0
Model=0
FromDate=2025.08.01
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
  printf '\xFF\xFE' > "$ini"
  iconv -f UTF-8 -t UTF-16LE "$tmp" >> "$ini"
  rm -f "$tmp"
  printf '%s' "$ini"
}

collect_ready(){
  local rd="$1" marker="$2" i
  for ((i=0;i<1200;i++)); do
    if [[ -s "$rd/monthly_summary.csv" && -s "$rd/trades.csv" && -s "$rd/manifest.txt" ]] \
       && grep -Fq "$marker" "$rd/manifest.txt" \
       && grep -Fq 'tester_only=1' "$rd/manifest.txt" \
       && grep -Fq 'native_broker_orders=0' "$rd/manifest.txt" \
       && grep -Fq 'external_broker_orders=0' "$rd/manifest.txt"; then
      return 0
    fi
    sleep 0.25
  done
  return 1
}

DEST="$CP/v42_baseline_router"
mkdir -p "$DEST"
if [[ -s "$DEST/DONE.txt" && -s "$DEST/monthly_summary.csv" && -s "$DEST/trades.csv" && -s "$DEST/manifest.txt" ]]; then
  say "REUSE EXACT-MT5 CHECKPOINT — MT5 NOT RERUN"
else
  STATE_TARGET="$INPUTS/v30_ml_dl_feature_lake_state.csv"
  BACKUP="$OUT/state_before_v42_resume.csv"
  HAD_STATE=0
  if [[ -s "$STATE_TARGET" ]]; then cp -f "$STATE_TARGET" "$BACKUP"; HAD_STATE=1; fi
  cp -f "$STATE1" "$STATE_TARGET"

  BEFORE=""
  [[ -s "$LATEST" ]] && BEFORE="$(read_kv run_id "$LATEST" || true)"
  INI="$(make_ini)"
  say "RUN v42_baseline_router — exact MT5 from verified compiled EA"
  if MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' "$TERMINAL_EXE" "/config:$(cygpath -w "$INI")"; then
    RC=0
  else
    RC=$?
  fi
  echo "MT5_LAUNCH_RC=$RC"

  [[ -s "$STATE_TARGET" ]] && cp -f "$STATE_TARGET" "$OUT/state_after_v42.csv"
  if [[ "$HAD_STATE" -eq 1 ]]; then cp -f "$BACKUP" "$STATE_TARGET"; else rm -f "$STATE_TARGET"; fi

  AFTER=""; FOLDER=""
  for ((i=0;i<3600;i++)); do
    if [[ -s "$LATEST" ]]; then
      AFTER="$(read_kv run_id "$LATEST" || true)"
      FOLDER="$(read_kv run_folder "$LATEST" || true)"
      [[ -n "$AFTER" && "$AFTER" != "$BEFORE" && -n "$FOLDER" ]] && break
    fi
    sleep 0.5
  done
  [[ -n "$AFTER" && "$AFTER" != "$BEFORE" && -n "$FOLDER" ]] || die "LATEST did not refresh after exact MT5; launcher_rc=$RC"
  FOLDER="${FOLDER//\\//}"
  RD="$COMMON/$FOLDER"
  [[ -d "$RD" ]] || die "new MT5 run folder missing: $RD"
  collect_ready "$RD" "v42_baseline_router_upgrade=1" || { ls -la "$RD" || true; die "MT5 run folder did not reach complete artifact/manifest postcondition"; }

  cp -f "$RD/monthly_summary.csv" "$DEST/monthly_summary.csv"
  cp -f "$RD/trades.csv" "$DEST/trades.csv"
  cp -f "$RD/manifest.txt" "$DEST/manifest.txt"
  cp -f "$LATEST" "$DEST/LATEST.txt"
  printf '%s' "$RD" > "$DEST/SOURCE_RUN_FOLDER.txt"
  printf '%s' "$AFTER" > "$DEST/MT5_DONE.txt"
  echo done > "$DEST/DONE.txt"
fi

ANJSON="$OUT/v42_baseline_router_analysis.json"
ANCSV="$OUT/v42_baseline_router_comparison.csv"
"$PY" "$A42" --run-folder "$(cygpath -w "$DEST")" --output "$(cygpath -w "$ANJSON")" --csv "$(cygpath -w "$ANCSV")"

EVID="$OUT/V42_EVIDENCE.txt"
{
  echo "schema=v42_baseline_router_exact_mt5_evidence_resume_v1"
  echo "head=$HEAD"
  echo "branch=$BRANCH"
  echo "resume_from_verified_compiled_ea=1"
  echo "metaeditor_launched_in_resume=0"
  echo "v42_source_sha=$V42_SOURCE_SHA"
  echo "v38_parent_zip_sha=$V38_ZIP_SHA"
  echo "v38_parent_source_sha=$PARENT38_SHA"
  echo "v34_tape_sha=$V34_TAPE_SHA"
  echo "state1_sha=$STATE1_SHA"
  echo "compile_summary=$COMPILE_SUMMARY"
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
} > "$EVID"

BUNDLE="$OUT/bundle"
rm -rf "$BUNDLE"; mkdir -p "$BUNDLE"
for f in "$EVID" "$LOG" "$COMPILE_U8" "$PARENT38" "$EA42" "$ANJSON" "$ANCSV" "$A42" "$0" "$DIRECT_RUNNER" "$BOOT"; do
  [[ -s "$f" ]] && cp -f "$f" "$BUNDLE/$(basename "$f")"
done
for f in DONE.txt MT5_DONE.txt LATEST.txt SOURCE_RUN_FOLDER.txt manifest.txt monthly_summary.csv trades.csv; do
  [[ -s "$DEST/$f" ]] && cp -f "$DEST/$f" "$BUNDLE/$f"
done
MAN="$BUNDLE/bundle_manifest_sha256.txt"
(cd "$BUNDLE"; find . -maxdepth 1 -type f ! -name bundle_manifest_sha256.txt -printf '%f\0' | sort -z | while IFS= read -r -d '' f; do sha256sum "$f"; done) > "$MAN"
ZIP="$OUT/v42_baseline_router_exact_mt5.zip"
rm -f "$ZIP"
"$PY" - "$BUNDLE" "$ZIP" <<'PYZIP'
from pathlib import Path
import hashlib,sys,zipfile
root=Path(sys.argv[1]); out=Path(sys.argv[2])
for line in (root/'bundle_manifest_sha256.txt').read_text(encoding='utf-8').splitlines():
    h,n=line.split('  ',1); assert hashlib.sha256((root/n).read_bytes()).hexdigest()==h
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in sorted(root.iterdir(),key=lambda x:x.name):
        if p.is_file(): z.write(p,p.name)
with zipfile.ZipFile(out) as z: assert z.testzip() is None
print('V42 RESUME ZIP/manifest PASS')
PYZIP
ZIP_SHA="$(sha256sum "$ZIP" | awk '{print $1}')"

say "V42 EXACT-MT5 RESUME DONE"
"$PY" - "$ANJSON" <<'PYPRINT'
import json,sys
d=json.load(open(sys.argv[1],encoding='utf-8')); c=d['exact_control']; w=next(x for x in d['v42_challengers'] if x['candidate']==d['development_v42_return_winner'])
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
