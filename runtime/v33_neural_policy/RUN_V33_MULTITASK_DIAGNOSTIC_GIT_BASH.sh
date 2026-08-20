#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
REPO_ROOT="$(cd -- "$ROOT/../.." && pwd -P)"
OUT="$ROOT/OUTPUT_V33_MULTITASK"
LOG="$OUT/v33_multitask_runner.log"
SCRIPT="$REPO_ROOT/scripts/v33_multitask_policy_research.py"
EXTRACTOR="$REPO_ROOT/scripts/extract_v33_source_contract.py"
mkdir -p "$OUT"
exec > >(tee -a "$LOG") 2>&1
say(){ printf '\n[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"; }
die(){ echo "FATAL: $*" >&2; exit 1; }
trap 'rc=$?; echo "FAILED rc=$rc line=${BASH_LINENO[0]:-?} cmd=${BASH_COMMAND:-?}" >&2; exit $rc' ERR

for c in cygpath sha256sum; do command -v "$c" >/dev/null || die "Missing Git Bash command: $c"; done
[[ -s "$SCRIPT" ]] || die "V33 script missing: $SCRIPT"
[[ -s "$EXTRACTOR" ]] || die "V33 extractor missing: $EXTRACTOR"

V31_PY="$REPO_ROOT/runtime/v31_mt5_model_gate/OUTPUT_V31_1_MT5/.venv/Scripts/python.exe"
V33_VENV="$OUT/.venv"; V33_PY="$V33_VENV/Scripts/python.exe"; PY=""
if [[ -x "$V31_PY" ]] && "$V31_PY" - <<'PYCHK' >/dev/null 2>&1
import numpy,pandas,sklearn
assert numpy.__version__=='2.3.5'
assert pandas.__version__=='2.2.3'
assert sklearn.__version__=='1.8.0'
PYCHK
then
  PY="$V31_PY"; say "Reuse pinned V31/V32 Python environment"
else
  if command -v python >/dev/null 2>&1; then SYS_PY="$(command -v python)"; elif command -v python3 >/dev/null 2>&1; then SYS_PY="$(command -v python3)"; else die "Python 3 required"; fi
  if [[ ! -x "$V33_PY" ]]; then "$SYS_PY" -m venv "$V33_VENV"; fi
  if ! "$V33_PY" - <<'PYCHK' >/dev/null 2>&1
import numpy,pandas,sklearn
assert numpy.__version__=='2.3.5'
assert pandas.__version__=='2.2.3'
assert sklearn.__version__=='1.8.0'
PYCHK
  then
    say "Install pinned V33 diagnostic dependencies"
    "$V33_PY" -m pip install --disable-pip-version-check --upgrade pip
    "$V33_PY" -m pip install --disable-pip-version-check "numpy==2.3.5" "pandas==2.2.3" "scikit-learn==1.8.0"
  fi
  PY="$V33_PY"
fi
"$PY" -m py_compile "$SCRIPT" "$EXTRACTOR"

APPDATA_U="$(cygpath -u "$APPDATA")"
TERMINAL_ROOT="$APPDATA_U/MetaQuotes/Terminal"
COMMON="$TERMINAL_ROOT/Common/Files"
[[ -d "$COMMON/mt5_quant/runs" ]] || die "MT5 Common Files research runs missing: $COMMON"

PRED="$OUT/v33_multitask_predictions.csv"
SUMMARY="$OUT/v33_multitask_summary.json"
CONTRACT="$OUT/v33_v30_source_contract.txt"
say "Run causal V33 multi-task neural diagnostic — READ ONLY, no MT5 launch"
"$PY" "$SCRIPT" --common-files "$(cygpath -w "$COMMON")" --output "$(cygpath -w "$PRED")" --summary "$(cygpath -w "$SUMMARY")"
[[ -s "$PRED" && -s "$SUMMARY" ]] || die "V33 diagnostic outputs missing"

say "Extract bounded source contract needed for the exact-MT5 V33 policy builder"
"$PY" "$EXTRACTOR" --terminal-root "$(cygpath -w "$TERMINAL_ROOT")" --output "$(cygpath -w "$CONTRACT")"
[[ -s "$CONTRACT" ]] || die "V33 source contract missing"

ZIP="$OUT/v33_multitask_diagnostic.zip"
"$PY" - "$PRED" "$SUMMARY" "$CONTRACT" "$LOG" "$ZIP" <<'PYZIP'
import sys,zipfile,os
files=sys.argv[1:-1]; out=sys.argv[-1]
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in files:
        if os.path.isfile(p): z.write(p,os.path.basename(p))
PYZIP
[[ -s "$ZIP" ]] || die "V33 ZIP missing"
SHA="$(sha256sum "$ZIP"|awk '{print $1}')"
say "ALL DONE"
printf '\nUPLOAD THIS ONE ZIP:\n%s\nSHA256=%s\n' "$(cygpath -w "$ZIP")" "$SHA"
printf '\nThis step is offline/read-only: it does not launch MT5 or alter adaptive state. The source-contract snippet is included only to build the next tester-only policy lab safely.\n'
