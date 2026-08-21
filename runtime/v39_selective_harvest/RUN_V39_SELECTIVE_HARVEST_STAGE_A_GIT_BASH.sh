#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
REPO_ROOT="$(cd -- "$ROOT/../.." && pwd -P)"
OUT="$ROOT/OUTPUT_V39_STAGE_A"
ART="$OUT/artifacts"
LOG="$OUT/v39_stage_a_runner.log"

ACCEPTED_V38_ZIP_SHA="224296ae1c02792493c690e3be563dd278b2eab5a13a6cfaefd6e5eae052cf5b"
SCRIPT="$REPO_ROOT/scripts/v39_selective_harvest_stage_a.py"
TEST="$REPO_ROOT/tests/test_v39_selective_harvest_static.py"
SECRET_SCAN="$REPO_ROOT/scripts/secret_scan.py"
V36_RUNNER="$REPO_ROOT/runtime/v36_sequence_exit/RUN_V36_SEQUENCE_EXIT_DL_GIT_BASH.sh"

mkdir -p "$OUT" "$ART"
: > "$LOG"
exec > >(tee -a "$LOG") 2>&1

say(){ printf '\n[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"; }
die(){ echo "FATAL: $*" >&2; exit 1; }
trap 'rc=$?; echo "FAILED rc=$rc line=${BASH_LINENO[0]:-?} cmd=${BASH_COMMAND:-?}" >&2; exit $rc' ERR

for c in cygpath sha256sum awk grep sed find sort bash; do
  command -v "$c" >/dev/null || die "Missing Git Bash command: $c"
done
[[ -s "$SCRIPT" && -s "$TEST" && -s "$SECRET_SCAN" ]] || die "V39 code/tests/safety scanner missing"

PINNED_PY="$REPO_ROOT/runtime/v31_mt5_model_gate/OUTPUT_V31_1_MT5/.venv/Scripts/python.exe"
if [[ -x "$PINNED_PY" ]]; then
  PY="$PINNED_PY"
elif command -v python >/dev/null 2>&1; then
  PY="$(command -v python)"
elif command -v python3 >/dev/null 2>&1; then
  PY="$(command -v python3)"
else
  die "Python 3 not found. V38 previously required a pinned Python environment; restore that environment first."
fi

"$PY" - <<'PYCHK'
import sys
if sys.version_info < (3,10):
    raise SystemExit("Python 3.10+ required")
import numpy, pandas, sklearn
print("Python", sys.version.split()[0])
print("numpy", numpy.__version__, "pandas", pandas.__version__, "sklearn", sklearn.__version__)
PYCHK

say "Repository preflight"
HEAD="$(git -C "$REPO_ROOT" rev-parse HEAD)"
BRANCH="$(git -C "$REPO_ROOT" branch --show-current)"
echo "HEAD=$HEAD"
echo "BRANCH=$BRANCH"
if [[ "$BRANCH" != "agent/v39-selective-harvest" ]]; then
  die "Wrong branch. Expected agent/v39-selective-harvest; actual=$BRANCH"
fi

say "Python compile + V39 static tests + repository secret scan"
"$PY" -m py_compile "$SCRIPT" "$TEST" "$SECRET_SCAN"
if "$PY" -c 'import pytest' >/dev/null 2>&1; then
  "$PY" -m pytest -q "$TEST"
else
  die "pytest missing from selected Python environment; do not silently skip the required test gate"
fi
"$PY" "$SECRET_SCAN" "$REPO_ROOT"
bash -n "$0"

# V39 Stage A is deliberately read-only/offline. It must not launch MT5/MetaEditor.
if grep -Eiq 'terminal64\.exe|metaeditor64\.exe|OrderSend[[:space:]]*\(|OrderSendAsync[[:space:]]*\(|\bCTrade\b|trade\.Buy[[:space:]]*\(|trade\.Sell[[:space:]]*\(' "$SCRIPT"; then
  die "Forbidden MT5/native-order token found in V39 Stage A code"
fi

resolve_v38_run(){
  local default_run="$REPO_ROOT/runtime/v38_fast_harvest/OUTPUT_V38/checkpoints/v38_fast_harvest"
  if [[ -s "$default_run/intra_trade_m1_fast.csv" && -s "$default_run/trades.csv" ]]; then
    printf '%s' "$default_run"
    return 0
  fi

  local zip="${V38_ZIP:-$REPO_ROOT/runtime/v38_fast_harvest/OUTPUT_V38/v38_fast_harvest_exact_mt5.zip}"
  [[ -s "$zip" ]] || return 1
  local got
  got="$(sha256sum "$zip" | awk '{print $1}')"
  [[ "$got" == "$ACCEPTED_V38_ZIP_SHA" ]] || die "V38 ZIP SHA mismatch expected=$ACCEPTED_V38_ZIP_SHA actual=$got"

  local dest="$OUT/accepted_v38_zip"
  rm -rf "$dest"
  mkdir -p "$dest"
  "$PY" - "$zip" "$dest" <<'PYUNZIP'
from pathlib import Path
import sys, zipfile
z=Path(sys.argv[1]); d=Path(sys.argv[2]).resolve()
with zipfile.ZipFile(z) as f:
    for info in f.infolist():
        p=(d/info.filename).resolve()
        if d not in p.parents and p != d:
            raise SystemExit(f"unsafe ZIP member: {info.filename}")
    f.extractall(d)
PYUNZIP
  local run="$dest/checkpoints/v38_fast_harvest"
  [[ -s "$run/intra_trade_m1_fast.csv" && -s "$run/trades.csv" ]] || die "Accepted V38 ZIP missing checkpoint evidence"
  printf '%s' "$run"
}

V38_RUN="$(resolve_v38_run || true)"
[[ -n "$V38_RUN" ]] || die "Accepted V38 evidence not found. Keep OUTPUT_V38 from the PASS run, or set V38_ZIP to the accepted ZIP."
say "V38 evidence: $V38_RUN"

# V36 is preserved, not replaced. Prefer accepted/recomputed prior output; only rerun the OFFLINE V36 diagnostic if missing.
V36_PRED="${V36_PREDICTIONS:-$REPO_ROOT/runtime/v36_sequence_exit/OUTPUT_V36_SEQUENCE_DL/v36_sequence_predictions.csv}"
V36_SUM="${V36_SUMMARY:-$REPO_ROOT/runtime/v36_sequence_exit/OUTPUT_V36_SEQUENCE_DL/v36_sequence_summary.json}"
if [[ ! -s "$V36_PRED" ]]; then
  [[ -s "$V36_RUNNER" ]] || die "V36 predictions missing and V36 offline runner unavailable"
  say "V36 Transformer predictions missing; recompute the accepted OFFLINE sequence diagnostic (no MT5 launch)"
  bash "$V36_RUNNER"
fi
[[ -s "$V36_PRED" ]] || die "V36 predictions still missing after offline recovery"
say "V36 predictions: $V36_PRED"

rm -rf "$ART"
mkdir -p "$ART"

say "Run V39 Stage A causal selective-harvest diagnostic"
"$PY" "$SCRIPT" \
  --v38-run-folder "$(cygpath -w "$V38_RUN")" \
  --v36-predictions "$(cygpath -w "$V36_PRED")" \
  --output-dir "$(cygpath -w "$ART")"

SUMMARY="$ART/v39_selective_harvest_summary.json"
[[ -s "$SUMMARY" ]] || die "V39 summary missing"

STATUS="$("$PY" - "$SUMMARY" <<'PYSTATUS'
import json,sys
d=json.load(open(sys.argv[1],encoding="utf-8"))
print(d.get("stage_a_status","UNKNOWN"))
PYSTATUS
)"
PRIMARY="$("$PY" - "$SUMMARY" <<'PYPRIMARY'
import json,sys
d=json.load(open(sys.argv[1],encoding="utf-8"))
print(d.get("primary_lane","UNKNOWN"))
PYPRIMARY
)"

