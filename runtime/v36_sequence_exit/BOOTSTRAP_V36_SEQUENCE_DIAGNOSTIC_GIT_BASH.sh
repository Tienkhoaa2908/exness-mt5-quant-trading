#!/usr/bin/env bash
set +e

WORK="${WORK:-$HOME/v31_mt5_40usd}"
BRANCH="${BRANCH:-agent/v30-ml-dl-feature-lake}"
ROOT="$WORK/runtime/v36_sequence_exit"
OUT="$ROOT/OUTPUT_V36"
LOG="$HOME/v36_sequence_exit_bootstrap.log"
exec > >(tee -a "$LOG") 2>&1

echo "=== V36 TRUE INTRA-TRADE SEQUENCE DL — READ ONLY ==="
date
echo "No MT5 launch. No broker orders. No adaptive-state writes."
RC=0

if [[ ! -d "$WORK/.git" ]]; then
  echo "FATAL: expected repository at $WORK"
  RC=2
else
  git -C "$WORK" fetch origin "$BRANCH"; RC=$?
  [[ $RC -eq 0 ]] && git -C "$WORK" checkout -f "$BRANCH"; RC=$?
  [[ $RC -eq 0 ]] && git -C "$WORK" reset --hard "origin/$BRANCH"; RC=$?
fi

if [[ $RC -eq 0 ]]; then
  mkdir -p "$OUT"
  echo "HEAD=$(git -C "$WORK" rev-parse HEAD)"
  SCRIPT="$WORK/scripts/v36_sequence_exit_models.py"
  [[ -s "$SCRIPT" ]] || { echo "FATAL: V36 script missing"; RC=3; }
fi

if [[ $RC -eq 0 ]]; then
  V31_PY="$WORK/runtime/v31_mt5_model_gate/OUTPUT_V31_1_MT5/.venv/Scripts/python.exe"
  if [[ ! -x "$V31_PY" ]]; then
    echo "FATAL: pinned V31 Python environment missing: $V31_PY"
    RC=4
  else
    PY="$V31_PY"
  fi
fi

if [[ $RC -eq 0 ]]; then
  "$PY" - <<'PYCHECK'
import numpy,pandas,sklearn
assert numpy.__version__ == '2.3.5'
assert pandas.__version__ == '2.2.3'
assert sklearn.__version__ == '1.8.0'
PYCHECK
  RC=$?
fi

if [[ $RC -eq 0 ]]; then
  if ! "$PY" - <<'PYTORCH' >/dev/null 2>&1
import torch
assert tuple(int(x) for x in torch.__version__.split('+')[0].split('.')[:2]) >= (2, 8)
PYTORCH
  then
    echo "Installing pinned PyTorch CPU research dependency..."
    "$PY" -m pip install --disable-pip-version-check "torch==2.10.0"
    RC=$?
  else
    echo "PyTorch already available; install skipped."
  fi
fi

if [[ $RC -eq 0 ]]; then
  "$PY" -m py_compile "$SCRIPT"
  RC=$?
fi

if [[ $RC -eq 0 ]]; then
  APPDATA_U="$(cygpath -u "$APPDATA")"
  COMMON="$APPDATA_U/MetaQuotes/Terminal/Common/Files"
  CP="$WORK/runtime/v34_parallel_alpha/OUTPUT_V34_V35/checkpoints/v34_parallel_alpha"
  [[ -s "$CP/DONE.txt" && -s "$CP/SOURCE_RUN_FOLDER.txt" && -s "$CP/intra_trade_m15.csv" && -s "$CP/trades.csv" ]] || {
    echo "FATAL: accepted V34 checkpoint/telemetry missing: $CP"
    RC=5
  }
fi

if [[ $RC -eq 0 ]]; then
  V34_RUN="$(cat "$CP/SOURCE_RUN_FOLDER.txt")"
  [[ -d "$V34_RUN" && -s "$V34_RUN/intra_trade_m15.csv" && -s "$V34_RUN/trades.csv" ]] || {
    echo "FATAL: V34 Common Files run folder missing: $V34_RUN"
    RC=6
  }
fi

if [[ $RC -eq 0 ]]; then
  SUMMARY="$OUT/v36_sequence_summary.json"
  PREDS="$OUT/v36_sequence_predictions.csv"
  rm -f "$SUMMARY" "$PREDS"
  echo
  echo "Training chronological GRU48 / true-causal TCN48 / Transformer48x2..."
  echo "Source telemetry: $V34_RUN/intra_trade_m15.csv"
  "$PY" "$SCRIPT" \
    --common-files "$(cygpath -w "$COMMON")" \
    --v34-run-folder "$(cygpath -w "$V34_RUN")" \
    --book "norm10k_r0p5_continuous" \
    --summary "$(cygpath -w "$SUMMARY")" \
    --predictions "$(cygpath -w "$PREDS")" \
    --epochs 12 \
    --seq-len 32 \
    --sample-step 4
  RC=$?
fi

if [[ $RC -eq 0 ]]; then
  [[ -s "$SUMMARY" && -s "$PREDS" ]] || { echo "FATAL: V36 outputs missing"; RC=7; }
fi

if [[ $RC -eq 0 ]]; then
  ZIP="$OUT/v36_sequence_exit_diagnostic.zip"
  "$PY" - "$OUT" "$ZIP" <<'PYZIP'
import os,sys,zipfile
root,out=sys.argv[1],sys.argv[2]
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for name in ['v36_sequence_summary.json','v36_sequence_predictions.csv']:
        p=os.path.join(root,name)
        z.write(p,name)
PYZIP
  SHA="$(sha256sum "$ZIP" | awk '{print $1}')"
  echo
  echo "=== V36 DONE ==="
  echo "UPLOAD THIS ONE ZIP:"
  cygpath -w "$ZIP"
  echo "SHA256=$SHA"
fi

echo
echo "V36 rc=$RC"
echo "Bootstrap log: $LOG"
read -r -p "Press ENTER after copying the final status... " _
exit $RC
