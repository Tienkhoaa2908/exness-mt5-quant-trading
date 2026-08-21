#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
REPO_ROOT="$(cd -- "$ROOT/../.." && pwd -P)"
OUT="$ROOT/OUTPUT_V36_SEQUENCE_DL"; LOG="$OUT/v36_sequence_dl.log"; SCRIPT="$REPO_ROOT/scripts/v36_sequence_exit_models.py"
mkdir -p "$OUT"; exec > >(tee -a "$LOG") 2>&1
say(){ printf '\n[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"; }; die(){ echo "FATAL: $*" >&2; exit 1; }
trap 'rc=$?; echo "FAILED rc=$rc line=${BASH_LINENO[0]:-?} cmd=${BASH_COMMAND:-?}" >&2; exit $rc' ERR
for c in cygpath sha256sum;do command -v "$c" >/dev/null||die "missing $c";done
[[ -s "$SCRIPT" ]]||die "script missing"
VENV="$OUT/.venv"; PY="$VENV/Scripts/python.exe"
if command -v python >/dev/null 2>&1;then SYS="$(command -v python)";elif command -v python3 >/dev/null 2>&1;then SYS="$(command -v python3)";else die "Python 3 required";fi
[[ -x "$PY" ]]||"$SYS" -m venv "$VENV"

# V36 imports sklearn.metrics directly, and pandas Spearman correlation relies on
# the SciPy stack. Probe the COMPLETE runtime dependency set before training.
if ! "$PY" - <<'PYCHK' >/dev/null 2>&1
import numpy, pandas, torch, sklearn, scipy
from sklearn.metrics import roc_auc_score
PYCHK
then
 say "Repair V36 CPU deep-learning environment (reuse already-installed wheels/packages)"
 "$PY" -m pip install --disable-pip-version-check \
   "numpy==2.3.5" \
   "pandas==2.2.3" \
   "torch==2.7.1" \
   "scikit-learn==1.8.0"
fi

# Fail here with an explicit dependency error instead of several minutes into
# model training. This also records the exact runtime versions in the log.
"$PY" - <<'PYVERS'
import sys
import numpy, pandas, torch, sklearn, scipy
from sklearn.metrics import roc_auc_score
print("V36 Python", sys.version.split()[0])
print("V36 numpy", numpy.__version__)
print("V36 pandas", pandas.__version__)
print("V36 torch", torch.__version__)
print("V36 sklearn", sklearn.__version__)
print("V36 scipy", scipy.__version__)
PYVERS

"$PY" -m py_compile "$SCRIPT"
APPDATA_U="$(cygpath -u "$APPDATA")"; COMMON="$APPDATA_U/MetaQuotes/Terminal/Common/Files"
P="$REPO_ROOT/runtime/v34_parallel_alpha/OUTPUT_V34_V35/checkpoints/v34_parallel_alpha/SOURCE_RUN_FOLDER.txt"
[[ -s "$P" ]]||die "V34 exact-MT5 checkpoint missing. Run V34/V35 first."
RUN="$(cat "$P")"; [[ -s "$RUN/intra_trade_m15.csv" && -s "$RUN/trades.csv" ]]||die "V34 intra-trade telemetry missing: $RUN"
SUM="$OUT/v36_sequence_summary.json"; PRED="$OUT/v36_sequence_predictions.csv"
say "Train chronological GRU / causal TCN / Transformer exit-state models — diagnostic only"
"$PY" "$SCRIPT" --common-files "$(cygpath -w "$COMMON")" --v34-run-folder "$(cygpath -w "$RUN")" --summary "$(cygpath -w "$SUM")" --predictions "$(cygpath -w "$PRED")"
[[ -s "$SUM" && -s "$PRED" ]] || die "V36 training returned without required summary/predictions"
ZIP="$OUT/v36_sequence_exit_dl_diagnostic.zip"
"$PY" - "$SUM" "$PRED" "$LOG" "$ZIP" <<'PYZIP'
import sys,zipfile,os
*outfiles,out=sys.argv[1:]
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in outfiles:
  if os.path.isfile(p):z.write(p,os.path.basename(p))
PYZIP
SHA="$(sha256sum "$ZIP"|awk '{print $1}')";say "ALL DONE";printf '\nUPLOAD THIS ONE ZIP:\n%s\nSHA256=%s\n' "$(cygpath -w "$ZIP")" "$SHA"
printf '\nThis run is offline/read-only model research. It does not launch MT5 and is not PnL evidence.\n'