cp -f "$SCRIPT" "$ART/v39_selective_harvest_stage_a.py"
cp -f "$TEST" "$ART/test_v39_selective_harvest_static.py"
[[ -s "$V36_SUM" ]] && cp -f "$V36_SUM" "$ART/v36_sequence_summary.json" || true

EVID="$ART/V39_EVIDENCE.txt"
{
  echo "schema=v39_selective_harvest_stage_a_evidence_v1"
  echo "head=$HEAD"
  echo "branch=$BRANCH"
  echo "accepted_v38_zip_sha256=$ACCEPTED_V38_ZIP_SHA"
  echo "v38_run_folder=$V38_RUN"
  echo "v38_m1_sha256=$(sha256sum "$V38_RUN/intra_trade_m1_fast.csv"|awk '{print $1}')"
  echo "v38_m15_sha256=$(sha256sum "$V38_RUN/intra_trade_m15.csv"|awk '{print $1}')"
  echo "v38_trades_sha256=$(sha256sum "$V38_RUN/trades.csv"|awk '{print $1}')"
  echo "v36_predictions_sha256=$(sha256sum "$V36_PRED"|awk '{print $1}')"
  echo "v39_script_sha256=$(sha256sum "$SCRIPT"|awk '{print $1}')"
  echo "stage_a_status=$STATUS"
  echo "primary_lane=$PRIMARY"
  echo "mt5_launched=0"
  echo "metaeditor_launched=0"
  echo "native_broker_orders=0"
  echo "external_broker_orders=0"
  echo "live_trading=FORBIDDEN"
  echo "risk_changed=0"
  echo "risk_ceiling_per_trade=1.00%"
  echo "decision_zone_min_r=1.00R"
  echo "universal_tp_sweep=0"
  echo "exact_mt5_pnl_claim=0"
  echo "aspirational_geo_month_target=15%_not_acceptance_override"
} > "$EVID"

