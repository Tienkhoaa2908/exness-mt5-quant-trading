#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
REPO_ROOT="$(cd -- "$ROOT/../.." && pwd -P)"
OUT="$ROOT/OUTPUT_V41_STAGE_A"; ART="$OUT/artifacts"; LOG="$OUT/v41_baseline_stack_runner.log"
ACCEPTED_V38_ZIP_SHA="224296ae1c02792493c690e3be563dd278b2eab5a13a6cfaefd6e5eae052cf5b"
ACCEPTED_V39_ZIP_SHA="27de4ef769833df0433755dd0e80ec39a5d39f7e8c153837015edd69be475b1b"
ACCEPTED_V40_ZIP_SHA="e59cd92b4fc257406b6721336a79422778a108dd5bb92a5ea086cb54d4b449f2"
SCRIPT="$REPO_ROOT/scripts/v41_baseline_stack_action_value_stage_a.py"
COMMON="$REPO_ROOT/scripts/v41_baseline_stack_common.py"; ENTRYMOD="$REPO_ROOT/scripts/v41_baseline_entry_value.py"; ACTIONMOD="$REPO_ROOT/scripts/v41_baseline_action_value.py"; ECONMOD="$REPO_ROOT/scripts/v41_baseline_stack_economics.py"
V40_ENTRY="$REPO_ROOT/scripts/v40_upgrade_campaign_stage_a.py"; V40_CORE="$REPO_ROOT/scripts/v40_upgrade_campaign_stage_a_core.py"
TEST="$REPO_ROOT/tests/test_v41_baseline_stack_action_value_static.py"; SECRET_SCAN="$REPO_ROOT/scripts/secret_scan.py"; ANALYZER="$REPO_ROOT/scripts/analyze_mt5_research_bundle.py"
V36_RUNNER="$REPO_ROOT/runtime/v36_sequence_exit/RUN_V36_SEQUENCE_EXIT_DL_GIT_BASH.sh"
mkdir -p "$OUT" "$ART"; : > "$LOG"; exec > >(tee -a "$LOG") 2>&1
say(){ printf '\n[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"; }; die(){ echo "FATAL: $*" >&2; exit 1; }
trap 'rc=$?; echo "FAILED rc=$rc line=${BASH_LINENO[0]:-?} cmd=${BASH_COMMAND:-?}" >&2; exit $rc' ERR
for c in cygpath sha256sum awk grep bash git; do command -v "$c" >/dev/null || die "Missing Git Bash command: $c"; done
for p in "$SCRIPT" "$COMMON" "$ENTRYMOD" "$ACTIONMOD" "$ECONMOD" "$V40_ENTRY" "$V40_CORE" "$TEST" "$SECRET_SCAN" "$ANALYZER"; do [[ -s "$p" ]] || die "required file missing: $p"; done
PINNED_PY="$REPO_ROOT/runtime/v31_mt5_model_gate/OUTPUT_V31_1_MT5/.venv/Scripts/python.exe"
if [[ -x "$PINNED_PY" ]]; then PY="$PINNED_PY"; elif command -v python >/dev/null 2>&1; then PY="$(command -v python)"; elif command -v python3 >/dev/null 2>&1; then PY="$(command -v python3)"; else die "Python 3 not found"; fi
"$PY" - <<'PYCHK'
import sys
if sys.version_info < (3,10): raise SystemExit("Python 3.10+ required")
import numpy,pandas,sklearn
print("Python",sys.version.split()[0]); print("numpy",numpy.__version__,"pandas",pandas.__version__,"sklearn",sklearn.__version__)
PYCHK
say "Repository preflight"
HEAD="$(git -C "$REPO_ROOT" rev-parse HEAD)"; BRANCH="$(git -C "$REPO_ROOT" branch --show-current)"; echo "HEAD=$HEAD"; echo "BRANCH=$BRANCH"
[[ "$BRANCH" == "agent/v41-baseline-stack-action-value" ]] || die "Wrong branch expected=agent/v41-baseline-stack-action-value actual=$BRANCH"
say "Compile + V41 tests + tracked-source secret scan"
"$PY" -m py_compile "$SCRIPT" "$COMMON" "$ENTRYMOD" "$ACTIONMOD" "$ECONMOD" "$V40_ENTRY" "$V40_CORE" "$TEST" "$SECRET_SCAN" "$ANALYZER"
if "$PY" -c 'import pytest' >/dev/null 2>&1; then "$PY" -m pytest -q "$TEST"; else echo "pytest unavailable: running dependency-free V41 gate"; "$PY" "$TEST"; fi
"$PY" "$SECRET_SCAN" "$REPO_ROOT"; bash -n "$0"
if grep -Eiq 'terminal64\.exe|metaeditor64\.exe|OrderSend[[:space:]]*\(|OrderSendAsync[[:space:]]*\(|\bCTrade\b|trade\.Buy[[:space:]]*\(|trade\.Sell[[:space:]]*\(' "$SCRIPT" "$COMMON" "$ENTRYMOD" "$ACTIONMOD" "$ECONMOD" "$V40_ENTRY" "$V40_CORE"; then die "Forbidden MT5/native-order token found in V41 Stage A dependency set"; fi
resolve_v38_run(){
 local default_run="$REPO_ROOT/runtime/v38_fast_harvest/OUTPUT_V38/checkpoints/v38_fast_harvest"
 if [[ -s "$default_run/intra_trade_m1_fast.csv" && -s "$default_run/intra_trade_m15.csv" && -s "$default_run/trades.csv" ]]; then printf '%s' "$default_run"; return 0; fi
 local zip="${V38_ZIP:-$REPO_ROOT/runtime/v38_fast_harvest/OUTPUT_V38/v38_fast_harvest_exact_mt5.zip}"; [[ -s "$zip" ]] || return 1
 local got; got="$(sha256sum "$zip"|awk '{print $1}')"; [[ "$got" == "$ACCEPTED_V38_ZIP_SHA" ]] || die "V38 ZIP SHA mismatch expected=$ACCEPTED_V38_ZIP_SHA actual=$got"
 local dest="$OUT/accepted_v38_zip"; rm -rf "$dest"; mkdir -p "$dest"
 "$PY" - "$zip" "$dest" <<'PYUNZIP'
from pathlib import Path
import sys,zipfile
z=Path(sys.argv[1]); d=Path(sys.argv[2]).resolve()
with zipfile.ZipFile(z) as f:
 bad=f.testzip()
 if bad: raise SystemExit(f"V38 ZIP CRC failure: {bad}")
 for info in f.infolist():
  p=(d/info.filename).resolve()
  if d not in p.parents and p!=d: raise SystemExit(f"unsafe ZIP member: {info.filename}")
 f.extractall(d)
PYUNZIP
 local run="$dest/checkpoints/v38_fast_harvest"; [[ -s "$run/intra_trade_m1_fast.csv" && -s "$run/intra_trade_m15.csv" && -s "$run/trades.csv" ]] || die "Accepted V38 ZIP missing checkpoint evidence"; printf '%s' "$run"
}
V38_RUN="$(resolve_v38_run || true)"; [[ -n "$V38_RUN" ]] || die "Accepted V38 evidence missing"; say "V38 accepted evidence: $V38_RUN"
V36_PRED="${V36_PREDICTIONS:-$REPO_ROOT/runtime/v36_sequence_exit/OUTPUT_V36_SEQUENCE_DL/v36_sequence_predictions.csv}"; V36_SUM="${V36_SUMMARY:-$REPO_ROOT/runtime/v36_sequence_exit/OUTPUT_V36_SEQUENCE_DL/v36_sequence_summary.json}"
if [[ ! -s "$V36_PRED" ]]; then [[ -s "$V36_RUNNER" ]] || die "V36 predictions missing and offline runner unavailable"; say "Recover accepted V36 predictions offline"; bash "$V36_RUNNER"; fi
[[ -s "$V36_PRED" ]] || die "V36 predictions still missing"; say "V36 predictions: $V36_PRED"
rm -rf "$ART"; mkdir -p "$ART"
say "Run V41 direct action-value + baseline upgrade stack — offline/read-only"
"$PY" "$SCRIPT" --v38-run-folder "$(cygpath -w "$V38_RUN")" --v36-predictions "$(cygpath -w "$V36_PRED")" --output-dir "$(cygpath -w "$ART")"
SUMMARY="$ART/v41_baseline_stack_action_value_summary.json"; [[ -s "$SUMMARY" ]] || die "V41 summary missing"
readarray -t REPORT < <("$PY" - "$SUMMARY" <<'PYR'
import json,sys
d=json.load(open(sys.argv[1],encoding='utf-8')); g=d['gate']; sm={x['lane']:x for x in d['stack_metrics']}
for v in [g.get('status','UNKNOWN'),g.get('promotion_lane') or 'NONE',sm['ENTRY_VALUE']['end_usd'],sm['ENTRY_VALUE']['geo_month'],sm['ENTRY_VALUE']['max_dd'],sm['ACTION_VALUE']['end_usd'],sm['ACTION_VALUE']['geo_month'],sm['ACTION_VALUE']['max_dd'],sm['INTEGRATED_STACK']['end_usd'],sm['INTEGRATED_STACK']['geo_month'],sm['INTEGRATED_STACK']['max_dd'],d['accepted_exact_baseline']['geo_month'],d['aspirational_target']['geo_month']]: print(v)
PYR
)
STATUS="${REPORT[0]}"; PROMOTION="${REPORT[1]}"; ENTRY_END="${REPORT[2]}"; ENTRY_GEO="${REPORT[3]}"; ENTRY_DD="${REPORT[4]}"; ACTION_END="${REPORT[5]}"; ACTION_GEO="${REPORT[6]}"; ACTION_DD="${REPORT[7]}"; STACK_END="${REPORT[8]}"; STACK_GEO="${REPORT[9]}"; STACK_DD="${REPORT[10]}"; BASE_GEO="${REPORT[11]}"; TARGET_GEO="${REPORT[12]}"
cp -f "$SCRIPT" "$ART/v41_baseline_stack_action_value_stage_a.py"; cp -f "$COMMON" "$ART/v41_baseline_stack_common.py"; cp -f "$ENTRYMOD" "$ART/v41_baseline_entry_value.py"; cp -f "$ACTIONMOD" "$ART/v41_baseline_action_value.py"; cp -f "$ECONMOD" "$ART/v41_baseline_stack_economics.py"; cp -f "$TEST" "$ART/test_v41_baseline_stack_action_value_static.py"; cp -f "$V40_ENTRY" "$ART/v40_upgrade_campaign_stage_a.py"; cp -f "$V40_CORE" "$ART/v40_upgrade_campaign_stage_a_core.py"; [[ -s "$V36_SUM" ]] && cp -f "$V36_SUM" "$ART/v36_sequence_summary.json" || true
EVID="$ART/V41_EVIDENCE.txt"
{
 echo "schema=v41_baseline_stack_action_value_evidence_v1"; echo "head=$HEAD"; echo "branch=$BRANCH"; echo "accepted_v38_zip_sha256=$ACCEPTED_V38_ZIP_SHA"; echo "accepted_v39_zip_sha256=$ACCEPTED_V39_ZIP_SHA"; echo "accepted_v40_zip_sha256=$ACCEPTED_V40_ZIP_SHA"; echo "v38_m1_sha256=$(sha256sum "$V38_RUN/intra_trade_m1_fast.csv"|awk '{print $1}')"; echo "v38_m15_sha256=$(sha256sum "$V38_RUN/intra_trade_m15.csv"|awk '{print $1}')"; echo "v38_trades_sha256=$(sha256sum "$V38_RUN/trades.csv"|awk '{print $1}')"; echo "v36_predictions_sha256=$(sha256sum "$V36_PRED"|awk '{print $1}')"; echo "v41_script_sha256=$(sha256sum "$SCRIPT"|awk '{print $1}')"; echo "stage_a_status=$STATUS"; echo "promotion_lane=$PROMOTION"; echo "baseline_model=adaptive_ewma_hl8_thr0_causal_mixture_of_experts"; echo "entry_layer=expected_r_keep60"; echo "action_layer=direct_delta_r_static_or_trail"; echo "exact_baseline_end_usd=107.43"; echo "exact_baseline_geo_month=8.58%"; echo "exact_baseline_max_dd=9.90%"; echo "entry_shadow_end_usd=$ENTRY_END"; echo "entry_shadow_geo_month=$ENTRY_GEO"; echo "entry_shadow_max_dd=$ENTRY_DD"; echo "action_shadow_end_usd=$ACTION_END"; echo "action_shadow_geo_month=$ACTION_GEO"; echo "action_shadow_max_dd=$ACTION_DD"; echo "stack_shadow_end_usd=$STACK_END"; echo "stack_shadow_geo_month=$STACK_GEO"; echo "stack_shadow_max_dd=$STACK_DD"; echo "target_geo_month=15%"; echo "shadow_is_exact_mt5=0"; echo "mt5_launched=0"; echo "metaeditor_launched=0"; echo "native_broker_orders=0"; echo "external_broker_orders=0"; echo "live_trading=FORBIDDEN"; echo "risk_changed=0"; echo "extra_entries=0"; echo "risk_ceiling_per_trade=1.00%"
} > "$EVID"
MANIFEST="$ART/bundle_manifest_sha256.txt"
"$PY" - "$ART" "$MANIFEST" <<'PYMAN'
from pathlib import Path
import hashlib,sys
root=Path(sys.argv[1]); out=Path(sys.argv[2]); rows=[]
for p in sorted(root.iterdir(),key=lambda x:x.name):
 if p.is_file() and p.name!=out.name: rows.append(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}")
out.write_text("\n".join(rows)+"\n",encoding='utf-8'); print(f"manifest files={len(rows)}")
PYMAN
"$PY" - "$ART" "$MANIFEST" <<'PYVERIFY'
from pathlib import Path
import hashlib,sys
root=Path(sys.argv[1]); man=Path(sys.argv[2])
for line in man.read_text(encoding='utf-8').splitlines():
 h,name=line.split('  ',1); p=root/name
 if not p.is_file(): raise SystemExit(f"manifest missing: {name}")
 if hashlib.sha256(p.read_bytes()).hexdigest()!=h: raise SystemExit(f"manifest mismatch: {name}")
print('bundle_manifest_sha256.txt PASS')
PYVERIFY
ZIP="$OUT/v41_baseline_stack_action_value_stage_a.zip"; rm -f "$ZIP"
"$PY" - "$ART" "$ZIP" <<'PYZIP'
from pathlib import Path
import sys,zipfile
root=Path(sys.argv[1]); out=Path(sys.argv[2])
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in sorted(root.iterdir(),key=lambda x:x.name):
  if p.is_file(): z.write(p,p.name)
with zipfile.ZipFile(out) as z:
 bad=z.testzip()
 if bad: raise SystemExit(f"ZIP CRC failure: {bad}")
 names=set(z.namelist())
 if 'bundle_manifest_sha256.txt' not in names or 'V41_EVIDENCE.txt' not in names: raise SystemExit('ZIP manifest/evidence missing')
print('ZIP integrity PASS')
PYZIP
"$PY" "$ANALYZER" "$ZIP" >/dev/null
ZIP_SHA="$(sha256sum "$ZIP"|awk '{print $1}')"
say "V41 BASELINE STACK DONE"
echo "STATUS=$STATUS"; echo "PROMOTION_LANE=$PROMOTION"; echo "EXACT_BASELINE_GEO_MONTH=$(awk 'BEGIN{printf "%.2f%%",100*'"$BASE_GEO"'}')"; echo "ENTRY_SHADOW_END_USD=$ENTRY_END"; echo "ENTRY_SHADOW_GEO_MONTH=$(awk 'BEGIN{printf "%.4f%%",100*'"$ENTRY_GEO"'}')"; echo "ENTRY_SHADOW_MAX_DD=$(awk 'BEGIN{printf "%.4f%%",100*'"$ENTRY_DD"'}')"; echo "ACTION_SHADOW_END_USD=$ACTION_END"; echo "ACTION_SHADOW_GEO_MONTH=$(awk 'BEGIN{printf "%.4f%%",100*'"$ACTION_GEO"'}')"; echo "ACTION_SHADOW_MAX_DD=$(awk 'BEGIN{printf "%.4f%%",100*'"$ACTION_DD"'}')"; echo "STACK_SHADOW_END_USD=$STACK_END"; echo "STACK_SHADOW_GEO_MONTH=$(awk 'BEGIN{printf "%.4f%%",100*'"$STACK_GEO"'}')"; echo "STACK_SHADOW_MAX_DD=$(awk 'BEGIN{printf "%.4f%%",100*'"$STACK_DD"'}')"; echo "TARGET_GEO_MONTH=$(awk 'BEGIN{printf "%.2f%%",100*'"$TARGET_GEO"'}')"; echo "Shadow metrics are NOT exact-MT5 PnL."; echo "UPLOAD THIS ONE ZIP:"; cygpath -w "$ZIP"; echo "SHA256=$ZIP_SHA"