MANIFEST="$ART/bundle_manifest_sha256.txt"
"$PY" - "$ART" "$MANIFEST" <<'PYMAN'
from pathlib import Path
import hashlib,sys
root=Path(sys.argv[1]); out=Path(sys.argv[2])
rows=[]
for p in sorted(root.iterdir(), key=lambda x:x.name):
    if not p.is_file() or p.name==out.name:
        continue
    h=hashlib.sha256(p.read_bytes()).hexdigest()
    rows.append(f"{h}  {p.name}")
out.write_text("\n".join(rows)+"\n",encoding="utf-8")
print(f"manifest files={len(rows)}")
PYMAN

"$PY" - "$ART" "$MANIFEST" <<'PYVERIFY'
from pathlib import Path
import hashlib,sys
root=Path(sys.argv[1]); manifest=Path(sys.argv[2])
for line in manifest.read_text(encoding="utf-8").splitlines():
    h,name=line.split("  ",1)
    p=root/name
    if not p.is_file():
        raise SystemExit(f"manifest missing file: {name}")
    got=hashlib.sha256(p.read_bytes()).hexdigest()
    if got!=h:
        raise SystemExit(f"manifest mismatch: {name}")
print("bundle_manifest_sha256.txt PASS")
PYVERIFY

ZIP="$OUT/v39_selective_harvest_stage_a.zip"
rm -f "$ZIP"
"$PY" - "$ART" "$ZIP" <<'PYZIP'
from pathlib import Path
import sys,zipfile
root=Path(sys.argv[1]); out=Path(sys.argv[2])
with zipfile.ZipFile(out,"w",zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in sorted(root.iterdir(), key=lambda x:x.name):
        if p.is_file():
            z.write(p,p.name)
PYZIP

ZIP_SHA="$(sha256sum "$ZIP"|awk '{print $1}')"
"$PY" - "$ZIP" <<'PYZIPVERIFY'
import sys,zipfile
z=sys.argv[1]
with zipfile.ZipFile(z) as f:
    bad=f.testzip()
    if bad:
        raise SystemExit(f"ZIP CRC failure: {bad}")
    names=set(f.namelist())
    if "bundle_manifest_sha256.txt" not in names or "V39_EVIDENCE.txt" not in names:
        raise SystemExit("ZIP evidence/manifest missing")
print("ZIP integrity PASS")
PYZIPVERIFY

say "V39 STAGE A DONE"
echo "STATUS=$STATUS"
echo "PRIMARY_LANE=$PRIMARY"
echo "This status is diagnostic only; it is NOT exact-MT5 PnL and does NOT authorize live trading."
echo "UPLOAD THIS ONE ZIP:"
cygpath -w "$ZIP"
echo "SHA256=$ZIP_SHA"
